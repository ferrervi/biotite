# Copyright 2017 Patrick Kunzmann.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.

import unittest
import biopython.sequence as seq
import numpy as np
import pytest


def test_encoding():
    string1 = "AATGCGTTA"
    dna = seq.NucleotideSequence(string1)
    string2 = str(dna)
    assert string1 == string2

def test_validity_check():
    dna = seq.NucleotideSequence()
    dna.code = np.array([0,1,0,3,3])
    assert dna.is_valid()
    dna.code = np.array([0,1,4,3,3])
    assert not dna.is_valid()
    
def test_access():
    string = "AATGCGTTA"
    dna = seq.NucleotideSequence(string)
    assert string[2] == dna[2]
    assert string == "".join([symbol for symbol in dna])
    dna[-1] = "C"
    assert "AATGCGTTC" == str(dna)
    dna = dna[3:-2]
    assert "GCGT" == str(dna)

def test_concatenation():
    str1 = "AAGTTA"
    str2 = "CGA"
    str3 = "NNN"
    concat_seq = seq.NucleotideSequence(str1) + seq.NucleotideSequence(str2)
    assert str1 + str2 == str(concat_seq)
    concat_seq = seq.NucleotideSequence(str1) + seq.NucleotideSequence(str3)
    assert str1 + str3 == str(concat_seq)
    concat_seq = seq.NucleotideSequence(str3) + seq.NucleotideSequence(str1)
    assert str3 + str1 == str(concat_seq)
    
def test_alph_error():
    string = "AATGCGTUTA"
    with pytest.raises(seq.AlphabetError):
        seq.NucleotideSequence(string)

def test_alphabet_extension():
    alph1 = seq.Alphabet("abc")
    alph2 = seq.Alphabet("abc")
    alph3 = seq.Alphabet("acb")
    alph4 = seq.Alphabet("abcde")
    assert alph1.extends(alph1)
    assert alph2.extends(alph1)
    assert not alph3.extends(alph1)
    assert alph4.extends(alph1)
    assert not alph1.extends(alph4)