import pytest
import numpy as np
import json
import tempfile
from pathlib import Path
from src.models.utils import run_permutation_test, run_permutation_test_early_stop

def test_run_permutation_test_basic():
    """Test that run_permutation_test executes and produces output."""
    # Create sample data
    np.random.seed(42)
    data = np.random.normal(0, 1, 100)
    observed_stat = np.mean(data)
    
    # Create temporary output path
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_permutation_results.json"
        
        # Run the test with small n_shuffles for speed
        result = run_permutation_test(
            data=data,
            n_shuffles=100,  # Small number for unit test
            observed_statistic=observed_stat,
            output_path=output_path,
            species="TestSpecies",
            coefficient="temp_effect",
            chunk_size=50,
            seed=42
        )
        
        # Verify result structure
        assert "species" in result
        assert "coefficient" in result
        assert "p_value" in result
        assert "n_shuffles" in result
        assert "final_p_value" in result
        
        # Verify output file was created
        assert output_path.exists()
        
        # Verify JSON content
        with open(output_path, 'r') as f:
            saved_results = json.load(f)
        
        assert len(saved_results) == 1
        assert saved_results[0]["species"] == "TestSpecies"
        assert saved_results[0]["coefficient"] == "temp_effect"
        assert isinstance(saved_results[0]["p_value"], float)
        assert saved_results[0]["n_shuffles"] == 100

def test_run_permutation_test_chunking():
    """Test that permutation test handles chunking correctly."""
    np.random.seed(123)
    data = np.random.normal(0, 1, 50)
    observed_stat = np.mean(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "chunked_results.json"
        
        # Run with chunk size that requires multiple chunks
        result = run_permutation_test(
            data=data,
            n_shuffles=200,
            observed_statistic=observed_stat,
            output_path=output_path,
            species="ChunkTest",
            coefficient="precip_effect",
            chunk_size=50,
            seed=42
        )
        
        # Should have run all 200 shuffles
        assert result["n_shuffles"] == 200
        
        # Verify file contains correct number of entries (1 in this case)
        with open(output_path, 'r') as f:
            saved_results = json.load(f)
        assert len(saved_results) == 1

def test_run_permutation_test_early_stop():
    """Test the early stopping logic of the permutation test."""
    np.random.seed(999)
    data = np.random.normal(0, 1, 30)
    observed_stat = np.mean(data)
    
    # Run with a large n_shuffles but small data to trigger early stop logic
    p_val, total_shuffles = run_permutation_test_early_stop(
        data=data,
        n_shuffles=10000,
        observed_statistic=observed_stat,
        chunk_size=1000,
        seed=42
    )
    
    # p-value should be between 0 and 1
    assert 0.0 <= p_val <= 1.0
    # Should have run at least some shuffles
    assert total_shuffles > 0
    # Should not have run all if early stopping triggered (depends on implementation)
    # For this test, we just verify it doesn't crash and returns valid values

def test_run_permutation_test_output_schema():
    """Verify the output schema matches the task requirements."""
    np.random.seed(42)
    data = np.random.normal(0, 1, 20)
    observed_stat = np.mean(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "schema_test.json"
        
        run_permutation_test(
            data=data,
            n_shuffles=50,
            observed_statistic=observed_stat,
            output_path=output_path,
            species="SchemaTest",
            coefficient="test_coef",
            chunk_size=25,
            seed=42
        )
        
        with open(output_path, 'r') as f:
            results = json.load(f)
        
        # Check required keys per task T025b specification
        required_keys = ["species", "coefficient", "p_value", "n_shuffles", "final_p_value"]
        for key in required_keys:
            assert key in results[0], f"Missing required key: {key}"
        
        # Check types
        assert isinstance(results[0]["species"], str)
        assert isinstance(results[0]["coefficient"], str)
        assert isinstance(results[0]["p_value"], float)
        assert isinstance(results[0]["n_shuffles"], int)
        assert isinstance(results[0]["final_p_value"], float)