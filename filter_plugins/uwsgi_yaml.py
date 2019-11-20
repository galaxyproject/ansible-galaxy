from __future__ import absolute_import

import yaml

from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types
from ansible.plugins.filter.core import to_nice_yaml


def _strip_quotes(item):
    # uWSGI internal parser treats everything as a string and doesn't understand quoting
    k, v = item.split(': ', 1)
    return ': '.join((k, v.strip('"\'\n') + '\n'))


def _iter_values(k, v):
    # Iterator yielding subvalues in uWSGI internal YAML format
    if (k.startswith('if-') or k == 'for'):
        # First item in v is the conditional value, remainder is the logic block contents and should consist of
        # option/value pairs (values can be lists just as in options outside blocks)
        if not isinstance(v, list):
            raise AnsibleError(
                "to_uwsgi_yaml value of '%s' must be a list (is type: %s, value: %s)" % (k, type(v), str(v)))
        vi = iter(v)
        yield {k: next(vi)}
        for i in vi:
            # Recurse for logic block members containing lists
            for _i in _iter_values(*(list(i.items())[0])):
                yield _i
        yield {'end' + k.split('-', 1)[0]: 'null'}
    elif isinstance(v, list):
        # Write each member out with the parent key
        for i in v:
            yield {k: i}
    elif isinstance(v, string_types) or isinstance(v, bool) or isinstance(v, int) or isinstance(v, float):
        yield {k: v}
    else:
        raise AnsibleError(
            "|to_uwsgi_yaml value type of '%s' unrecognized (is type: %s, value: %s)" % (k, type(v), str(v)))


def _iter_options(a):
    # Iterator returning tuples from either a hash or list where members are one-pair hashes
    if isinstance(a, dict):
        for k in sorted(a.keys()):
            yield (k, a[k])
    elif isinstance(a, list):
        for i in a:
            yield list(i.items())[0]
    else:
        raise AnsibleError(
            "|to_uwsgi_yaml value must be a dictionary (hash) or list (is type: %s, value: %s)" % (type(a), str(a)))


def to_uwsgi_yaml(a, indent=4, width=9999, *args, **kwargs):
    # uWSGI's internal YAML parser is not real YAML - all values are expected to be strings, and lists are created by
    # repeating keys
    if not isinstance(a, dict):
        raise AnsibleError("|to_uwsgi_yaml expects a dictionary (hash)")
    r = []
    for pk, pv in a.items():
        r.append(pk)
        items = []
        for k, v in _iter_options(pv):
            for d in _iter_values(k, v):
                items.append(_strip_quotes(to_nice_yaml(d, indent=indent, width=width, *args, **kwargs)))
        r.append((' ' * indent).join(items))
    return (':\n' + ' ' * indent).join(r)


class FilterModule(object):
    def filters(self):
        return {
            'to_uwsgi_yaml': to_uwsgi_yaml,
        }
