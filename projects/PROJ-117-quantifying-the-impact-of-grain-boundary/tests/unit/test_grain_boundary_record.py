"""
Unit tests for the GrainBoundaryRecord dataclass.
"""

import pytest
from code.models.grain_boundary_record import GrainBoundaryRecord


def test_create_record():
    """Test basic creation of a GrainBoundaryRecord."""
    record = GrainBoundaryRecord(
        material_id="mp-1234",
        structure_file="data/raw/poscar_1.vasp",
        misorientation_angle=36.87,
        rotation_axis=[0.0, 0.0, 1.0],
        boundary_plane_normal=[1.0, 0.0, 0.0],
        sigma_value=5,
        boundary_width=15.5,
        excess_volume=0.12,
        temperature=800.0,
        composition="Cu",
        diffusivity=1.5e-12,
        simulation_method="MD",
        potential_id="EAM_Cu_2010",
        source="OpenKIM",
        raw_metadata={"run_id": "abc-123"},
    )

    assert record.material_id == "mp-1234"
    assert record.sigma_value == 5
    assert record.simulation_method == "MD"
    assert record.raw_metadata["run_id"] == "abc-123"


def test_to_dict_and_from_dict_roundtrip():
    """Test that converting to dict and back preserves data."""
    original = GrainBoundaryRecord(
        material_id="mp-5678",
        structure_file="data/raw/poscar_2.vasp",
        misorientation_angle=45.0,
        rotation_axis=[0.707, 0.0, 0.707],
        boundary_plane_normal=[0.0, 1.0, 0.0],
        sigma_value=3,
        boundary_width=20.0,
        excess_volume=0.15,
        temperature=1000.0,
        composition="Ni",
        diffusivity=2.0e-11,
        simulation_method="DFT",
        potential_id="LJ_Ni",
        source="NIST",
    )

    data = original.to_dict()
    reconstructed = GrainBoundaryRecord.from_dict(data)

    assert reconstructed.material_id == original.material_id
    assert reconstructed.diffusivity == original.diffusivity
    assert reconstructed.rotation_axis == original.rotation_axis


def test_json_serialization():
    """Test JSON serialization and deserialization."""
    record = GrainBoundaryRecord(
        material_id="mp-9999",
        structure_file="data/raw/poscar_3.vasp",
        misorientation_angle=60.0,
        rotation_axis=[0.0, 1.0, 0.0],
        boundary_plane_normal=[1.0, 1.0, 0.0],
        sigma_value=7,
        boundary_width=12.0,
        excess_volume=0.08,
        temperature=900.0,
        composition="Al",
        diffusivity=5.0e-13,
        simulation_method="KMC",
        potential_id="EAM_Al",
        source="Materials Project",
    )

    json_str = record.to_json()
    assert isinstance(json_str, str)

    loaded_record = GrainBoundaryRecord.from_json(json_str)
    assert loaded_record.material_id == record.material_id
    assert loaded_record.sigma_value == record.sigma_value
    assert loaded_record.composition == record.composition