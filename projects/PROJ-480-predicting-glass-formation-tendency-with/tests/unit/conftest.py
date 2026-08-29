"""
Pytest configuration and fixtures for unit tests.

This file provides shared fixtures and configuration for the test suite.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_element_data():
    """Provide mock element data for testing."""
    return {
        "Cu": {"radius": 128.0, "electronegativity": 1.90, "atomic_number": 29},
        "Zr": {"radius": 160.0, "electronegativity": 1.33, "atomic_number": 40},
        "Fe": {"radius": 124.0, "electronegativity": 1.83, "atomic_number": 26},
        "Co": {"radius": 125.0, "electronegativity": 1.88, "atomic_number": 27},
        "Ni": {"radius": 124.0, "electronegativity": 1.91, "atomic_number": 28},
        "Ti": {"radius": 147.0, "electronegativity": 1.54, "atomic_number": 22},
        "Al": {"radius": 143.0, "electronegativity": 1.61, "atomic_number": 13},
    }


@pytest.fixture
def mock_mixing_enthalpy_data():
    """Provide mock mixing enthalpy data for testing."""
    # Format: frozenset({element1, element2}): value (kJ/mol)
    return {
        frozenset(["Cu", "Zr"]): -10.0,
        frozenset(["Cu", "Fe"]): -5.0,
        frozenset(["Cu", "Co"]): -2.0,
        frozenset(["Cu", "Ni"]): -1.0,
        frozenset(["Cu", "Ti"]): -8.0,
        frozenset(["Cu", "Al"]): -12.0,
        frozenset(["Zr", "Fe"]): -15.0,
        frozenset(["Zr", "Co"]): -14.0,
        frozenset(["Zr", "Ni"]): -13.0,
        frozenset(["Zr", "Ti"]): -5.0,
        frozenset(["Zr", "Al"]): -18.0,
    }


@pytest.fixture
def sample_composition():
    """Provide a sample composition string for testing."""
    return "Cu50Zr50"


@pytest.fixture
def sample_dataframe():
    """Provide a sample DataFrame for testing."""
    data = {
        "composition": ["Cu50Zr50", "Fe30Co30Ni40", "Ti60Cu40"],
        "delta": [11.11, 0.5, 5.2],
        "delta_H_mix": [-5.0, -2.0, -8.0],
        "delta_chi": [0.403, 0.03, 0.25],
    }
    return pd.DataFrame(data)


@pytest.fixture(autouse=True)
def setup_mock_pymatgen(mock_element_data, mock_mixing_enthalpy_data):
    """Automatically mock pymatgen dependencies for all tests."""
    with patch('src.data.descriptors.Element') as MockElement:
        # Configure mock Element class
        MockElement.__getitem__ = lambda self, key: mock_element_data.get(key, {"radius": None, "electronegativity": None})
        
        # Mock the mixing enthalpy function
        with patch('src.data.descriptors._get_mixing_enthalpy', side_effect=lambda e1, e2: mock_mixing_enthalpy_data.get(frozenset([e1, e2]), 0.0)):
            yield
