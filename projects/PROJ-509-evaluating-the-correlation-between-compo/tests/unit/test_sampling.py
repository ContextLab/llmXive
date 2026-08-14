import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.sampling import sample_by_chemical_family
from utils.chemical_families import assign_chemical_family


def test_assign_chemical_family():
    """Test chemical family assignment."""
    assert assign_chemical_family("Na") == "Alkali"
    assert assign_chemical_family("Fe") == "Transition"
    assert assign_chemical_family("O") == "Non_Metal"
    assert assign_chemical_family("Unknown") == "Unknown"


def test_sample_by_chemical_family():
    """Test stratified sampling by chemical family."""
    df = pd.DataFrame(
        {
            "dominant_element": ["Na", "Na", "Fe", "Fe", "Fe", "O", "O"],
            "value": range(7),
        }
    )

    sampled = sample_by_chemical_family(df, target_rows=4, random_state=42)

    assert len(sampled) <= 4
    assert "chem_family" in sampled.columns


def test_sample_by_chemical_family_small():
    """Test sampling when target is larger than dataset."""
    df = pd.DataFrame(
        {
            "dominant_element": ["Na", "Fe"],
            "value": [1, 2],
        }
    )

    sampled = sample_by_chemical_family(df, target_rows=100, random_state=42)
    assert len(sampled) == 2
