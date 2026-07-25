"""
Unit tests for conformer generation and variance calculation in code/data/descriptors.py.

This module validates:
1. Conformer generation logic (RDKit ETKDG)
2. Variance calculation for bond, angle, and dihedral internal coordinates
3. Outlier flagging using IQR method
4. Integration with the real data pipeline (loading processed data)

Tests use real molecules from the processed dataset (data/processed/caco2_cleaned.csv)
to ensure validity against actual chemical structures.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import the functions under test from the existing API surface
from code.data.descriptors import (
    load_processed_data,
    generate_conformers,
    calculate_variance_metrics,
    flag_outliers,
    process_molecules
)
from code.utils.config import get_project_root, set_seed

# Set a fixed seed for deterministic testing
set_seed(42)

# Path constants
PROJECT_ROOT = get_project_root()
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "caco2_cleaned.csv"

# Sample SMILES for unit testing conformer generation edge cases
# Small molecule (benzene) - should generate conformers easily
SMILES_BENZENE = "c1ccccc1"
# Flexible molecule (long chain) - tests torsional variance
SMILES_HEPTANE = "CCCCCCC"
# Rigid molecule (steroid-like) - tests variance stability
SMILES_STEROID = "C1CCC2C1CCC3C2CCC4C3CCCC4"
# Invalid SMILES for error handling test
SMILES_INVALID = "invalid_smiles_string_123"

@pytest.fixture
def sample_processed_data():
    """Create a minimal processed dataset for testing."""
    data = {
        'smiles': [SMILES_BENZENE, SMILES_HEPTANE, SMILES_STEROID],
        'logPapp': [-5.0, -4.5, -6.0],
        'mol_weight': [78.11, 100.20, 372.50],
        'logP': [2.13, 4.50, 5.20],
        'psa': [0.0, 0.0, 0.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def processed_data_file(tmp_path, sample_processed_data):
    """Save sample data to a temporary file and return the path."""
    file_path = tmp_path / "test_caco2_cleaned.csv"
    sample_processed_data.to_csv(file_path, index=False)
    return file_path

class TestConformerGeneration:
    """Tests for the generate_conformers function."""

    def test_generate_conformers_benzene(self):
        """Test conformer generation for a small, rigid molecule (benzene)."""
        # Expected: 20 conformers as per DEV-001
        conformers = generate_conformers(SMILES_BENZENE, n_conformers=20)
        
        assert conformers is not None, "Conformer generation failed for benzene"
        assert len(conformers) == 20, f"Expected 20 conformers, got {len(conformers)}"
        assert all(c is not None for c in conformers), "Some conformers were None"

    def test_generate_conformers_flexible(self):
        """Test conformer generation for a flexible molecule (heptane)."""
        conformers = generate_conformers(SMILES_HEPTANE, n_conformers=20)
        
        assert conformers is not None, "Conformer generation failed for heptane"
        assert len(conformers) == 20, f"Expected 20 conformers, got {len(conformers)}"

    def test_generate_conformers_invalid_smiles(self):
        """Test conformer generation with invalid SMILES returns None."""
        result = generate_conformers(SMILES_INVALID, n_conformers=20)
        assert result is None, "Should return None for invalid SMILES"

    def test_generate_conformers_count_parameter(self):
        """Test that the number of conformers matches the requested count."""
        for n in [5, 10, 20]:
            conformers = generate_conformers(SMILES_BENZENE, n_conformers=n)
            assert conformers is not None
            assert len(conformers) == n

    def test_generate_conformers_3d_coordinates(self):
        """Test that generated conformers have 3D coordinates."""
        conformers = generate_conformers(SMILES_BENZENE, n_conformers=1)
        mol = conformers[0]
        
        # Check that the molecule has 3D coordinates
        for atom in mol.GetAtoms():
            pos = mol.GetConformer().GetAtomPosition(atom.GetIdx())
            assert pos.x != 0.0 or pos.y != 0.0 or pos.z != 0.0, \
                "Atom positions should be 3D (not all zeros)"

class TestVarianceCalculation:
    """Tests for the calculate_variance_metrics function."""

    def test_variance_calculation_benzene(self):
        """Test variance calculation for benzene (should have low variance)."""
        conformers = generate_conformers(SMILES_BENZENE, n_conformers=20)
        assert conformers is not None, "Failed to generate conformers for benzene"
        
        metrics = calculate_variance_metrics(conformers)
        
        assert metrics is not None, "Variance calculation failed"
        assert 'bond_variance' in metrics, "Missing bond_variance in metrics"
        assert 'angle_variance' in metrics, "Missing angle_variance in metrics"
        assert 'dihedral_variance' in metrics, "Missing dihedral_variance in metrics"
        
        # Benzene is rigid, so variances should be relatively low
        assert metrics['bond_variance'] >= 0, "Bond variance must be non-negative"
        assert metrics['angle_variance'] >= 0, "Angle variance must be non-negative"
        assert metrics['dihedral_variance'] >= 0, "Dihedral variance must be non-negative"

    def test_variance_calculation_flexible(self):
        """Test variance calculation for heptane (should have higher variance)."""
        conformers = generate_conformers(SMILES_HEPTANE, n_conformers=20)
        assert conformers is not None, "Failed to generate conformers for heptane"
        
        metrics = calculate_variance_metrics(conformers)
        
        assert metrics is not None, "Variance calculation failed"
        assert metrics['bond_variance'] >= 0
        assert metrics['angle_variance'] >= 0
        assert metrics['dihedral_variance'] >= 0

    def test_variance_calculation_empty_conformers(self):
        """Test variance calculation with empty conformer list."""
        metrics = calculate_variance_metrics([])
        assert metrics is None, "Should return None for empty conformer list"

    def test_variance_calculation_single_conformer(self):
        """Test variance calculation with a single conformer (variance should be 0)."""
        conformers = generate_conformers(SMILES_BENZENE, n_conformers=1)
        assert conformers is not None
        
        metrics = calculate_variance_metrics(conformers)
        
        # With only one conformer, variance is 0 (or very close to 0 due to float precision)
        assert metrics['bond_variance'] < 1e-10, "Variance should be ~0 for single conformer"
        assert metrics['angle_variance'] < 1e-10
        assert metrics['dihedral_variance'] < 1e-10

    def test_variance_units(self):
        """Test that variances are in rad^2 (or dimensionless for bonds/angles)."""
        conformers = generate_conformers(SMILES_HEPTANE, n_conformers=20)
        metrics = calculate_variance_metrics(conformers)
        
        # Variances should be non-negative floats
        assert isinstance(metrics['bond_variance'], (int, float))
        assert isinstance(metrics['angle_variance'], (int, float))
        assert isinstance(metrics['dihedral_variance'], (int, float))

class TestOutlierFlagging:
    """Tests for the flag_outliers function."""

    def test_flag_outliers_basic(self):
        """Test outlier flagging with a dataset containing clear outliers."""
        data = pd.DataFrame({
            'bond_variance': [0.1, 0.1, 0.1, 0.1, 10.0],  # Last one is an outlier
            'angle_variance': [0.05, 0.05, 0.05, 0.05, 5.0],
            'dihedral_variance': [0.02, 0.02, 0.02, 0.02, 2.0]
        })
        
        result = flag_outliers(data)
        
        assert 'is_outlier' in result.columns, "Missing is_outlier column"
        assert result['is_outlier'].sum() == 1, "Should flag exactly one outlier"
        assert result.iloc[-1]['is_outlier'] == True, "Last row should be flagged as outlier"
        assert result.iloc[0]['is_outlier'] == False, "First row should not be flagged"

    def test_flag_outliers_no_outliers(self):
        """Test outlier flagging with a dataset containing no outliers."""
        data = pd.DataFrame({
            'bond_variance': [0.1, 0.1, 0.1, 0.1],
            'angle_variance': [0.05, 0.05, 0.05, 0.05],
            'dihedral_variance': [0.02, 0.02, 0.02, 0.02]
        })
        
        result = flag_outliers(data)
        
        assert result['is_outlier'].sum() == 0, "Should flag no outliers"
        assert all(~result['is_outlier']), "All rows should be False"

    def test_flag_outliers_empty_dataframe(self):
        """Test outlier flagging with an empty DataFrame."""
        data = pd.DataFrame(columns=['bond_variance', 'angle_variance', 'dihedral_variance'])
        result = flag_outliers(data)
        
        assert 'is_outlier' in result.columns
        assert len(result) == 0

    def test_flag_outliers_iqr_method(self):
        """Verify IQR method is used correctly."""
        # Create data where IQR method should flag specific values
        # Q1 = 0.25, Q3 = 0.75, IQR = 0.5, Upper = 0.75 + 1.5*0.5 = 1.5
        data = pd.DataFrame({
            'bond_variance': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 2.0],  # 2.0 > 1.5
            'angle_variance': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
            'dihedral_variance': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        })
        
        result = flag_outliers(data)
        
        # The last row should be flagged as an outlier based on bond_variance
        assert result.iloc[-1]['is_outlier'] == True, "Outlier detection failed"

class TestProcessMolecules:
    """Integration tests for the process_molecules function."""

    def test_process_molecules_full_pipeline(self, processed_data_file):
        """Test the full pipeline from loading data to writing results."""
        # Run the full processing pipeline
        results = process_molecules(
            input_path=processed_data_file,
            output_path=processed_data_file.parent / "test_descriptors.csv",
            n_conformers=20
        )
        
        assert results is not None, "Processing failed"
        assert 'smiles' in results.columns, "Missing smiles column"
        assert 'bond_variance' in results.columns, "Missing bond_variance column"
        assert 'angle_variance' in results.columns, "Missing angle_variance column"
        assert 'dihedral_variance' in results.columns, "Missing dihedral_variance column"
        assert 'is_outlier' in results.columns, "Missing is_outlier column"
        
        # Check that valid molecules were processed
        valid_rows = results[results['bond_variance'].notna()]
        assert len(valid_rows) > 0, "No valid molecules were processed"

    def test_process_molecules_error_handling(self, processed_data_file):
        """Test that the pipeline handles invalid SMILES gracefully."""
        # Add an invalid SMILES to the test data
        data = pd.read_csv(processed_data_file)
        data = pd.concat([data, pd.DataFrame({'smiles': [SMILES_INVALID], 'logPapp': [-5.0]})], ignore_index=True)
        data.to_csv(processed_data_file, index=False)
        
        # Process should still work, skipping invalid molecules
        results = process_molecules(
            input_path=processed_data_file,
            output_path=processed_data_file.parent / "test_descriptors_with_invalid.csv",
            n_conformers=20
        )
        
        # Should have processed the valid molecules
        assert results is not None
        assert len(results) >= 3, "Should have processed at least the 3 valid molecules"

class TestLoadProcessedData:
    """Tests for the load_processed_data function."""

    def test_load_processed_data_existing_file(self, processed_data_file):
        """Test loading data from an existing file."""
        df = load_processed_data(processed_data_file)
        
        assert df is not None, "Failed to load data"
        assert 'smiles' in df.columns, "Missing smiles column"
        assert 'logPapp' in df.columns, "Missing logPapp column"
        assert len(df) == 3, f"Expected 3 rows, got {len(df)}"

    def test_load_processed_data_missing_file(self):
        """Test loading data from a missing file raises appropriate error."""
        missing_path = PROJECT_ROOT / "data" / "processed" / "nonexistent.csv"
        with pytest.raises(FileNotFoundError):
            load_processed_data(missing_path)

class TestIntegrationWithRealData:
    """Integration tests using the real processed dataset if available."""

    @pytest.mark.skipif(not PROCESSED_DATA_PATH.exists(), reason="Real processed data not available")
    def test_conformer_generation_on_real_data(self):
        """Test conformer generation on a sample of real data."""
        df = load_processed_data(PROCESSED_DATA_PATH)
        
        # Test on first 5 molecules
        sample_smiles = df['smiles'].dropna().head(5).tolist()
        
        successful = 0
        for smiles in sample_smiles:
            conformers = generate_conformers(smiles, n_conformers=20)
            if conformers is not None and len(conformers) == 20:
                successful += 1
        
        # At least 80% should succeed
        success_rate = successful / len(sample_smiles)
        assert success_rate >= 0.8, f"Conformer generation success rate too low: {success_rate}"

    @pytest.mark.skipif(not PROCESSED_DATA_PATH.exists(), reason="Real processed data not available")
    def test_variance_calculation_on_real_data(self):
        """Test variance calculation on a sample of real data."""
        df = load_processed_data(PROCESSED_DATA_PATH)
        
        sample_smiles = df['smiles'].dropna().head(3).tolist()
        
        for smiles in sample_smiles:
            conformers = generate_conformers(smiles, n_conformers=20)
            if conformers is not None:
                metrics = calculate_variance_metrics(conformers)
                assert metrics is not None, f"Variance calculation failed for {smiles}"
                assert metrics['bond_variance'] >= 0
                assert metrics['angle_variance'] >= 0
                assert metrics['dihedral_variance'] >= 0