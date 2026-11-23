import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os
import shutil

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from statistical_analysis import main, load_metrics, calculate_learning_curve_stats, plot_learning_curve, generate_summary_statistics
from utils.logging import get_logger

RESULTS_DIR = Path("data/results")
PLOTS_DIR = RESULTS_DIR / "plots"
METRICS_FILE = RESULTS_DIR / "metrics.csv"
SUMMARY_FILE = RESULTS_DIR / "stat_summary.json"

@pytest.fixture
def mock_metrics_file(tmp_path):
    """Create a temporary metrics file for testing."""
    # Override global paths for the test
    original_metrics = METRICS_FILE
    original_summary = SUMMARY_FILE
    original_plots = PLOTS_DIR
    
    # Create temp dirs
    temp_results = tmp_path / "data" / "results"
    temp_results.mkdir(parents=True)
    temp_plots = temp_results / "plots"
    temp_plots.mkdir()
    
    # Mock data
    data = {
        'sparsity_level': ['10', '10', '20', '20', '30', '30'],
        'model': ['GPR', 'RF', 'GPR', 'RF', 'GPR', 'RF'],
        'seed': [1, 1, 1, 1, 1, 1],
        'rmse': [1.0, 1.2, 0.8, 0.9, 0.6, 0.7],
        'mae': [0.5, 0.6, 0.4, 0.45, 0.3, 0.35],
        'variance': [0.1, 0.12, 0.08, 0.09, 0.06, 0.07],
        'calibration_slope': [0.95, 0.98, 1.02, 1.01, 1.00, 0.99]
    }
    df = pd.DataFrame(data)
    
    mock_path = temp_results / "metrics.csv"
    df.to_csv(mock_path, index=False)
    
    return mock_path, temp_results, temp_plots

@pytest.mark.integration
def test_full_analysis_pipeline(mock_metrics_file, tmp_path):
    """Test the full statistical analysis pipeline end-to-end."""
    metrics_path, temp_results, temp_plots = mock_metrics_file
    
    # Patch the global constants in the module
    import statistical_analysis as sa
    sa.METRICS_FILE = metrics_path
    sa.RESULTS_DIR = temp_results
    sa.PLOTS_DIR = temp_plots
    sa.SUMMARY_FILE = temp_results / "stat_summary.json"
    
    # Run main
    # We expect it to run successfully and produce files
    try:
        sa.main()
    except SystemExit as e:
        if e.code != 0:
            pytest.fail(f"Main execution failed with code {e.code}")
    
    # Verify outputs exist
    assert (temp_results / "learning_curve_rmse.png").exists(), "RMSE plot not generated"
    assert (temp_results / "learning_curve_mae.png").exists(), "MAE plot not generated"
    assert (temp_results / "stat_summary.json").exists(), "Summary JSON not generated"
    
    # Verify summary content
    with open(temp_results / "stat_summary.json", 'r') as f:
        summary = json.load(f)
    
    assert summary['n_levels'] == 3
    assert len(summary['levels']) == 3
    
    # Check specific values (approximate)
    level_10 = next(l for l in summary['levels'] if l['sparsity_level'] == '10')
    assert np.isclose(level_10['mean_rmse'], 1.1, atol=0.01)
    
    # Verify plot is not empty (size > 0)
    assert (temp_results / "learning_curve_rmse.png").stat().st_size > 1000

@pytest.mark.integration
def test_plot_generation(mock_metrics_file):
    """Test specific plot generation logic."""
    metrics_path, temp_results, temp_plots = mock_metrics_file
    
    df = pd.read_csv(metrics_path)
    stats_df = calculate_learning_curve_stats(df)
    
    output_path = temp_plots / "test_plot.png"
    plot_learning_curve(stats_df, output_path, metric='rmse')
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0
