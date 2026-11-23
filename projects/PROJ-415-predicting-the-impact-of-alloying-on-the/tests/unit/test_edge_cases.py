"""
Unit tests for edge cases in data ingestion and curation.

Covers:
1. Missing atomic data (solute radii not in constants)
2. Single host metal datasets (stratification fallback)
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import tempfile
import os
import json

# Import project modules
from code.data.ingestion import load_and_filter, split_data_stratified
from code.data.curation import exclude_missing_concentration, validate_atomic_radii, log_exclusions
from code.utils.constants import get_metallic_radius

# Configure logging for tests
logging.basicConfig(level=logging.INFO)

class TestMissingAtomicData:
    """Tests for handling missing atomic radii data."""

    def test_validate_atomic_radii_missing_element(self):
        """Verify that missing atomic radii are detected and reported."""
        # Create a dataframe with a non-existent element
        data = {
            'solute_symbol': ['Fe', 'NonExistentElement', 'Cu'],
            'host_symbol': ['Ni', 'Ni', 'Ni'],
            'activation_energy': [1.2, 1.5, 1.3]
        }
        df = pd.DataFrame(data)

        # Check that get_metallic_radius raises KeyError for non-existent element
        # The curation logic should catch this
        assert get_metallic_radius('Fe') is not None
        assert get_metallic_radius('Cu') is not None
        
        # Verify that a non-existent element raises an error
        with pytest.raises(KeyError):
            get_metallic_radius('NonExistentElement')

    def test_validate_atomic_radii_returns_missing_list(self):
        """Verify validate_atomic_radii returns correct missing elements."""
        data = {
            'solute_symbol': ['Fe', 'Unknown', 'Cu', 'AnotherUnknown'],
            'host_symbol': ['Ni', 'Ni', 'Ni', 'Ni'],
            'activation_energy': [1.2, 1.5, 1.3, 1.4]
        }
        df = pd.DataFrame(data)

        missing_elements, missing_details = validate_atomic_radii(df, 'solute_symbol')
        
        assert len(missing_elements) == 2
        assert 'Unknown' in missing_elements
        assert 'AnotherUnknown' in missing_elements
        assert len(missing_details) == 2

    def test_log_exclusions_creates_file(self):
        """Verify that log_exclusions creates the exclusion log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_exclusions.log"
            errors_path = Path(tmpdir) / "errors"
            errors_path.mkdir()
            missing_data_path = errors_path / "missing_atomic_data.csv"
            
            # Create mock exclusions
            exclusions = [
                {'row_id': 1, 'reason_code': 'MISSING_CONCENTRATION'},
                {'row_id': 2, 'reason_code': 'MISSING_ATOMIC_RADIUS'}
            ]
            
            log_exclusions(exclusions, log_path, missing_data_path)
            
            # Verify log file exists and has content
            assert log_path.exists()
            content = log_path.read_text()
            assert 'MISSING_CONCENTRATION' in content
            assert 'MISSING_ATOMIC_RADIUS' in content
            
            # Verify missing atomic data file exists if there were atomic radius issues
            assert missing_data_path.exists()

class TestSingleHostMetal:
    """Tests for handling single host metal datasets."""

    def test_split_data_stratified_single_class_fallback(self):
        """Verify fallback to random split when only one host metal exists."""
        # Create a dataset with only one host metal
        data = {
            'host_symbol': ['Ni', 'Ni', 'Ni', 'Ni', 'Ni', 'Ni', 'Ni', 'Ni'],
            'solute_symbol': ['Fe', 'Cu', 'Zn', 'Ag', 'Au', 'Pd', 'Pt', 'Co'],
            'activation_energy': [1.2, 1.3, 1.1, 1.4, 1.5, 1.25, 1.35, 1.15],
            'concentration': [0.1, 0.2, 0.3, 0.4, 0.5, 0.15, 0.25, 0.35]
        }
        df = pd.DataFrame(data)
        
        features = ['activation_energy', 'concentration']
        target = 'activation_energy'
        
        # This should trigger the fallback to random split
        with pytest.warns(UserWarning) as warning_info:
            train_df, test_df = split_data_stratified(
                df, 
                features + [target], 
                target, 
                test_size=0.2, 
                random_state=42
            )
            
            # Verify the warning message
            assert any('Stratification by host metal was not possible' in str(w.message) 
                      for w in warning_info)
        
        # Verify split still works (random split fallback)
        assert len(train_df) + len(test_df) == len(df)
        assert len(test_df) == int(len(df) * 0.2)

    def test_split_data_stratified_multiple_classes(self):
        """Verify normal stratified split with multiple host metals."""
        # Create a dataset with multiple host metals
        data = {
            'host_symbol': ['Ni', 'Ni', 'Cu', 'Cu', 'Fe', 'Fe', 'Ni', 'Cu'],
            'solute_symbol': ['Fe', 'Cu', 'Zn', 'Ag', 'Au', 'Pd', 'Pt', 'Co'],
            'activation_energy': [1.2, 1.3, 1.1, 1.4, 1.5, 1.25, 1.35, 1.15],
            'concentration': [0.1, 0.2, 0.3, 0.4, 0.5, 0.15, 0.25, 0.35]
        }
        df = pd.DataFrame(data)
        
        features = ['activation_energy', 'concentration']
        target = 'activation_energy'
        
        # This should perform stratified split
        train_df, test_df = split_data_stratified(
            df, 
            features + [target], 
            target, 
            test_size=0.25, 
            random_state=42
        )
        
        # Verify split worked
        assert len(train_df) + len(test_df) == len(df)
        
        # Verify stratification preserved proportions (approximately)
        train_proportions = train_df['host_symbol'].value_counts(normalize=True)
        test_proportions = test_df['host_symbol'].value_counts(normalize=True)
        
        # Check that proportions are similar (within 10% tolerance)
        for host in df['host_symbol'].unique():
            train_prop = train_proportions.get(host, 0)
            test_prop = test_proportions.get(host, 0)
            assert abs(train_prop - test_prop) < 0.1, \
                f"Stratification failed for {host}: train={train_prop}, test={test_prop}"

class TestIntegrationEdgeCases:
    """Integration tests combining multiple edge cases."""

    def test_full_pipeline_missing_data_and_single_host(self):
        """Test full ingestion and curation pipeline with edge cases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data with missing atomic radii and single host
            data = {
                'host_symbol': ['Ni', 'Ni', 'Ni', 'Ni', 'Ni'],
                'solute_symbol': ['Fe', 'Unknown1', 'Cu', 'Unknown2', 'Zn'],
                'activation_energy': [1.2, 1.3, 1.1, 1.4, 1.5],
                'concentration': [0.1, 0.2, None, 0.4, 0.5],  # One missing concentration
                'crystal_structure': ['FCC', 'FCC', 'FCC', 'FCC', 'FCC'],
                'diffusion_mode': ['self', 'self', 'self', 'self', 'self']
            }
            df = pd.DataFrame(data)
            
            # Save to temporary CSV
            csv_path = Path(tmpdir) / "test_data.csv"
            df.to_csv(csv_path, index=False)
            
            # Test ingestion (should filter for FCC self-diffusion)
            filtered_df = load_and_filter([csv_path])
            assert len(filtered_df) == 5  # All should pass initial filter
            assert all(filtered_df['crystal_structure'] == 'FCC')
            assert all(filtered_df['diffusion_mode'] == 'self')
            
            # Test curation (should exclude missing concentration and missing radii)
            log_path = Path(tmpdir) / "exclusions.log"
            errors_dir = Path(tmpdir) / "errors"
            errors_dir.mkdir()
            missing_data_path = errors_dir / "missing_atomic_data.csv"
            
            # This should handle missing concentration and missing atomic radii
            curated_df, exclusions = exclude_missing_concentration(
                filtered_df, 
                log_path=log_path, 
                missing_atomic_data_path=missing_data_path
            )
            
            # Verify exclusions were recorded
            assert len(exclusions) > 0
            assert log_path.exists()
            assert missing_data_path.exists()
            
            # Verify final dataset has only valid entries
            # Should exclude: row with None concentration, rows with Unknown1 and Unknown2
            assert len(curated_df) == 2  # Only Fe and Cu should remain
            assert 'Unknown1' not in curated_df['solute_symbol'].values
            assert 'Unknown2' not in curated_df['solute_symbol'].values
            assert None not in curated_df['concentration'].values