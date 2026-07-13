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


# --- Task identity must survive claim-marker churn (the in_progress doom loop) ---
#
# The claims layer RE-ANNOTATES artifacts (tasks.md included) on every tick, stamping
# ``[UNRESOLVED-CLAIM: <fresh-id> — …]`` markers whose ids are regenerated each pass.
# When a task's identity was its full line TEXT, that rewrite minted a NEW key every
# tick, so (a) the ``already_verified`` snapshot no longer matched a settled ``[X]``
# task — it was re-judged as "newly claimed" and could be un-checked back to ``[ ]``,
# and (b) ``reject_counts`` never accumulated, so REJECT_CAP never fired. Result: an
# unbreakable redo loop — every one of the 433 in_progress projects drifted BACKWARD
# (PROJ-492: done 64 -> 55 over 24h) and none ever reached research_complete.
# Identity is therefore the STABLE task id (T009 / PT005C), never the mutable line.

_CHURN_A = "T009 Set up logging in `src/utils/logger.py` (verify codes)."
_CHURN_B = (
    "T009 Set up logging in `src/utils/logger.py` "
    "(verify codes [UNRESOLVED-CLAIM: c_c3bf9b30 — status=not_enough_info])."
)


def test_task_key_is_stable_under_claim_marker_churn() -> None:
    """The same task, re-annotated with a fresh claim id, keeps ONE identity."""
    assert tv._task_key(_CHURN_A) == tv._task_key(_CHURN_B)


def test_task_key_distinguishes_distinct_ids() -> None:
    """Aliased-but-distinct tasks (T005C vs PT005C) must NOT collapse together."""
    assert tv._task_key("T005C **[P]** Implement checker") != tv._task_key(
        "PT005C **[P]** Implement checker"
    )


def test_settled_task_not_rejudged_after_reannotation(tmp_path: Path, monkeypatch) -> None:
    """A verifier-accepted ``[X]`` task that the claims layer then re-annotates must
    stay ``[X]``: it is settled work and must never be re-judged (nor un-checked)."""
    tasks = tmp_path / "tasks.md"
    tasks.write_text(f"# Tasks\n\n- [X] {_CHURN_A}\n", encoding="utf-8")
    snapshot = tv.claimed_done_keys(tasks.read_text(encoding="utf-8"))

    # Claims layer rewrites the line with a fresh marker (identity must not change).
    tasks.write_text(f"# Tasks\n\n- [X] {_CHURN_B}\n", encoding="utf-8")

    def _never(*a, **k):  # the verifier must not spend a call on settled work
        raise AssertionError("settled task was re-judged")

    monkeypatch.setattr(tv, "verify_task", _never)
    result = tv.run_verification_pass(
        tmp_path, tasks, already_verified=snapshot,
        notes_path=tmp_path / "notes.md", state_path=tmp_path / "state.yaml",
    )
    assert result["accepted"] == 0 and not result["rejected"] and not result["deferred"]
    assert "- [X] " in tasks.read_text(encoding="utf-8")


def test_reject_counts_accumulate_across_reannotation(tmp_path: Path, monkeypatch) -> None:
    """Repeated rejection of the SAME task must reach REJECT_CAP even though the claims
    layer rewrites its line between ticks — otherwise the redo loop never breaks."""
    from types import SimpleNamespace

    monkeypatch.setattr(
        tv, "verify_task",
        lambda **k: SimpleNamespace(complete=False, reason="stub only", deferred=False),
    )
    tasks = tmp_path / "tasks.md"
    state = tmp_path / "state.yaml"
    marks = []
    for tick in range(tv.REJECT_CAP):
        # Each tick the claims layer stamps a DIFFERENT fresh claim id.
        line = (
            f"T009 Set up logging in `src/utils/logger.py` "
            f"(verify codes [UNRESOLVED-CLAIM: c_tick{tick} — status=not_enough_info])."
        )
        tasks.write_text(f"# Tasks\n\n- [X] {line}\n", encoding="utf-8")
        tv.run_verification_pass(
            tmp_path, tasks, already_verified=set(),  # re-claimed by the implementer
            notes_path=tmp_path / "notes.md", state_path=state,
        )
        marks.append(tasks.read_text(encoding="utf-8").split("\n")[2][:6])

    # Rejected the first REJECT_CAP-1 ticks, then ACCEPTED (loop-breaker fires).
    assert marks[:-1] == ["- [ ] "] * (tv.REJECT_CAP - 1), marks
    assert marks[-1] == "- [X] ", marks
