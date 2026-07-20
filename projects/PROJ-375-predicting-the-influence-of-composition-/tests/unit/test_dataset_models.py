"""
Unit tests for MetallicGlassEntry Pydantic model validation.
"""
import pytest
from code.features.dataset_models import MetallicGlassEntry, AlloyFamily, DataSource

def test_valid_entry_creation():
    """Test creation of a valid MetallicGlassEntry."""
    entry = MetallicGlassEntry(
        composition="Zr50Cu40Al10",
        cte=12.5,
        weighted_mean_atomic_radius=155.2,
        electronegativity_variance=0.15,
        vec=4.2,
        atomic_size_mismatch=0.08,
        amorphous_state_flag=1,
        alloy_family=AlloyFamily.ZR,
        source=DataSource.MP,
        entry_id="mp-12345"
    )
    assert entry.composition == "Zr50Cu40Al10"
    assert entry.cte == 12.5
    assert entry.amorphous_state_flag == 1
    assert entry.alloy_family == AlloyFamily.ZR

def test_to_dict_conversion():
    """Test conversion to dictionary."""
    entry = MetallicGlassEntry(
        composition="Pd40Ni40P20",
        cte=10.1,
        weighted_mean_atomic_radius=138.5,
        electronegativity_variance=0.12,
        vec=5.1,
        atomic_size_mismatch=0.06,
        amorphous_state_flag=1,
        alloy_family=AlloyFamily.PD,
        source=DataSource.AFLOW,
        entry_id="aflow-67890"
    )
    data = entry.to_dict()
    assert data['composition'] == "Pd40Ni40P20"
    assert data['alloy_family'] == "Pd"
    assert data['source'] == "AFLOW"

def test_invalid_composition_format():
    """Test rejection of invalid composition format."""
    with pytest.raises(ValueError):
        MetallicGlassEntry(
            composition="invalid",
            cte=10.0,
            weighted_mean_atomic_radius=150.0,
            electronegativity_variance=0.1,
            vec=4.0,
            atomic_size_mismatch=0.05,
            amorphous_state_flag=1,
            alloy_family=AlloyFamily.ZR,
            source=DataSource.MP,
            entry_id="test-001"
        )

def test_negative_cte_rejected():
    """Test rejection of negative CTE values."""
    with pytest.raises(ValueError):
        MetallicGlassEntry(
            composition="Zr50Cu50",
            cte=-1.0,
            weighted_mean_atomic_radius=150.0,
            electronegativity_variance=0.1,
            vec=4.0,
            atomic_size_mismatch=0.05,
            amorphous_state_flag=1,
            alloy_family=AlloyFamily.ZR,
            source=DataSource.MP,
            entry_id="test-002"
        )

def test_invalid_amorphous_flag():
    """Test rejection of invalid amorphous flag values."""
    with pytest.raises(ValueError):
        MetallicGlassEntry(
            composition="Zr50Cu50",
            cte=10.0,
            weighted_mean_atomic_radius=150.0,
            electronegativity_variance=0.1,
            vec=4.0,
            atomic_size_mismatch=0.05,
            amorphous_state_flag=2,
            alloy_family=AlloyFamily.ZR,
            source=DataSource.MP,
            entry_id="test-003"
        )

def test_valid_alloy_families():
    """Test all valid alloy families."""
    families = [f.value for f in AlloyFamily]
    assert "Zr" in families
    assert "Pd" in families
    assert "Fe" in families
    assert "Mg" in families
    assert "Ti" in families
    assert "Cu" in families
    assert "Other" in families
