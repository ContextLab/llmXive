import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.chemical_families import assign_chemical_family


def test_alkali():
    """Test alkali metal assignment."""
    assert assign_chemical_family("Li") == "Alkali"
    assert assign_chemical_family("Na") == "Alkali"
    assert assign_chemical_family("K") == "Alkali"


def test_transition():
    """Test transition metal assignment."""
    assert assign_chemical_family("Fe") == "Transition"
    assert assign_chemical_family("Cu") == "Transition"
    assert assign_chemical_family("Zn") == "Transition"


def test_non_metal():
    """Test non-metal assignment."""
    assert assign_chemical_family("O") == "Non_Metal"
    assert assign_chemical_family("N") == "Non_Metal"
    assert assign_chemical_family("C") == "Non_Metal"


def test_unknown():
    """Test unknown element assignment."""
    assert assign_chemical_family("Xx") == "Unknown"
    assert assign_chemical_family("") == "Unknown"
