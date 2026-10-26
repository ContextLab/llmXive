"""Focused tests for T001: dataset loader (FR-001 via mmbench/ocean)."""

import json
from pathlib import Path

import jsonschema
import pytest
import yaml

from code.src.data import load_dataset as ld

PROJECT_ROOT = ld.PROJECT_ROOT
JSONL = PROJECT_ROOT / "data" / "raw" / "video_metadata.jsonl"
SCHEMA_PATH = ld.SCHEMA_PATH


def _schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def test_output_exists_with_records():
    assert JSONL.exists(), "data/raw/video_metadata.jsonl must exist (run the loader)"
    lines = JSONL.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) > 0


def test_every_record_conforms_to_schema():
    schema = _schema()
    validator = jsonschema.Draft7Validator(schema)
    with open(JSONL, "r", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            rec = json.loads(line)
            errors = list(validator.iter_errors(rec))
            assert not errors, f"record {i}: {errors[0].message}"


def test_record_count_matches_stats():
    stats_path = PROJECT_ROOT / "data" / "raw" / "dataset_stats.json"
    assert stats_path.exists()
    stats = json.loads(stats_path.read_text(encoding="utf-8"))
    n_lines = sum(1 for _ in open(JSONL, "r", encoding="utf-8"))
    assert stats["n_records"] == n_lines
    assert "sample_size_power_limitation" in stats
    assert stats["sample_size_power_limitation"].strip()


def test_checksums_file_matches_jsonl():
    cs_path = PROJECT_ROOT / "data" / "raw" / "checksums.json"
    assert cs_path.exists()
    cs = json.loads(cs_path.read_text(encoding="utf-8"))
    entry = cs["files"]["data/raw/video_metadata.jsonl"]
    assert entry["sha256"] == ld.sha256_file(JSONL)
    assert entry["record_count"] > 0


def test_forced_fetch_failure_raises(monkeypatch):
    """A fetch failure must propagate — no synthetic fallback (FR-001)."""

    def boom(*args, **kwargs):
        raise RuntimeError("simulated network failure")

    monkeypatch.setattr(ld, "load_dataset", boom)
    with pytest.raises(RuntimeError, match="simulated network failure"):
        list(ld.stream_records())


def test_normalize_record_missing_video_id_raises():
    with pytest.raises(ValueError):
        ld.normalize_record({"transcript": "hello"}, 0)


def test_normalize_record_maps_fields():
    rec = ld.normalize_record(
        {
            "video": "vid_001",
            "video_url": "https://example.com/v.mp4",
            "transcript": " hi there ",
            "setting": "job interview",
            "culture": "East Asian",
            "behavior_tags": "smiles, nods",
            "answer": "B",
        },
        0,
    )
    assert rec["video_id"] == "vid_001"
    assert rec["video_url"] == "https://example.com/v.mp4"
    assert rec["transcript"] == "hi there"
    assert rec["setting"] == "job interview"
    assert rec["culture"] == "East Asian"
    assert rec["behavior_tags"] == ["smiles", "nods"]
    assert rec["expert_labels"] == {"label": "B"}
    schema = _schema()
    jsonschema.validate(rec, schema)