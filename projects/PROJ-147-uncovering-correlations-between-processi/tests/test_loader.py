"""
Tests for code/data/loader.py

Validates:
1. Real data loading attempt (mocked)
2. Synthetic data generation fallback
3. Alloy family validation logic
4. Combined dataset requirements (>=3 families, >=50 samples/family)
"""
import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.data.loader import (
    load_real_materials_project_data,
    load_synthetic_data,
    validate_alloy_families,
    load_and_validate_dataset,
    MIN_SAMPLES_PER_FAMILY,
    MIN_DISTINCT_FAMILIES
)

# Test fixtures
@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory structure for testing."""
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    return tmp_path

@pytest.fixture
def sample_real_data():
    """Create sample real data DataFrame."""
    data = {
        "material_id": [f"mp-{i}" for i in range(100)],
        "formula": ["Al", "Cu", "Mg", "Al", "Cu", "Mg", "Al", "Cu", "Mg", "Al"] * 10,
        "structure_type": ["fcc", "bcc", "hcp"] * 33 + ["fcc"],
        "energy_per_atom": np.random.uniform(-5, 0, 100),
        "density": np.random.uniform(1, 10, 100),
        "band_gap": np.random.uniform(0, 5, 100),
        "n_polarizability": np.random.uniform(0, 10, 100),
        "strain_rate": np.random.uniform(0.001, 0.1, 100),
        "temperature": np.random.uniform(300, 800, 100),
        "reduction_ratio": np.random.uniform(0.1, 0.5, 100),
        "odf_100": np.random.uniform(0.5, 2.0, 100),
        "odf_110": np.random.uniform(0.5, 2.0, 100),
        "odf_111": np.random.uniform(0.5, 2.0, 100),
    }
    df = pd.DataFrame(data)
    # Add alloy_family column
    df['alloy_family'] = df['formula'].apply(
        lambda x: x if x in ['Al', 'Cu', 'Mg'] else 'unknown'
    )
    return df

@pytest.fixture
def sample_synthetic_data():
    """Create sample synthetic data with known ground truth."""
    data = {
        "sample_id": [f"syn-{i}" for i in range(150)],
        "alloy_family": ["Al-alloy"] * 50 + ["Cu-alloy"] * 50 + ["Mg-alloy"] * 50,
        "strain_rate": np.random.uniform(0.001, 0.1, 150),
        "temperature": np.random.uniform(300, 800, 150),
        "reduction_ratio": np.random.uniform(0.1, 0.5, 150),
        "odf_100": np.random.uniform(0.5, 2.0, 150),
        "odf_110": np.random.uniform(0.5, 2.0, 150),
        "odf_111": np.random.uniform(0.5, 2.0, 150),
    }
    return pd.DataFrame(data)

class TestLoadRealData:
    """Tests for real data loading functionality."""
    
    def test_mp_api_import_failure(self, temp_dir):
        """Test graceful handling when mp-api is not installed."""
        output_path = temp_dir / "data" / "raw" / "test_real.csv"
        
        with patch.dict('sys.modules', {'mp_api.client': None}):
            success, df = load_real_materials_project_data(output_path)
        
        assert success is False
        assert df.empty
        
    def test_connection_error_handling(self, temp_dir):
        """Test handling of network errors."""
        output_path = temp_dir / "data" / "raw" / "test_real.csv"
        
        with patch('code.data.loader.MPRester') as mock_mpr:
            mock_mpr.side_effect = ConnectionError("Network error")
            success, df = load_real_materials_project_data(output_path)
        
        assert success is False
        assert df.empty
        
    def test_successful_real_data_load(self, temp_dir, sample_real_data):
        """Test successful real data loading."""
        output_path = temp_dir / "data" / "raw" / "test_real.csv"
        
        with patch('code.data.loader.MPRester') as mock_mpr:
            # Mock the search method to return our sample data
            mock_mpr.return_value.__enter__.return_value.materials.search.return_value = [
                MagicMock(
                    material_id=row['material_id'],
                    formula_pretty=row['formula'],
                    structure_types=[row['structure_type']],
                    energy_per_atom=row['energy_per_atom'],
                    density=row['density'],
                    band_gap=row['band_gap'],
                    n_polarizability=row['n_polarizability']
                ) for _, row in sample_real_data.head(100).iterrows()
            ]
            
            success, df = load_real_materials_project_data(output_path)
        
        assert success is True
        assert not df.empty
        assert len(df) >= 10  # Should have at least 10 samples
        assert output_path.exists()

class TestLoadSyntheticData:
    """Tests for synthetic data generation."""
    
    def test_synthetic_generation(self, temp_dir):
        """Test synthetic data generation with correct family counts."""
        output_path = temp_dir / "data" / "raw" / "test_synthetic.csv"
        
        df = load_synthetic_data(output_path, n_samples=150)
        
        assert not df.empty
        assert len(df) >= 150
        assert output_path.exists()
        
        # Check for at least 3 families
        if 'alloy_family' in df.columns:
            num_families = df['alloy_family'].nunique()
            assert num_families >= MIN_DISTINCT_FAMILIES
        
        # Check ground truth file
        gt_path = temp_dir / "data" / "raw" / "ground_truth.json"
        assert gt_path.exists()
        
        with open(gt_path, 'r') as f:
            gt = json.load(f)
        
        assert gt['family_count'] >= MIN_DISTINCT_FAMILIES
        assert all(count >= MIN_SAMPLES_PER_FAMILY for count in gt['family_counts'].values())

class TestValidateAlloyFamilies:
    """Tests for alloy family validation."""
    
    def test_valid_dataset(self, sample_synthetic_data):
        """Test validation passes for valid dataset."""
        is_valid, report = validate_alloy_families(
            sample_synthetic_data,
            min_families=3,
            min_samples_per_family=50
        )
        
        assert is_valid is True
        assert report['num_families'] >= 3
        assert report['min_samples_per_family'] >= 50
        assert report['meets_min_families'] is True
        assert report['meets_min_samples'] is True
        
    def test_insufficient_families(self):
        """Test validation fails with insufficient families."""
        data = {
            "alloy_family": ["Al-alloy"] * 100,  # Only 1 family
            "value": np.random.uniform(0, 1, 100)
        }
        df = pd.DataFrame(data)
        
        is_valid, report = validate_alloy_families(
            df,
            min_families=3,
            min_samples_per_family=50
        )
        
        assert is_valid is False
        assert report['num_families'] == 1
        assert report['meets_min_families'] is False
        
    def test_insufficient_samples_per_family(self):
        """Test validation fails with insufficient samples per family."""
        data = {
            "alloy_family": ["Al-alloy"] * 30 + ["Cu-alloy"] * 30 + ["Mg-alloy"] * 30,
            "value": np.random.uniform(0, 1, 90)
        }
        df = pd.DataFrame(data)
        
        is_valid, report = validate_alloy_families(
            df,
            min_families=3,
            min_samples_per_family=50
        )
        
        assert is_valid is False
        assert report['min_samples_per_family'] == 30
        assert report['meets_min_samples'] is False
        
    def test_missing_alloy_family_column(self):
        """Test validation with missing alloy_family column."""
        data = {
            "formula": ["Al", "Cu", "Mg"] * 30,
            "value": np.random.uniform(0, 1, 90)
        }
        df = pd.DataFrame(data)
        
        is_valid, report = validate_alloy_families(df)
        
        # Should try to infer from formula
        assert 'alloy_family' in df.columns  # Should be added
        assert report['num_families'] >= 3

class TestLoadAndValidateDataset:
    """Integration tests for the full loading pipeline."""
    
    def test_full_pipeline_synthetic_fallback(self, temp_dir):
        """Test full pipeline with synthetic fallback."""
        raw_path = temp_dir / "data" / "raw" / "test_real.csv"
        processed_path = temp_dir / "data" / "processed" / "test_final.csv"
        
        # Force synthetic mode
        df, report = load_and_validate_dataset(
            raw_data_path=raw_path,
            processed_data_path=processed_path,
            force_synthetic=True
        )
        
        assert not df.empty
        assert report['source_type'] == "Synthetic"
        assert report['num_families'] >= MIN_DISTINCT_FAMILIES
        assert report['min_samples_per_family'] >= MIN_SAMPLES_PER_FAMILY
        assert processed_path.exists()
        
    def test_validation_failure_raises_error(self, temp_dir):
        """Test that validation failure raises ValueError."""
        # Create a dataset that will fail validation
        with patch('code.data.loader.load_synthetic_data') as mock_load:
            # Return a dataset with only 2 families
            bad_data = pd.DataFrame({
                "alloy_family": ["Al-alloy"] * 50 + ["Cu-alloy"] * 50,
                "value": np.random.uniform(0, 1, 100)
            })
            mock_load.return_value = bad_data
            
            with pytest.raises(ValueError, match="Dataset validation failed"):
                load_and_validate_dataset(
                    raw_data_path=temp_dir / "data" / "raw" / "test.csv",
                    processed_data_path=temp_dir / "data" / "processed" / "test.csv",
                    force_synthetic=True
                )
        
    def test_combined_dataset_validation(self, temp_dir, sample_real_data):
        """Test validation of combined real+synthetic dataset."""
        # This test verifies the combined dataset logic
        # In practice, this would merge real and synthetic data
        # For now, we test the validation logic on a valid combined-like dataset
        
        combined_df = pd.concat([
            sample_real_data.head(60).assign(alloy_family=lambda x: x['formula']),
            pd.DataFrame({
                "alloy_family": ["Zn-alloy"] * 50,
                "value": np.random.uniform(0, 1, 50)
            })
        ], ignore_index=True)
        
        is_valid, report = validate_alloy_families(combined_df)
        
        assert is_valid is True
        assert report['num_families'] >= 3
        assert report['min_samples_per_family'] >= 50

class TestMainFunction:
    """Tests for the main entry point."""
    
    def test_main_execution(self, temp_dir, caplog):
        """Test main function execution."""
        import sys
        from code.data import loader as loader_module
        
        # Temporarily change working directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Mock the load_and_validate_dataset to avoid actual file operations
            with patch.object(loader_module, 'load_and_validate_dataset') as mock_load:
                mock_load.return_value = (
                    pd.DataFrame({"alloy_family": ["Al"] * 50, "value": [1] * 50}),
                    {"num_families": 1, "source_type": "Test"}
                )
                
                loader_module.main()
                
                mock_load.assert_called_once()
        finally:
            os.chdir(original_cwd)
