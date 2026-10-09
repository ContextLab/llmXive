"""
Unit test for ``code.generate_mobius``.

The test executes the script's ``main`` function and verifies that
the expected output files are created and contain sensible data.
"""

import json
from pathlib import Path

import numpy as np

# Import the script as a module; the ``code`` package already has an
# ``__init__.py`` so ``import code.generate_mobius`` works.
from code import generate_mobius

def test_generate_mobius_creates_files(tmp_path, monkeypatch):
    """
    Run ``generate_mobius.main`` and check that:

    1. ``data/raw/mobius_array.npy`` exists.
    2. ``data/raw/window_starts.json`` exists.
    3. For each L ∈ {10³, 10⁴, 10⁵} there are exactly M = 20 start indices,
       each within the valid range [1, N‑L+1].
    """
    # Ensure the test runs in an isolated working directory.
    # The repository already contains a ``data`` directory; we let the
    # script write to that location because the task explicitly requires
    # those paths.
    generate_mobius.main()

    mobius_path = Path("data/raw/mobius_array.npy")
    starts_path = Path("data/raw/window_starts.json")

    assert mobius_path.is_file(), "Möbius array file was not created"
    assert starts_path.is_file(), "Window starts JSON file was not created"

    # Load and validate the JSON mapping.
    with starts_path.open("r", encoding="utf-8") as fp:
        starts_by_L = json.load(fp)

    N = 10_000_000
    M_expected = 20
    for L_str, starts in starts_by_L.items():
        L = int(L_str)
        assert isinstance(starts, list), f"Starts for L={L} not a list"
        assert len(starts) == M_expected, (
            f"Expected {M_expected} starts for L={L}, got {len(starts)}"
        )
        max_start = N - L + 1
        for s in starts:
            assert isinstance(s, int), "Start index is not an integer"
            assert 1 <= s <= max_start, (
                f"Start index {s} out of bounds for L={L} (max {max_start})"
            )

    # Spot‑check that the Möbius array has the correct dtype and shape.
    mobius_arr = np.load(mobius_path)
    assert mobius_arr.dtype == np.int8, "Möbius array dtype should be int8"
    assert mobius_arr.shape == (N + 1,), (
        f"Expected shape {(N + 1,)}, got {mobius_arr.shape}"
    )