"""Contract: exhaustion-evidence escalation records (spec 023 / FR-017;
contracts/escalation-record.md).

A human escalation without proof the bounded loop ran to its cap is a
contract violation — validated AT WRITE TIME (Constitution V fail-fast).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from llmxive.state.escalations import (
    EscalationRecord,
    EscalationValidationError,
    build_digest_markdown,
    list_records,
    write_record,
)


def _record(**overrides) -> EscalationRecord:
    base = dict(
        project_id="PROJ-910-esc",
        stage="plan",
        loop="convergence-kickback",
        bound=3,
        rounds_used=3,
        attempts=[
            {"round": "1", "summary": "revised plan", "outcome": "panel rejected"},
            {"round": "2", "summary": "revised again", "outcome": "panel rejected"},
            {"round": "3", "summary": "revised again", "outcome": "panel rejected"},
        ],
        recommended_action="review the unresolved concerns",
    )
    base.update(overrides)
    return EscalationRecord(**base)


def test_valid_record_round_trips(tmp_path: Path) -> None:
    path = write_record(_record(), repo_root=tmp_path)
    assert path.is_file()
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["project_id"] == "PROJ-910-esc"
    assert data["rounds_used"] == 3
    assert data["bound"] == 3
    assert data["timestamp"], "timestamp stamped on write"
    assert data["digest_id"] is None
    records = list_records(repo_root=tmp_path)
    assert len(records) == 1
    assert records[0].loop == "convergence-kickback"


def test_premature_escalation_fails_fast(tmp_path: Path) -> None:
    """rounds_used < bound → the loop is NOT exhausted; writing is a hard
    error, not a warning."""
    with pytest.raises(EscalationValidationError, match="NOT exhausted"):
        write_record(_record(rounds_used=1), repo_root=tmp_path)
    assert list_records(repo_root=tmp_path) == []


def test_unbounded_loop_rejected(tmp_path: Path) -> None:
    with pytest.raises(EscalationValidationError, match="no bounded loop"):
        write_record(_record(bound=0, rounds_used=0), repo_root=tmp_path)


def test_open_only_listing_excludes_digested(tmp_path: Path) -> None:
    write_record(_record(), repo_root=tmp_path)
    write_record(
        _record(project_id="PROJ-911-esc", digest_id="42"), repo_root=tmp_path
    )
    assert len(list_records(repo_root=tmp_path)) == 2
    open_recs = list_records(repo_root=tmp_path, open_only=True)
    assert [r.project_id for r in open_recs] == ["PROJ-910-esc"]


def test_digest_markdown_has_one_row_per_record() -> None:
    md = build_digest_markdown([_record(), _record(project_id="PROJ-911-esc")])
    assert md.count("| PROJ-9") == 2
    assert "3/3" in md
