import unittest

from filter_plugins import seqtodict


class TestSeqToDictFilter(unittest.TestCase):

    def test_transform_one_sequence(self):
        input = '''
            a: v1 
            b: v2
            foo:
                - c: v3
                - c: v3
            d: v4
        '''

        expected = '''
            a: v1 
            b: v2
            c: v3
            c: v3
            d: v4
        '''

        result = seqtodict.seqtodict(input, 'foo')
        self.assertEqual(result, expected)

    def test_transform_two_sequence(self):
        input = '''
            a: v1 
            b: v2
            foo:
                - c: v3
                - c: v3
            d: 
                foo:
                    - e: v4
                    - e: v5
                f: v6
        '''

        expected = '''
            a: v1 
            b: v2
            c: v3
            c: v3
            d: 
                e: v4
                e: v5
                f: v6
        '''

        result = seqtodict.seqtodict(input, 'foo')
        self.assertEqual(result, expected)

    def test_ignore_whitespace(self):
        input = '''
            a: v1 
            b: v2
            foo:

                -  c: v3

                - c :  v3

            d: v4
        '''

        expected = '''
            a: v1 
            b: v2

            c: v3

            c :  v3

            d: v4
        '''

        result = seqtodict.seqtodict(input, 'foo')
        self.assertEqual(result, expected)
