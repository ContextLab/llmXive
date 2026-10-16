"""Unit tests for the T017 data export (data/raw/ + data/manifest.jsonl)."""

import json
import sys
from pathlib import Path

import pytest
from llmxive_toolkit import paths

CODE_ROOT = paths.code()
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from src.data_synthesis.verify_volume import (  # noqa: E402
    calculate_total_duration,
    load_manifest,
)

MANIFEST_PATH = paths.data("manifest.jsonl")
RAW_DIR = paths.data("raw")


class TestManifestExport:
    def test_manifest_exists(self):
        if not MANIFEST_PATH.exists():
            pytest.skip("Export has not been run yet (run run_export.py first)")
        assert MANIFEST_PATH.stat().st_size > 0

    def test_manifest_entries_have_required_fields(self):
        if not MANIFEST_PATH.exists():
            pytest.skip("Export has not been run yet")
        required = {
            "chunk_id",
            "file_path",
            "frame_count",
            "duration_seconds",
            "sha256",
            "label_source",
        }
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
        assert lines, "manifest.jsonl is empty"
        for rec in lines:
            missing = required - set(rec)
            assert not missing, f"Missing fields {missing} in {rec}"

    def test_manifest_chunk_files_exist(self):
        if not MANIFEST_PATH.exists():
            pytest.skip("Export has not been run yet")
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                assert Path(rec["file_path"]).exists(), rec["file_path"]

    def test_manifest_duration_positive(self):
        if not MANIFEST_PATH.exists():
            pytest.skip("Export has not been run yet")
        data = load_manifest(MANIFEST_PATH)
        total = calculate_total_duration(data)
        assert total > 0

    def test_raw_dir_has_chunks(self):
        if not RAW_DIR.exists():
            pytest.skip("Export has not been run yet")
        chunks = list(RAW_DIR.glob("chunk_*.jsonl"))
        assert chunks, "data/raw/ contains no chunk files"