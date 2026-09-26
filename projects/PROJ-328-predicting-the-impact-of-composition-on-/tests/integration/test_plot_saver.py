"""
Integration test for T038: Plot Saver.
Verifies that plots are generated and saved to the correct location.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_data_processed_dir, get_data_outputs_dir
from visualization.plot_saver import main

@pytest.fixture
def setup_mock_data():
    """Create mock input data files required by plot_saver."""
    processed_dir = get_data_processed_dir()
    processed_path = Path(processed_dir)
    processed_path.mkdir(parents=True, exist_ok=True)
    
    # Create mock predictions.csv
    predictions_data = {
        'hardness_hv': [10.0, 15.0, 20.0, 25.0, 30.0],
        'predicted_hv': [10.5, 14.8, 20.2, 24.5, 30.1],
        'ci_lower': [9.0, 13.5, 18.5, 23.0, 28.5],
        'ci_upper': [12.0, 16.1, 21.9, 26.0, 31.7]
    }
    predictions_df = pd.DataFrame(predictions_data)
    predictions_path = processed_path / "predictions.csv"
    predictions_df.to_csv(predictions_path, index=False)
    
    # Create mock shap_ranking.yaml
    shap_data = [
        {"feature_name": "weighted_mean_atomic_mass", "mean_abs_shap_value": 0.45, "rank": 1},
        {"feature_name": "electronegativity_variance", "mean_abs_shap_value": 0.32, "rank": 2},
        {"feature_name": "atomic_radius_variance", "mean_abs_shap_value": 0.28, "rank": 3},
        {"feature_name": "weighted_avg_melting_point", "mean_abs_shap_value": 0.15, "rank": 4},
        {"feature_name": "valence_electron_concentration", "mean_abs_shap_value": 0.12, "rank": 5}
    ]
    shap_path = processed_path / "shap_ranking.yaml"
    with open(shap_path, 'w') as f:
        yaml.dump(shap_data, f)
    
    # Ensure output directory exists
    output_dir = get_data_outputs_dir()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    yield {
        'predictions_path': predictions_path,
        'shap_path': shap_path,
        'output_dir': output_path
    }
    
    # Cleanup
    if predictions_path.exists():
        predictions_path.unlink()
    if shap_path.exists():
        shap_path.unlink()
    
    # Clean generated plots
    for f in output_path.glob("*.png"):
        f.unlink()

def test_plot_saver_execution(setup_mock_data):
    """Test that plot_saver runs without error and generates expected outputs."""
    result = main()
    
    assert result == 0, "Plot saver execution failed"
    
    output_dir = setup_mock_data['output_dir']
    
    # Check scatter plot exists
    scatter_path = output_dir / "scatter_predicted_vs_measured.png"
    assert scatter_path.exists(), f"Scatter plot not found: {scatter_path}"
    assert scatter_path.stat().st_size > 0, "Scatter plot is empty"
    
    # Check partial dependence plot exists
    pdp_path = output_dir / "partial_dependence_top_features.png"
    assert pdp_path.exists(), f"Partial dependence plot not found: {pdp_path}"
    assert pdp_path.stat().st_size > 0, "Partial dependence plot is empty"