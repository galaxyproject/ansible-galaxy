from __future__ import absolute_import

import yaml

from ansible.errors import AnsibleError
from ansible.plugins.filter.core import to_nice_yaml


def _strip_quotes(item):
    # uWSGI internal parser treats everything as a string and doesn't understand quoting
    k, v = item.split(': ', 1)
    return ': '.join((k, v.strip('"\'\n') + '\n'))


def to_uwsgi_yaml(a, indent=4, *args, **kwargs):
    # uWSGI's internal YAML parser is not real YAML - all values are expected to be strings, and lists are created by
    # repeating keys
    if not isinstance(a, dict):
        raise AnsibleError("|to_uwsgi_yaml expects a dictionary")
    r = []
    for pk, pv in a.items():
        r.append(pk)
        items = []
        for k, v in pv.items():
            if isinstance(v, list):
                for i in v:
                    items.append(_strip_quotes(to_nice_yaml({k: i}, indent=indent, *args, **kwargs)))
            else:
                items.append(_strip_quotes(to_nice_yaml({k: v}, indent=indent, *args, **kwargs)))
        r.append((' ' * indent).join(items))
    return (':\n' + ' ' * indent).join(r)


class FilterModule(object):
    def filters(self):
        return {
            'to_uwsgi_yaml': to_uwsgi_yaml,
        }
