import re

from ansible.errors import AnsibleFilterError


def seqtodict(yaml_string, seq_key):
    '''Transforms sequence of YAML-formatted key-value pairs to dictionary.
    
    This Ansible plugin transforms all instances of sequences under seq_key:
    1. "flattens" sequence moving its items one level up (to same level as seq_key)
    2. removes seq_key
    
    Purpose: solves problem of duplicate keys that are illegal in YAML (and
    Ansible) but are sometimes used in uWSGI YAML-style congifuration.

    Args:
        yaml_string: YAML-formatted unicode string. 
        seq_key: dictionary key whose value is a sequence.

    Returns:
        YAML-formatted unicode string. 
        For example:

            [variables]
            my_config:
              foo: some-value 
              bar:
                - baz: some-value
                - baz: some-value
                - baz: some-value
            
            [template]
            {{ my_config | to_nice_yaml | seqtodict('baz') }}

            [output file]
            my_config:
              foo: some-value
              baz: some-value
              baz: some-value
              baz: some-value

    Raises: 
        AnsibleFilterError: error due to illegal/incomplete arguments.
    '''

    DELETE_MARKER = '#DELETE-ME#'

    #check type: str (Python 3) or unicode (Python 2)
    if not (isinstance(yaml_string, str) or isinstance(yaml_string, unicode)):
        raise AnsibleFilterError('seqtodict expects a string')
    if seq_key is None or seq_key == '':
        raise AnsibleFilterError('seq_key cannot be empty')

    seq_key = seq_key.strip() #strip unnecessary whitespace

    #regex for sequence element search
    r_whitespace = re.compile('^\s*$')
    r_element = re.compile('^\s*-\s*(\w+)\s*')

    lines = yaml_string.split('\n') 

    #look for sequences
    r_seq = re.compile('^\s*{}\s*:\s*$'.format(seq_key))
    for i, line in enumerate(lines):
        if r_seq.match(line):
            lws = line[:line.index(seq_key)] #get leading whitespace
            lines[i] = DELETE_MARKER #mark line for deletion 
            _reformat_seq_items(lines, i+1, r_whitespace, r_element, lws)

    lines = [line for line in lines if line != DELETE_MARKER] #remove marked elements
    return '\n'.join(lines) 


def _reformat_seq_items(lines, start, r_whitespace, r_element, lws):
    for i in range(start, len(lines)):
        line = lines[i]
        if r_element.match(line):
            element = r_element.match(line).groups()[0] #extract 'foo' from ' - foo '
            element_index = line.index(element)
            lines[i] = lws + line[element_index:]
        elif r_whitespace.match(line):
            continue #ignore whitespace
        else:
            break #found end of sequence


class FilterModule(object):
    def filters(self):
        return {
            'seqtodict': seqtodict,
        }
