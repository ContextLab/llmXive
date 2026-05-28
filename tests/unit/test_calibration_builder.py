"""Tests for the calibration set builder (spec 015 T067)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llmxive.calibration.builder import (
    build_set_for_stage,
    write_all,
    write_set_for_stage,
)


@pytest.mark.parametrize("stage", ["idea", "spec", "plan", "tasks", "paper"])
def test_build_set_for_stage_returns_positive_plus_negatives(stage: str):
    entries = build_set_for_stage(stage)
    # At least 2 entries (1 positive + ≥1 negative for every stage).
    assert len(entries) >= 2
    # Exactly one positive.
    positives = [e for e in entries if e.label == "positive"]
    assert len(positives) == 1
    # Every negative is labeled `negative_<injector>` and carries an
    # expected_lens.
    negatives = [e for e in entries if e.label.startswith("negative_")]
    assert len(negatives) >= 1
    for n in negatives:
        assert n.expected_lens is not None
        assert n.expected_lens, "expected_lens MUST be non-empty for negatives"
    # The positive has no expected_lens (it shouldn't be flagged at all).
    assert positives[0].expected_lens is None


def test_build_set_for_unknown_stage_raises():
    with pytest.raises(ValueError, match="no seed positive for stage"):
        build_set_for_stage("totally_unknown")


def test_negatives_differ_from_positive():
    """Every negative entry's text MUST differ from its positive — a
    silently-no-op injector would otherwise silently produce a
    'positive-disguised-as-negative' that confuses the calibration."""
    for stage in ("idea", "tasks", "paper"):
        entries = build_set_for_stage(stage)
        positive = next(e for e in entries if e.label == "positive")
        negatives = [e for e in entries if e.label != "positive"]
        for n in negatives:
            assert n.text != positive.text, (
                f"stage {stage!r}: negative {n.label!r} text matches "
                "positive — injector was a no-op"
            )


def test_write_set_for_stage_creates_md_and_label_pairs(tmp_path: Path):
    written = write_set_for_stage("tasks", tmp_path)
    # We expect 2 files per entry (md + label sidecar).
    assert len(written) % 2 == 0
    # Every .md has a sidecar .label.json next to it.
    md_files = [p for p in written if p.suffix == ".md"]
    for md in md_files:
        sidecar = md.with_suffix("").with_suffix(".label.json")
        # The above replaces .md with .label.json (Path API: with_suffix
        # replaces the LAST suffix only — we strip .md then add .label.json).
        sidecar = md.parent / (md.stem + ".label.json")
        assert sidecar.exists(), f"missing sidecar for {md}"
        data = json.loads(sidecar.read_text())
        assert data["stage"] == "tasks"
        # Positive sidecar has expected_lens=null; negatives have a string.
        if data["label"] == "positive":
            assert data["expected_lens"] is None
        else:
            assert isinstance(data["expected_lens"], str)


def test_write_all_emits_every_stage(tmp_path: Path):
    written = write_all(tmp_path)
    # Every stage subdir was populated.
    stages_seen = {p.parent.name for p in written if p.suffix == ".md"}
    assert "idea" in stages_seen
    assert "spec" in stages_seen
    assert "plan" in stages_seen
    assert "tasks" in stages_seen
    assert "paper" in stages_seen


def test_calibration_set_entry_is_immutable():
    """CalibrationSetEntry is a frozen dataclass — drivers must NOT
    mutate entries after build_set returns them (the entries are passed
    to the differential harness which assumes immutable inputs)."""
    entries = build_set_for_stage("idea")
    with pytest.raises((AttributeError, Exception)):  # FrozenInstanceError
        entries[0].text = "mutated"  # type: ignore[misc]


def test_entries_carry_human_readable_description():
    """The driver writes the description into the adjudication report;
    empty/None would be unhelpful for the maintainer."""
    for stage in ("idea", "spec", "plan", "tasks", "paper"):
        entries = build_set_for_stage(stage)
        for e in entries:
            assert isinstance(e.description, str)
            assert e.description.strip()
