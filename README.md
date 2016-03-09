Galaxy
======

An [Ansible][ansible] role for installing and managing [Galaxy][galaxyproject]
servers.  Despite the name confusion, [Galaxy][galaxyproject] bears no relation
to [Ansible Galaxy][ansiblegalaxy].

[ansible]: http://www.ansible.com/
[galaxyproject]: https://galaxyproject.org/
[ansiblegalaxy]: https://galaxy.ansible.com/

Requirements
------------

This role has the same dependencies as the VCS module in use, namely
[Mercurial][hg] if using `hg` or [Git][git] if using `git`.  In addition,
[Python virtualenv][venv] is required (as is [pip][pip], but pip will
automatically installed with virtualenv). These can easily be installed via a
pre-task in the same play as this role:

    - hosts: galaxyservers
        pre_tasks:
          - name: Install Mercurial
            apt: pkg={{ item }} state=installed
            sudo: yes
            when: ansible_os_family = 'Debian'
            with_items:
              - mercurial
              - python-virtualenv
          - name: Install Mercurial
            yum: pkg={{ item }} state=installed
            sudo: yes
            when: ansible_os_family = 'RedHat'
            with_items:
              - mercurial
              - python-virtualenv
        roles:
          - galaxy

If your `hg` executable is not on `$PATH`, you can specify its location with
the `hg_executable` variable. Likewise with the `virtualenv` executable and
corresponding `pip_virtualenv_command` variable.

[hg]: http://mercurial.selenic.com/
[git]: http://git-scm.com/
[venv]: http://virtualenv.readthedocs.org/
[pip]: http://pip.readthedocs.org/

Role Variables
--------------

### Required variables ###

- `galaxy_server_dir`: Filesystem path where the Galaxy server code will be
  installed (cloned).

### Optional variables ###

Several variables control which functions this role will perform (all default
to `yes`):

- `galaxy_manage_clone`: Clone Galaxy from the source repository and maintain
  it at a specified version (changeset), as well as set up a
  [virtualenv][virtualenv] from which it can be run.
    - `galaxy_vcs` (default: `hg`): Choose between cloning using Mercurial or
      Git. Options are `hg` or `git`. If you choose git, be sure to change
      `galaxy_changeset_id` from the default value of `stable` to a ref that
      exists in the git repository (e.g. `master`).
- `galaxy_manage_static_setup`: Manage "static" Galaxy configuration files -
  ones which are not modifiable by the Galaxy server itself. At a minimum, this
  is the primary Galaxy configuration file, `galaxy.ini`.
- `galaxy_manage_mutable_setup`: Manage "mutable" Galaxy configuration files -
  ones which are modifiable by Galaxy (e.g. as you install tools from the
  Galaxy Tool Shed).
- `galaxy_manage_database`: Upgrade the database schema as necessary, when new
  schema versions become available.
- `galaxy_fetch_dependencies`: Fetch Galaxy dependent modules to the Galaxy
  virtualenv.

You can control various things about where you get Galaxy from, what version
you use, and where its configuration files will be placed:

- `galaxy_repo` (default: `https://bitbucket.org/galaxy/galaxy-dist`): Upstream
  Mercurial repository from which Galaxy should be cloned.
- `galaxy_git_repo` (default: `https://github.com/galaxyproject/galaxy.git`):
  Upstream Git repository from which Galaxy should be cloned.
- `galaxy_changeset_id` (default: `stable`): A changeset id, tag, branch, or
  other valid Git or Mercurial identifier for which changeset Galaxy should be
  updated to. Specifying a branch will update to the latest changeset on that
  branch. A debugging message will notify you if the current changeset of your
  Galaxy server is different from this value. There is no harm in this, but:
    - if this annoys you, you must use a full (long) changeset hash to prevent
      that task from reporting **changed** on every run, and
    - using a real changeset hash is the only way to explicitly lock Galaxy at
      a specific version.
- `galaxy_force_checkout` (default: `no`): If `yes`, any modified files in the
  Galaxy repository will be discarded.
- `galaxy_requirements_file` (default:
  `<galaxy_server_dir>/lib/galaxy/dependencies/pinned-requirements.txt`): The
  Python `requirements.txt` file that should be used to install Galaxy
  dependent modules using pip.
- `galaxy_venv_dir` (default: `<galaxy_server_dir>/.venv`): The role will
  create a [virtualenv][virtualenv] from which Galaxy will run, this controls
  where the virtualenv will be placed.
- `galaxy_config_dir` (default: `<galaxy_server_dir>`): Directory that will be
  used for "static" configuration files.
- `galaxy_mutable_config_dir` (default: `<galaxy_server_dir>`): Directory that
  will be used for "mutable" configuration files, must be writable by the user
  running Galaxy.
- `galaxy_mutable_data_dir` (default: `<galaxy_server_dir>/database`):
  Directory that will be used for "mutable" data and caches, must be writable
  by the user running Galaxy.
- `galaxy_config_file` (default: `<galaxy_config_dir>/galaxy.ini`):
  Galaxy's primary configuration file.
- `galaxy_shed_tool_conf_file` (default:
  `<galaxy_mutable_config_dir>/shed_tool_conf.xml`): Configuration file for
  tools installed from the Galaxy Tool Shed.
- `galaxy_config`: The contents of the Galaxy configuration file
  (`galaxy.ini` by default) are controlled by this variable. It is a hash of
  hashes (or dictionaries) that will be translated in to the configuration
  file. See the Example Playbooks below for usage.
- `galaxy_config_files`: List of hashes (with `src` and `dest` keys) of files
  to copy from the control machine.
- `galaxy_config_templates`: List of hashes (with `src` and `dest` keys) of
  templates to fill from the control machine.
- `galaxy_admin_email_to`: If set, email this address when Galaxy has been
  updated. Assumes mail is properly configured on the managed host.
- `galaxy_admin_email_from`: Address to send the aforementioned email from.

Dependencies
------------

None

Example Playbook
----------------

Install Galaxy on your local system with all the default options:

    - hosts: localhost
      vars:
        galaxy_server_dir: /home/nate/galaxy-dist
      connection: local
      roles:
         - galaxy

Once installed, you can start with:

    % cd /home/nate/galaxy-dist
    % python ./scripts/paster.py serve universe_wsgi.ini

Install Galaxy with the clone and configs owned by a different user than the
user running Galaxy, and backed by PostgreSQL, on the hosts in the
`galaxyservers` group in your inventory:

    - hosts: galaxyservers
      vars:
        galaxy_server_dir: /opt/galaxy/server
        galaxy_config_dir: /opt/galaxy/config
        galaxy_mutable_config_dir: /var/opt/galaxy/config
        galaxy_mutable_data_dir: /var/opt/galaxy/data
        galaxy_repo: https://bitbucket.org/galaxy/galaxy-central/
        galaxy_changeset_id: tip
        postgresql_objects_users:
          - name: galaxy
            password: null
        postgresql_objects_databases:
          - name: galaxy
            owner: galaxy
        galaxy_config:
          "server:main":
            host: 0.0.0.0
          "app:main":
            database_connection: "postgresql:///galaxy?host=/var/run/postgresql"
        pkg_module: '{{ "yum" if ansible_os_family == "RedHat" else "apt" }}'
      pre_tasks:
        - name: Create Galaxy code owner user
          user: name=gxcode comment="Galaxy Code" system=yes home=/opt/galaxy createhome=yes
          sudo: yes
        - name: Create Galaxy runtime user
          user: name=galaxy comment="Galaxy Server" system=yes home=/var/opt/galaxy createhome=yes
          sudo: yes
        - name: Install Mercurial
          action: '{{ pkg_module }} pkg=mercurial state=installed'
          sudo: yes
        - name: Install virtualenv
          action: '{{ pkg_module }} pkg=python-virtualenv state=installed'
          sudo: yes
        - name: Install psycopg2
          action: '{{ pkg_module }} pkg=python-psycopg2 state=installed'
          sudo: yes
        # Precreating the mutable config directory may be necessary (it's not in
        # our example since we set the user's home directory to
        # galaxy_mutable_config_dir's parent).
        #- name: Create mutable configuration file directory
        #  file: state=directory path={{ galaxy_mutable_config_dir }} owner=galaxy
        #  sudo: yes
      roles:
        # Install with:
        #   % ansible-galaxy install zzet.postgresql
        - zzet.postgresql
        # Install with:
        #   % ansible-galaxy install natefoo.postgresql_objects
        - role: natefoo.postgresql_objects
          sudo: yes
          sudo_user: postgres
        - role: galaxy
          sudo: yes
          sudo_user: gxcode
          galaxy_manage_mutable_setup: no
          galaxy_manage_database: no
        - role: galaxy
          sudo: yes
          sudo_user: galaxy
          galaxy_manage_clone: no
          galaxy_manage_static_setup: no

License
-------

[Academic Free License ("AFL") v. 3.0][afl]

[afl]: http://opensource.org/licenses/AFL-3.0

Author Information
------------------

This role was written and contributed to by the following people:

[Enis Afgan](https://github.com/afgane)  
[Dannon Baker](https://github.com/dannon)  
[Simon Belluzzo](https://github.com/simonalpha)  
[John Chilton](https://github.com/jmchilton)  
[Nate Coraor](https://github.com/natefoo)  
