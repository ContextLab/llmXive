"""
Test suite for plot_final_figures.py
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.config.environment import get_local_paths
from code.analysis.plot_final_figures import (
    ensure_output_dir,
    load_processed_dataset,
    load_sensitivity_results,
    load_subgroup_results,
    plot_linear_fit,
    plot_threshold_sensitivity,
    plot_subgroup_comparison,
    main
)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    temp_base = tempfile.mkdtemp()
    yield {
        'base': temp_base,
        'data': os.path.join(temp_base, 'data', 'processed'),
        'figures': os.path.join(temp_base, 'paper', 'figures')
    }
    shutil.rmtree(temp_base)

@pytest.fixture
def mock_processed_data(temp_dirs):
    """Create mock processed dataset."""
    os.makedirs(temp_dirs['data'], exist_ok=True)
    df = pd.DataFrame({
        'sample_id': [f'S{i}' for i in range(100)],
        'heteroplasmy_burden': np.random.uniform(0, 10, 100),
        'age': np.random.uniform(20, 80, 100),
        'sex': np.random.choice(['M', 'F'], 100),
        'ancestry': np.random.choice(['EUR', 'AFR', 'EAS'], 100)
    })
    path = os.path.join(temp_dirs['data'], 'mito_aging_dataset.csv')
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def mock_sensitivity_data(temp_dirs):
    """Create mock sensitivity results."""
    os.makedirs(temp_dirs['data'], exist_ok=True)
    df = pd.DataFrame({
        'threshold': [0.5, 1.0, 2.0],
        'coefficient': [0.15, 0.18, 0.12],
        'p_value': [0.01, 0.005, 0.02]
    })
    path = os.path.join(temp_dirs['data'], 'sensitivity_results.csv')
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def mock_subgroup_data(temp_dirs):
    """Create mock subgroup results."""
    os.makedirs(temp_dirs['data'], exist_ok=True)
    df = pd.DataFrame({
        'ancestry': ['EUR', 'AFR', 'EAS', 'SAS', 'AMR'],
        'coefficient': [0.18, 0.12, 0.15, 0.10, 0.14],
        'p_value': [0.005, 0.02, 0.01, 0.03, 0.015]
    })
    path = os.path.join(temp_dirs['data'], 'subgroup_results.csv')
    df.to_csv(path, index=False)
    return path

def test_ensure_output_dir(temp_dirs):
    """Test that output directory is created."""
    # Mock get_local_paths to use temp dirs
    import code.analysis.plot_final_figures as pf_module
    original_get_local_paths = pf_module.get_local_paths
    
    def mock_get_local_paths():
        return {
            'figures_dir': temp_dirs['figures'],
            'processed_dataset_path': os.path.join(temp_dirs['data'], 'mito_aging_dataset.csv'),
            'sensitivity_results_path': os.path.join(temp_dirs['data'], 'sensitivity_results.csv'),
            'subgroup_results_path': os.path.join(temp_dirs['data'], 'subgroup_results.csv')
        }
    
    pf_module.get_local_paths = mock_get_local_paths
    
    try:
        result_dir = ensure_output_dir()
        assert os.path.exists(result_dir)
        assert result_dir == temp_dirs['figures']
    finally:
        pf_module.get_local_paths = original_get_local_paths

def test_load_processed_dataset(mock_processed_data, temp_dirs):
    """Test loading processed dataset."""
    import code.analysis.plot_final_figures as pf_module
    original_get_local_paths = pf_module.get_local_paths
    
    def mock_get_local_paths():
        return {
            'figures_dir': temp_dirs['figures'],
            'processed_dataset_path': mock_processed_data,
            'sensitivity_results_path': os.path.join(temp_dirs['data'], 'sensitivity_results.csv'),
            'subgroup_results_path': os.path.join(temp_dirs['data'], 'subgroup_results.csv')
        }
    
    pf_module.get_local_paths = mock_get_local_paths
    
    try:
        df = load_processed_dataset()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 100
        assert 'heteroplasmy_burden' in df.columns
        assert 'age' in df.columns
    finally:
        pf_module.get_local_paths = original_get_local_paths

def test_load_sensitivity_results(mock_sensitivity_data, temp_dirs):
    """Test loading sensitivity results."""
    import code.analysis.plot_final_figures as pf_module
    original_get_local_paths = pf_module.get_local_paths
    
    def mock_get_local_paths():
        return {
            'figures_dir': temp_dirs['figures'],
            'processed_dataset_path': os.path.join(temp_dirs['data'], 'mito_aging_dataset.csv'),
            'sensitivity_results_path': mock_sensitivity_data,
            'subgroup_results_path': os.path.join(temp_dirs['data'], 'subgroup_results.csv')
        }
    
    pf_module.get_local_paths = mock_get_local_paths
    
    try:
        df = load_sensitivity_results()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert 'threshold' in df.columns
        assert 'coefficient' in df.columns
    finally:
        pf_module.get_local_paths = original_get_local_paths

def test_load_subgroup_results(mock_subgroup_data, temp_dirs):
    """Test loading subgroup results."""
    import code.analysis.plot_final_figures as pf_module
    original_get_local_paths = pf_module.get_local_paths
    
    def mock_get_local_paths():
        return {
            'figures_dir': temp_dirs['figures'],
            'processed_dataset_path': os.path.join(temp_dirs['data'], 'mito_aging_dataset.csv'),
            'sensitivity_results_path': os.path.join(temp_dirs['data'], 'sensitivity_results.csv'),
            'subgroup_results_path': mock_subgroup_data
        }
    
    pf_module.get_local_paths = mock_get_local_paths
    
    try:
        df = load_subgroup_results()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert 'ancestry' in df.columns
        assert 'coefficient' in df.columns
    finally:
        pf_module.get_local_paths = original_get_local_paths

def test_plot_linear_fit(mock_processed_data, temp_dirs):
    """Test linear fit plot generation."""
    import code.analysis.plot_final_figures as pf_module
    original_get_local_paths = pf_module.get_local_paths
    
    def mock_get_local_paths():
        return {
            'figures_dir': temp_dirs['figures'],
            'processed_dataset_path': mock_processed_data,
            'sensitivity_results_path': os.path.join(temp_dirs['data'], 'sensitivity_results.csv'),
            'subgroup_results_path': os.path.join(temp_dirs['data'], 'subgroup_results.csv')
        }
    
    pf_module.get_local_paths = mock_get_local_paths
    
    try:
        output_path = os.path.join(temp_dirs['figures'], 'test_fit.png')
        df = load_processed_dataset()
        plot_linear_fit(df, output_path)
        
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    finally:
        pf_module.get_local_paths = original_get_local_paths

def test_plot_threshold_sensitivity(mock_sensitivity_data, temp_dirs):
    """Test threshold sensitivity plot generation."""
    import code.analysis.plot_final_figures as pf_module
    original_get_local_paths = pf_module.get_local_paths
    
    def mock_get_local_paths():
        return {
            'figures_dir': temp_dirs['figures'],
            'processed_dataset_path': os.path.join(temp_dirs['data'], 'mito_aging_dataset.csv'),
            'sensitivity_results_path': mock_sensitivity_data,
            'subgroup_results_path': os.path.join(temp_dirs['data'], 'subgroup_results.csv')
        }
    
    pf_module.get_local_paths = mock_get_local_paths
    
    try:
        output_path = os.path.join(temp_dirs['figures'], 'test_sensitivity.png')
        df = load_sensitivity_results()
        plot_threshold_sensitivity(df, output_path)
        
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    finally:
        pf_module.get_local_paths = original_get_local_paths

def test_plot_subgroup_comparison(mock_subgroup_data, temp_dirs):
    """Test subgroup comparison plot generation."""
    import code.analysis.plot_final_figures as pf_module
    original_get_local_paths = pf_module.get_local_paths
    
    def mock_get_local_paths():
        return {
            'figures_dir': temp_dirs['figures'],
            'processed_dataset_path': os.path.join(temp_dirs['data'], 'mito_aging_dataset.csv'),
            'sensitivity_results_path': os.path.join(temp_dirs['data'], 'sensitivity_results.csv'),
            'subgroup_results_path': mock_subgroup_data
        }
    
    pf_module.get_local_paths = mock_get_local_paths
    
    try:
        output_path = os.path.join(temp_dirs['figures'], 'test_subgroup.png')
        df = load_subgroup_results()
        plot_subgroup_comparison(df, output_path)
        
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    finally:
        pf_module.get_local_paths = original_get_local_paths

def test_main_integration(mock_processed_data, mock_sensitivity_data, mock_subgroup_data, temp_dirs):
    """Test main function generates all figures."""
    import code.analysis.plot_final_figures as pf_module
    original_get_local_paths = pf_module.get_local_paths
    
    def mock_get_local_paths():
        return {
            'figures_dir': temp_dirs['figures'],
            'processed_dataset_path': mock_processed_data,
            'sensitivity_results_path': mock_sensitivity_data,
            'subgroup_results_path': mock_subgroup_data
        }
    
    pf_module.get_local_paths = mock_get_local_paths
    
    try:
        main()
        
        # Check all expected files exist
        expected_files = [
            'rank_ols_fit.png',
            'threshold_sensitivity.png',
            'subgroup_comparison.png'
        ]
        
        for filename in expected_files:
            filepath = os.path.join(temp_dirs['figures'], filename)
            assert os.path.exists(filepath), f"Missing expected file: {filepath}"
            assert os.path.getsize(filepath) > 0, f"Empty file: {filepath}"
    finally:
        pf_module.get_local_paths = original_get_local_paths

def test_missing_data_raises_error(temp_dirs):
    """Test that missing data files raise appropriate errors."""
    import code.analysis.plot_final_figures as pf_module
    original_get_local_paths = pf_module.get_local_paths
    
    def mock_get_local_paths():
        return {
            'figures_dir': temp_dirs['figures'],
            'processed_dataset_path': '/nonexistent/path.csv',
            'sensitivity_results_path': '/nonexistent/path.csv',
            'subgroup_results_path': '/nonexistent/path.csv'
        }
    
    pf_module.get_local_paths = mock_get_local_paths
    
    try:
        with pytest.raises(FileNotFoundError):
            load_processed_dataset()
    finally:
        pf_module.get_local_paths = original_get_local_paths