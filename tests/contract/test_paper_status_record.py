"""Contract: per-paper status records (spec 023 / FR-022..024;
contracts/paper-status-record.md).

The load-bearing rule: serving the original (un-restyled) PDF REQUIRES a
recorded failure reason — a fallback without a report is rejected at
write time. Pre-023, 18 of 94 shelf papers were silent fallbacks.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llmxive.state import paper_status as ps

PAPER = "PROJ-930-status"


def test_successful_restyle_records_unaudited(tmp_path: Path) -> None:
    rec = ps.record_compile_result(
        PAPER,
        {
            "ok": True,
            "strategy": "llmxive-compile",
            "pdf": f"projects/{PAPER}/paper/pdf/main-llmxive.pdf",
            "errors": [],
        },
        repo_root=tmp_path,
    )
    assert rec["status"] == ps.STATUS_RESTYLED_UNAUDITED
    assert rec["failure"] is None
    on_disk = json.loads(
        (tmp_path / "state" / "paper_status" / f"{PAPER}.json").read_text()
    )
    assert on_disk["paper_id"] == PAPER
    assert on_disk["updated_at"]


def test_fallback_requires_failure_report(tmp_path: Path) -> None:
    rec = ps.record_compile_result(
        PAPER,
        {
            "ok": True,
            "strategy": "arxiv-fallback",
            "pdf": f"projects/{PAPER}/paper/pdf/2605.12345.pdf",
            "errors": ["restyle step failed"],
        },
        repo_root=tmp_path,
    )
    assert rec["status"] == ps.STATUS_FALLBACK
    assert rec["failure"]["stage"] == "restyle"
    assert "restyle step failed" in rec["failure"]["reason"]


def test_silent_fallback_is_rejected_at_write_time(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="silent fallback is prohibited"):
        ps._save(
            PAPER,
            {"status": ps.STATUS_FALLBACK, "pdf": "x.pdf", "failure": None},
            repo_root=tmp_path,
        )


def test_unknown_status_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must be one of"):
        ps._save(PAPER, {"status": "fine-probably"}, repo_root=tmp_path)


def test_audit_pass_promotes_to_audited(tmp_path: Path) -> None:
    ps.record_compile_result(
        PAPER,
        {"ok": True, "strategy": "llmxive-compile",
         "pdf": "p/main-llmxive.pdf", "errors": []},
        repo_root=tmp_path,
    )
    rec = ps.record_audit_result(
        PAPER, {"passed": True, "defects": []}, repo_root=tmp_path
    )
    assert rec["status"] == ps.STATUS_AUDITED
    assert rec["audit"]["passed"] is True


def test_audit_defects_keep_unaudited_and_record_them(tmp_path: Path) -> None:
    ps.record_compile_result(
        PAPER,
        {"ok": True, "strategy": "llmxive-compile",
         "pdf": "p/main-llmxive.pdf", "errors": []},
        repo_root=tmp_path,
    )
    rec = ps.record_audit_result(
        PAPER,
        {"passed": False, "defects": [{"kind": "literal_command_text", "page": 3}]},
        repo_root=tmp_path,
    )
    assert rec["status"] == ps.STATUS_RESTYLED_UNAUDITED
    assert rec["audit"]["defects"][0]["page"] == 3


def test_record_updates_on_reaudit(tmp_path: Path) -> None:
    """FR-023: the record updates after a repair round's re-audit."""
    ps.record_compile_result(
        PAPER,
        {"ok": True, "strategy": "llmxive-compile",
         "pdf": "p/main-llmxive.pdf", "errors": []},
        repo_root=tmp_path,
    )
    ps.record_audit_result(
        PAPER, {"passed": False, "defects": [{"kind": "x", "page": 1}]},
        repo_root=tmp_path,
    )
    rec = ps.record_audit_result(
        PAPER, {"passed": True, "defects": []}, repo_root=tmp_path
    )
    assert rec["status"] == ps.STATUS_AUDITED
    assert rec["audit"]["defects"] == []
