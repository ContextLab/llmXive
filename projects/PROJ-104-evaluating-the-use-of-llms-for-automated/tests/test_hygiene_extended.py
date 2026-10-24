"""Extended hygiene tests for Task T013.

These tests go beyond the original suite by checking:

1. **Checksum stability** – a raw data file created during the test
   should retain the same SHA‑256 checksum across successive calls to
   ``code.data_hygiene.update_all_metadata``.
2. **Seed import compliance** – every Python module under ``code/`` must
   import the global seed ``SEED`` from ``code.seeds`` to satisfy the
   reproducibility policy.
"""
import pathlib

import yaml

from llmxive_toolkit import paths

from code import data_hygiene
from code.seeds import SEED

def test_seed_is_pinned():
    """The global seed must be 42 (also verifies import works)."""
    assert SEED == 42

def test_checksum_stability(tmp_path):
    """A raw file's checksum must remain unchanged across metadata updates."""
    # Create a dummy raw file inside the project data tree.
    raw_dir = paths.root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    dummy_file = raw_dir / "dummy_raw.txt"
    dummy_file.write_text("initial content for checksum test", encoding="utf-8")

    # First metadata generation.
    data_hygiene.update_all_metadata()
    meta_path = paths.data("metadata.yaml")
    with meta_path.open() as f:
        meta1 = yaml.safe_load(f) or {}
    rel = str(dummy_file.relative_to(paths.root))
    checksum1 = meta1.get(rel)
    assert checksum1 is not None, f"Checksum for {rel} missing after first update"

    # Second metadata generation without modifying the file.
    data_hygiene.update_all_metadata()
    with meta_path.open() as f:
        meta2 = yaml.safe_load(f) or {}
    checksum2 = meta2.get(rel)
    assert checksum2 == checksum1, "Checksum changed between updates for a raw file"

def test_all_code_modules_import_seed():
    """Every module in ``code/`` must import the global SEED."""
    code_dir = pathlib.Path(__file__).parents[1] / "code"
    for py_path in code_dir.rglob("*.py"):
        # Skip __init__ and test files.
        if py_path.name.startswith("__") or py_path.name.startswith("test_"):
            continue
        content = py_path.read_text()
        assert "from code.seeds import SEED" in content, (
            f"Module {py_path.relative_to(paths.root)} does not import SEED"
        )
