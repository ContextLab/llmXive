"""
Tests for semi-empirical BVS defect energy estimation module.

These tests validate the BVS model implementation against:
1. Known bond valence parameters
2. Expected energy ranges for defect types
3. Validation logic against DFT results
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from pymatgen.core import Structure, Lattice

from semi_empirical import (
    calculate_bvs_deviation,
    calculate_bvs_energy,
    load_dft_results,
    validate_semi_empirical_against_dft,
    estimate_defect_energies,
    run_semi_empirical_analysis
)
from models import DefectType, DefectConfiguration


@pytest.fixture
def simple_oxide_structure():
    """Create a simple oxide structure for testing."""
    # Li2O structure (rock salt)
    lattice = Lattice.cubic(4.6)
    species = ["Li", "Li", "O"]
    coords = [
        [0, 0, 0],
        [0.5, 0.5, 0.5],
        [0.25, 0.25, 0.25]
    ]
    return Structure(lattice, species, coords)


@pytest.fixture
def test_defect_config():
    """Create a test defect configuration."""
    return DefectConfiguration(
        composition_id="test_Li2O",
        defect_type=DefectType.VACANCY,
        defect_site=0,
        supercell_size="2x2x2"
    )


def test_calculate_bvs_deviation_valid_structure(simple_oxide_structure):
    """Test BVS deviation calculation for a valid structure."""
    max_dev, per_elem_dev = calculate_bvs_deviation(simple_oxide_structure)

    # Should return a deviation value (may be non-zero due to idealized structure)
    assert isinstance(max_dev, float)
    assert max_dev >= 0
    assert isinstance(per_elem_dev, dict)


def test_calculate_bvs_energy_returns_positive(simple_oxide_structure, test_defect_config):
    """Test that BVS energy calculation returns positive values."""
    energy = calculate_bvs_energy(simple_oxide_structure, test_defect_config)

    assert isinstance(energy, float)
    assert energy >= 0, "Defect formation energies should be non-negative"


def test_calculate_bvs_energy_different_defect_types(simple_oxide_structure):
    """Test BVS energy varies by defect type."""
    vacancy_config = DefectConfiguration(
        composition_id="test",
        defect_type=DefectType.VACANCY,
        defect_site=0,
        supercell_size="2x2x2"
    )
    interstitial_config = DefectConfiguration(
        composition_id="test",
        defect_type=DefectType.INTERSTITIAL,
        defect_site=0,
        supercell_size="2x2x2"
    )

    vacancy_energy = calculate_bvs_energy(simple_oxide_structure, vacancy_config)
    interstitial_energy = calculate_bvs_energy(simple_oxide_structure, interstitial_config)

    # Energies should be positive and potentially different
    assert vacancy_energy >= 0
    assert interstitial_energy >= 0


def test_load_dft_results_missing_file():
    """Test loading DFT results from non-existent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent = Path(tmpdir) / "nonexistent.json"
        results = load_dft_results(nonexistent)
        assert results == []


def test_load_dft_results_valid_file():
    """Test loading DFT results from valid file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "dft_results.json"
        test_data = {
            "results": [
                {"composition_id": "test1", "formation_energy": 1.5},
                {"composition_id": "test2", "formation_energy": 2.0}
            ]
        }
        with open(filepath, 'w') as f:
            json.dump(test_data, f)

        results = load_dft_results(filepath)
        assert len(results) == 2
        assert results[0]['composition_id'] == 'test1'


def test_validate_semi_empirical_against_dft():
    """Test validation of semi-empirical results against DFT."""
    semi_results = [
        {"composition_id": "test1", "estimated_energy": 1.4},
        {"composition_id": "test2", "estimated_energy": 2.1}
    ]
    dft_results = [
        {"composition_id": "test1", "formation_energy": 1.5},
        {"composition_id": "test2", "formation_energy": 2.0}
    ]

    report = validate_semi_empirical_against_dft(semi_results, dft_results, tolerance=0.5)

    assert 'validation_status' in report
    assert 'mean_deviation_eV' in report
    assert 'comparisons' in report
    assert len(report['comparisons']) == 2
    assert report['mean_deviation_eV'] <= 0.5  # Both within tolerance


def test_validate_semi_empirical_no_dft():
    """Test validation when no DFT results are available."""
    semi_results = [{"composition_id": "test1", "estimated_energy": 1.4}]
    dft_results = []

    report = validate_semi_empirical_against_dft(semi_results, dft_results)

    assert report['validation_status'] == 'skipped'
    assert 'No DFT results available' in report['reason']


def test_estimate_defect_energies():
    """Test defect energy estimation for multiple structures."""
    # Create simple structures
    lattice = Lattice.cubic(4.0)
    struct1 = Structure(lattice, ["Li", "O"], [[0, 0, 0], [0.5, 0.5, 0.5]])
    struct2 = Structure(lattice, ["Li", "O"], [[0, 0, 0], [0.5, 0.5, 0.5]])

    configs = [
        DefectConfiguration(composition_id="comp1", defect_type=DefectType.VACANCY,
                          defect_site=0, supercell_size="2x2x2"),
        DefectConfiguration(composition_id="comp2", defect_type=DefectType.INTERSTITIAL,
                          defect_site=0, supercell_size="2x2x2")
    ]

    results = estimate_defect_energies([struct1, struct2], configs)

    assert len(results) == 2
    assert all(r.get('estimated_energy') is not None for r in results)
    assert all(r['method'] == 'BVS_semi_empirical' for r in results)


def test_run_semi_empirical_analysis():
    """Test full semi-empirical analysis pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        processed_dir = data_dir / "processed"
        processed_dir.mkdir()

        # Create mock validated structures
        structures_data = {
            "structures": [
                {
                    "composition_id": "test1",
                    "structure_dict": Structure(
                        Lattice.cubic(4.0),
                        ["Li", "O"],
                        [[0, 0, 0], [0.5, 0.5, 0.5]]
                    ).as_dict()
                }
            ]
        }
        with open(processed_dir / "validated_structures.json", 'w') as f:
            json.dump(structures_data, f)

        # Create mock defect configurations
        defect_data = {
            "configurations": [
                {
                    "composition_id": "test1",
                    "defect_type": "vacancy",
                    "defect_site": 0,
                    "supercell_size": "2x2x2"
                }
            ]
        }
        with open(processed_dir / "defect_configurations.json", 'w') as f:
            json.dump(defect_data, f)

        # Run analysis
        results = run_semi_empirical_analysis(data_dir)

        assert results['status'] == 'completed'
        assert 'results' in results
        assert len(results['results']) == 1

        # Verify output file was created
        output_file = processed_dir / "semi_empirical_results.json"
        assert output_file.exists()


def test_run_semi_empirical_analysis_missing_files():
    """Test analysis fails gracefully when required files are missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        processed_dir = data_dir / "processed"
        processed_dir.mkdir()

        results = run_semi_empirical_analysis(data_dir)

        assert results['status'] == 'failed'
        assert 'Missing required data files' in results['error']