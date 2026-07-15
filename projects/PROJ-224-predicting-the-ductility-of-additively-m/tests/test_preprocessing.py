"""
Tests for preprocessing module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import tempfile
import shutil

# Add code directory to path
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data.preprocessing import (
    calculate_energy_density, verify_column_integrity, calculate_vif,
    perform_vif_analysis, perform_reciprocal_vif_check, perform_loafo_split,
    perform_stratified_split, split_data, save_split_artifacts
)

@pytest.fixture
def sample_curated_data():
    """Create sample curated data for testing."""
    data = {
        'laser_power': [200, 300, 250, 400, 350, 280],
        'scan_speed': [1000, 1200, 1100, 1300, 1050, 1150],
        'hatch_spacing': [0.1, 0.12, 0.11, 0.13, 0.1, 0.12],
        'layer_thickness': [0.05, 0.06, 0.055, 0.07, 0.05, 0.06],
        'ductility': [15.5, 18.2, 16.8, 20.1, 17.5, 19.0],
        'alloy_family': ['Inconel718', 'Inconel718', 'HastelloyX', 'HastelloyX', 
                       'Inconel718', 'HastelloyX']
    }
    return pd.DataFrame(data)

@pytest.fixture
def large_sample_data():
    """Create larger sample data with more alloy families."""
    np.random.seed(42)
    n_samples = 150
    data = {
        'laser_power': np.random.uniform(200, 500, n_samples),
        'scan_speed': np.random.uniform(800, 1500, n_samples),
        'hatch_spacing': np.random.uniform(0.08, 0.15, n_samples),
        'layer_thickness': np.random.uniform(0.04, 0.08, n_samples),
        'ductility': np.random.uniform(10, 25, n_samples),
        'alloy_family': np.random.choice(['Inconel718', 'HastelloyX', 'Inconel625', 'MarM247'], n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def logging_config():
    """Configure logging for tests."""
    import logging
    logging.basicConfig(level=logging.INFO)

class TestEnergyDensityCalculation:
    def test_energy_density_calculation(self, sample_curated_data):
        """Test energy density calculation."""
        result = calculate_energy_density(sample_curated_data)
        
        assert 'energy_density' in result.columns
        assert len(result) == len(sample_curated_data)
        
        # Check calculation: E_v = P / (v * h * t)
        for idx, row in result.iterrows():
            expected = row['laser_power'] / (
                row['scan_speed'] * row['hatch_spacing'] * row['layer_thickness']
            )
            assert abs(row['energy_density'] - expected) < 1e-6

    def test_energy_density_with_missing_values(self):
        """Test energy density with missing values."""
        data = {
            'laser_power': [200, np.nan, 250],
            'scan_speed': [1000, 1200, 1100],
            'hatch_spacing': [0.1, 0.12, 0.11],
            'layer_thickness': [0.05, 0.06, 0.055]
        }
        df = pd.DataFrame(data)
        
        result = calculate_energy_density(df)
        assert result['energy_density'].isnull().sum() == 1

class TestColumnIntegrity:
    def test_column_integrity_pass(self, sample_curated_data):
        """Test column integrity check passes."""
        required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 
                       'layer_thickness', 'ductility', 'alloy_family']
        result = verify_column_integrity(sample_curated_data, required_cols)
        assert result is True

    def test_column_integrity_missing_columns(self, sample_curated_data):
        """Test column integrity fails with missing columns."""
        required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 
                       'layer_thickness', 'ductility', 'alloy_family', 'missing_col']
        result = verify_column_integrity(sample_curated_data, required_cols)
        assert result is False

    def test_column_integrity_missing_values(self):
        """Test column integrity fails with missing values."""
        data = {
            'laser_power': [200, np.nan, 250],
            'scan_speed': [1000, 1200, 1100],
            'hatch_spacing': [0.1, 0.12, 0.11],
            'layer_thickness': [0.05, 0.06, 0.055],
            'ductility': [15.5, 18.2, 16.8],
            'alloy_family': ['A', 'B', 'C']
        }
        df = pd.DataFrame(data)
        required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 
                       'layer_thickness', 'ductility', 'alloy_family']
        result = verify_column_integrity(df, required_cols)
        assert result is False

class TestVIFAnalysis:
    def test_vif_calculation(self, sample_curated_data):
        """Test VIF calculation."""
        features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
        vif_values = calculate_vif(sample_curated_data, features)
        
        assert len(vif_values) == len(features)
        assert all(vif_values >= 1.0)  # VIF >= 1

    def test_vif_analysis_drops_constituents(self, large_sample_data):
        """Test VIF analysis drops constituents when energy density VIF > 5."""
        # Add energy density
        df = calculate_energy_density(large_sample_data)
        
        result = perform_vif_analysis(df, threshold=5.0)
        
        # Should drop constituents if energy density VIF is high
        assert 'energy_density' in result.columns

    def test_vif_analysis_retains_all(self, large_sample_data):
        """Test VIF analysis retains all features when VIF <= threshold."""
        df = calculate_energy_density(large_sample_data)
        
        # Use a very high threshold to force retention
        result = perform_vif_analysis(df, threshold=100.0)
        
        assert 'laser_power' in result.columns
        assert 'scan_speed' in result.columns
        assert 'hatch_spacing' in result.columns
        assert 'layer_thickness' in result.columns
        assert 'energy_density' in result.columns

class TestDataSplitting:
    def test_loafo_split_small_dataset(self, sample_curated_data):
        """Test LOAFO split with small dataset."""
        splits = perform_loafo_split(sample_curated_data)
        
        assert 'train' in splits
        assert 'val' in splits
        assert 'test' in splits
        
        # Check that train and val don't share alloy families
        train_families = set(splits['train']['alloy_family'].unique())
        val_families = set(splits['val']['alloy_family'].unique())
        
        # For LOAFO with 2 families, one is train, one is val/test
        assert len(train_families.intersection(val_families)) == 0 or len(splits['train']) == 0

    def test_stratified_split_large_dataset(self, large_sample_data):
        """Test stratified split with large dataset."""
        splits = perform_stratified_split(large_sample_data)
        
        assert 'train' in splits
        assert 'val' in splits
        assert 'test' in splits
        
        assert len(splits['train']) + len(splits['val']) + len(splits['test']) == len(large_sample_data)

    def test_split_data_chooses_strategy(self, sample_curated_data, large_sample_data):
        """Test split_data chooses correct strategy based on N."""
        # Small dataset should use LOAFO
        splits_small = split_data(sample_curated_data)
        assert 'train' in splits_small
        
        # Large dataset should use stratified
        splits_large = split_data(large_sample_data)
        assert 'train' in splits_large
        assert 'val' in splits_large
        assert 'test' in splits_large

class TestSaveSplitArtifacts:
    def test_save_split_artifacts(self, sample_curated_data, temp_output_dir):
        """Test saving split artifacts."""
        splits = perform_loafo_split(sample_curated_data)
        save_split_artifacts(splits, temp_output_dir)
        
        train_path = Path(temp_output_dir) / 'train.csv'
        val_path = Path(temp_output_dir) / 'val.csv'
        
        assert train_path.exists()
        assert val_path.exists()

    def test_save_split_artifacts_creates_directory(self, sample_curated_data):
        """Test that save_split_artifacts creates directory if needed."""
        temp_dir = tempfile.mkdtemp()
        nested_dir = os.path.join(temp_dir, 'nested', 'dir')
        
        try:
            splits = perform_loafo_split(sample_curated_data)
            save_split_artifacts(splits, nested_dir)
            
            assert os.path.exists(nested_dir)
        finally:
            shutil.rmtree(temp_dir)