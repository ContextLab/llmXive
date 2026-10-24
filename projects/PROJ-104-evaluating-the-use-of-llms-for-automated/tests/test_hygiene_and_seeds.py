"""Tests for the data‑hygiene utilities and the global seed.

The test suite verifies:
1. The globally pinned seed is indeed ``42``.
2. Every file under ``data/`` has a checksum entry in ``data/metadata.yaml``.
3. All files in ``data/`` (raw, intermediate, processed) are immutable.
4. Stochastic scripts (e.g., T002 power analysis) are deterministic given SEED.
5. Stochastic scripts explicitly import SEED from ``code.seeds``.
"""
import os
import yaml
import pytest
from pathlib import Path

from llmxive_toolkit import paths
from code.seeds import SEED
from code import data_hygiene
from code.power_analysis import run_power_analysis

def test_seed_is_pinned():
    """The global seed must be 42."""
    assert SEED == 42

def test_metadata_covers_all_data_files():
    """Every file under ``data/`` must have a checksum entry."""
    data_hygiene.update_all_metadata()
    metadata_path = paths.data("metadata.yaml")
    assert metadata_path.is_file()

    with metadata_path.open() as f:
        meta = yaml.safe_load(f) or {}

    data_root = paths.root / "data"
    for file_path in data_root.rglob("*"):
        if file_path.is_file():
            rel = str(file_path.relative_to(paths.root))
            # Skip metadata file itself
            if rel == str(metadata_path.relative_to(paths.root)):
                continue
            assert rel in meta, f"Missing checksum for {rel}"
            assert "checksum" in meta[rel], f"Missing checksum field for {rel}"

def test_data_files_are_immutable(tmp_path):
    """Verify that modifying any file in data/ triggers a RuntimeError in update_all_metadata."""
    # Test raw file
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file = raw_dir / "immutability_raw.txt"
    raw_file.write_text("raw content")
    
    # Test processed file
    proc_dir = paths.data("processed")
    proc_dir.mkdir(parents=True, exist_ok=True)
    proc_file = proc_dir / "immutability_proc.txt"
    proc_file.write_text("proc content")
    
    # First pass: record the checksums
    data_hygiene.update_all_metadata()
    
    # Modify the raw file
    raw_file.write_text("modified raw content")
    with pytest.raises(RuntimeError, match="Data hygiene violation"):
        data_hygiene.update_all_metadata()
    
    # Restore raw file, then modify processed file
    raw_file.write_text("raw content")
    proc_file.write_text("modified proc content")
    with pytest.raises(RuntimeError, match="Data hygiene violation"):
        data_hygiene.update_all_metadata()
    
    # Cleanup
    raw_file.unlink()
    proc_file.unlink()

def test_stochastic_consistency_t002():
    """Re-running T002 (power analysis) twice must yield identical power estimates."""
    res1 = run_power_analysis()
    res2 = run_power_analysis()
    assert res1["estimated_power"] == res2["estimated_power"], "T002 is not deterministic"

def test_seed_import_coverage():
    """Verify that key stochastic scripts import SEED from code.seeds."""
    stochastic_scripts = [
        "code/power_analysis.py",
        "code/gold_annotation.py",
        "code/generation.py",
        "code/entity_extraction_intent.py"
    ]
    for script_rel in stochastic_scripts:
        script_path = paths.root / script_rel
        if script_path.is_file():
            content = script_path.read_text(encoding="utf-8")
            assert "from code.seeds import SEED" in content or "import code.seeds" in content, \
                f"{script_rel} does not appear to import the pinned SEED"
