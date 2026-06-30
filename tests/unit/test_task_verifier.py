"""Independent task-completion verifier (spec-contract consistency).

The verifier is a SEPARATE LLM call (outside the implementer's session) that judges
whether a claimed-done task's actual artifacts satisfy its requirements. These
tests pin the pure parsing / evidence-gathering / fail-closed behavior; the live
model call is exercised by the real-call suite.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.agents import task_verifier as tv


def test_parse_complete_and_incomplete() -> None:
    assert tv._parse("VERDICT: COMPLETE\nthe csv has the required columns").complete is True
    assert tv._parse("VERDICT: INCOMPLETE\nthe file is a stub").complete is False


def test_parse_uninterpretable_defers_not_accepts() -> None:
    """An unparseable / empty response must DEFER (None), never silently accept."""
    assert tv._parse("").complete is None
    assert tv._parse("I think it's probably fine").complete is None


def test_gather_evidence_reads_referenced_artifacts(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "results.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    ev = tv.gather_evidence(tmp_path, "T012 Produce data/results.csv with columns a,b")
    assert "data/results.csv" in ev and "a,b" in ev


def test_gather_evidence_flags_missing_artifact(tmp_path: Path) -> None:
    ev = tv.gather_evidence(tmp_path, "T013 Write data/missing.json")
    assert "data/missing.json" in ev and "MISSING" in ev


def test_verify_task_defers_on_backend_failure(monkeypatch) -> None:
    """A transient backend outage DEFERS (complete=None) — an unverifiable task is
    never accepted as done (fail-closed, unlike the relevance judge's fail-open)."""
    def _boom(*a, **k):
        raise RuntimeError("backend down")

    monkeypatch.setattr(tv, "chat_with_fallback", _boom)
    v = tv.verify_task(task_text="T1 do thing", evidence="- `data/x.csv`: MISSING")
    assert v.complete is None and v.deferred


def test_verify_task_accepts_on_complete(monkeypatch) -> None:
    from types import SimpleNamespace

    monkeypatch.setattr(
        tv, "chat_with_fallback",
        lambda *a, **k: SimpleNamespace(text="VERDICT: COMPLETE\nartifact present and correct", model="m"),
    )
    v = tv.verify_task(task_text="T1 produce data/x.csv", evidence="- `data/x.csv` (10 bytes)")
    assert v.complete is True


def test_verify_task_rejects_on_incomplete(monkeypatch) -> None:
    from types import SimpleNamespace

    monkeypatch.setattr(
        tv, "chat_with_fallback",
        lambda *a, **k: SimpleNamespace(text="VERDICT: INCOMPLETE\nthe csv is empty", model="m"),
    )
    v = tv.verify_task(task_text="T1 produce data/x.csv", evidence="- `data/x.csv`: MISSING")
    assert v.complete is False and "empty" in v.reason
