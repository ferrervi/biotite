# Copyright 2017 Patrick Kunzmann.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.

from .matrix import SubstitutionMatrix
from ..sequence import Sequence
import numpy as np
import copy


class Alignment(object):
    
    def __init__(self, seq1, seq2, trace, score):
        self.seq1 = seq1
        self.seq2 = seq2
        self.trace = trace
        self.score = score
        
    def format_compact(self, line_length=72):
        str_seq1, str_seq2 = self.get_gapped_seq_strings()
        return str_seq1 + "\n" + str_seq2
    
    def format_detail(self, matrix, cutoff=0, line_length=72):
        str_seq1, str_seq2 = self.get_gapped_seq_strings()
        conservation = self.get_conservation_string(matrix, cutoff)
        i = 0
        string = ""
        # String contains 'line_length' symbols per line
        while i+line_length <= len(self.trace):
            string += str_seq1[i : i+line_length] + "\n"
            string += conservation[i : i+line_length] + "\n"
            string += str_seq2[i : i+line_length] + "\n"
            string += "\n"
            i += line_length
        # Add symbol remainder if present
        if i < len(self.trace):
            string += str_seq1[i:] + "\n"
            string += conservation[i:] + "\n"
            string += str_seq2[i:] + "\n"
            string += "\n"
        # Return string without terminal 'newlines'
        return string[:-2]
    
    def get_conservation_string(self, matrix, cutoff=0):
        seq_code1 = self.seq1.get_seq_code()
        seq_code2 = self.seq2.get_seq_code()
        conservation = ""
        for i in range(len(self.trace)):
            if self.trace[i,0] == -1 or self.trace[i,1] == -1:
                conservation += " "
            else:
                score = matrix.get_score_by_code(seq_code1[self.trace[i,0]],
                                                 seq_code2[self.trace[i,1]])
                if score >= cutoff:
                    conservation += "|"
                else:
                    conservation += "."
        return conservation
    
    def get_gapped_seq_strings(self):
        str_seq1 = ""
        str_seq2 = ""
        for e in range(len(self.trace)):
            i = self.trace[e,0]
            j = self.trace[e,1]
            if i != -1:
                str_seq1 += self.seq1[i]
            else:
                str_seq1 += "-"
            if j != -1:
                str_seq2 += self.seq2[j]
            else:
                str_seq2 += "-"
        return str_seq1, str_seq2
    
    def __str__(self):
        return self.format_compact()
    
    def __getitem__(self, index):
        if not isinstance(index, slice):
            raise TypeError("Alignments only support slice indexing")
        return Alignment(self.seq1, self.seq2, self.trace[index], self.score)


def simple_score(seq1, seq2, matrix):
    if len(seq1) != len(seq2):
        raise ValueError("Sequence lengths of {:d} and {:d} are not equal"
                         .format( len(seq1), len(seq2) ))
    if (matrix.alphabet1() != seq1.get_alphabet() and
        matrix.alphabet2() != seq2.get_alphabet()):
            raise ValueError("The sequences' alphabets do not fit the matrix")
    seq1_code = seq1.get_seq_code()
    seq2_code = seq1.get_seq_code()
    score = 0
    for i in range(len(seq1)):
        score += matrix.get_score_by_code(seq1_code[i], seq2_code[i])
    return score


def align_global(seq1, seq2, matrix, gap_opening=-3, gap_extension=-1):
    # This implementation uses transposed tables in comparison
    # to the original algorithm
    # Therefore the first sequence is one the left
    # and the second sequence is at the top  
    # The table for saving the scores
    score_table = np.zeros(( len(seq1)+1, len(seq2)+1 ), dtype="i4")
    # The table the directions a field came from
    # A "1" in the corresponding bit means
    # the field came from this direction
    # The values: bit 1 -> 1 -> diagonal -> alignment of symbols
    #             bit 2 -> 2 -> left     -> gap in first sequence
    #             bit 3 -> 4 -> top      -> gap in second sequence
    trace_table = np.zeros(( len(seq1)+1, len(seq2)+1 ), dtype="u1")
    score_table[:,0] = -np.arange(0, len(seq1)+1)
    score_table[0,:] = -np.arange(0, len(seq2)+1)
    trace_table[1:,0] = 4
    trace_table[0,1:] = 2
    code1 = seq1.get_seq_code()
    code2 = seq2.get_seq_code()
    
    # Fill table
    max_i = score_table.shape[0]
    max_j = score_table.shape[1]
    i = 1
    while i < max_i:
        j = 1
        while j < max_j:
            # Evaluate score from diagonal direction
            from_diag = score_table[i-1, j-1]
            # -1 is necessary due to the shift of the sequences
            # to the bottom/right in the table
            from_diag += matrix.get_score_by_code(code1[i-1], code2[j-1])
            # Evaluate score from left direction
            from_left = score_table[i, j-1]
            if trace_table[i, j-1] & 2:
                from_left += gap_extension
            else:
                from_left += gap_opening
            # Evaluate score from top direction
            from_top = score_table[i-1, j]
            if trace_table[i-1, j] & 2:
                from_top += gap_extension
            else:
                from_top += gap_opening
            # Find maximum
            trace, score = _eval_trace_from_score(from_diag,from_left,from_top)
            score_table[i,j] = score
            trace_table[i,j] = trace
            j +=1
        i += 1
    
    # Traceback
    i = max_i-1
    j = max_j-1
    max_score = score_table[i,j]
    trace = []
    trace_list = []
    _traceback(trace_table, i, j, trace, trace_list)
    trace_list = [np.flip(np.array(tr, dtype=int), axis=0)
                  for tr in trace_list]
    # Replace gap entries with -1
    for i, trace in enumerate(trace_list):
        gap_filter = np.zeros(trace.shape, dtype=bool)
        gap_filter[np.unique(trace[:,0], return_index=True)[1], 0] = True
        gap_filter[np.unique(trace[:,1], return_index=True)[1], 1] = True
        trace[~gap_filter] = -1
        trace_list[i] = trace
    
    return [Alignment(seq1, seq2, trace, max_score) for trace in trace_list]


def align_local(seq1, seq2, matrix, gap_opening=-3, gap_extension=-1):
    # Procedure is analogous to align_global()
    score_table = np.zeros(( len(seq1)+1, len(seq2)+1 ), dtype="i4")
    trace_table = np.zeros(( len(seq1)+1, len(seq2)+1 ), dtype="u1")
    code1 = seq1.get_seq_code()
    code2 = seq2.get_seq_code()
    
    # Fill table
    max_i = score_table.shape[0]
    max_j = score_table.shape[1]
    i = 1
    while i < max_i:
        j = 1
        while j < max_j:
            # Evaluate score from diagonal direction
            from_diag = score_table[i-1, j-1]
            from_diag += matrix.get_score_by_code(code1[i-1], code2[j-1])
            # Evaluate score from left direction
            from_left = score_table[i, j-1]
            if trace_table[i, j-1] & 2:
                from_left += gap_extension
            else:
                from_left += gap_opening
            # Evaluate score from top direction
            from_top = score_table[i-1, j]
            if trace_table[i-1, j] & 2:
                from_top += gap_extension
            else:
                from_top += gap_opening
            # Find maximum
            trace, score = _eval_trace_from_score(from_diag,from_left,from_top)
            # Local alignment specialty:
            # If score is less than or equal to 0,
            # then 0 is saved on the field and the trace ends here
            if score <= 0:
                score_table[i,j] = 0
            else:
                score_table[i,j] = score
                trace_table[i,j] = trace
            j +=1
        i += 1
    
    # Traceback
    # The start point is the maximal score in the table
    i, j = np.unravel_index(np.argmax(score_table), score_table.shape)
    max_score = score_table[i,j]
    trace = []
    trace_list = []
    _traceback(trace_table, i, j, trace, trace_list)
    trace_list = [np.flip(np.array(tr, dtype=int), axis=0)
                  for tr in trace_list]
    # Replace gap entries with -1
    for i, trace in enumerate(trace_list):
        gap_filter = np.zeros(trace.shape, dtype=bool)
        gap_filter[np.unique(trace[:,0], return_index=True)[1], 0] = True
        gap_filter[np.unique(trace[:,1], return_index=True)[1], 1] = True
        trace[~gap_filter] = -1
        trace_list[i] = trace
    
    return [Alignment(seq1, seq2, trace, max_score)
            for trace in trace_list]    


def _eval_trace_from_score(from_diag, from_left, from_top):
    if from_diag > from_left:
        if from_diag > from_top:
            return 1, from_diag
        elif from_diag == from_top:
            return 5, from_diag
        else:
            return 4, from_top
    elif from_diag == from_left:
        if from_diag > from_top:
            return 3, from_diag
        elif from_diag == from_top:
            return 7, from_diag
        else:
            return 4, from_top
    else:
        if from_left > from_top:
            return 2, from_left
        elif from_left == from_top:
            return 6, from_diag
        else:
            return 4, from_top


def _traceback(trace_table, i, j, trace, trace_list):
    while trace_table[i,j] != 0:
        # -1 is necessary due to the shift of the sequences
        # to the bottom/right in the table
        trace.append((i-1, j-1))
        # Traces may split
        next_indices = []
        trace_value = trace_table[i,j]
        if trace_value & 1:
            next_indices.append((i-1, j-1))
        if trace_value & 2:
            next_indices.append((i, j-1))
        if trace_value & 4:
            next_indices.append((i-1, j))
        # Trace split -> Recursive call of _traceback() for indices[1:]
        for k in range(1, len(next_indices)):
            new_i, new_j = next_indices[k]
            _traceback(trace_table, new_i, new_j, copy.copy(trace), trace_list)
        # Continue in this method with indices[0]
        i, j = next_indices[0]
    trace_list.append(trace)