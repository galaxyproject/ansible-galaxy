#!/usr/bin/env bash
# Run every tests/test_*.yml playbook against localhost and fail if any of them fails.
# Usage: tests/run.sh [test_name.yml ...]
set -u
cd "$(dirname "$0")"
mkdir -p roles
ln -sfn ../.. roles/galaxyproject.galaxy
export ANSIBLE_CONFIG="$PWD/ansible.cfg"
if [ $# -eq 0 ]; then set -- test_*.yml; fi
status=0
for t in "$@"; do
    [ "${GITHUB_ACTIONS:-}" = true ] && echo "::group::$t"
    ansible-playbook "$t" || { status=1; echo "FAILED: $t"; }
    [ "${GITHUB_ACTIONS:-}" = true ] && echo "::endgroup::"
done
exit $status
