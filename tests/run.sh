#!/usr/bin/env bash
# Run every tests/test_*.yml playbook against localhost and fail if any of them fails.
# Usage: tests/run.sh [test_name.yml ...]
set -eu
cd "$(dirname "$0")"
# Like Molecule, link the role in as galaxyproject.galaxy from outside the repository, so there is no
# tests/roles for ansible-lint to follow into the whole role.
roles_path=$(mktemp -d)
trap 'rm -rf "$roles_path"' EXIT
ln -s "$(cd .. && pwd)" "$roles_path/galaxyproject.galaxy"
export ANSIBLE_ROLES_PATH="$roles_path"
export ANSIBLE_CONFIG="$PWD/ansible.cfg"
if [ $# -eq 0 ]; then set -- test_*.yml; fi
status=0
for t in "$@"; do
    [ "${GITHUB_ACTIONS:-}" = true ] && echo "::group::$t"
    ansible-playbook "$t" || { status=1; echo "FAILED: $t"; }
    [ "${GITHUB_ACTIONS:-}" = true ] && echo "::endgroup::"
done
exit $status
