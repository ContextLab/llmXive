"""
Unit tests for AlloyEntry data model.
"""
import pytest
from datetime import datetime
from code.models.alloy_entry import AlloyEntry, ElementDescriptor


def test_valid_alloy_entry():
    """Test creation of a valid alloy entry."""
    entry = AlloyEntry(
        entry_id="TEST-001",
        composition=[
            ElementDescriptor(element_symbol="Fe", atomic_fraction=0.5, atomic_radius=1.24),
            ElementDescriptor(element_symbol="Ni", atomic_fraction=0.5, atomic_radius=1.24)
        ],
        bulk_modulus=150.0,
        shear_modulus=80.0,
        source_dataset="OQMD"
    )
    assert entry.entry_id == "TEST-001"
    assert entry.bulk_modulus == 150.0
    assert entry.shear_modulus == 80.0
    assert entry.is_validated is False


def test_composition_sum_validation():
    """Test that composition fractions must sum to 1.0."""
    with pytest.raises(ValueError) as exc_info:
        AlloyEntry(
            entry_id="TEST-002",
            composition=[
                ElementDescriptor(element_symbol="Fe", atomic_fraction=0.6),
                ElementDescriptor(element_symbol="Ni", atomic_fraction=0.3)
            ]
        )
    assert "sum to 1.0" in str(exc_info.value)


def test_negative_modulus_rejected():
    """Test that negative modulus values are rejected."""
    with pytest.raises(ValueError) as exc_info:
        AlloyEntry(
            entry_id="TEST-003",
            composition=[
                ElementDescriptor(element_symbol="Fe", atomic_fraction=1.0)
            ],
            bulk_modulus=-10.0
        )
    assert "cannot be negative" in str(exc_info.value).lower()


def test_fraction_bounds():
    """Test that atomic fractions must be between 0 and 1."""
    with pytest.raises(ValueError):
        AlloyEntry(
            entry_id="TEST-004",
            composition=[
                ElementDescriptor(element_symbol="Fe", atomic_fraction=1.5)
            ]
        )


def test_empty_composition_rejected():
    """Test that empty composition list is rejected."""
    with pytest.raises(ValueError):
        AlloyEntry(
            entry_id="TEST-005",
            composition=[]
        )


def test_to_dict_serialization():
    """Test conversion to dictionary."""
    entry = AlloyEntry(
        entry_id="TEST-006",
        composition=[
            ElementDescriptor(element_symbol="Cu", atomic_fraction=1.0, atomic_radius=1.28)
        ],
        bulk_modulus=100.0
    )
    data = entry.to_dict()
    assert data["entry_id"] == "TEST-006"
    assert data["bulk_modulus"] == 100.0
    assert "created_at" in data


def test_from_dict_deserialization():
    """Test creation from dictionary."""
    data = {
        "entry_id": "TEST-007",
        "composition": [
            {"element_symbol": "Al", "atomic_fraction": 1.0, "atomic_radius": 1.43}
        ],
        "bulk_modulus": 70.0,
        "shear_modulus": 26.0
    }
    entry = AlloyEntry.from_dict(data)
    assert entry.entry_id == "TEST-007"
    assert entry.bulk_modulus == 70.0
    assert entry.shear_modulus == 26.0


def test_missing_moduli_allowed():
    """Test that missing moduli are allowed (optional fields)."""
    entry = AlloyEntry(
        entry_id="TEST-008",
        composition=[
            ElementDescriptor(element_symbol="Ti", atomic_fraction=1.0)
        ]
    )
    assert entry.bulk_modulus is None
    assert entry.shear_modulus is None
    assert entry.is_validated is False