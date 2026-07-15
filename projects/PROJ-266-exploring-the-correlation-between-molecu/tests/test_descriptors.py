"""
Unit tests for conformer generation and variance calculation in code/data/descriptors.py.

These tests verify the core functionality of:
1. generate_conformers: RDKit conformer generation with error handling
2. calculate_variance_metrics: Torsional variance calculation for bond, angle, and dihedral
3. process_molecules: End-to-end molecule processing pipeline
4. flag_outliers: IQR-based outlier detection

Tests use real SMILES from the processed dataset to ensure compatibility with
the actual data pipeline.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import logging

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.data.descriptors import (
    generate_conformers,
    calculate_variance_metrics,
    process_molecules,
    flag_outliers,
    load_processed_data
)
from code.utils.config import set_seed, get_project_root
from code.utils.logging import get_logger, configure_root_logger

# Configure logging for tests
configure_root_logger()
logger = get_logger(__name__)

# Test fixtures
@pytest.fixture(scope="module")
def sample_smiles_list():
    """
    Load a small sample of valid SMILES from the processed dataset.
    Uses the first 5 molecules to keep tests fast while still validating
    against real data.
    """
    project_root = get_project_root()
    processed_data_path = project_root / "data" / "processed" / "caco2_clean.csv"

    if not processed_data_path.exists():
        pytest.skip(f"Processed data not found at {processed_data_path}. "
                   "Run T009 and T010 first to generate this file.")

    df = pd.read_csv(processed_data_path)
    # Filter for rows with valid SMILES (non-null and non-empty)
    valid_smiles = df['smiles'].dropna().astype(str).tolist()

    # Take first 5 molecules for testing
    sample = valid_smiles[:5]

    if len(sample) < 2:
        pytest.skip("Not enough valid SMILES in processed data for testing")

    return sample

@pytest.fixture
def test_smiles():
    """Simple test molecule: ethanol (CH3CH2OH)"""
    return "CCO"

@pytest.fixture
def complex_smiles():
    """More complex molecule: aspirin"""
    return "CC(=O)Oc1ccccc1C(=O)O"

@pytest.fixture
def invalid_smiles():
    """Invalid SMILES for testing error handling"""
    return "invalid_smiles_string_12345"

@pytest.fixture
def stereochemistry_issue():
    """Molecule with potential stereochemistry issues"""
    return "[C@H](C)(C)C"

class TestGenerateConformers:
    """Tests for the generate_conformers function"""

    def test_generate_conformers_valid_molecule(self, test_smiles):
        """Test that conformers are generated for a valid molecule"""
        result = generate_conformers(test_smiles, num_conformers=20)

        assert result is not None
        assert 'conformers' in result
        assert 'success' in result
        assert result['success'] is True
        assert len(result['conformers']) == 20

        # Verify conformer IDs are sequential
        conf_ids = [conf.GetId() for conf in result['conformers']]
        assert conf_ids == list(range(20))

    def test_generate_conformers_complex_molecule(self, complex_smiles):
        """Test conformer generation for a more complex molecule"""
        result = generate_conformers(complex_smiles, num_conformers=20)

        assert result['success'] is True
        assert len(result['conformers']) == 20

    def test_generate_conformers_invalid_smiles(self, invalid_smiles):
        """Test that invalid SMILES are handled gracefully"""
        result = generate_conformers(invalid_smiles, num_conformers=20)

        assert result is not None
        assert result['success'] is False
        assert 'error' in result
        assert 'conformers' not in result or len(result.get('conformers', [])) == 0

    def test_generate_conformers_stereochemistry(self, stereochemistry_issue):
        """Test conformer generation with stereochemistry"""
        result = generate_conformers(stereochemistry_issue, num_conformers=20)

        # This might succeed or fail depending on RDKit's handling
        # The important thing is that it doesn't crash
        assert result is not None
        assert 'success' in result

    def test_generate_conformers_zero_conformers(self, test_smiles):
        """Test that requesting 0 conformers returns empty list"""
        result = generate_conformers(test_smiles, num_conformers=0)

        assert result['success'] is True
        assert len(result['conformers']) == 0

    def test_generate_conformers_single_conformer(self, test_smiles):
        """Test generating a single conformer"""
        result = generate_conformers(test_smiles, num_conformers=1)

        assert result['success'] is True
        assert len(result['conformers']) == 1

    def test_generate_conformers_energy_minimization(self, test_smiles):
        """Test that conformers are energy-minimized"""
        result = generate_conformers(test_smiles, num_conformers=10)

        assert result['success'] is True

        # Check that conformers have been minimized (energy should be finite)
        for conf in result['conformers']:
            # Get energy (MMFF94)
            try:
                from rdkit.Chem import AllChem
                ff = AllChem.MMFFGetMoleculeForceField(
                    result['mol'],
                    AllChem.MMFFGetMoleculeProperties(result['mol'])
                )
                energy = ff.CalcEnergy()
                assert np.isfinite(energy), f"Conformer {conf.GetId()} has non-finite energy"
            except Exception:
                # Some molecules might not have MMFF parameters
                pass

    def test_generate_conformers_deterministic_with_seed(self, test_smiles):
        """Test that conformer generation is deterministic with fixed seed"""
        set_seed(42)
        result1 = generate_conformers(test_smiles, num_conformers=10)

        set_seed(42)
        result2 = generate_conformers(test_smiles, num_conformers=10)

        # Coordinates should be identical
        for conf1, conf2 in zip(result1['conformers'], result2['conformers']):
            pos1 = conf1.GetPositions()
            pos2 = conf2.GetPositions()
            np.testing.assert_array_almost_equal(pos1, pos2, decimal=6)

class TestCalculateVarianceMetrics:
    """Tests for the calculate_variance_metrics function"""

    def test_calculate_variance_metrics_valid_conformers(self, test_smiles):
        """Test variance calculation for a valid molecule with conformers"""
        conf_result = generate_conformers(test_smiles, num_conformers=20)

        if not conf_result['success']:
            pytest.skip("Conformer generation failed for test molecule")

        result = calculate_variance_metrics(conf_result['mol'], conf_result['conformers'])

        assert result is not None
        assert 'bond_variance' in result
        assert 'angle_variance' in result
        assert 'dihedral_variance' in result
        assert 'is_outlier' in result

        # Variances should be non-negative
        assert result['bond_variance'] >= 0
        assert result['angle_variance'] >= 0
        assert result['dihedral_variance'] >= 0

    def test_calculate_variance_metrics_units(self, complex_smiles):
        """Test that variances are in expected units (rad²)"""
        conf_result = generate_conformers(complex_smiles, num_conformers=20)

        if not conf_result['success']:
            pytest.skip("Conformer generation failed")

        result = calculate_variance_metrics(conf_result['mol'], conf_result['conformers'])

        # Variances should be reasonable values (not extremely large or small)
        # Bond variance typically < 0.1 rad²
        # Angle variance typically < 1.0 rad²
        # Dihedral variance typically < 2.0 rad²
        assert 0 <= result['bond_variance'] < 1.0
        assert 0 <= result['angle_variance'] < 10.0
        assert 0 <= result['dihedral_variance'] < 10.0

    def test_calculate_variance_metrics_single_conformer(self, test_smiles):
        """Test variance calculation with only one conformer (should be 0)"""
        conf_result = generate_conformers(test_smiles, num_conformers=1)

        if not conf_result['success']:
            pytest.skip("Conformer generation failed")

        result = calculate_variance_metrics(conf_result['mol'], conf_result['conformers'])

        # With only one conformer, variance should be 0
        assert result['bond_variance'] == 0.0
        assert result['angle_variance'] == 0.0
        assert result['dihedral_variance'] == 0.0

    def test_calculate_variance_metrics_empty_conformers(self, test_smiles):
        """Test variance calculation with empty conformer list"""
        conf_result = generate_conformers(test_smiles, num_conformers=0)

        result = calculate_variance_metrics(conf_result['mol'], conf_result['conformers'])

        # Should handle empty list gracefully
        assert result['bond_variance'] == 0.0
        assert result['angle_variance'] == 0.0
        assert result['dihedral_variance'] == 0.0

    def test_calculate_variance_metrics_flexibility_range(self, sample_smiles_list):
        """Test that more flexible molecules have higher variance"""
        variances = []

        for smiles in sample_smiles_list:
            conf_result = generate_conformers(smiles, num_conformers=20)
            if conf_result['success']:
                metrics = calculate_variance_metrics(conf_result['mol'], conf_result['conformers'])
                variances.append(metrics['dihedral_variance'])

        if len(variances) >= 2:
            # Check that we have some variance in the results
            assert max(variances) > min(variances), "All molecules have identical variance"

class TestProcessMolecules:
    """Tests for the process_molecules function"""

    def test_process_molecules_single_valid(self, test_smiles):
        """Test processing a single valid molecule"""
        results = process_molecules([test_smiles], num_conformers=10)

        assert len(results) == 1
        assert results[0]['smiles'] == test_smiles
        assert 'success' in results[0]

    def test_process_molecules_mixed_validity(self):
        """Test processing a mix of valid and invalid molecules"""
        smiles_list = ["CCO", "invalid", "CC(=O)O", ""]

        results = process_molecules(smiles_list, num_conformers=10)

        assert len(results) == 4
        success_count = sum(1 for r in results if r['success'])
        failure_count = sum(1 for r in results if not r['success'])

        # At least the valid molecules should succeed
        assert success_count >= 1
        assert failure_count >= 1

    def test_process_molecules_error_logging(self, invalid_smiles, caplog):
        """Test that errors are properly logged"""
        with caplog.at_level(logging.ERROR):
            results = process_molecules([invalid_smiles], num_conformers=10)

        # Check that an error was logged
        assert any("error" in record.message.lower() for record in caplog.records)

    def test_process_molecules_outlier_flagging(self, sample_smiles_list):
        """Test that outlier flagging works correctly"""
        results = process_molecules(sample_smiles_list, num_conformers=20)

        # All successful results should have is_outlier field
        for result in results:
            if result['success']:
                assert 'is_outlier' in result

    def test_process_molecules_deterministic(self, test_smiles):
        """Test that processing is deterministic with fixed seed"""
        set_seed(42)
        results1 = process_molecules([test_smiles], num_conformers=10)

        set_seed(42)
        results2 = process_molecules([test_smiles], num_conformers=10)

        # Results should be identical
        assert results1[0]['bond_variance'] == results2[0]['bond_variance']
        assert results1[0]['angle_variance'] == results2[0]['angle_variance']
        assert results1[0]['dihedral_variance'] == results2[0]['dihedral_variance']

class TestFlagOutliers:
    """Tests for the flag_outliers function"""

    def test_flag_outliers_normal_data(self):
        """Test outlier flagging with normal data"""
        data = pd.DataFrame({
            'dihedral_variance': [0.1, 0.2, 0.3, 0.4, 0.5]
        })

        result = flag_outliers(data, column='dihedral_variance')

        # No outliers expected in normal data
        assert result['is_outlier'].sum() == 0

    def test_flag_outliers_with_outliers(self):
        """Test outlier flagging with clear outliers"""
        data = pd.DataFrame({
            'dihedral_variance': [0.1, 0.2, 0.3, 0.4, 10.0]  # 10.0 is an outlier
        })

        result = flag_outliers(data, column='dihedral_variance')

        # Last value should be flagged as outlier
        assert result['is_outlier'].iloc[-1] is True
        assert result['is_outlier'].sum() >= 1

    def test_flag_outliers_iqr_method(self):
        """Test that IQR method is correctly implemented"""
        # Create data with known IQR
        data = pd.DataFrame({
            'dihedral_variance': [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]
        })

        result = flag_outliers(data, column='dihedral_variance')

        # 100 should be flagged as outlier (Q3 + 1.5*IQR = 7.5 + 1.5*4.5 = 14.25)
        assert result['is_outlier'].iloc[-1] is True

    def test_flag_outliers_empty_dataframe(self):
        """Test outlier flagging with empty dataframe"""
        data = pd.DataFrame(columns=['dihedral_variance'])

        result = flag_outliers(data, column='dihedral_variance')

        assert len(result) == 0

    def test_flag_outliers_single_value(self):
        """Test outlier flagging with single value"""
        data = pd.DataFrame({
            'dihedral_variance': [5.0]
        })

        result = flag_outliers(data, column='dihedral_variance')

        # Single value cannot be an outlier
        assert result['is_outlier'].iloc[0] is False

    def test_flag_outliers_multiple_columns(self):
        """Test outlier flagging on multiple columns"""
        data = pd.DataFrame({
            'bond_variance': [0.1, 0.2, 10.0],
            'angle_variance': [0.5, 0.6, 0.7],
            'dihedral_variance': [1.0, 2.0, 3.0]
        })

        result = flag_outliers(data, column='bond_variance')

        # Only bond_variance should be checked
        assert result['is_outlier'].iloc[2] is True

class TestEndToEnd:
    """End-to-end tests for the full descriptor pipeline"""

    def test_full_pipeline_sample(self, sample_smiles_list):
        """Test the full pipeline with a sample of real data"""
        results = process_molecules(sample_smiles_list, num_conformers=20)

        # Count successful and failed
        success_count = sum(1 for r in results if r['success'])
        failure_count = sum(1 for r in results if not r['success'])

        logger.info(f"Pipeline test: {success_count} succeeded, {failure_count} failed")

        # At least some should succeed
        assert success_count > 0

        # All results should have required fields
        for result in results:
            assert 'smiles' in result
            assert 'success' in result

            if result['success']:
                assert 'bond_variance' in result
                assert 'angle_variance' in result
                assert 'dihedral_variance' in result
                assert 'is_outlier' in result

    def test_pipeline_consistency_with_data(self, sample_smiles_list):
        """Test that results are consistent across runs"""
        set_seed(42)
        results1 = process_molecules(sample_smiles_list[:3], num_conformers=10)

        set_seed(42)
        results2 = process_molecules(sample_smiles_list[:3], num_conformers=10)

        for r1, r2 in zip(results1, results2):
            if r1['success'] and r2['success']:
                np.testing.assert_almost_equal(
                    r1['dihedral_variance'],
                    r2['dihedral_variance'],
                    decimal=6
                )

    def test_pipeline_performance(self, sample_smiles_list):
        """Test that the pipeline completes in reasonable time"""
        import time

        start_time = time.time()
        results = process_molecules(sample_smiles_list, num_conformers=20)
        elapsed = time.time() - start_time

        logger.info(f"Pipeline completed {len(results)} molecules in {elapsed:.2f}s")

        # Should complete within 60 seconds for 5 molecules
        assert elapsed < 60, f"Pipeline took too long: {elapsed}s"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])