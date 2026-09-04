import json
import os
import tempfile
from pathlib import Path
import pytest

from save_markov_artifacts import (
    load_standardized_data,
    compute_transition_matrices,
    save_markov_artifacts,
    run_t017b
)

def test_compute_transition_matrices_basic():
    """Test basic transition matrix computation."""
    data = [
        {"stimulus_sequence": "A", "surprisal": 0.1},
        {"stimulus_sequence": "B", "surprisal": 0.2},
        {"stimulus_sequence": "A", "surprisal": 0.1},
        {"stimulus_sequence": "B", "surprisal": 0.2},
    ]
    
    matrix, alphabet, order = compute_transition_matrices(data)
    
    assert order == 1, "Order must be 1"
    assert set(alphabet) == {"A", "B"}
    
    # Check probabilities sum to 1 (with smoothing)
    # Alphabet size = 2, alpha = 1.0
    # Total transitions from A: 1 (to B). Denom = 1 + 1*2 = 3.
    # P(A->A) = (0+1)/3 = 0.333, P(A->B) = (1+1)/3 = 0.666
    assert abs(matrix["A"]["A"] - 1/3) < 0.001
    assert abs(matrix["A"]["B"] - 2/3) < 0.001

def test_save_markov_artifacts_validation():
    """Test that save_markov_artifacts enforces order=1."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.json"
        
        # Valid
        save_markov_artifacts({}, [], 1, output_path)
        assert output_path.exists()
        
        # Invalid order
        with pytest.raises(ValueError, match="Constraint violation"):
            save_markov_artifacts({}, [], 2, output_path)

def test_run_t017b_integration():
    """Integration test for the full T017b pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        input_file = tmp_path / "standardized.csv"
        output_file = tmp_path / "markov_state.json"
        
        # Create fake standardized CSV
        input_file.write_text("stimulus_sequence,surprisal\nA,0.1\nB,0.2\nA,0.1\n")
        
        run_t017b(input_file, output_file)
        
        assert output_file.exists()
        
        with open(output_file) as f:
            data = json.load(f)
        
        assert "transition_matrix" in data
        assert "alphabet" in data
        assert "order" in data
        assert data["order"] == 1

def test_load_standardized_data_missing_file():
    """Test error handling for missing input file."""
    with pytest.raises(FileNotFoundError):
        load_standardized_data(Path("nonexistent.csv"))

def test_load_standardized_data_missing_columns():
    """Test error handling for missing required columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "bad.csv"
        input_file.write_text("stimulus_sequence\nA\nB\n") # Missing surprisal
        
        with pytest.raises(ValueError, match="Missing required columns"):
            load_standardized_data(input_file)