"""
Tests for semi-empirical defect energy estimation module.
"""

import json
import pytest
from pathlib import Path
import numpy as np

from pymatgen.core import Structure

from semi_empirical import (
    calculate_bvs_deviation,
    calculate_bvs_energy,
    validate_semi_empirical_against_dft,
    estimate_defect_energies,
    run_semi_empirical_analysis
)


@pytest.fixture
def sample_structure():
    """Create a sample Li7La3Zr2O12 structure for testing."""
    # Create a simple cubic structure for testing
    lattice = [[4.0, 0, 0], [0, 4.0, 0], [0, 0, 4.0]]
    species = ["Li", "La", "Zr", "O"]
    coords = [
        [0.0, 0.0, 0.0],
        [0.5, 0.5, 0.5],
        [0.25, 0.25, 0.25],
        [0.125, 0.125, 0.125]
    ]
    return Structure(lattice, species, coords)


@pytest.fixture
def sample_dft_results():
    """Create sample DFT results for validation testing."""
    return [
        {
            'composition_id': 'comp_0001',
            'formation_energy': -2.5,
            'structure': None
        },
        {
            'composition_id': 'comp_0002',
            'formation_energy': -3.1,
            'structure': None
        },
        {
            'composition_id': 'comp_0003',
            'formation_energy': -2.8,
            'structure': None
        }
    ]


@pytest.fixture
def sample_semi_empirical_results():
    """Create sample semi-empirical results for validation testing."""
    return [
        {
            'composition_id': 'comp_0001',
            'energy': -2.4,
            'bvs_energy': 0.1
        },
        {
            'composition_id': 'comp_0002',
            'energy': -3.0,
            'bvs_energy': 0.15
        },
        {
            'composition_id': 'comp_0003',
            'energy': -2.7,
            'bvs_energy': 0.12
        }
    ]


def test_calculate_bvs_deviation(sample_structure):
    """Test BVS deviation calculation."""
    deviations = calculate_bvs_deviation(sample_structure)

    assert isinstance(deviations, dict)
    assert len(deviations) == len(sample_structure)

    # All deviations should be numeric (or NaN)
    for idx, dev in deviations.items():
        assert isinstance(dev, (float, int)) or np.isnan(dev)


def test_calculate_bvs_energy(sample_structure):
    """Test BVS energy calculation."""
    energy = calculate_bvs_energy(sample_structure)

    assert isinstance(energy, float)
    assert energy >= 0.0, "Energy should be non-negative"


def test_calculate_bvs_energy_with_defects(sample_structure):
    """Test BVS energy calculation with specific defect indices."""
    defect_indices = [0, 2]
    energy = calculate_bvs_energy(sample_structure, defect_indices)

    assert isinstance(energy, float)
    assert energy >= 0.0


def test_validate_semi_empirical_against_dft(sample_semi_empirical_results, sample_dft_results):
    """Test validation of semi-empirical results against DFT."""
    stats = validate_semi_empirical_against_dft(
        sample_semi_empirical_results,
        sample_dft_results
    )

    assert 'correlation' in stats
    assert 'mean_absolute_error' in stats
    assert 'root_mean_squared_error' in stats
    assert 'r_squared' in stats
    assert 'comparison_count' in stats
    assert 'status' in stats

    # Check that comparison count matches
    assert stats['comparison_count'] == 3

    # Check that status is 'complete'
    assert stats['status'] == 'complete'


def test_validate_empty_results():
    """Test validation with empty result lists."""
    stats = validate_semi_empirical_against_dft([], [])

    assert stats['status'] == 'incomplete'
    assert stats['comparison_count'] == 0


def test_validate_insufficient_data(sample_semi_empirical_results, sample_dft_results):
    """Test validation with insufficient matching data."""
    # Modify results to have no matching composition IDs
    modified_se_results = [
        {
            'composition_id': 'comp_9999',
            'energy': -2.4
        }
    ]

    stats = validate_semi_empirical_against_dft(
        modified_se_results,
        sample_dft_results
    )

    assert stats['status'] == 'insufficient_data'
    assert stats['comparison_count'] == 0


def test_estimate_defect_energies(sample_structure):
    """Test defect energy estimation."""
    structures = [sample_structure]
    defect_types = ['vacancy', 'interstitial']

    results = estimate_defect_energies(structures, defect_types)

    assert isinstance(results, list)
    assert len(results) == 1

    result = results[0]
    assert 'composition_id' in result
    assert 'bvs_energy' in result
    assert 'total_energy' in result
    assert 'energy_unit' in result
    assert result['energy_unit'] == 'eV'


def test_estimate_defect_energies_with_concentration(sample_structure):
    """Test defect energy estimation with concentration scaling."""
    structures = [sample_structure]
    defect_types = ['vacancy']
    concentrations = [0.1]

    results = estimate_defect_energies(structures, defect_types, concentrations)

    assert len(results) == 1
    assert 'total_energy' in results[0]


def test_run_semi_empirical_analysis(tmp_path):
    """Test complete semi-empirical analysis pipeline."""
    # Create a temporary DFT results file
    dft_results = [
        {
            'composition_id': 'comp_0001',
            'formation_energy': -2.5,
            'structure': None
        }
    ]

    dft_file = tmp_path / "dft_results.json"
    with open(dft_file, 'w') as f:
        json.dump(dft_results, f)

    output_file = tmp_path / "semi_empirical_results.json"

    # Run analysis
    results = run_semi_empirical_analysis(str(dft_file), str(output_file))

    assert results['status'] == 'complete'
    assert 'semi_empirical_results' in results
    assert 'validation_stats' in results

    # Check that output file was created
    assert output_file.exists()

    # Verify output file contents
    with open(output_file, 'r') as f:
        saved_results = json.load(f)

    assert 'status' in saved_results
    assert saved_results['status'] == 'complete'