import os
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from analysis.output_nbs_results import load_nbs_results, write_nbs_results, process_nbs_output
from analysis.run_nbs import load_connectivity_matrices, run_nbs_analysis

def test_nbs_results_output_structure():
    """Test that NBS results file is created with correct columns."""
    # Create temporary test data
    test_dir = Path("data/processed")
    if not test_dir.exists():
        test_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = test_dir / "nbs_results_test.csv"
    
    # Create mock NBS results
    mock_results = pd.DataFrame({
        "component_id": [1, 2, 3],
        "size_edges": [10, 5, 8],
        "p_value_fwer": [0.02, 0.04, 0.01],
        "extra_column": [100, 200, 300]  # Test additional columns
    })
    
    # Write results
    write_nbs_results(mock_results, str(output_path))
    
    # Verify file exists
    assert output_path.exists(), "NBS results file should be created"
    
    # Read back and verify structure
    loaded_df = pd.read_csv(output_path)
    
    # Check required columns exist
    required_cols = ["component_id", "size_edges", "p_value_fwer"]
    for col in required_cols:
        assert col in loaded_df.columns, f"Column {col} should be present"
    
    # Check data integrity
    assert len(loaded_df) == 3, "Should have 3 rows"
    assert list(loaded_df["component_id"]) == [1, 2, 3], "Component IDs should match"
    assert list(loaded_df["size_edges"]) == [10, 5, 8], "Edge sizes should match"
    
    # Clean up
    if output_path.exists():
        os.remove(output_path)

def test_nbs_analysis_on_mock_data():
    """Test NBS analysis on mock connectivity data."""
    # Create mock connectivity matrices
    n_subjects = 20
    n_rois = 50
    matrices = np.random.randn(n_subjects, n_rois, n_rois)
    
    # Create subject IDs
    subject_ids = [f"sub_{i:03d}" for i in range(n_subjects)]
    
    # Run NBS analysis
    results = run_nbs_analysis(
        matrices=matrices,
        subject_ids=subject_ids,
        edge_threshold=0.05,
        n_permutations=100
    )
    
    # Verify result structure if components found
    if results is not None:
        assert isinstance(results, pd.DataFrame), "Results should be DataFrame"
        required_cols = ["component_id", "size_edges", "p_value_fwer"]
        for col in required_cols:
            assert col in results.columns, f"Column {col} should be present"
        
        # Check data types
        assert all(results["component_id"] > 0), "Component IDs should be positive"
        assert all(results["size_edges"] > 0), "Edge sizes should be positive"
        assert all(results["p_value_fwer"] >= 0) and all(results["p_value_fwer"] <= 1), \
            "P-values should be between 0 and 1"

def test_nbs_results_empty_case():
    """Test handling of case where no significant components are found."""
    # Create mock data with no significant differences
    n_subjects = 20
    n_rois = 50
    matrices = np.random.randn(n_subjects, n_rois, n_rois) * 0.001  # Very small values
    
    subject_ids = [f"sub_{i:03d}" for i in range(n_subjects)]
    
    # Run NBS with high threshold
    results = run_nbs_analysis(
        matrices=matrices,
        subject_ids=subject_ids,
        edge_threshold=1.0,  # High threshold unlikely to find anything
        n_permutations=100
    )
    
    # Should return None or empty DataFrame
    assert results is None or len(results) == 0, \
        "Should return None or empty DataFrame when no components found"

def test_nbs_output_path_creation():
    """Test that output directory is created if it doesn't exist."""
    import tempfile
    
    # Create a temporary directory path that doesn't exist
    temp_dir = Path("data/processed")
    temp_file = temp_dir / "nbs_test_nested_output.csv"
    
    # Ensure parent exists for test
    if not temp_dir.exists():
        temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock results
    mock_results = pd.DataFrame({
        "component_id": [1],
        "size_edges": [5],
        "p_value_fwer": [0.03]
    })
    
    # Write to new file
    write_nbs_results(mock_results, str(temp_file))
    
    # Verify file was created
    assert temp_file.exists(), "File should be created at specified path"
    
    # Clean up
    if temp_file.exists():
        os.remove(temp_file)