import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.visualization import (
    create_boxplot,
    load_metric_data,
    generate_all_boxplots,
    update_state_with_figures,
    run_visualization_pipeline
)
from code.data_model import MetricResult

@pytest.fixture
def mock_metric_data(tmp_path):
    """Create mock metric data for testing."""
    # Create data directory structure
    metrics_dir = tmp_path / "data" / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock CSV for cyclomatic_complexity
    data = {
        'snippet_id': [f'snippet_{i}' for i in range(100)],
        'group': ['human'] * 50 + ['llm'] * 50,
        'value': np.concatenate([
            np.random.normal(5, 1, 50),
            np.random.normal(7, 1.5, 50)
        ])
    }
    df = pd.DataFrame(data)
    csv_path = metrics_dir / "cyclomatic_complexity.csv"
    df.to_csv(csv_path, index=False)
    
    return {
        'metrics_dir': metrics_dir,
        'data_path': csv_path,
        'df': df
    }

@pytest.fixture
def setup_test_environment(tmp_path):
    """Set up temporary directories for testing."""
    # Create necessary directories
    (tmp_path / "data" / "metrics").mkdir(parents=True, exist_ok=True)
    (tmp_path / "results" / "figures").mkdir(parents=True, exist_ok=True)
    (tmp_path / "state" / "projects").mkdir(parents=True, exist_ok=True)
    
    return tmp_path

def test_load_metric_data_valid(mock_metric_data):
    """Test loading valid metric data."""
    # Temporarily change METRICS_DIR to our mock directory
    import visualization
    original_path = visualization.METRICS_DIR
    visualization.METRICS_DIR = mock_metric_data['metrics_dir']
    
    try:
        df = load_metric_data('cyclomatic_complexity')
        assert df is not None
        assert len(df) == 100
        assert 'snippet_id' in df.columns
        assert 'group' in df.columns
        assert 'value' in df.columns
        assert set(df['group'].unique()) == {'human', 'llm'}
    finally:
        visualization.METRICS_DIR = original_path

def test_load_metric_data_missing_file(mock_metric_data):
    """Test loading non-existent metric file."""
    import visualization
    original_path = visualization.METRICS_DIR
    visualization.METRICS_DIR = mock_metric_data['metrics_dir']
    
    try:
        df = load_metric_data('nonexistent_metric')
        assert df is None
    finally:
        visualization.METRICS_DIR = original_path

def test_create_boxplot(setup_test_environment):
    """Test boxplot creation."""
    # Create mock data
    data = {
        'snippet_id': [f'snippet_{i}' for i in range(60)],
        'group': ['group_a'] * 30 + ['group_b'] * 30,
        'value': np.concatenate([
            np.random.normal(5, 1, 30),
            np.random.normal(8, 2, 30)
        ])
    }
    df = pd.DataFrame(data)
    
    output_path = setup_test_environment / "results" / "figures" / "test_boxplot.png"
    
    success = create_boxplot(df, 'test_metric', output_path)
    
    assert success
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_create_boxplot_insufficient_groups(setup_test_environment):
    """Test boxplot with insufficient groups."""
    data = {
        'snippet_id': [f'snippet_{i}' for i in range(30)],
        'group': ['single_group'] * 30,
        'value': np.random.normal(5, 1, 30)
    }
    df = pd.DataFrame(data)
    
    output_path = setup_test_environment / "results" / "figures" / "test_single_group.png"
    
    success = create_boxplot(df, 'test_metric', output_path)
    
    # Should fail because we need at least 2 groups
    assert not success

def test_run_visualization_pipeline(setup_test_environment, mock_metric_data):
    """Test the full visualization pipeline."""
    import visualization
    
    # Set up paths
    original_metrics_dir = visualization.METRICS_DIR
    original_figures_dir = visualization.FIGURES_DIR
    
    visualization.METRICS_DIR = mock_metric_data['metrics_dir']
    visualization.FIGURES_DIR = setup_test_environment / "results" / "figures"
    
    try:
        results = run_visualization_pipeline()
        
        assert 'total_metrics' in results
        assert 'successful' in results
        assert 'failed' in results
        assert 'results' in results
        
        # At least one metric should be successful (cyclomatic_complexity)
        assert results['successful'] >= 1
        
        # Check that figure files were created
        for result in results['results']:
            if result['success']:
                assert Path(result['path']).exists()
    finally:
        visualization.METRICS_DIR = original_metrics_dir
        visualization.FIGURES_DIR = original_figures_dir
