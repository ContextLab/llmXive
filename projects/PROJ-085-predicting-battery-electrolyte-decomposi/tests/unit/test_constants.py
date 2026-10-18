"""
Unit tests for ``code.utils.constants``.

These tests verify that the core constants have the expected values and that
the helper functions behave correctly.
"""

import pytest

from utils.constants import (
    FARADAY_C,
    PHI_VALUES,
    get_potential_bin,
    DEFAULT_SEED,
    load_reactions,
)


def test_farad_constant():
    """Faraday constant must match the specification."""
    assert isinstance(FARADAY_C, float)
    assert abs(FARADAY_C - 96485.33212) < 1e-6


@pytest.mark.parametrize(
    "potential,expected_bin",
    [
        (0.0, "low"),
        (1.5, "low"),
        (2.0, "low"),
        (2.5, "high"),
        (4.0, "high"),
        (5.0, "high"),
    ],
)
def test_potential_binning(potential, expected_bin):
    """Potential values should be mapped to the correct bin."""
    assert get_potential_bin(potential) == expected_bin


def test_default_seed():
    """The default seed should be an integer and equal to the documented value."""
    assert isinstance(DEFAULT_SEED, int)
    assert DEFAULT_SEED == 42


def test_load_reactions_structure():
    """The reactions YAML must contain an ``entries`` list."""
    data = load_reactions()
    assert isinstance(data, dict)
    assert "entries" in data
    assert isinstance(data["entries"], list)
    # Spot‑check the first entry for required keys
    if data["entries"]:
        entry = data["entries"][0]
        for key in [
            "molecule_id",
            "potential_v",
            "reactants",
            "products",
            "n_electrons",
            "energy_products",
            "energy_reactants",
        ]:
            assert key in entry
