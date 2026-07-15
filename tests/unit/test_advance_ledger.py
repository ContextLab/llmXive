"""Typed advancement-failure ledger (issue #1139, defect D5).

Real files, real functions — no mocks (Constitution III). Exercises the shared
:mod:`llmxive.pipeline.advance_ledger` module both ``cli.py`` and the scheduler
route through: the 9-fingerprint classifier, exponential-backoff dispositions,
and the record read/write/clear lifecycle against tmp files.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from llmxive.pipeline import advance_ledger as al
from llmxive.types import Project, Stage

# One representative real message per fingerprint (verbatim shapes from the recon
# / the live state/advance_errors/*.json records) → expected (fingerprint, class).
_CASES: list[tuple[str, str, al.ErrorClass]] = [
    (
        "research.md reference is unreachable: 'https://trec.nist.gov/data/robust/04/' "
        "(HTTP 404). FR-006 admits NO transient-retry leniency",
        al.FP_UNREACHABLE_REFERENCE,
        al.ErrorClass.PERMANENT,
    ),
    (
        "speckit refused to emit a 'template' artifact at /x/tasks.md.\n  Rules fired: "
        "unfilled_bracket_density=31 bracket markers; sample=['[User Story 1]']",
        al.FP_TEMPLATE_REJECTION,
        al.ErrorClass.PERMANENT,
    ),
    (
        "every backend in chain ['dartmouth', 'local'] failed; errors: "
        "dartmouth(outage): every model in chain ['qwen.qwen3.5-122b'] failed on "
        "backend 'dartmouth'",  # nests "every model in chain" -> ordering matters
        al.FP_BACKEND_CHAIN_FAILED,
        al.ErrorClass.TRANSIENT,
    ),
    (
        "invalid transition paper_analyzed -> paper_planned",
        al.FP_INVALID_TRANSITION,
        al.ErrorClass.INVARIANT,
    ),
    (
        "[Errno 17] File exists: '/home/runner/work/llmXive/llmXive/projects/"
        "PROJ-770-x/code'",
        al.FP_FILESYSTEM_FILE_EXISTS,
        al.ErrorClass.DETERMINISTIC_REPAIR,
    ),
    (
        "every model in chain ['qwen.qwen3.5-122b', 'google.gemma-3-27b-it'] failed "
        "on backend 'dartmouth'",
        al.FP_MODEL_CHAIN_FAILED,
        al.ErrorClass.TRANSIENT,
    ),
    (
        "Clarifier left 3 of 3 markers unresolved (attempt 1/5); will not advance.",
        al.FP_UNRESOLVED_MARKERS,
        al.ErrorClass.EMITTER_CONTEXT,
    ),
    (
        "PROJ-654: no paper/source/*.tex draft to seed from — the ingested paper "
        "LaTeX is missing",
        al.FP_NO_SEED_DRAFT,
        al.ErrorClass.EMITTER_CONTEXT,
    ),
    (
        "Tasker produced only 0 task IDs (need >= 5; total chars: 11382). "
        "Re-running on next cycle.",
        al.FP_TASKER_ZERO_TASKS,
        al.ErrorClass.EMITTER_CONTEXT,
    ),
]


def _proj(pid: str, stage: Stage = Stage.PROJECT_INITIALIZED) -> Project:
    now = datetime.now(UTC)
    return Project(
        id=pid, title=pid, field="test", current_stage=stage,
        created_at=now, updated_at=now,
    )


@pytest.mark.parametrize("message,fingerprint,klass", _CASES)
def test_classifier_maps_each_fingerprint_to_correct_class(
    message: str, fingerprint: str, klass: al.ErrorClass
) -> None:
    fp, cls = al.classify_message(message)
    assert fp == fingerprint
    assert cls == klass
    # classify(exc) delegates to classify_message and must agree.
    assert al.classify(RuntimeError(message)) == (fingerprint, klass)


def test_backend_chain_wins_over_nested_model_chain() -> None:
    # The outer backend-chain failure embeds a "every model in chain" substring;
    # it must classify as backend_chain (transient), not model_chain.
    msg = ("every backend in chain ['dartmouth', 'local'] failed; errors: "
           "dartmouth: every model in chain ['x'] failed on backend 'dartmouth'")
    assert al.classify_message(msg)[0] == al.FP_BACKEND_CHAIN_FAILED


def test_unknown_message_defaults_to_transient() -> None:
    fp, cls = al.classify_message("something totally unrecognized happened")
    assert fp == al.FP_UNKNOWN
    assert cls == al.ErrorClass.TRANSIENT  # safe default: backoff, not abandon


def test_backoff_monotonic_and_capped() -> None:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    delays = [
        (al.compute_retry_after(base, n) - base).total_seconds()
        for n in range(0, al.BACKOFF_CAP + 3)
    ]
    # Strictly increasing up to the cap...
    for i in range(al.BACKOFF_CAP):
        assert delays[i] < delays[i + 1], (i, delays)
    # ...then saturated (count beyond the cap does not grow the window).
    capped = al.BASE_BACKOFF_SECONDS * (2 ** al.BACKOFF_CAP)
    assert delays[al.BACKOFF_CAP] == capped
    assert delays[al.BACKOFF_CAP + 1] == capped
    assert delays[al.BACKOFF_CAP + 2] == capped
    # Non-decreasing overall.
    assert delays == sorted(delays)


def test_transient_disposition_sets_future_retry_after() -> None:
    ls = datetime(2026, 1, 1, tzinfo=UTC)
    status, retry_after = al.disposition(
        al.ErrorClass.TRANSIENT, last_seen=ls, consecutive_count=1
    )
    assert status == al.LedgerStatus.RETRY_SCHEDULED
    assert retry_after is not None and retry_after > ls


def test_deterministic_repair_also_backs_off() -> None:
    ls = datetime(2026, 1, 1, tzinfo=UTC)
    status, retry_after = al.disposition(
        al.ErrorClass.DETERMINISTIC_REPAIR, last_seen=ls, consecutive_count=2
    )
    assert status == al.LedgerStatus.RETRY_SCHEDULED
    assert retry_after is not None and retry_after > ls  # spaced, not every-tick


def test_invariant_sets_no_retry_after() -> None:
    status, retry_after = al.disposition(
        al.ErrorClass.INVARIANT, last_seen=datetime.now(UTC), consecutive_count=5
    )
    assert status == al.LedgerStatus.TERMINAL
    assert retry_after is None  # never consumes retry budget


@pytest.mark.parametrize(
    "klass", [al.ErrorClass.PERMANENT, al.ErrorClass.EMITTER_CONTEXT]
)
def test_permanent_and_emitter_reroute_without_retry_after(klass) -> None:
    status, retry_after = al.disposition(
        klass, last_seen=datetime.now(UTC), consecutive_count=3
    )
    assert status == al.LedgerStatus.REROUTED
    assert retry_after is None  # do NOT re-dispatch unchanged


def test_record_failure_increments_consecutive_count(tmp_path) -> None:
    p = _proj("PROJ-701-x", Stage.PROJECT_INITIALIZED)
    msg = "every backend in chain ['dartmouth', 'local'] failed"
    r1 = al.record_failure(p, RuntimeError(msg), repo_root=tmp_path)
    r2 = al.record_failure(p, RuntimeError(msg), repo_root=tmp_path)
    assert r1["consecutive_count"] == 1
    assert r2["consecutive_count"] == 2
    assert r2["first_seen"] == r1["first_seen"]  # streak start preserved
    assert r2["class"] == al.ErrorClass.TRANSIENT.value
    assert r2["fingerprint"] == al.FP_BACKEND_CHAIN_FAILED
    assert r2["status"] == al.LedgerStatus.RETRY_SCHEDULED.value
    assert r2["stage"] == "project_initialized"
    # On-disk record matches the returned record.
    assert al.load_record("PROJ-701-x", repo_root=tmp_path) == r2


def test_invalid_transition_record_is_terminal_no_retry(tmp_path) -> None:
    p = _proj("PROJ-702-x", Stage.PROJECT_INITIALIZED)
    rec = al.record_failure(
        p, RuntimeError("invalid transition in_progress -> clarified"),
        repo_root=tmp_path,
    )
    assert rec["class"] == al.ErrorClass.INVARIANT.value
    assert rec["status"] == al.LedgerStatus.TERMINAL.value
    assert rec["retry_after"] is None


def test_clear_resets_consecutive_count(tmp_path) -> None:
    p = _proj("PROJ-703-x", Stage.PROJECT_INITIALIZED)
    msg = "every backend in chain ['dartmouth', 'local'] failed"
    al.record_failure(p, RuntimeError(msg), repo_root=tmp_path)
    al.record_failure(p, RuntimeError(msg), repo_root=tmp_path)
    assert al.load_record("PROJ-703-x", repo_root=tmp_path)["consecutive_count"] == 2

    assert al.clear(p, repo_root=tmp_path) is True
    cleared = al.load_record("PROJ-703-x", repo_root=tmp_path)
    assert cleared["status"] == al.LedgerStatus.CLEARED.value
    assert cleared["consecutive_count"] == 0
    assert cleared["retry_after"] is None

    # A subsequent failure restarts the CONSECUTIVE streak at 1.
    r = al.record_failure(p, RuntimeError(msg), repo_root=tmp_path)
    assert r["consecutive_count"] == 1


def test_clear_is_noop_without_a_record(tmp_path) -> None:
    p = _proj("PROJ-704-x")
    assert al.clear(p, repo_root=tmp_path) is False


def test_is_schedulable_backoff_gate() -> None:
    now = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    future = {
        "status": al.LedgerStatus.RETRY_SCHEDULED.value,
        "retry_after": (now + timedelta(hours=1)).isoformat(),
    }
    past = {
        "status": al.LedgerStatus.RETRY_SCHEDULED.value,
        "retry_after": (now - timedelta(hours=1)).isoformat(),
    }
    assert al.is_schedulable(None, now=now) is True
    assert al.is_schedulable({"status": "cleared"}, now=now) is True
    assert al.is_schedulable(future, now=now) is False  # inside backoff window
    assert al.is_schedulable(past, now=now) is True  # backoff elapsed
    # Hold statuses are never schedulable, regardless of any retry_after.
    assert al.is_schedulable({"status": "rerouted", "retry_after": None}, now=now) is False
    assert al.is_schedulable(
        {"status": "terminal", "retry_after": (now - timedelta(days=9)).isoformat()},
        now=now,
    ) is False  # a past retry_after does NOT resurrect a terminal record
