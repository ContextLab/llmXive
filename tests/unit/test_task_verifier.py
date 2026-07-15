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


def test_duplicate_task_ids_get_distinct_keys() -> None:
    """18% of live projects (78/433, 240 lines) carry DUPLICATE task ids — two
    different tasks both numbered T001, from merged task lists. Keying on the bare
    id would collapse them: the second would inherit the first's ``[X]`` snapshot
    entry and silently ESCAPE independent verification, and their reject counts
    would share a counter (firing REJECT_CAP early). Disambiguate by occurrence."""
    text = (
        "- [X] T001 Set up GitHub Actions workflow\n"
        "- [X] T001 Create repository skeleton with src/\n"
        "- [ ] T002 Something else\n"
    )
    keys = tv.task_keys(text)
    assert len(set(keys.values())) == 3, keys
    # ...and the numbering is positional, so it survives claim-marker churn.
    churned = text.replace(
        "Set up GitHub Actions workflow",
        "Set up GitHub Actions workflow [UNRESOLVED-CLAIM: c_9f21 — status=x]",
    )
    assert list(tv.task_keys(churned).values()) == list(keys.values())


def test_second_duplicate_id_is_still_verified(tmp_path: Path, monkeypatch) -> None:
    """A newly-claimed task must be judged even when an EARLIER task shares its id."""
    tasks = tmp_path / "tasks.md"
    tasks.write_text("# T\n\n- [X] T001 first task\n", encoding="utf-8")
    snapshot = tv.claimed_done_keys(tasks.read_text(encoding="utf-8"))
    # The implementer now claims a SECOND, different task that reuses id T001.
    tasks.write_text(
        "# T\n\n- [X] T001 first task\n- [X] T001 a different second task\n",
        encoding="utf-8",
    )
    judged: list[str] = []

    def _spy(**kw):
        from types import SimpleNamespace

        judged.append(kw["task_text"])
        return SimpleNamespace(complete=True, reason="ok", deferred=False)

    monkeypatch.setattr(tv, "verify_task", _spy)
    tv.run_verification_pass(
        tmp_path, tasks, already_verified=snapshot,
        notes_path=tmp_path / "n.md", state_path=tmp_path / "s.yaml",
    )
    assert len(judged) == 1 and "different second task" in judged[0], judged


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


def test_reject_cap_records_unverifiable_never_accepts(tmp_path: Path, monkeypatch) -> None:
    """REJECT_CAP consecutive INCOMPLETE verdicts must NEVER force-accept the task
    (the fail-open removed in issue #1139). Instead, after the cap the task is
    reopened ``[ ]`` AND recorded in :mod:`llmxive.state.unverifiable` — which both
    breaks the redo loop (a recorded task is not re-judged) and signals CORE to
    route the project to research_full_revision. Reject counts still accumulate
    across the claims layer's per-tick re-annotation of the line."""
    from types import SimpleNamespace

    from llmxive.state import unverifiable

    monkeypatch.setattr(
        tv, "verify_task",
        lambda **k: SimpleNamespace(complete=False, reason="stub only", deferred=False),
    )
    tasks = tmp_path / "tasks.md"
    state = tmp_path / "state.yaml"
    marks = []
    result: dict = {}
    for tick in range(tv.REJECT_CAP):
        # Each tick the claims layer stamps a DIFFERENT fresh claim id. The task has
        # NO artifact path, so it routes to the (forced-INCOMPLETE) semantic verifier.
        line = (
            f"T009 wire up the pipeline module "
            f"(verify codes [UNRESOLVED-CLAIM: c_tick{tick} — status=not_enough_info])."
        )
        tasks.write_text(f"# Tasks\n\n- [X] {line}\n", encoding="utf-8")
        result = tv.run_verification_pass(
            tmp_path, tasks, already_verified=set(),  # re-claimed by the implementer
            notes_path=tmp_path / "notes.md", state_path=state,
            project_id="PROJ-CAP", repo_root=tmp_path,
        )
        marks.append(tasks.read_text(encoding="utf-8").split("\n")[2][:6])

    # NEVER accepted — reopened [ ] every tick, and [X] appears at NO point.
    assert marks == ["- [ ] "] * tv.REJECT_CAP, marks
    assert "- [X]" not in tasks.read_text(encoding="utf-8")
    # The final tick recorded the task as unverifiable and flagged it in the result.
    assert result["unverifiable"] == ["T009"], result
    recorded = unverifiable.load("PROJ-CAP", repo_root=tmp_path)
    assert [t["task_key"] for t in recorded] == ["T009"], recorded
    assert unverifiable.has_unverifiable("PROJ-CAP", repo_root=tmp_path)
