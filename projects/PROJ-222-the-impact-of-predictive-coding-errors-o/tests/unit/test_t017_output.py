import pytest
import pandas as pd
import json
import os
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_standardized_output import (
    validate_schema, 
    verify_markov_derivation, 
    compute_sha256,
    get_processed_dir
)

class TestT017SchemaValidation:
    def test_valid_schema(self, tmp_path):
        """Test that a valid dataframe passes schema validation."""
        df = pd.DataFrame({
            'duration_estimate': [1.0, 2.0],
            'stimulus_sequence': ['A B C', 'B C A'],
            'participant_id': ['P1', 'P2'],
            'surprisal': [0.5, 0.6]
        })
        assert validate_schema(df) is True

    def test_missing_duration_estimate(self):
        """Test that missing duration_estimate fails."""
        df = pd.DataFrame({
            'stimulus_sequence': ['A B C'],
            'participant_id': ['P1'],
            'surprisal': [0.5]
        })
        assert validate_schema(df) is False

    def test_missing_surprisal(self):
        """Test that missing surprisal fails."""
        df = pd.DataFrame({
            'duration_estimate': [1.0],
            'stimulus_sequence': ['A B C'],
            'participant_id': ['P1']
        })
        assert validate_schema(df) is False

    def test_raw_sequence_fallback(self):
        """Test that raw_stimulus_sequence is accepted if stimulus_sequence is missing."""
        df = pd.DataFrame({
            'duration_estimate': [1.0],
            'raw_stimulus_sequence': ['A B C'],
            'participant_id': ['P1'],
            'surprisal': [0.5]
        })
        assert validate_schema(df) is True

class TestT017MarkovVerification:
    def test_valid_markov_state(self, tmp_path):
        """Test verification with a valid first-order Markov state."""
        markov_state = {
            'transition_matrix': {'A': {'B': 0.5, 'C': 0.5}},
            'alphabet': ['A', 'B', 'C'],
            'order': 1
        }
        path = tmp_path / "markov_state.json"
        with open(path, 'w') as f:
            json.dump(markov_state, f)
        
        assert verify_markov_derivation(path) is True

    def test_invalid_order(self, tmp_path):
        """Test verification fails if order is not 1."""
        markov_state = {
            'transition_matrix': {'A': {'B': 0.5}},
            'alphabet': ['A', 'B'],
            'order': 2
        }
        path = tmp_path / "markov_state.json"
        with open(path, 'w') as f:
            json.dump(markov_state, f)
        
        assert verify_markov_derivation(path) is False

    def test_missing_keys(self, tmp_path):
        """Test verification fails if required keys are missing."""
        markov_state = {
            'transition_matrix': {'A': {'B': 0.5}},
            'alphabet': ['A', 'B']
            # 'order' missing
        }
        path = tmp_path / "markov_state.json"
        with open(path, 'w') as f:
            json.dump(markov_state, f)
        
        assert verify_markov_derivation(path) is False

    def test_file_not_found(self, tmp_path):
        """Test verification fails if file does not exist."""
        assert verify_markov_derivation(tmp_path / "nonexistent.json") is False

class TestT017Checksum:
    def test_checksum_consistency(self, tmp_path):
        """Test that checksum is consistent for the same file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")
        
        c1 = compute_sha256(file_path)
        c2 = compute_sha256(file_path)
        assert c1 == c2
        
        # Different content should yield different checksum
        file_path.write_text("different content")
        c3 = compute_sha256(file_path)
        assert c1 != c3
