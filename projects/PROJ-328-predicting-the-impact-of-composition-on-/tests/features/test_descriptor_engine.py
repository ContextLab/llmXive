import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path

# Mock the config to return temp directories if needed, or rely on real paths if setup
# For unit test, we create a minimal valid CSV
from features.descriptor_engine import DescriptorEngine

def create_mock_cleaned_csv(tmp_path):
    """Creates a minimal valid solder_hardness_cleaned.csv for testing."""
    data = {
        'element_Sn': [60.0, 95.0, 50.0],
        'element_Pb': [40.0, 0.0, 10.0],
        'element_Ag': [0.0, 5.0, 40.0],
        'hardness_hv': [15.5, 20.0, 18.0],
        'alloy_family': ['SnPb', 'SnAg', 'SnAgCu'],
        'source_citation': ['A', 'B', 'C'],
        'measurement_temp_c': [25.0, 25.0, 25.0]
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "solder_hardness_cleaned.csv"
    df.to_csv(file_path, index=False)
    return file_path

def test_clr_transform(tmp_path):
    """Test T023b: Apply CLR Transform"""
    input_file = create_mock_cleaned_csv(tmp_path)
    output_file = tmp_path / "clr_features.csv"

    engine = DescriptorEngine()
    # Patch the data directory for the test
    original_dir = engine.data_processed_dir
    engine.data_processed_dir = tmp_path

    try:
        engine.apply_clr_transform(str(input_file), str(output_file))
        
        assert output_file.exists(), "CLR output file was not created."
        
        clr_df = pd.read_csv(output_file)
        
        # Check columns exist (clr_ prefixed)
        assert 'clr_element_Sn' in clr_df.columns
        assert 'clr_element_Pb' in clr_df.columns
        assert 'clr_element_Ag' in clr_df.columns
        
        # Check values are numeric
        assert np.issubdtype(clr_df['clr_element_Sn'].dtype, np.number)
        
        # Basic sanity check: CLR values should sum to 0 for each row (approx, due to float precision)
        # Sum of log(x_i) - log(gm) = sum(log(x_i)) - n*log(gm)
        # Actually, sum(clr) = sum(log(x_i/gm)) = sum(log(x_i)) - sum(log(gm)) = sum(log(x_i)) - n*log(gm)
        # Since gm = (prod(x_i))^(1/n), log(gm) = (1/n) sum(log(x_i))
        # So sum(clr) = sum(log(x_i)) - n * (1/n) sum(log(x_i)) = 0.
        row_sums = clr_df[[c for c in clr_df.columns if c.startswith('clr_')]].sum(axis=1)
        assert np.allclose(row_sums, 0.0, atol=1e-5), "CLR transform property (sum=0) violated."
        
    finally:
        engine.data_processed_dir = original_dir

def test_physical_descriptors(tmp_path):
    """Test T023c: Compute Physical Descriptors (sanity check on structure)"""
    input_file = create_mock_cleaned_csv(tmp_path)
    output_file = tmp_path / "descriptors.csv"

    engine = DescriptorEngine()
    original_dir = engine.data_processed_dir
    engine.data_processed_dir = tmp_path

    try:
        engine.compute_physical_descriptors(str(input_file), str(output_file))
        
        assert output_file.exists(), "Descriptors output file was not created."
        
        desc_df = pd.read_csv(output_file)
        
        expected_cols = [
            'alloy_id', 'weighted_mean_atomic_mass', 'electronegativity_variance',
            'atomic_radius_variance', 'weighted_avg_melting_point', 'valence_electron_concentration'
        ]
        
        for col in expected_cols:
            assert col in desc_df.columns, f"Missing column: {col}"
            
    finally:
        engine.data_processed_dir = original_dir
