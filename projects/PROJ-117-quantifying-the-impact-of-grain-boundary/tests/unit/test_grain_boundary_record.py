"""
Unit tests for GrainBoundaryRecord dataclass.
"""
import pytest
import numpy as np
from code.models.grain_boundary_record import GrainBoundaryRecord

def test_grain_boundary_record_creation():
    """Test basic creation of a GrainBoundaryRecord."""
    record = GrainBoundaryRecord(
        source_id="mp-12345",
        material_formula="Fe",
        misorientation_angle=36.87,
        sigma_value=5.0,
        boundary_plane_normal=(1.0, 0.0, 0.0),
        boundary_width=10.5,
        excess_volume=0.5,
        temperature=300.0
    )
    assert record.source_id == "mp-12345"
    assert record.material_formula == "Fe"
    assert record.misorientation_angle == 36.87
    assert record.sigma_value == 5.0
    assert record.boundary_plane_normal == (1.0, 0.0, 0.0)
    assert record.boundary_width == 10.5
    assert record.excess_volume == 0.5
    assert record.temperature == 300.0
    assert record.diffusivity is None
    assert record.simulation_method is None

def test_to_dict():
    """Test serialization to dictionary."""
    record = GrainBoundaryRecord(
        source_id="mp-12345",
        material_formula="Fe",
        misorientation_angle=36.87,
        sigma_value=5.0,
        boundary_plane_normal=(1.0, 0.0, 0.0),
        boundary_width=10.5,
        excess_volume=0.5,
        temperature=300.0,
        composition="pure",
        diffusivity=1.2e-10,
        simulation_method="MD",
        potential_id="EAM_Fe_01"
    )
    d = record.to_dict()
    assert d["source_id"] == "mp-12345"
    assert d["material_formula"] == "Fe"
    assert d["diffusivity"] == 1.2e-10
    assert d["simulation_method"] == "MD"
    assert d["potential_id"] == "EAM_Fe_01"

def test_from_dict():
    """Test deserialization from dictionary."""
    data = {
        "source_id": "mp-67890",
        "material_formula": "Cu",
        "misorientation_angle": 53.13,
        "sigma_value": 3.0,
        "boundary_plane_normal": (0.0, 1.0, 0.0),
        "boundary_width": 12.0,
        "excess_volume": 0.6,
        "temperature": 500.0,
        "composition": None,
        "diffusivity": 2.5e-10,
        "simulation_method": "DFT",
        "potential_id": None
    }
    record = GrainBoundaryRecord.from_dict(data)
    assert record.source_id == "mp-67890"
    assert record.material_formula == "Cu"
    assert record.sigma_value == 3.0
    assert record.diffusivity == 2.5e-10
    assert record.simulation_method == "DFT"

def test_from_dict_missing_optional_fields():
    """Test that from_dict handles missing optional fields gracefully."""
    data = {
        "source_id": "mp-111",
        "material_formula": "Ni",
        "misorientation_angle": 45.0,
        "sigma_value": 9.0,
        "boundary_plane_normal": (0.0, 0.0, 1.0),
        "boundary_width": 8.0,
        "excess_volume": 0.4,
        "temperature": 400.0
    }
    record = GrainBoundaryRecord.from_dict(data)
    assert record.composition is None
    assert record.diffusivity is None
    assert record.simulation_method is None
    assert record.potential_id is None
    assert record.notes is None

def test_boundary_plane_normal_type():
    """Ensure boundary_plane_normal is stored as a tuple."""
    record = GrainBoundaryRecord(
        source_id="mp-1",
        material_formula="Al",
        misorientation_angle=30.0,
        sigma_value=7.0,
        boundary_plane_normal=[1.0, 1.0, 0.0],  # Input as list
        boundary_width=5.0,
        excess_volume=0.2,
        temperature=298.0
    )
    assert isinstance(record.boundary_plane_normal, tuple)
    assert record.boundary_plane_normal == (1.0, 1.0, 0.0)