"""
Unit tests for the data models (DefectEntry and MaterialProperty).
"""
import pytest
import json
from src.models.defect_entry import DefectEntry
from src.models.material_property import MaterialProperty


class TestDefectEntry:
    def test_create_entry(self):
        entry = DefectEntry(
            entry_id="e1",
            material_id="graphene",
            structure_id="s1",
            defect_type="vacancy",
            defect_density=0.05
        )
        assert entry.defect_type == "vacancy"
        assert entry.defect_density == 0.05

    def test_to_dict_roundtrip(self):
        original = DefectEntry(
            entry_id="e2",
            material_id="MoS2",
            structure_id="s2",
            defect_type="substitution",
            defect_density=0.1,
            grain_size=50.0
        )
        d = original.to_dict()
        recovered = DefectEntry.from_dict(d)
        assert recovered.entry_id == original.entry_id
        assert recovered.grain_size == original.grain_size

    def test_from_row(self):
        row = {
            "entry_id": "e3",
            "material_id": "graphene",
            "structure_id": "s3",
            "defect_type": "grain_boundary",
            "defect_density": "0.02",
            "grain_size": "100.0",
            "data_source": "synthetic"
        }
        entry = DefectEntry.from_row(row)
        assert entry.defect_density == 0.02
        assert entry.grain_size == 100.0
        assert entry.data_source == "synthetic"


class TestMaterialProperty:
    def test_create_property(self):
        prop = MaterialProperty(
            entry_id="e1",
            conductivity=100.0,
            elastic_tensor=[1.0] * 21,
            fracture_energy=10.0
        )
        assert prop.conductivity == 100.0
        assert len(prop.elastic_tensor) == 21

    def test_from_row_string_tensor(self):
        row = {
            "entry_id": "e1",
            "conductivity": "50.0",
            "elastic_tensor": "[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0]",
            "fracture_energy": "5.0",
            "young_modulus": "1000.0"
        }
        prop = MaterialProperty.from_row(row)
        assert prop.conductivity == 50.0
        assert prop.young_modulus == 1000.0
        assert len(prop.elastic_tensor) == 21

    def test_from_row_comma_tensor(self):
        row = {
            "entry_id": "e2",
            "conductivity": "20.0",
            "elastic_tensor": "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21",
            "fracture_energy": "2.0"
        }
        prop = MaterialProperty.from_row(row)
        assert prop.conductivity == 20.0
        assert prop.elastic_tensor[0] == 1.0
        assert prop.elastic_tensor[-1] == 21.0

    def test_validate_positive(self):
        prop = MaterialProperty(
            entry_id="e1",
            conductivity=10.0,
            elastic_tensor=[1.0] * 21,
            fracture_energy=10.0
        )
        assert prop.validate() is True

    def test_validate_negative_conductivity(self):
        prop = MaterialProperty(
            entry_id="e1",
            conductivity=-5.0,
            elastic_tensor=[1.0] * 21,
            fracture_energy=10.0
        )
        assert prop.validate() is False