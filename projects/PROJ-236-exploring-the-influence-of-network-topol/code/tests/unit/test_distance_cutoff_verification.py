"""
Unit tests for the distance‑cutoff verification logic (T019).
The tests monkey‑patch the I/O helpers and the nearest‑neighbour distance
calculator so that they operate on deterministic in‑memory data.
"""

import builtins
import types

import numpy as np
import pytest

# Import the module under test.
from ci import check_distance_cutoff

@pytest.fixture
def mock_io(monkeypatch):
    """
    Replace ``load_simulation_config`` and ``get_config_value`` with simple
    deterministic stand‑ins.
    """
    def fake_load():
        # The actual value will be injected by the test via ``factor`` attribute.
        return {"cutoff_factor": mock_io.factor}

    def fake_get(config, key):
        return config[key]

    monkeypatch.setattr(check_distance_cutoff, "load_simulation_config", fake_load)
    monkeypatch.setattr(check_distance_cutoff, "get_config_value", fake_get)

@pytest.fixture
def mock_distance(monkeypatch):
    """
    Stub ``nearest_neighbor_distance`` to return a constant value.
    """
    monkeypatch.setattr(
        check_distance_cutoff,
        "nearest_neighbor_distance",
        lambda _: 2.5,  # arbitrary NN distance in Å
    )
    # Stub ``find_first_seed_file`` – the path is never used thanks to the stub above.
    monkeypatch.setattr(
        check_distance_cutoff,
        "find_first_seed_file",
        lambda: builtins.str("dummy_path"),
    )

@pytest.mark.parametrize(
    "factor,expected",
    [
        (1.0, False),   # No change – verification should fail.
        (1.5, True),    # Effective scaling – verification should pass.
        (0.8, True),    # Effective scaling – verification should pass.
    ],
)
def test_cutoff_scaling_behavior(factor, expected, monkeypatch, mock_io, mock_distance):
    """
    Ensure ``check_cutoff_scaling`` returns the correct boolean based on the
    supplied scaling factor.
    """
    # Inject the desired factor into the fixture.
    mock_io.factor = factor

    result = check_distance_cutoff.check_cutoff_scaling()
    assert result is expected, f"Factor {factor} produced {result}, expected {expected}"
