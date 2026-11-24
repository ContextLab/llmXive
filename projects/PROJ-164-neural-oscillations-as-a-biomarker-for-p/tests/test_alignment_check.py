"""Unit tests for the T015 Data Alignment Check (FR-011).

Tests subject-ID extraction, alignment verification, and the
Data-Insufficient mode switch on mismatch.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "code" / "05_data_alignment_check.py"

spec = importlib.util.spec_from_file_location("data_alignment_check", MODULE_PATH)
dac = importlib.util.module_from_spec(spec)
sys.modules["data_alignment_check"] = dac
spec.loader.exec_module(dac)


class TestExtractSubjectId:
    def test_valid_pattern(self):
        assert dac.extract_subject_id("sub-01_run-1.edf") == "01"

    def test_second_subject(self):
        assert dac.extract_subject_id("sub-S42_run-03.edf") == "S42"

    def test_non_matching_filename_returns_none(self):
        assert dac.extract_subject_id("random_file.edf") is None

    def test_empty_string_returns_none(self):
        assert dac.extract_subject_id("") is None


class TestVerifyAlignment:
    def _make_raw(self, tmp_path, names):
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        for n in names:
            f = raw_dir / n
            f.write_bytes(b"placeholder-not-loaded")
        return raw_dir

    def test_report_structure(self, tmp_path):
        raw_dir = self._make_raw(
            tmp_path, ["sub-01_run-1.edf", "sub-01_run-2.edf", "sub-02_run-1.edf"]
        )
        manifest = {"status": "found", "N_actual": 2, "dataset": {"id": "x"}}
        report = dac.verify_alignment(raw_dir, manifest)
        for key in ("status", "subjects_found", "expected_count", "message"):
            assert key in report
        assert set(report["subjects_found"]) == {"01", "02"}
        assert report["status"] in ("aligned", "mismatch")

    def test_empty_raw_dir_is_mismatch(self, tmp_path):
        raw_dir = self._make_raw(tmp_path, [])
        report = dac.verify_alignment(raw_dir, {"status": "found", "N_actual": 5})
        assert report["status"] == "mismatch"
        assert report["subjects_found"] == []

    def test_unparseable_files_reported(self, tmp_path):
        raw_dir = self._make_raw(tmp_path, ["notes.txt"])
        report = dac.verify_alignment(raw_dir, {"status": "found"})
        assert report["subjects_found"] == []


class TestSetModeInsufficient:
    def test_updates_manifest_and_mode_flag(self, tmp_path):
        manifest_path = tmp_path / "verified_source_manifest.json"
        manifest = {"status": "found", "mode_flag": "Primary", "N_actual": 10}
        manifest_path.write_text(json.dumps(manifest))
        mode_flag_path = tmp_path / "mode_flag.txt"

        dac.set_mode_insufficient(
            mode_flag_path, manifest_path, "subject overlap mismatch"
        )

        updated = json.loads(manifest_path.read_text())
        assert updated["mode_flag"] == "Data Insufficient"
        assert "subject overlap mismatch" in updated.get("reason", "")
        flag_text = mode_flag_path.read_text().strip() if mode_flag_path.exists() else ""
        assert "Data Insufficient" in flag_text or flag_text == ""

    def test_missing_manifest_raises(self, tmp_path):
        with pytest.raises(Exception):
            dac.set_mode_insufficient(
                tmp_path / "mode.txt",
                tmp_path / "does_not_exist.json",
                "reason",
            )