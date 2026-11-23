"""
Unit tests for T038: SHAP Rank Shift Analysis.
"""
import os
import sys
import tempfile
import json
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.shap_ranking import (
    load_shap_values, 
    get_feature_names_from_schema, 
    calculate_mean_rank_shift,
    main
)

@pytest.fixture
def temp_dirs():
    """Create temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create mock directories
        shap_dir = tmpdir / "results" / "shap_analysis"
        data_dir = tmpdir / "data" / "processed"
        shap_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)
        yield tmpdir, shap_dir, data_dir

def test_load_shap_values(temp_dirs):
    tmpdir, shap_dir, _ = temp_dirs
    test_file = shap_dir / "test.npy"
    data = np.array([[1.0, 2.0], [3.0, 4.0]])
    np.save(test_file, data)
    
    loaded = load_shap_values(test_file)
    assert np.array_equal(loaded, data)

def test_load_shap_values_not_found(temp_dirs):
    tmpdir, shap_dir, _ = temp_dirs
    with pytest.raises(FileNotFoundError):
        load_shap_values(shap_dir / "nonexistent.npy")

def test_get_feature_names_from_schema(temp_dirs):
    tmpdir, _, data_dir = temp_dirs
    schema_file = data_dir / "descriptor_schema.json"
    schema_data = {"columns": ["feat_A", "feat_B", "feat_C"]}
    with open(schema_file, 'w') as f:
        json.dump(schema_data, f)
    
    names = get_feature_names_from_schema(schema_file)
    assert names == ["feat_A", "feat_B", "feat_C"]

def test_get_feature_names_from_schema_not_found(temp_dirs):
    tmpdir, _, data_dir = temp_dirs
    with pytest.raises(FileNotFoundError):
        get_feature_names_from_schema(data_dir / "missing.json")

def test_calculate_mean_rank_shift():
    ranked_features = ["f1", "f2", "f3"]
    rank_dict = {"f1": 1.0, "f2": 3.0, "f3": 2.0}
    mean_shift = calculate_mean_rank_shift(ranked_features, rank_dict)
    # (1 + 3 + 2) / 3 = 2.0
    assert mean_shift == 2.0

def test_main_integration(temp_dirs):
    """
    Test the full main() flow with mock data.
    """
    tmpdir, shap_dir, data_dir = temp_dirs
    
    # Mock SHAP data: 10 samples, 3 features
    shap_skewed = np.random.rand(10, 3)
    shap_balanced = np.random.rand(10, 3)
    
    np.save(shap_dir / "shap_skewed.npy", shap_skewed)
    np.save(shap_dir / "shap_balanced.npy", shap_balanced)
    
    # Mock Schema
    schema_file = data_dir / "descriptor_schema.json"
    with open(schema_file, 'w') as f:
        json.dump({"columns": ["feat_0", "feat_1", "feat_2"]}, f)
    
    # Run main
    # We need to patch the paths in main() or pass them? 
    # The current main() uses hardcoded PROJECT_ROOT logic.
    # To test this properly, we would need to refactor main to accept paths or 
    # mock PROJECT_ROOT. For unit test purposes, let's just verify the logic 
    # by running it in a controlled env or mocking the file system.
    # Since main() relies on global paths, let's just test the core logic 
    # functions which we already did. 
    # However, to ensure the script runs without error:
    
    # We will mock the environment to point to our temp dir
    import code.shap_ranking as module
    original_root = module.PROJECT_ROOT
    
    # Temporarily override PROJECT_ROOT logic by monkey-patching
    # This is a bit hacky but necessary for unit testing a script with hardcoded paths
    module.PROJECT_ROOT = tmpdir
    
    try:
        # This should run without crashing
        result_df = main()
        
        assert isinstance(result_df, pd.DataFrame)
        assert 'feature' in result_df.columns
        assert 'rank_skewed' in result_df.columns
        assert 'rank_balanced' in result_df.columns
        assert 'rank_shift' in result_df.columns
        
        # Check file was created
        output_file = shap_dir / "rank_shift.csv"
        assert output_file.exists()
        
        # Check content
        saved_df = pd.read_csv(output_file)
        assert len(saved_df) == 3
        assert saved_df['feature'].tolist() == ["feat_0", "feat_1", "feat_2"]
        
    finally:
        module.PROJECT_ROOT = original_root