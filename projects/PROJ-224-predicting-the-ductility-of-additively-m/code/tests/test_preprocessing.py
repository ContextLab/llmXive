import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import json
import tempfile
import shutil

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.preprocessing import (
    calculate_energy_density,
    verify_column_integrity,
    calculate_vif,
    perform_vif_analysis,
    perform_loafo_split,
    perform_stratified_split,
    split_data,
    save_split_artifacts
)

@pytest.fixture
def sample_curated_data():
    """Create a sample curated dataset for testing."""
    data = {
        'laser_power': [200, 300, 400, 250, 350, 200, 300, 400],
        'scan_speed': [100, 200, 150, 100, 200, 150, 100, 200],
        'hatch_spacing': [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
        'layer_thickness': [0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05],
        'ductility': [10.5, 12.0, 11.5, 10.0, 13.0, 11.0, 12.5, 14.0],
        'alloy_family': ['Inconel', 'Inconel', 'Inconel', 'Hastelloy', 'Hastelloy', 'Hastelloy', 'Inconel', 'Hastelloy']
    }
    return pd.DataFrame(data)

@pytest.fixture
def large_sample_data():
    """Create a larger sample dataset (>=100 rows) for stratified split testing."""
    np.random.seed(42)
    n = 120
    data = {
        'laser_power': np.random.uniform(200, 400, n),
        'scan_speed': np.random.uniform(100, 300, n),
        'hatch_spacing': np.random.uniform(0.08, 0.12, n),
        'layer_thickness': np.random.uniform(0.03, 0.07, n),
        'ductility': np.random.uniform(8, 15, n),
        'alloy_family': np.random.choice(['Inconel', 'Hastelloy', 'CMSX', 'René'], n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output artifacts."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)

class TestEnergyDensityCalculation:
    def test_calculate_energy_density(self, sample_curated_data):
        """Test energy density calculation."""
        df = calculate_energy_density(sample_curated_data)
        
        assert 'energy_density' in df.columns
        assert not df['energy_density'].isna().all()
        
        # Manual check for first row: P=200, v=100, h=0.1, t=0.05
        # E_v = 200 / (100 * 0.1 * 0.05) = 200 / 0.5 = 400
        expected = 200 / (100 * 0.1 * 0.05)
        assert abs(df['energy_density'].iloc[0] - expected) < 0.01

    def test_calculate_energy_density_zero_denominator(self):
        """Test handling of zero denominator."""
        data = {
            'laser_power': [200],
            'scan_speed': [0],
            'hatch_spacing': [0.1],
            'layer_thickness': [0.05],
            'ductility': [10.0],
            'alloy_family': ['Inconel']
        }
        df = pd.DataFrame(data)
        df = calculate_energy_density(df)
        
        assert df['energy_density'].iloc[0] != df['energy_density'].iloc[0]  # NaN

class TestColumnIntegrity:
    def test_verify_column_integrity_success(self, sample_curated_data):
        """Test successful column verification."""
        required = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'ductility']
        assert verify_column_integrity(sample_curated_data, required) is True

    def test_verify_column_integrity_missing(self, sample_curated_data):
        """Test missing column detection."""
        required = ['laser_power', 'scan_speed', 'missing_col']
        assert verify_column_integrity(sample_curated_data, required) is False

class TestVIFAnalysis:
    def test_calculate_vif(self, sample_curated_data):
        """Test VIF calculation."""
        features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
        vif_series = calculate_vif(sample_curated_data, features)
        
        assert len(vif_series) == len(features)
        assert not vif_series.isna().all()

    def test_perform_vif_analysis(self, sample_curated_data):
        """Test VIF analysis and FR-005 logic."""
        # Add energy density first
        df = calculate_energy_density(sample_curated_data)
        
        filtered_df, predictors = perform_vif_analysis(df)
        
        assert isinstance(filtered_df, pd.DataFrame)
        assert isinstance(predictors, list)
        assert len(predictors) > 0

class TestDataSplitting:
    def test_perform_loafo_split(self, sample_curated_data):
        """Test LOAFO split logic (N < 100)."""
        splits = perform_loafo_split(sample_curated_data, 'ductility', 'alloy_family')
        
        assert 'train' in splits
        assert 'val' in splits
        assert 'test' in splits
        assert splits['strategy'] == 'LOAFO'
        
        # Verify no overlap between train/val and test
        train_groups = set(splits['train']['alloy_family'])
        test_groups = set(splits['test']['alloy_family'])
        assert len(train_groups.intersection(test_groups)) == 0

    def test_perform_stratified_split(self, large_sample_data):
        """Test stratified split logic (N >= 100)."""
        splits = perform_stratified_split(large_sample_data, 'ductility', 'alloy_family')
        
        assert 'train' in splits
        assert 'val' in splits
        assert 'test' in splits
        assert splits['strategy'] == 'Stratified'
        
        # Verify approximate sizes
        total = len(large_sample_data)
        assert abs(len(splits['train']) - 0.7 * total) < total * 0.1
        assert abs(len(splits['val']) - 0.15 * total) < total * 0.1
        assert abs(len(splits['test']) - 0.15 * total) < total * 0.1

    def test_split_data_auto_strategy(self, sample_curated_data, large_sample_data):
        """Test automatic strategy selection based on N."""
        # Small dataset -> LOAFO
        splits_small = split_data(sample_curated_data, 'ductility', 'alloy_family')
        assert splits_small['strategy'] == 'LOAFO'
        
        # Large dataset -> Stratified
        splits_large = split_data(large_sample_data, 'ductility', 'alloy_family')
        assert splits_large['strategy'] == 'Stratified'

    def test_split_data_missing_target(self, sample_curated_data):
        """Test error handling for missing target column."""
        with pytest.raises(ValueError):
            split_data(sample_curated_data, target_col='nonexistent', group_col='alloy_family')

    def test_split_data_deterministic(self, sample_curated_data):
        """Test reproducibility of splits."""
        splits1 = split_data(sample_curated_data, 'ductility', 'alloy_family')
        splits2 = split_data(sample_curated_data, 'ductility', 'alloy_family')
        
        # Compare indices
        assert list(splits1['train'].index) == list(splits2['train'].index)
        assert list(splits1['val'].index) == list(splits2['val'].index)
        assert list(splits1['test'].index) == list(splits2['test'].index)

class TestSaveSplitArtifacts:
    def test_save_split_artifacts_creates_files(self, sample_curated_data, temp_output_dir):
        """Test that split artifacts are saved correctly."""
        splits = split_data(sample_curated_data, 'ductility', 'alloy_family')
        save_split_artifacts(splits, temp_output_dir)
        
        # Check files exist
        assert os.path.exists(os.path.join(temp_output_dir, 'split_train.csv'))
        assert os.path.exists(os.path.join(temp_output_dir, 'split_val.csv'))
        assert os.path.exists(os.path.join(temp_output_dir, 'split_test.csv'))
        assert os.path.exists(os.path.join(temp_output_dir, 'split_metadata.json'))
        
        # Check metadata content
        with open(os.path.join(temp_output_dir, 'split_metadata.json'), 'r') as f:
            metadata = json.load(f)
        
        assert metadata['strategy'] == 'LOAFO'
        assert metadata['n_total'] == len(sample_curated_data)
        assert 'train' in metadata
        assert 'val' in metadata
        assert 'test' in metadata

    def test_save_split_artifacts_creates_directories(self, sample_curated_data):
        """Test that missing directories are created."""
        splits = split_data(sample_curated_data, 'ductility', 'alloy_family')
        new_dir = tempfile.mkdtemp()
        nested_dir = os.path.join(new_dir, 'nested', 'output')
        
        try:
            save_split_artifacts(splits, nested_dir)
            assert os.path.exists(os.path.join(nested_dir, 'split_train.csv'))
        finally:
            shutil.rmtree(new_dir)
