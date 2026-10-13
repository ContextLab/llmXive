"""Unit tests for T014 oversampling verification (FR-001)."""

import json
import pytest

from analysis.verify_oversampling import verify, recompute_high_difficulty


def _write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return path


def _traj_schema(tid, score, tags):
    return {
        "trajectory_id": tid,
        "dialogue_history": ["a", "b"],
        "emotional_reactivity_score": score,
        "cultural_identity_tags": tags,
        "ideal_resolution": "resolve peacefully",
    }


def _traj_meta(tid, er, ci):
    return {
        "trajectory_id": tid,
        "turns": [{"turn_index": 0, "text": "hi", "speaker": "A"}],
        "initial_state": "neutral",
        "final_state": "neutral",
        "metadata": {"emotional_reactivity": er, "cultural_identity": ci},
    }


def test_recompute_schema_style(tmp_path):
    trajs = [
        _traj_schema("t1", 0.9, ["A"]),        # high emotion only
        _traj_schema("t2", 0.2, ["A", "B"]),   # diverse cultural only
        _traj_schema("t3", 0.1, ["A"]),        # neither
        _traj_schema("t4", 0.8, ["A", "B"]),   # both
        _traj_schema("t5", 0.95, ["A"]),       # high emotion
    ]
    total, he, hc, hd = recompute_high_difficulty(trajs)
    assert total == 5
    assert he == 3
    assert hc == 2
    assert hd == 4

def test_recompute_metadata_style(tmp_path):
    trajs = [
        _traj_meta("t1", "high", "low"),
        _traj_meta("t2", "low", "highly_diverse"),
        _traj_meta("t3", "low", "low"),
    ]
    total, he, hc, hd = recompute_high_difficulty(trajs)
    assert (total, he, hc, hd) == (3, 1, 1, 2)

def test_verify_passes_and_writes_report(tmp_path):
    trajs = [_traj_schema(f"t{i}", 0.9 if i < 3 else 0.1, ["A", "B"] if i < 2 else ["A"])
             for i in range(5)]
    stats = {"total_count": 5, "high_emotion_count": 3, "high_cultural_count": 2,
             "oversampling_ratio": 0.8, "underpowered_flag": False}
    tpath = _write(tmp_path / "trajectories.json", trajs)
    spath = _write(tmp_path / "generation_stats.json", stats)
    rpath = tmp_path / "results" / "oversampling_report.json"

    report = verify(tpath, spath, rpath)

    assert rpath.exists()
    data = json.loads(rpath.read_text())
    assert data["total_count"] == 5
    assert data["high_difficulty_count"] == 5
    assert data["oversampling_ratio"] == 1.0
    assert data["passes_fr001"] is True
    assert report["passes_fr001"] is True

def test_verify_fails_below_threshold(tmp_path):
    trajs = [_traj_schema(f"t{i}", 0.1, ["A"]) for i in range(10)]
    stats = {"total_count": 10, "high_emotion_count": 0, "high_cultural_count": 0,
             "oversampling_ratio": 0.0, "underpowered_flag": False}
    tpath = _write(tmp_path / "trajectories.json", trajs)
    spath = _write(tmp_path / "generation_stats.json", stats)
    rpath = tmp_path / "results" / "oversampling_report.json"

    report = verify(tpath, spath, rpath)
    assert report["passes_fr001"] is False
    assert report["oversampling_ratio"] == 0.0

def test_verify_fails_loudly_on_missing_inputs(tmp_path):
    with pytest.raises(FileNotFoundError):
        verify(tmp_path / "missing.json", tmp_path / "stats.json",
               tmp_path / "out.json")

def test_verify_fails_loudly_on_malformed_stats(tmp_path):
    trajs = [_traj_schema("t1", 0.9, ["A"])]
    tpath = _write(tmp_path / "trajectories.json", trajs)
    spath = _write(tmp_path / "generation_stats.json", {"total_count": 1})
    with pytest.raises(ValueError):
        verify(tpath, spath, tmp_path / "out.json")

def test_verify_fails_loudly_on_malformed_trajectory(tmp_path):
    trajs = [{"no_id": True}]
    tpath = _write(tmp_path / "trajectories.json", trajs)
    spath = _write(tmp_path / "generation_stats.json",
                   {"total_count": 1, "high_emotion_count": 0,
                    "high_cultural_count": 0, "oversampling_ratio": 0.0})
    with pytest.raises(ValueError):
        verify(tpath, spath, tmp_path / "out.json")