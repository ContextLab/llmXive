"""
Tests for semi-empirical defect energy calculations.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest
from pymatgen.core import Structure, Lattice

from semi_empirical import (
    calculate_bvs_energy,
    estimate_defect_energies,
    load_dft_results,
    run_semi_empirical_analysis
)
from models import DefectType

@pytest.fixture
def sample_structure():
    """Create a simple Li-O structure for testing."""
    lattice = Lattice.cubic(4.0)
    coords = [
        [0, 0, 0],
        [0.5, 0.5, 0.5],
        [0.5, 0, 0],
        [0, 0.5, 0],
        [0, 0, 0.5],
    ]
    species = ["Li", "O", "Li", "Li", "Li"]
    return Structure(lattice, species, coords)

@pytest.fixture
def sample_compositions():
    """Create sample composition data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        structure_path = Path(tmpdir) / "test_structure.cif"
        # Create a dummy CIF file
        with open(structure_path, "w") as f:
            f.write("""
            data_test
            _cell_length_a 4.0
            _cell_length_b 4.0
            _cell_length_c 4.0
            _cell_angle_alpha 90
            _cell_angle_beta 90
            _cell_angle_gamma 90
            _symmetry_space_group_name_H-M 'P m -3 m'
            loop_
            _atom_site_label
            _atom_site_type_symbol
            _atom_site_fract_x
            _atom_site_fract_y
            _atom_site_fract_z
            Li1 Li 0.0 0.0 0.0
            O1 O 0.5 0.5 0.5
            """)

        return [
            {
                "id": "comp_1",
                "structure_path": str(structure_path),
                "defect_type": "vacancy",
                "defect_site": 0
            },
            {
                "id": "comp_2",
                "structure_path": str(structure_path),
                "defect_type": "interstitial",
                "defect_site": 1
            }
        ]

def test_calculate_bvs_energy(sample_structure):
    """Test BVS energy calculation."""
    energy = calculate_bvs_energy(
        sample_structure,
        DefectType.vacancy,
        0
    )
    assert isinstance(energy, float)
    assert energy >= 0.0

def test_estimate_defect_energies(sample_compositions):
    """Test defect energy estimation for multiple compositions."""
    results = estimate_defect_energies(sample_compositions)

    assert len(results) == 2
    for r in results:
        assert "id" in r
        assert "energy" in r
        assert "method" in r
        assert r["method"] == "semi_empirical_bvs"
        if r.get("energy") is not None:
            assert isinstance(r["energy"], float)

def test_load_dft_results():
    """Test loading DFT results from JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dft_path = Path(tmpdir) / "dft_results.json"
        data = {
            "results": [
                {"id": "comp_1", "energy": 2.5},
                {"id": "comp_2", "energy": 3.0}
            ]
        }
        with open(dft_path, "w") as f:
            json.dump(data, f)

        results = load_dft_results(str(dft_path))

        assert "comp_1" in results
        assert results["comp_1"] == 2.5
        assert "comp_2" in results
        assert results["comp_2"] == 3.0

def test_run_semi_empirical_analysis(sample_compositions):
    """Test full semi-empirical analysis pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "compositions.json"
        output_path = Path(tmpdir) / "results.json"

        with open(input_path, "w") as f:
            json.dump(sample_compositions, f)

        summary = run_semi_empirical_analysis(
            input_compositions_path=str(input_path),
            output_path=str(output_path)
        )

        assert "total_compositions" in summary
        assert "successful" in summary
        assert "results" in summary
        assert Path(output_path).exists()

        # Verify output file content
        with open(output_path, "r") as f:
            saved_data = json.load(f)

        assert saved_data["total_compositions"] == len(sample_compositions)

def test_validation_against_dft(sample_compositions):
    """Test validation of BVS results against DFT."""
    dft_results = {
        "comp_1": 2.0,
        "comp_2": 3.0
    }

    results = estimate_defect_energies(sample_compositions, dft_results)

    # First 3 should attempt validation
    for i, r in enumerate(results):
        if i < 3:
            assert "validation_status" in r
            # Status should be one of: validated, unvalidated_high_deviation, low_fidelity
            assert r["validation_status"] in [
                "validated",
                "unvalidated_high_deviation",
                "low_fidelity"
            ]