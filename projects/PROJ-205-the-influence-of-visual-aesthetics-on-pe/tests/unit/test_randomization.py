"""
Unit tests for Latin Square randomization logic.

This module verifies that the hardcoded sequences in code/survey/constants.py
form a valid balanced Latin Square.

A balanced Latin Square of order N ensures:
1. Each stimulus appears exactly once in each position (row validity).
2. Each stimulus appears exactly once in each column (column validity).
3. Each stimulus follows every other stimulus exactly once (or as balanced as possible for even N)
   across the set of sequences.
"""
import pytest
import sys
import os

# Add project root to path to allow imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from code.survey.constants import LATIN_SQUARE_MATRIX, STIMULI_LIST

def test_latin_square_dimensions():
    """Verify the matrix has the correct dimensions (N x N)."""
    n = len(STIMULI_LIST)
    assert len(LATIN_SQUARE_MATRIX) == n, f"Matrix must have {n} rows, got {len(LATIN_SQUARE_MATRIX)}"
    for i, row in enumerate(LATIN_SQUARE_MATRIX):
        assert len(row) == n, f"Row {i} must have {n} elements, got {len(row)}"

def test_row_uniqueness():
    """Verify each row contains every stimulus exactly once."""
    n = len(STIMULI_LIST)
    for i, row in enumerate(LATIN_SQUARE_MATRIX):
        assert sorted(row) == sorted(STIMULI_LIST), \
            f"Row {i} does not contain all stimuli exactly once. Found: {row}"

def test_column_uniqueness():
    """Verify each column contains every stimulus exactly once."""
    n = len(STIMULI_LIST)
    for col_idx in range(n):
        column = [row[col_idx] for row in LATIN_SQUARE_MATRIX]
        assert sorted(column) == sorted(STIMULI_LIST), \
            f"Column {col_idx} does not contain all stimuli exactly once. Found: {column}"

def test_balanced_succession():
    """
    Verify that each stimulus follows every other stimulus an equal number of times.
    For a 4x4 Latin Square, each stimulus should follow every other stimulus exactly once.
    Note: In a standard Latin Square, immediate succession balance is not guaranteed,
    but for a *balanced* Latin Square designed for this study, we expect it.
    """
    n = len(STIMULI_LIST)
    # Count transitions: (stimulus_a, stimulus_b) -> count
    transitions = {}
    
    for row in LATIN_SQUARE_MATRIX:
        for i in range(len(row) - 1):
            a = row[i]
            b = row[i + 1]
            key = (a, b)
            transitions[key] = transitions.get(key, 0) + 1
    
    # Check that each stimulus follows every other stimulus exactly once
    # (excluding self-follows, which shouldn't happen in a Latin Square)
    for stimulus_a in STIMULI_LIST:
        for stimulus_b in STIMULI_LIST:
            if stimulus_a != stimulus_b:
                count = transitions.get((stimulus_a, stimulus_b), 0)
                # For a 4x4 balanced Latin Square, each pair should appear exactly once
                assert count == 1, \
                    f"Stimulus {stimulus_b} follows {stimulus_a} {count} times, expected 1"

def test_all_stimuli_defined():
    """Ensure all stimuli in the matrix are defined in STIMULI_LIST."""
    for row in LATIN_SQUARE_MATRIX:
        for stimulus in row:
            assert stimulus in STIMULI_LIST, f"Unknown stimulus '{stimulus}' found in matrix"