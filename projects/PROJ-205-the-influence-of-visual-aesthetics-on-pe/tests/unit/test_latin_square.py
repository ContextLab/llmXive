"""
Unit tests for Latin Square selection logic (T016b).
"""
import pytest
import uuid
from code.survey.constants import LATIN_SQUARE_MATRIX

def test_latin_square_balance():
    """
    Verify that the Latin Square matrix is balanced.
    Every stimulus must appear exactly once in each position (column) across all rows.
    """
    stimuli = ["Professional", "Minimalist", "Low-Quality", "Neutral"]
    n_conditions = len(stimuli)
    n_rows = len(LATIN_SQUARE_MATRIX)
    
    # Check row count
    assert n_rows == n_conditions, "Number of rows must equal number of conditions"
    
    # Check each column
    for col_idx in range(n_conditions):
        seen_stimuli = []
        for row_idx in range(n_rows):
            stimulus = LATIN_SQUARE_MATRIX[row_idx][col_idx]
            seen_stimuli.append(stimulus)
        
        # Each stimulus must appear exactly once in this column
        assert sorted(seen_stimuli) == sorted(stimuli), f"Column {col_idx} is not balanced: {seen_stimuli}"

def test_latin_square_uniqueness():
    """
    Verify that each row is a unique permutation.
    """
    rows_as_tuples = [tuple(row) for row in LATIN_SQUARE_MATRIX]
    assert len(rows_as_tuples) == len(set(rows_as_tuples)), "All rows must be unique"

def test_selection_logic():
    """
    Verify that the selection logic (hash % 4) produces a valid row index.
    """
    # Generate a few random UUIDs and verify selection
    for _ in range(100):
        participant_id = str(uuid.uuid4())
        hash_val = int(uuid.UUID(participant_id).int)
        row_index = hash_val % len(LATIN_SQUARE_MATRIX)
        
        assert 0 <= row_index < len(LATIN_SQUARE_MATRIX), f"Invalid row index: {row_index}"
        assert isinstance(LATIN_SQUARE_MATRIX[row_index], list), "Selected row must be a list"
        assert len(LATIN_SQUARE_MATRIX[row_index]) == 4, "Selected row must have 4 elements"
        # Verify all elements are valid stimuli
        for stimulus in LATIN_SQUARE_MATRIX[row_index]:
            assert stimulus in ["Professional", "Minimalist", "Low-Quality", "Neutral"], f"Invalid stimulus: {stimulus}"