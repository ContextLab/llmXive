"""
Unit test for the claim‑fetching script.

The test runs the script (via its ``main`` function) and checks that the
expected JSON file is created and contains a non‑empty ``label`` field.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Import the script's public API
from claims.fetch_memory_claim import main, fetch_claim, CLAIM_MAP


@pytest.fixture
def output_path(tmp_path: Path) -> Path:
    """
    Provide a temporary output directory and monkey‑patch the script's
    ``Path('data/claims/memory_claim.json')`` to point inside it.
    """
    # Patch the Path used inside the script
    original_path = Path("data/claims/memory_claim.json")
    patched_path = tmp_path / "memory_claim.json"

    # Monkey‑patch the module-level constant used by ``main``.
    # The script builds the path at runtime, so we replace the ``Path`` class
    # temporarily.
    import builtins

    class PatchedPath(Path):
        # type: ignore
        _flavour = Path._flavour

        def __new__(cls, *args, **kwargs):
            if args and args[0] == str(original_path):
                return patched_path.__class__(patched_path)
            return super().__new__(cls, *args, **kwargs)

    builtins.Path = PatchedPath  # type: ignore

    yield patched_path

    # Restore the original Path class after the test
    builtins.Path = Path  # type: ignore


def test_fetch_claim_returns_expected_structure():
    """
    Verify that ``fetch_claim`` returns a dictionary with the expected keys.
    """
    claim_id = "c_9aceca76"
    result = fetch_claim(claim_id)
    assert result["claim_id"] == claim_id
    assert result["wikidata_id"] == CLAIM_MAP[claim_id]
    assert isinstance(result["label"], str) and result["label"]
    assert isinstance(result["description"], str)
    assert isinstance(result["statements"], dict)


def test_main_writes_json_file(output_path: Path):
    """
    Run ``main`` and confirm that the JSON file is written and contains a
    ``label`` field.
    """
    main()
    assert output_path.is_file()
    with output_path.open() as f:
        data = json.load(f)
    assert data["label"]  # non‑empty label, e.g. \"memory\"
