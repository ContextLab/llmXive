"""
Integration tests for Task T017b: Save Markov Artifacts.

Tests verify that:
1. The script runs without error given valid input.
2. The output files (transition probabilities, counts, metadata) are created.
3. The JSON structure of the artifacts is valid and contains expected keys.
4. The transition probabilities sum to ~1.0 for each state.
"""
import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

# Add project root to path if running from tests directory
sys_path = Path(__file__).parent.parent.parent
if str(sys_path) not in os.sys.path:
    os.sys.path.insert(0, str(sys_path))

from save_markov_artifacts import compute_transition_matrices, save_markov_artifacts

class TestT017bIntegration:
    """Integration tests for Markov artifact generation."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create a mock standardized dataframe with stimulus sequences."""
        data = {
            'participant_id': ['P1', 'P1', 'P2'],
            'duration_estimate': [1.2, 1.5, 1.1],
            'stimulus_sequence': [
                ['A', 'B', 'A', 'C'],
                ['A', 'A', 'B', 'B', 'C'],
                ['C', 'B', 'A']
            ],
            'surprisal': [0.5, 0.2, 0.8] # Dummy column
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_compute_transition_matrices_basic(self, sample_dataframe):
        """Test that transition matrices are computed correctly."""
        result = compute_transition_matrices(sample_dataframe)
        
        assert "transition_probabilities" in result
        assert "transition_counts" in result
        assert "unique_states" in result
        assert "sequence_length" in result
        
        # Check unique states
        assert set(result["unique_states"]) == {"A", "B", "C"}
        
        # Check sequence length: 4 + 5 + 3 = 12
        assert result["sequence_length"] == 12
        
        # Check specific transition: A -> B should exist
        # In data: P1 (A->B), P2 (A->B), P2 (B->A is not there, B->B, B->C)
        # P1: A->B, B->A, A->C
        # P2: A->A, A->B, B->B, B->C
        # P3: C->B, B->A
        # Counts:
        # A->B: 2
        # A->A: 1
        # A->C: 1
        # B->A: 2
        # B->B: 1
        # B->C: 1
        # C->B: 1
        
        assert result["transition_counts"]["A"]["B"] == 2
        assert result["transition_counts"]["B"]["A"] == 2
        
        # Check probabilities sum to 1
        for state, probs in result["transition_probabilities"].items():
            total = sum(probs.values())
            assert abs(total - 1.0) < 1e-6, f"Probabilities for {state} sum to {total}, not 1.0"

    def test_compute_transition_matrices_empty(self):
        """Test handling of empty or invalid sequences."""
        df = pd.DataFrame({
            'participant_id': ['P1'],
            'stimulus_sequence': [['A']] # Length 1, no transitions
        })
        result = compute_transition_matrices(df)
        
        assert result["total_transitions"] == 0
        assert result["sequence_length"] == 1

    def test_save_markov_artifacts_creates_files(self, sample_dataframe, temp_output_dir):
        """Test that save function creates the required files."""
        transition_data = compute_transition_matrices(sample_dataframe)
        
        save_markov_artifacts(transition_data, temp_output_dir)
        
        # Check files exist
        files = list(temp_output_dir.glob("*.json"))
        assert len(files) >= 3, f"Expected at least 3 JSON files, found {len(files)}: {[f.name for f in files]}"
        
        # Check specific file patterns
        prob_files = list(temp_output_dir.glob("transition_probabilities_*.json"))
        counts_files = list(temp_output_dir.glob("transition_counts_*.json"))
        meta_files = list(temp_output_dir.glob("markov_model_state_*.json"))
        manifest_files = list(temp_output_dir.glob("latest_markov_artifacts.json"))
        
        assert len(prob_files) == 1
        assert len(counts_files) == 1
        assert len(meta_files) == 1
        assert len(manifest_files) == 1

    def test_artifact_content_validity(self, sample_dataframe, temp_output_dir):
        """Test that the saved JSON files have valid structure."""
        transition_data = compute_transition_matrices(sample_dataframe)
        save_markov_artifacts(transition_data, temp_output_dir)
        
        # Load and verify manifest
        manifest_path = temp_output_dir / "latest_markov_artifacts.json"
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert "probabilities" in manifest
        assert "counts" in manifest
        assert "metadata" in manifest
        
        # Load and verify metadata structure
        meta_path = temp_output_dir / manifest["metadata"]
        with open(meta_path, 'r') as f:
            meta = json.load(f)
        
        assert meta["artifact_type"] == "markov_model_state"
        assert "unique_states" in meta
        assert "total_transitions" in meta
        assert "generated_at" in meta

    def test_artifact_probability_consistency(self, sample_dataframe, temp_output_dir):
        """Test that saved probabilities match computed ones."""
        transition_data = compute_transition_matrices(sample_dataframe)
        save_markov_artifacts(transition_data, temp_output_dir)
        
        # Load saved probabilities
        prob_path = temp_output_dir / "latest_markov_artifacts.json"
        with open(prob_path, 'r') as f:
            manifest = json.load(f)
        
        saved_prob_path = temp_output_dir / manifest["probabilities"]
        with open(saved_prob_path, 'r') as f:
            saved_probs = json.load(f)
        
        # Compare with computed
        for state in transition_data["unique_states"]:
            for dst in transition_data["unique_states"]:
                expected = transition_data["transition_probabilities"][state][dst]
                actual = saved_probs[state][dst]
                assert abs(expected - actual) < 1e-9, f"Mismatch for {state}->{dst}"