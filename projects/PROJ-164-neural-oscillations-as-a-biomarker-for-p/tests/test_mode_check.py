"""Unit tests for T012: Mode Propagation Task."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "code" / "04_mode_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("mode_check", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["mode_check"] = module
    spec.loader.exec_module(module)
    return module


mc = _load_module()


class TestDetermineMode:
    def test_data_insufficient_when_absent(self):
        manifest = {"status": "absent", "mode_flag": "Data Insufficient"}
        assert mc.determine_mode(manifest) == "Data Insufficient"

    def test_primary_when_found(self):
        manifest = {"status": "found", "mode_flag": "Primary", "N_actual": 100}
        assert mc.determine_mode(manifest) == "Primary"

    def test_underpowered(self):
        manifest = {"status": "found", "mode_flag": "Underpowered"}
        assert mc.determine_mode(manifest) == "Underpowered"

    def test_fallback_to_status_absent(self):
        manifest = {"status": "absent"}
        assert mc.determine_mode(manifest) == "Data Insufficient"

    def test_fallback_to_status_found(self):
        manifest = {"status": "found"}
        assert mc.determine_mode(manifest) == "Primary"

    def test_inconsistent_manifest_raises(self):
        manifest = {"status": "absent", "mode_flag": "Primary"}
        with pytest.raises(ValueError):
            mc.determine_mode(manifest)

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError):
            mc.determine_mode({"mode_flag": "Bogus"})

    def test_missing_fields_raises(self):
        with pytest.raises(ValueError):
            mc.determine_mode({})


class TestSaveModeFlag:
    def test_save_writes_flag_file(self, tmp_path, monkeypatch):
        flag_path = tmp_path / "mode_flag.json"
        monkeypatch.setattr(mc, "MODE_FLAG_PATH", flag_path)
        mc.save_mode_flag("Data Insufficient")
        payload = json.loads(flag_path.read_text())
        assert payload["mode_flag"] == "Data Insufficient"
        assert payload["downstream_execution_skipped"] is True

    def test_save_primary_not_skipped(self, tmp_path, monkeypatch):
        flag_path = tmp_path / "mode_flag.json"
        monkeypatch.setattr(mc, "MODE_FLAG_PATH", flag_path)
        mc.save_mode_flag("Primary")
        payload = json.loads(flag_path.read_text())
        assert payload["mode_flag"] == "Primary"
        assert payload["downstream_execution_skipped"] is False

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError):
            mc.save_mode_flag("Bogus")


class TestLoadManifest:
    def test_missing_manifest_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mc, "MANIFEST_PATH", tmp_path / "nope.json")
        with pytest.raises(FileNotFoundError):
            mc.load_manifest()

    def test_malformed_manifest_raises(self, tmp_path, monkeypatch):
        p = tmp_path / "m.json"
        p.write_text(json.dumps([1, 2, 3]))
        monkeypatch.setattr(mc, "MANIFEST_PATH", p)
        with pytest.raises(ValueError):
            mc.load_manifest()


class TestMainIntegration:
    def test_main_returns_zero_with_real_manifest(self):
        # Requires the real manifest from T011 on disk.
        if not mc.MANIFEST_PATH.exists():
            pytest.skip("verified_source_manifest.json not present")
        assert mc.main() == 0
        payload = json.loads(mc.MODE_FLAG_PATH.read_text())
        assert payload["mode_flag"] in mc.VALID_MODES