"""
Unit tests for code/config.py
"""
import pytest
from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import Paths, Hyperparams, get_seed, get_paths, get_hyperparams

def test_paths_exist():
    """Verify that the Paths class attributes are valid Path objects."""
    assert isinstance(Paths.ROOT, Path)
    assert isinstance(Paths.DATA, Path)
    assert isinstance(Paths.CODE, Path)
    assert Paths.ROOT.exists()

def test_paths_ensure_dirs():
    """Verify that ensure_dirs creates the necessary directories."""
    # Create a temporary test directory structure if needed, 
    # but ensure_dirs should handle creation without error.
    Paths.ensure_dirs()
    assert Paths.DATA_PROCESSED.exists()
    assert Paths.SALIENCE_MAPS.exists()

def test_hyperparams_defaults():
    """Verify default hyperparameters are set correctly."""
    hp = Hyperparams.get()
    assert hp["seed"] == 42
    assert hp["salience_device"] == "cpu"
    assert hp["vif_threshold"] == 5.0
    assert hp["power_target"] == 0.80

def test_segmentation_classes():
    """Verify that weapons are excluded and face is included."""
    assert Hyperparams.SEGMENTATION_TARGET_CLASSES == ["face"]
    assert "weapon" not in Hyperparams.SEGMENTATION_TARGET_CLASSES

def test_get_functions():
    """Verify global getter functions return expected types."""
    assert isinstance(get_seed(), int)
    assert isinstance(get_paths(), Paths)
    assert isinstance(get_hyperparams(), dict)
    assert get_seed() == Hyperparams.SEED