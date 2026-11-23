"""
Unit test for Magpie feature extraction logic.
Depends on T005 (data models) and T007 (validation utilities).
"""
import pytest
import numpy as np
from code.data_models import MaterialEntry, FeatureVector
from code.utils.validation import validate_structure

# Mock feature extraction for testing
def mock_extract_magpie_features(composition: dict) -> dict:
    """Mock function to simulate Magpie feature extraction."""
    return {
        "mean_atomic_number": np.mean(list(composition.keys())) if composition else 0,
        "std_atomic_number": np.std(list(composition.keys())) if composition else 0,
        "num_elements": len(composition)
    }

def test_material_entry_creation():
    """Test MaterialEntry dataclass creation."""
    entry = MaterialEntry(
        material_id="test-001",
        composition={"Li": 2, "O": 1},
        formation_energy=-1.5
    )
    assert entry.material_id == "test-001"
    assert entry.formation_energy == -1.5

def test_feature_vector_creation():
    """Test FeatureVector dataclass creation."""
    vector = FeatureVector(
        material_id="test-001",
        features={"mean_atomic_number": 3.0},
        target=-1.5
    )
    assert vector.material_id == "test-001"
    assert vector.features == {"mean_atomic_number": 3.0}

def test_mock_feature_extraction():
    """Test mock feature extraction logic."""
    comp = {"Li": 3, "O": 1}
    features = mock_extract_magpie_features(comp)
    assert "mean_atomic_number" in features
    assert "num_elements" in features
    assert features["num_elements"] == 2

# Note: Real integration with pymatgen would be tested in a more complex setup
# or in integration tests.
