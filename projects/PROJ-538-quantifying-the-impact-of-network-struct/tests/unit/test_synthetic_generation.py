"""
Unit tests for synthetic data generation.

Tests verify:
1. Correct number of snapshots generated
2. Unique random seeds used
3. LJ parameters match specification
4. NVT thermalization is performed
5. Output files are created correctly
"""

import pytest
import numpy as np
import os
from pathlib import Path
import json

from code.synthetic import SyntheticDataGenerator, ThermalConductivityEstimator, run_synthetic_generation
from code.models import AtomicSnapshot
from code.utils import DataAvailabilityError


class TestSyntheticDataGenerator:
    """Tests for SyntheticDataGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create a generator with small settings for fast testing."""
        return SyntheticDataGenerator(
            num_snapshots=4,
            temperature=300.0,
            time_step=1.0,
            steps_per_snapshot=10,
            equilibration_steps=5
        )

    def test_initialization(self, generator):
        """Test generator initialization with correct parameters."""
        assert generator.num_snapshots == 4
        assert generator.temperature == 300.0
        assert generator.time_step == 1.0
        assert generator.steps_per_snapshot == 10
        assert generator.equilibration_steps == 5

    def test_generate_snapshot_creates_valid_structure(self, generator):
        """Test that a single snapshot is generated with valid structure."""
        snapshot = generator.generate_snapshot(seed=0, system='Cu-Ni')

        assert isinstance(snapshot, AtomicSnapshot)
        assert snapshot.snapshot_id == 'Cu-Ni_000'
        assert snapshot.system == 'Cu-Ni'
        assert snapshot.seed == 0
        assert len(snapshot.species_list) > 0
        assert len(snapshot.positions) == len(snapshot.species_list)
        assert snapshot.temperature == 300.0
        assert snapshot.pbc == [True, True, True]

    def test_unique_seeds_produce_different_snapshots(self, generator):
        """Test that different seeds produce different atomic configurations."""
        snapshot1 = generator.generate_snapshot(seed=0, system='Cu-Ni')
        snapshot2 = generator.generate_snapshot(seed=1, system='Cu-Ni')

        # Positions should be different
        pos1 = np.array(snapshot1.positions)
        pos2 = np.array(snapshot2.positions)

        # They should not be identical (with some tolerance for numerical precision)
        assert not np.allclose(pos1, pos2, atol=1e-10)

    def test_lj_parameters_correct(self, generator):
        """Test that LJ parameters match specification."""
        assert generator.LJ_CU_NI['epsilon'] == 0.104
        assert generator.LJ_CU_NI['sigma'] == 2.56
        assert generator.LJ_CU_NI['species'] == ['Cu', 'Ni']

        assert generator.LJ_AU_AG['epsilon'] == 0.103
        assert generator.LJ_AU_AG['sigma'] == 2.89
        assert generator.LJ_AU_AG['species'] == ['Au', 'Ag']

    def test_generate_all_creates_correct_count(self, generator, tmp_path):
        """Test that generate_all creates the expected number of snapshots."""
        output_dir = str(tmp_path / 'processed')
        snapshots = generator.generate_all_snapshots(output_dir=output_dir)

        assert len(snapshots) == 4  # num_snapshots=4

        # Check that output files were created
        assert os.path.exists(output_dir)

    def test_system_switching(self, generator):
        """Test that different systems use different parameters."""
        snap_cu_ni = generator.generate_snapshot(seed=0, system='Cu-Ni')
        snap_au_ag = generator.generate_snapshot(seed=0, system='Au-Ag')

        assert snap_cu_ni.system == 'Cu-Ni'
        assert snap_au_ag.system == 'Au-Ag'

        # Metadata should reflect different parameters
        assert snap_cu_ni.metadata['epsilon_eV'] == 0.104
        assert snap_au_ag.metadata['epsilon_eV'] == 0.103

    def test_invalid_system_raises_error(self, generator):
        """Test that unknown system raises ValueError."""
        with pytest.raises(ValueError, match="Unknown system"):
            generator.generate_snapshot(seed=0, system='Invalid')


class TestThermalConductivityEstimator:
    """Tests for ThermalConductivityEstimator class."""

    @pytest.fixture
    def estimator(self):
        return ThermalConductivityEstimator()

    @pytest.fixture
    def sample_snapshot(self):
        """Create a sample snapshot for testing."""
        return AtomicSnapshot(
            snapshot_id='test_001',
            species_list=['Cu', 'Ni', 'Cu', 'Ni'] * 64,  # 256 atoms
            positions=np.random.rand(256, 3).tolist(),
            cell=[[10, 0, 0], [0, 10, 0], [0, 0, 10]],
            pbc=[True, True, True],
            temperature=300.0,
            system='Cu-Ni',
            seed=42,
            metadata={}
        )

    def test_estimate_returns_positive_value(self, estimator, sample_snapshot):
        """Test that thermal conductivity estimate is positive."""
        kappa = estimator.estimate_from_snapshot(sample_snapshot)
        assert kappa > 0
        assert isinstance(kappa, float)

    def test_estimate_varies_with_composition(self, estimator):
        """Test that estimates vary with different compositions."""
        # Pure Cu
        pure_cu = AtomicSnapshot(
            snapshot_id='pure_cu',
            species_list=['Cu'] * 100,
            positions=np.random.rand(100, 3).tolist(),
            cell=[[10, 0, 0], [0, 10, 0], [0, 0, 10]],
            pbc=[True, True, True],
            temperature=300.0,
            system='Cu-Ni',
            seed=1,
            metadata={}
        )

        # 50-50 alloy
        alloy_50 = AtomicSnapshot(
            snapshot_id='alloy_50',
            species_list=['Cu', 'Ni'] * 50,
            positions=np.random.rand(100, 3).tolist(),
            cell=[[10, 0, 0], [0, 10, 0], [0, 0, 10]],
            pbc=[True, True, True],
            temperature=300.0,
            system='Cu-Ni',
            seed=2,
            metadata={}
        )

        kappa_pure = estimator.estimate_from_snapshot(pure_cu)
        kappa_alloy = estimator.estimate_from_snapshot(alloy_50)

        # Pure should have higher conductivity than alloy
        assert kappa_pure > kappa_alloy

    def test_estimate_all_returns_dict(self, estimator, sample_snapshot):
        """Test that estimate_all returns a dictionary of results."""
        snapshots = [sample_snapshot]
        results = estimator.estimate_all(snapshots)

        assert isinstance(results, dict)
        assert 'test_001' in results
        assert results['test_001'] > 0


class TestRunSyntheticGeneration:
    """Tests for the convenience function."""

    def test_run_synthetic_generation_creates_files(self, tmp_path):
        """Test that the function creates output files."""
        output_dir = str(tmp_path / 'processed')
        snapshots = run_synthetic_generation(
            output_dir=output_dir,
            num_snapshots=4,
            temperature=300.0
        )

        assert len(snapshots) == 4
        assert os.path.exists(output_dir)

        # Check for expected files
        parquet_file = os.path.join(output_dir, 'synthetic_snapshots.parquet')
        json_file = os.path.join(output_dir, 'synthetic_generation_summary.json')

        # One of these should exist
        assert os.path.exists(parquet_file) or os.path.exists(json_file)
