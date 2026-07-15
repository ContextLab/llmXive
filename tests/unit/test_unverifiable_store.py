"""Round-trip tests for the repeatedly-unverifiable-task store (issue #1139, D6).

Exercises the REAL JSON files under ``state/unverifiable_tasks/<id>.json`` — no
mocks — pinning the cross-cluster contract the pipeline graph consumes to route a
project to ``research_full_revision``.
"""

from __future__ import annotations

import json
from pathlib import Path

from llmxive.state import unverifiable as unv


def test_record_load_clear_round_trip(tmp_path: Path) -> None:
    pid = "PROJ-777-demo"
    assert unv.load(pid, repo_root=tmp_path) == []
    assert not unv.has_unverifiable(pid, repo_root=tmp_path)

    rec = unv.record_unverifiable(pid, "T012", "artifact missing", repo_root=tmp_path)
    assert rec["project_id"] == pid
    assert unv.has_unverifiable(pid, repo_root=tmp_path)

    loaded = unv.load(pid, repo_root=tmp_path)
    assert len(loaded) == 1
    entry = loaded[0]
    # Contract schema: task_key, reject_count, last_reason, first_seen, last_seen.
    assert entry["task_key"] == "T012"
    assert entry["reject_count"] == 1
    assert entry["last_reason"] == "artifact missing"
    assert "first_seen" in entry and "last_seen" in entry
    assert unv.recorded_keys(pid, repo_root=tmp_path) == {"T012"}

    # The file lives at the documented path and is valid JSON with an updated_at.
    p = tmp_path / "state" / "unverifiable_tasks" / f"{pid}.json"
    assert p.is_file()
    raw = json.loads(p.read_text(encoding="utf-8"))
    assert raw["project_id"] == pid and "updated_at" in raw

    unv.clear(pid, repo_root=tmp_path)
    assert unv.load(pid, repo_root=tmp_path) == []
    assert not unv.has_unverifiable(pid, repo_root=tmp_path)
    assert not p.exists()


def test_record_same_key_bumps_count_and_preserves_first_seen(tmp_path: Path) -> None:
    pid = "PROJ-778-bump"
    unv.record_unverifiable(pid, "T003", "reason one", repo_root=tmp_path)
    first_seen = unv.load(pid, repo_root=tmp_path)[0]["first_seen"]

    unv.record_unverifiable(pid, "T003", "reason two", repo_root=tmp_path)
    loaded = unv.load(pid, repo_root=tmp_path)
    assert len(loaded) == 1  # same key → one entry, not two
    entry = loaded[0]
    assert entry["reject_count"] == 2
    assert entry["last_reason"] == "reason two"
    assert entry["first_seen"] == first_seen  # preserved


def test_multiple_keys_and_recorded_keys(tmp_path: Path) -> None:
    pid = "PROJ-779-multi"
    unv.record_unverifiable(pid, "T001", "a", repo_root=tmp_path)
    unv.record_unverifiable(pid, "T002", "b", repo_root=tmp_path)
    assert unv.recorded_keys(pid, repo_root=tmp_path) == {"T001", "T002"}
    assert len(unv.load(pid, repo_root=tmp_path)) == 2


def test_load_tolerates_missing_and_corrupt_file(tmp_path: Path) -> None:
    pid = "PROJ-780-corrupt"
    # Missing file → empty list, no raise.
    assert unv.load(pid, repo_root=tmp_path) == []
    # Corrupt JSON → empty list, no raise.
    p = tmp_path / "state" / "unverifiable_tasks" / f"{pid}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{not valid json", encoding="utf-8")
    assert unv.load(pid, repo_root=tmp_path) == []
    assert unv.recorded_keys(pid, repo_root=tmp_path) == set()
