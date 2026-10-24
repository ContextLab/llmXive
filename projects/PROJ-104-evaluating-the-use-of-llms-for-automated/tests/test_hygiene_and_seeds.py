"""Tests for the data‑hygiene utilities and the global seed.

The test suite verifies two core non‑functional requirements:
1. The globally pinned seed is indeed ``42`` (Constitution I).
2. After the full data‑generation stages have run, every file under the
   ``data/`` directory has a corresponding SHA‑256 entry in
   ``data/metadata.yaml``.
"""
import yaml

from llmxive_toolkit import paths

from code.seeds import SEED
from code import data_hygiene

def test_seed_is_pinned():
    """The global seed must be 42."""
    assert SEED == 42

def test_metadata_covers_all_data_files():
    """Every file under ``data/`` must have a checksum entry."""
    # Run the checksum update – this recomputes the manifest.
    data_hygiene.update_all_metadata()

    metadata_path = paths.data("metadata.yaml")
    assert metadata_path.is_file(), "metadata.yaml was not created"

    with metadata_path.open() as f:
        meta = yaml.safe_load(f) or {}

    data_root = paths.root / "data"
    for file_path in data_root.rglob("*"):
        if file_path.is_file():
            rel = str(file_path.relative_to(paths.root))
            assert rel in meta, f"Missing checksum for {rel}"