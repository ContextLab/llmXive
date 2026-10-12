"""Tests for node-limit enforcement in load_cascade (task T014)."""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from pipeline.utils import load_cascade, validate_all_cascades

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _write_cascade(path: Path, cascade_id: str, n_nodes: int) -> Path:
    nodes = [
        {
            "node_id": f"{cascade_id}_n{i}",
            "timestamp": (BASE + timedelta(seconds=i)).isoformat(),
            "cascade_id": cascade_id,
        }
        for i in range(n_nodes)
    ]
    path.write_text(json.dumps({"nodes": nodes}), encoding="utf-8")
    return path


def test_oversized_cascade_is_skipped(tmp_path):
    skipped_log = tmp_path / "skipped_cascades.log"
    f = _write_cascade(tmp_path / "big.json", "big", 2001)
    df = load_cascade(
        str(f), node_limit=2000, skipped_log_path=str(skipped_log)
    )
    assert df is None
    log_text = skipped_log.read_text(encoding="utf-8")
    assert "cascade_id=big" in log_text
    assert "node_limit_exceeded" in log_text
    assert "nodes=2001" in log_text


def test_cascade_at_limit_is_loaded(tmp_path):
    skipped_log = tmp_path / "skipped_cascades.log"
    f = _write_cascade(tmp_path / "ok.json", "ok", 2000)
    df = load_cascade(
        str(f), node_limit=2000, skipped_log_path=str(skipped_log)
    )
    assert df is not None
    assert df["node_id"].nunique() == 2000
    assert not skipped_log.exists()


def test_small_cascade_loaded_and_normalized(tmp_path):
    f = _write_cascade(tmp_path / "small.json", "small", 5)
    df = load_cascade(str(f), node_limit=2000)
    assert df is not None
    assert len(df) == 5
    assert all(
        ts.tzinfo is not None and ts.utcoffset().total_seconds() == 0
        for ts in df["timestamp"]
    )


def test_validate_all_cascades_reports_skipped(tmp_path):
    skipped_log = tmp_path / "skipped_cascades.log"
    _write_cascade(tmp_path / "a.json", "a", 3)
    _write_cascade(tmp_path / "b.json", "b", 2500)
    valid, skipped = validate_all_cascades(
        str(tmp_path), node_limit=2000, skipped_log_path=str(skipped_log)
    )
    assert len(valid) == 1
    assert skipped == 1
    assert "cascade_id=b" in skipped_log.read_text(encoding="utf-8")


def test_missing_columns_raise(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps([{"node_id": "x"}]), encoding="utf-8")
    with pytest.raises(ValueError):
        load_cascade(str(bad))