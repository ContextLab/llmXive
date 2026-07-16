"""
Unit tests for the interpretability module (T021).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest
from xgboost import XGBRegressor

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.interpret import (
    load_model_and_data,
    generate_shap_analysis,
    perform_sensitivity_analysis,
    main
)

# Fixtures
@pytest.fixture
def mock_model():
    model = XGBRegressor()
    model.fit(pd.DataFrame({'a': [1, 2, 3]}), [1, 2, 3])
    return model

@pytest.fixture
def mock_data():
    X = pd.DataFrame({
        'feature1': [1.0, 2.0, 3.0, 4.0, 5.0],
        'feature2': [2.0, 3.0, 4.0, 5.0, 6.0]
    })
    y = pd.Series([1.5, 2.5, 3.5, 4.5, 5.5])
    return X, y

@pytest.fixture
def temp_dirs():
    # Create temporary directories for artifacts
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        models_dir = tmppath / "models"
        data_dir = tmppath / "data" / "processed"
        artifacts_dir = tmppath / "artifacts"
        figures_dir = artifacts_dir / "figures"
        reports_dir = artifacts_dir / "reports"
        
        models_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)
        figures_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)
        
        yield {
            "models": models_dir,
            "data": data_dir,
            "figures": figures_dir,
            "reports": reports_dir,
            "root": tmppath
        }

def test_generate_shap_analysis(mock_model, mock_data, temp_dirs):
    """Test SHAP analysis generation and file outputs."""
    X, y = mock_data
    
    # Patch the global directories to use temp_dirs
    with patch('code.interpret.FIGURES_DIR', temp_dirs["figures"]), \
         patch('code.interpret.REPORTS_DIR', temp_dirs["reports"]):
        
        result = generate_shap_analysis(mock_model, X, 'target')
        
        # Check return structure
        assert 'shap_plot_path' in result
        assert 'ranking_path' in result
        assert 'top_features' in result
        
        # Check file existence
        assert Path(result['shap_plot_path']).exists()
        assert Path(result['ranking_path']).exists()
        
        # Check ranking content
        with open(result['ranking_path'], 'r') as f:
            ranking_data = json.load(f)
        assert isinstance(ranking_data, list)
        assert len(ranking_data) > 0
        assert 'feature' in ranking_data[0]
        assert 'mean_abs_shap' in ranking_data[0]

def test_perform_sensitivity_analysis(mock_model, mock_data, temp_dirs):
    """Test sensitivity analysis table generation."""
    X, y = mock_data
    
    with patch('code.interpret.FIGURES_DIR', temp_dirs["figures"]), \
         patch('code.interpret.REPORTS_DIR', temp_dirs["reports"]), \
         patch('code.interpret.get_threshold_justification', return_value="Test Justification"), \
         patch('code.interpret.get_r2_threshold', return_value=0.7):
        
        result_df = perform_sensitivity_analysis(mock_model, X, y, 'target')
        
        assert isinstance(result_df, pd.DataFrame)
        assert 'threshold' in result_df.columns
        assert 'pass_rate' in result_df.columns
        assert 'model_r2' in result_df.columns
        
        # Check that the file was saved
        output_path = temp_dirs["reports"] / "threshold-sensitivity-table.csv"
        assert output_path.exists()
        
        # Check content logic
        assert result_df['threshold'].min() >= 0.0
        assert result_df['threshold'].max() <= 0.95

def test_load_model_and_data_missing_file(temp_dirs):
    """Test that load_model_and_data fails loudly if files are missing."""
    with patch('code.interpret.MODELS_DIR', temp_dirs["models"]), \
         patch('code.interpret.DATA_PROCESSED_DIR', temp_dirs["data"]):
        
        with pytest.raises(FileNotFoundError):
            load_model_and_data()

def test_main_integration(temp_dirs, mock_model, mock_data):
    """Test the main entry point."""
    # Setup mock files
    model_path = temp_dirs["models"] / "best_model.json"
    data_path = temp_dirs["data"] / "cleaned_dataset.parquet"
    
    mock_model.save_model(str(model_path))
    
    df = pd.concat([mock_data[0], mock_data[1].to_frame(name='diffusivity')], axis=1)
    df.to_parquet(str(data_path))
    
    # Patch paths
    with patch('code.interpret.MODELS_DIR', temp_dirs["models"]), \
         patch('code.interpret.DATA_PROCESSED_DIR', temp_dirs["data"]), \
         patch('code.interpret.FIGURES_DIR', temp_dirs["figures"]), \
         patch('code.interpret.REPORTS_DIR', temp_dirs["reports"]), \
         patch('code.interpret.get_threshold_justification', return_value="Test"), \
         patch('code.interpret.get_r2_threshold', return_value=0.7):
        
        # Run main
        try:
            main()
        except SystemExit as e:
            # Should exit with 0 on success
            assert e.code == 0
        
        # Check outputs
        assert (temp_dirs["figures"] / "shap_summary_plot.png").exists()
        assert (temp_dirs["reports"] / "feature_ranking.json").exists()
        assert (temp_dirs["reports"] / "threshold-sensitivity-table.csv").exists()