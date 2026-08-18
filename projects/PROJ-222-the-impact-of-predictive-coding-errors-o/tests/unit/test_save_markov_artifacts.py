import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from save_markov_artifacts import load_standardized_data, compute_transition_matrices, save_markov_artifacts

class TestLoadStandardizedData:
    def test_load_existing_data(self):
        """Test loading a valid standardized CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "standardized.csv"
            df = pd.DataFrame({
                'stimulus_sequence': ['A,B', 'B,C', 'A,A'],
                'duration_estimate': [1.0, 1.2, 0.9],
                'participant_id': ['P1', 'P1', 'P2']
            })
            df.to_csv(data_path, index=False)
            
            loaded = load_standardized_data(Path(tmpdir))
            assert len(loaded) == 3
            assert 'stimulus_sequence' in loaded.columns

    def test_missing_file_raises(self):
        """Test that missing file raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                load_standardized_data(Path(tmpdir))

    def test_missing_columns_raises(self):
        """Test that missing required columns raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "standardized.csv"
            df = pd.DataFrame({
                'wrong_col': [1, 2, 3]
            })
            df.to_csv(data_path, index=False)
            
            with pytest.raises(ValueError):
                load_standardized_data(Path(tmpdir))

class TestComputeTransitionMatrices:
    def test_basic_transitions(self):
        """Test basic transition probability calculation."""
        df = pd.DataFrame({
            'stimulus_sequence': ['A,B,C', 'B,C', 'A,B'],
            'participant_id': ['P1', 'P1', 'P1'],
            'duration_estimate': [1.0, 1.1, 1.2]
        })
        
        result = compute_transition_matrices(df)
        
        assert 'transitions' in result
        assert 'statistics' in result
        assert 'metadata' in result
        
        # Check that P1 has a transition matrix
        assert 'P1' in result['transitions']
        
        # Check transition A->B exists (should be 2/3 roughly)
        # A->B appears in 'A,B,C' and 'A,B'
        # B->C appears in 'A,B,C' and 'B,C'
        matrix = result['transitions']['P1']
        assert 'A' in matrix
        assert 'B' in matrix['A']
        assert 'C' in matrix['B']

    def test_probabilities_sum_to_one(self):
        """Test that transition probabilities sum to 1 for each source state."""
        df = pd.DataFrame({
            'stimulus_sequence': ['A,B', 'A,C'],
            'participant_id': ['P1', 'P1']
        })
        
        result = compute_transition_matrices(df)
        matrix = result['transitions']['P1']
        
        # From A, we go to B (1) and C (1) -> prob 0.5 each
        prob_sum = sum(matrix['A'].values())
        assert abs(prob_sum - 1.0) < 1e-6

    def test_multiple_participants(self):
        """Test handling of multiple participants."""
        df = pd.DataFrame({
            'stimulus_sequence': ['A,B', 'C,D'],
            'participant_id': ['P1', 'P2']
        })
        
        result = compute_transition_matrices(df)
        
        assert 'P1' in result['transitions']
        assert 'P2' in result['transitions']

class TestSaveMarkovArtifacts:
    def test_save_and_load(self):
        """Test that artifacts can be saved and reloaded."""
        artifacts = {
            'transitions': {'P1': {'A': {'B': 1.0}}},
            'statistics': {'total_sequences': 1},
            'metadata': {'version': '1.0'}
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = save_markov_artifacts(artifacts, Path(tmpdir))
            
            assert Path(path).exists()
            
            with open(path) as f:
                loaded = json.load(f)
            
            assert loaded['transitions'] == artifacts['transitions']