#!/usr/bin/python
"""Ansible module that clones a directory tree using symlinks.

Clone a directory tree using symlinks. Creates the target directory if it does
not exist, otherwise merges the source tree with the target directory tree.
Only files are symlinked; subdirectories within the target directory are
created as normal directories.

Permissions and ownership of the target directory and its subdirectories can
be set using the standard file attributes of Ansible. This does not affect the
symlinked files, which retain their original permissions and ownership.

For example, if the source directory looks like

```
source/
├── dir1
│   ├── file1.txt
│   └── file2.txt
└── dir2
```

then after running the module, the target directory will look like

```
target/
├── dir1
│   ├── file1.txt -> /absolute/path/to/source/dir1/file1.txt
│   └── file2.txt -> /absolute/path/to/source/dir1/file2.txt
└── dir2
```
"""
from __future__ import annotations

import filecmp
import grp
import os
import pwd
import shutil
import tempfile
from pathlib import Path

from ansible.module_utils.basic import AnsibleModule


def merge_using_symlinks(src: Path, dst: Path) -> None:
    """Merge a directory tree with a target directory using symlinks.

    Creates the target directory if it does not exist. Only files are
    symlinked; directories are created as normal directories. Existing files
    in the target directory (or any of its subdirectories) are replaced,
    as well as symlinks to directories.
    """
    for root, dirs, files in os.walk(src):
        root = Path(root)
        dirs = [Path(d) for d in dirs]
        files = [Path(f) for f in files]

        rel_path = root.relative_to(src)
        dst_dir = dst / rel_path
        if not dst_dir.exists():
            dst_dir.mkdir()
            shutil.copystat(root, dst_dir)

        for name in dirs + files:
            src_path = root / name
            dst_path = dst_dir / name
            if src_path.is_dir():
                if dst_path.is_symlink():
                    dst_path.unlink()
                if not dst_path.exists():
                    dst_path.mkdir()
                    shutil.copystat(src_path, dst_path)
            else:
                if dst_path.exists():
                    dst_path.unlink()
                dst_path.symlink_to(src_path.absolute())


def compare_permissions(src: Path, dest: Path) -> bool:
    """Compare permissions of a source and destination directory tree.

    Compares permissions, ownership, and type (file or directory) of all
    contents of the source directory tree with the ones in the destination
    directory tree. Extra files in the destination directory are ignored.
    """
    for root, dirs, files in os.walk(src, followlinks=False):
        root = Path(root)
        dirs = [Path(d) for d in dirs]
        files = [Path(f) for f in files]

        for name in [root] + dirs + files:
            src_path = root / name if name != root else root
            dst_path = dest / src_path.relative_to(src)

            if src_path.is_symlink() or dst_path.is_symlink():
                continue

            src_stat = src_path.lstat()
            dst_stat = dst_path.lstat()
            if src_path.is_dir() != dst_path.is_dir():
                return True
            if src_stat.st_mode != dst_stat.st_mode:
                return True
            if src_stat.st_uid != dst_stat.st_uid:
                return True
            if src_stat.st_gid != dst_stat.st_gid:
                return True

    return False


def set_permissions(
    path: Path, owner: int | None, group: int | None, mode: int | None
) -> None:
    """Set permissions on a directory recursively, ignoring symlinks.

    Ignores executable bits for files.

    Warning: This function does not handle SELinux contexts or extended
             attributes.
    """
    for root, dirs, files in os.walk(path, followlinks=False):
        root = Path(root)
        dirs = [Path(d) for d in dirs]
        files = [Path(f) for f in files]

        for name in [root] + dirs + files:
            path = root / name if name != root else root
            if path.is_symlink():
                continue
            if mode is not None:
                if path.is_file():
                    path.chmod(
                        mode & ~0o111
                    )  # remove executable bits for files
                else:
                    path.chmod(mode)
            if owner is not None or group is not None:
                os.chown(
                    path,
                    owner if owner is not None else -1,
                    group if group is not None else -1,
                )


def run_module():
    """Run the Ansible module."""
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(type="path", required=True),
            path=dict(type="path", required=True, aliases=["dest", "name"]),
            state=dict(
                type="str",
                required=False,
                choices=["directory"],
                default="directory",
            ),
        ),
        add_file_common_args=True,
        supports_check_mode=False,
    )

    # load common file arguments
    file_args = module.load_file_common_arguments(
        module.params, path=module.params["path"]
    )
    module.params.update(file_args)

    path_info = module.add_path_info(dict(path=module.params["path"]))
    result = {
        "changed": False,
        "src": module.params["src"],
        **path_info,
        "diff": {
            "before": {**path_info},
            "after": {**path_info},
        },
    }

    # validate source
    source = Path(module.params["src"])
    if source.exists() and not source.is_dir():
        module.fail_json(
            msg=f"{source} exists but it is not a directory", **result
        )
    elif not source.exists():
        module.fail_json(
            msg=f"source directory {source} does not exist", **result
        )

    # validate target
    path = Path(module.params["path"])
    if not path.parent.exists():
        module.fail_json(
            msg=f"parent directory {path.parent} does not exist", **result
        )
    if path.exists() and not path.is_dir():
        module.fail_json(msg=f"{path} exists and is not a directory", **result)

    source = Path(module.params["src"])
    target = Path(module.params["path"])
    # determine if anything will change after merging
    with tempfile.TemporaryDirectory(
        dir=path.parent, prefix=".ansible_tmp_"
    ) as temp_dir:
        temp_path = Path(temp_dir)

        # clone using symlinks
        merge_using_symlinks(source, temp_path)
        mode = (
            int(module.params["mode"], 8)
            if not isinstance(module.params["mode"], int)
            else module.params["mode"]
        )
        owner = (
            module.params["owner"]
            if isinstance(module.params["owner"], int)
            else pwd.getpwnam(module.params["owner"]).pw_uid
        )
        group = (
            module.params["group"]
            if isinstance(module.params["group"], int)
            else grp.getgrnam(module.params["group"]).gr_gid
        )
        if mode is not None or owner is not None or group is not None:
            set_permissions(temp_path, owner=owner, group=group, mode=mode)

        # determine if anything was changed
        if target.exists():
            comparison = filecmp.dircmp(temp_path, target)
            permissions = compare_permissions(temp_path, target)
            changed = bool(
                comparison.left_only
                # or comparison.right_only  # target contain have extra files
                or comparison.diff_files
                or comparison.funny_files
                or permissions
            )
        else:
            changed = True
    # merge source with target if anything changed
    if changed:
        merge_using_symlinks(source, target)
        mode = (
            int(module.params["mode"], 8)
            if not isinstance(module.params["mode"], int)
            else module.params["mode"]
        )
        owner = (
            module.params["owner"]
            if isinstance(module.params["owner"], int)
            else pwd.getpwnam(module.params["owner"]).pw_uid
        )
        group = (
            module.params["group"]
            if isinstance(module.params["group"], int)
            else grp.getgrnam(module.params["group"]).gr_gid
        )
        if mode is not None or owner is not None or group is not None:
            set_permissions(target, owner=owner, group=group, mode=mode)
        result["changed"] = True

    path_info = module.add_path_info(dict(path=module.params["path"]))
    result.update(path_info)
    result["diff"]["after"].update(path_info)

    # adjust attributes
    result["changed"] = module.set_fs_attributes_if_different(
        file_args, changed=result["changed"], diff=result["diff"]
    )
    path_info = module.add_path_info(dict(path=module.params["path"]))
    result.update(path_info)
    result["diff"]["after"].update(path_info)

    module.exit_json(**result)


if __name__ == "__main__":
    run_module()
