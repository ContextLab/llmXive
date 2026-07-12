"""
Integration tests for error handling in the molecular complexity pipeline.

This module tests that invalid SMILES strings are correctly identified and skipped
while valid ones are processed, ensuring the pipeline's robustness against malformed input.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from metrics import process_chunk, TimeoutError


class TestInvalidSmilesSkipped:
    """Test suite for verifying invalid SMILES handling."""

    def test_invalid_smiles_skipped(self):
        """
        Test that invalid SMILES strings are skipped and valid ones are processed.
        
        Given: A list containing valid and invalid SMILES strings
        When:  process_chunk is called with this list
        Then:  The skipped_count should be 1 and valid_count should be 2
        
        Input: ["CCO", "INVALID_SMILES_STRING", "CC"]
        Expected: skipped_count == 1, valid_count == 2
        """
        # Input data as specified in the task
        input_data = [
            {"cid": 1, "smiles": "CCO"},  # Valid: Ethanol
            {"cid": 2, "smiles": "INVALID_SMILES_STRING"},  # Invalid
            {"cid": 3, "smiles": "CC"}  # Valid: Ethane
        ]
        
        # Process the chunk
        results = process_chunk(input_data)
        
        # Count valid and skipped entries
        valid_count = len(results)
        skipped_count = len(input_data) - valid_count
        
        # Assertions as required by the task
        assert skipped_count == 1, f"Expected 1 skipped entry, got {skipped_count}"
        assert valid_count == 2, f"Expected 2 valid entries, got {valid_count}"
        
        # Additional verification: ensure the valid results contain the expected CIDs
        result_cids = [r['cid'] for r in results]
        assert 1 in result_cids, "Valid ethanol (CID 1) should be in results"
        assert 3 in result_cids, "Valid ethane (CID 3) should be in results"
        
        # Verify that the invalid entry was not included
        assert 2 not in result_cids, "Invalid entry (CID 2) should not be in results"
        
        # Verify that skipped entries are logged appropriately (if logging is implemented)
        # This is a secondary check to ensure the system is robust
        for result in results:
            assert 'entropy' in result or 'sa' in result or 'qed' in result, \
                "Valid results should contain at least one metric"

    def test_all_invalid_smiles(self):
        """Test handling when all input SMILES are invalid."""
        input_data = [
            {"cid": 1, "smiles": "INVALID1"},
            {"cid": 2, "smiles": "INVALID2"},
            {"cid": 3, "smiles": "INVALID3"}
        ]
        
        results = process_chunk(input_data)
        
        assert len(results) == 0, "Expected 0 valid results when all inputs are invalid"
        assert len(input_data) == 3, "Input should remain unchanged"

    def test_all_valid_smiles(self):
        """Test handling when all input SMILES are valid."""
        input_data = [
            {"cid": 1, "smiles": "CCO"},  # Ethanol
            {"cid": 2, "smiles": "CC"},   # Ethane
            {"cid": 3, "smiles": "c1ccccc1"}  # Benzene
        ]
        
        results = process_chunk(input_data)
        
        assert len(results) == 3, "Expected 3 valid results when all inputs are valid"
        
        # Verify all CIDs are present
        result_cids = [r['cid'] for r in results]
        assert all(cid in result_cids for cid in [1, 2, 3]), "All valid CIDs should be in results"

    def test_empty_input(self):
        """Test handling of empty input list."""
        input_data = []
        
        results = process_chunk(input_data)
        
        assert len(results) == 0, "Expected 0 results for empty input"