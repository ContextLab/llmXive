"""
Tests for T025: SHAP plot generation.
"""
import os
import json
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

from config import get_config, reset_config
from models.generate_shap_plots import (
    load_models,
    load_final_dataset,
    load_shap_values,
    get_feature_columns,
    main
)

@pytest.fixture
def setup_test_env(tmp_path):
    """Setup a temporary test environment."""
    reset_config()
    # Set config to use temporary paths
    os.environ["DATA_DIR"] = str(tmp_path / "data")
    os.environ["MODEL_DIR"] = str(tmp_path / "models")
    os.environ["REPORT_DIR"] = str(tmp_path / "docs" / "reports")
    
    # Create directories
    for subdir in ["data/processed", "models", "docs/reports/shap_plots"]:
        (tmp_path / subdir).mkdir(parents=True, exist_ok=True)
    
    # Create dummy final_dataset.parquet
    df = pd.DataFrame({
        'composition_id': ['C1', 'C2', 'C3'],
        'chemical_family': ['oxide', 'sulfide', 'organic'],
        'Tg_K': [500.0, 600.0, 450.0],
        'Tx_K': [600.0, 700.0, 550.0],
        'crystallization_label': [0, 1, 0],
        'rdf_peak_pos': [3.5, 3.6, 3.4],
        'rdf_peak_width': [0.5, 0.6, 0.4],
        'bond_angle_variance': [10.0, 12.0, 8.0],
        'coordination_numbers': [4.0, 4.5, 3.8]
    })
    df.to_parquet(tmp_path / "data/processed" / "final_dataset.parquet")
    
    # Create dummy SHAP values
    shap_data = {
        'oxide': {
            'regressor_shap_values': np.array([[1.0, 0.5, 0.2, 0.1], [0.8, 0.6, 0.3, 0.2]]),
            'classifier_shap_values': None
        },
        'sulfide': {
            'regressor_shap_values': np.array([[0.9, 0.7, 0.4, 0.15], [1.1, 0.5, 0.25, 0.1]]),
            'classifier_shap_values': None
        },
        'organic': {
            'regressor_shap_values': np.array([[0.7, 0.8, 0.3, 0.2], [0.6, 0.9, 0.35, 0.25]]),
            'classifier_shap_values': None
        }
    }
    with open(tmp_path / "models" / "shap_values.json", 'w') as f:
        json.dump(shap_data, f)
    
    yield tmp_path

def test_load_final_dataset(setup_test_env):
    """Test loading the final dataset."""
    df = load_final_dataset()
    assert len(df) == 3
    assert 'chemical_family' in df.columns
    assert 'Tg_K' in df.columns

def test_get_feature_columns(setup_test_env):
    """Test feature column extraction."""
    df = load_final_dataset()
    feature_cols = get_feature_columns(df)
    expected = ['rdf_peak_pos', 'rdf_peak_width', 'bond_angle_variance', 'coordination_numbers']
    assert feature_cols == expected

def test_shap_plot_generation(setup_test_env, monkeypatch):
    """Test that SHAP plots are generated."""
    # Mock the plot functions to avoid actual plotting
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    
    from models import generate_shap_plots
    from utils import plots
    
    generated_files = []
    
    def mock_save_plot(*args, **kwargs):
        # Create a dummy file to simulate generation
        output_path = kwargs.get('output_path', args[0] if args else None)
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(b'PNG_DUMMY_DATA')
            generated_files.append(output_path)
        return True
    
    monkeypatch.setattr(plots, 'plot_shap_summary', mock_save_plot)
    monkeypatch.setattr(plots, 'plot_shap_beeswarm', mock_save_plot)
    monkeypatch.setattr(plots, 'plot_feature_importance_bar', mock_save_plot)
    
    # Run main
    main()
    
    # Verify files were created
    output_dir = Path(get_config().report_dir) / "shap_plots"
    assert (output_dir / "oxide").exists()
    assert (output_dir / "sulfide").exists()
    assert (output_dir / "organic").exists()
    
    # Check for JSON files
    assert (output_dir / "oxide" / "ranked_features_oxide.json").exists()
    assert (output_dir / "sulfide" / "ranked_features_sulfide.json").exists()
    assert (output_dir / "organic" / "ranked_features_organic.json").exists()

def test_ranked_features_json_format(setup_test_env, monkeypatch):
    """Test the format of ranked features JSON files."""
    import matplotlib
    matplotlib.use('Agg')
    
    from models import generate_shap_plots
    from utils import plots
    
    def mock_save_plot(*args, **kwargs):
        output_path = kwargs.get('output_path', args[0] if args else None)
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(b'PNG_DUMMY_DATA')
        return True
    
    monkeypatch.setattr(plots, 'plot_shap_summary', mock_save_plot)
    monkeypatch.setattr(plots, 'plot_shap_beeswarm', mock_save_plot)
    monkeypatch.setattr(plots, 'plot_feature_importance_bar', mock_save_plot)
    
    main()
    
    config = get_config()
    output_dir = Path(config.report_dir) / "shap_plots"
    
    for family in ['oxide', 'sulfide', 'organic']:
        json_path = output_dir / family / f"ranked_features_{family}.json"
        assert json_path.exists(), f"Missing JSON for {family}"
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        assert 'family' in data
        assert data['family'] == family
        assert 'features' in data
        assert len(data['features']) > 0
        
        for feature in data['features']:
            assert 'rank' in feature
            assert 'feature' in feature
            assert 'mean_abs_shap' in feature
            assert feature['rank'] > 0