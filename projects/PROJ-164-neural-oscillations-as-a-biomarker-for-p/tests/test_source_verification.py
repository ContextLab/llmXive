"""Unit tests for T011 source verification logic (no network required)."""

import importlib.util
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "code" / "03_source_verification.py"

def _load_module():
    spec = importlib.util.spec_from_file_location("source_verification", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["source_verification"] = mod
    spec.loader.exec_module(mod)
    return mod

@pytest.fixture(scope="module")
def mod():
    return _load_module()

def test_paired_detection_positive(mod):
    entry = {"name": "EEG during tDCS motor task",
             "description": "raw EEG with tDCS stimulation scores"}
    assert mod.is_paired_eeg_tdcs(entry) is True

def test_paired_detection_eeg_only(mod):
    entry = {"name": "EEG Motor Movement/Imagery",
             "description": "resting state EEG recordings"}
    assert mod.is_paired_eeg_tdcs(entry) is False

def test_paired_detection_tdcs_only(mod):
    entry = {"name": "tDCS motor learning behavioral scores",
             "description": "behavioral outcomes only"}
    assert mod.is_paired_eeg_tdcs(entry) is False

def test_query_and_scope_constants(mod):
    assert mod.QUERY_STRING == "EEG AND tDCS AND motor"
    assert sorted(mod.SEARCH_SCOPE) == ["Kaggle", "OpenNeuro", "PhysioNet"]

def test_manifest_written_with_mandatory_fields():
    """If the executed script ran, the manifest must carry FR-018 fields."""
    import json
    manifest_path = _MODULE_PATH.parents[1] / "data" / "verified_source_manifest.json"
    if not manifest_path.exists():
        pytest.skip("manifest not yet generated (script not executed)")
    manifest = json.loads(manifest_path.read_text())
    assert manifest["query_string"] == "EEG AND tDCS AND motor"
    assert set(["OpenNeuro", "PhysioNet", "Kaggle"]) <= set(manifest["search_scope"])
    assert manifest["status"] in ("found", "absent")
    assert isinstance(manifest["N_actual"], int)
    assert "mode_flag" in manifest