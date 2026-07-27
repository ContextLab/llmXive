"""EventStoreRouteAudit + unknown-dispatch reconciliation (spec 025 slice 1A, T10-T12).

The sink is exercised through the real slice-0 dataclasses and the real ``emit_audit``
path, because the contract that matters is the one ``execute`` depends on: durable before
return, idempotent on a byte-identical replay, fatal on a conflicting payload.
"""

from __future__ import annotations

import subprocess
import threading

import pytest

from llmxive.model_selection.attempt_hooks import (
    CandidateOutcome,
    ChainResolved,
    DispatchCompleted,
    DispatchStarted,
    DispatchUnknown,
    RouteAuditError,
    emit_audit,
)
from llmxive.model_selection.types import ModelRef, SnapshotProvenance
from llmxive.self_improvement.audit_sink import (
    EventStoreRouteAudit,
    dangling_dispatches,
    reconcile_unknown,
)
from llmxive.self_improvement.credit_ledger import (
    STATE_OPEN,
    STATE_RETAINED,
    AttemptCreditLedger,
    project_reservations,
)
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log, read

TS = "2026-07-24T00:00:00+00:00"
LATER = "2026-07-24T01:00:00+00:00"
CANDIDATE = ModelRef(backend="dartmouth", serving_endpoint="chat", model_id="m1",
                     model_family="f", vendor="v")


def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    bootstrap_lane_log(tmp_path, config=LaneLogConfig())
    return tmp_path


def _sink(repo, *, clock=lambda: TS, config=None, attempt="A1"):
    return EventStoreRouteAudit(repo=repo, problem_id="P1", attempt_id=attempt, actor="exec",
                                clock=clock, config=config)


def _started(route="r-1", index=0, reservation="res-1"):
    return DispatchStarted(route_id=route, candidate_index=index, candidate=CANDIDATE,
                           reservation_id=reservation)


# ---- T10: record ----


def test_record_persists_the_event_to_the_stream(repo):
    sink = _sink(repo)
    sink.record(_started())
    stored = read(repo, "P1")
    assert [e.event_type for e in stored] == ["DispatchStarted"]
    assert stored[0].payload["route_id"] == "r-1"
    assert stored[0].payload["candidate"]["model_id"] == "m1"
    assert stored[0].payload["audit_event_id"] == _started().event_id
    assert stored[0].attempt_id == "A1"


def test_record_projects_nested_audit_types(repo):
    sink = _sink(repo)
    sink.record(ChainResolved(
        route_id="r-1", requirement_digest="d1", prompt_digest="d2", context_digest="d3",
        snapshot_digest="d4",
        snapshot_provenance={"catalog": SnapshotProvenance(source="live", observed_at=TS,
                                                           age_s=0.0)},
        selection_policy_version=1, resolved_at=TS, explanation=("because",),
        candidates=(CANDIDATE,),
    ))
    payload = read(repo, "P1")[0].payload
    assert payload["candidates"] == [{"backend": "dartmouth", "serving_endpoint": "chat",
                                      "model_id": "m1", "model_family": "f", "vendor": "v"}]
    assert payload["snapshot_provenance"] == {
        "catalog": {"source": "live", "observed_at": TS, "age_s": 0.0}
    }
    assert payload["explanation"] == ["because"]


def test_record_is_idempotent_on_a_byte_identical_replay(repo):
    # The timestamp is NOT part of an event's identity, so a replay from a later clock is
    # still the same record — otherwise every retry would look like an integrity violation.
    _sink(repo, clock=lambda: TS).record(_started())
    _sink(repo, clock=lambda: LATER).record(_started())
    assert len(read(repo, "P1")) == 1


def test_a_conflicting_payload_under_the_same_audit_id_is_route_fatal(repo):
    # Same route + candidate index (so the same derived event_id) but a different
    # reservation — a conflicting dispatch masquerading as a replay.
    sink = _sink(repo)
    sink.record(_started(reservation="res-1"))
    with pytest.raises(RouteAuditError):
        emit_audit(sink, _started(reservation="res-2"))
    assert len(read(repo, "P1")) == 1


def test_an_unprojectable_field_is_refused_rather_than_stringified(repo):
    class Opaque:
        pass

    sink = _sink(repo)
    bad = DispatchStarted(route_id="r-1", candidate_index=0, candidate=CANDIDATE,
                          reservation_id=Opaque())
    with pytest.raises(RouteAuditError):
        emit_audit(sink, bad)
    assert read(repo, "P1") == []


# ---- T11: claim_dispatch ----


def test_the_first_claim_wins_and_a_replay_does_not(repo):
    sink = _sink(repo)
    assert sink.claim_dispatch(_started()) is True
    assert sink.claim_dispatch(_started()) is False  # replay: MUST NOT re-dispatch
    assert len(read(repo, "P1")) == 1


def test_a_conflicting_claim_raises_rather_than_reporting_a_replay(repo):
    sink = _sink(repo)
    sink.claim_dispatch(_started(reservation="res-1"))
    with pytest.raises(Exception, match="append-only"):
        sink.claim_dispatch(_started(reservation="res-2"))


def test_two_clones_claiming_one_dispatch_exactly_one_wins(tmp_path):
    # The guarantee is CROSS-PROCESS, so a shared in-memory lock cannot be what provides
    # it: two clones sync to the same parent and race the actual ref update.
    bare = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
    clones = []
    for name in ("c1", "c2"):
        dst = tmp_path / name
        subprocess.run(["git", "clone", "-q", str(bare), str(dst)], check=True)
        _git(dst, "config", "user.email", "t@t")
        _git(dst, "config", "user.name", "t")
        clones.append(dst)
    anchor = bootstrap_lane_log(clones[0], config=LaneLogConfig(remote="origin"))
    cfg = LaneLogConfig(remote="origin", expected_anchor=anchor)

    barrier = threading.Barrier(2, timeout=30)
    results, errors, lock = [], [], threading.Lock()

    def _worker(clone):
        try:
            sink = _sink(clone, config=cfg)
            barrier.wait()
            outcome = sink.claim_dispatch(_started())
            with lock:
                results.append(outcome)
        except BaseException as exc:
            with lock:
                errors.append(exc)

    ts = [threading.Thread(target=_worker, args=(c,)) for c in clones]
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout=60)

    assert not errors, f"claim raised: {errors}"
    assert sorted(results) == [False, True], f"both clones claimed the dispatch: {results}"
    assert len(read(clones[0], "P1", config=cfg)) == 1


# ---- T12: reconciliation ----


def _record_started(repo, *, clock=lambda: TS, reservation="res-1", route="r-1", index=0,
                    attempt="A1"):
    _sink(repo, clock=clock, attempt=attempt).record(_started(route, index, reservation))


def test_a_dangling_dispatch_is_marked_unknown_and_retains_its_reservation(repo):
    # ONE event does both jobs. Asserting BOTH from the single record is the point: there
    # is no crash window where a dispatch is unknown but its credits were released.
    led = AttemptCreditLedger(repo=repo, problem_id="P1", attempt_id="A1",
                              attempt_budget_credits=10.0, call_ceiling=56, actor="exec",
                              clock=lambda: TS)
    led.reserve(4.0, reservation_id="res-1", call_id="c1")
    _record_started(repo)
    before = len(read(repo, "P1"))

    assert reconcile_unknown(repo, problem_id="P1", attempt_id="A1", actor="exec",
                             clock=lambda: LATER, now=LATER, timeout_s=60.0) == ["r-1"]
    events = read(repo, "P1")
    assert "DispatchUnknown" in [e.event_type for e in events]
    assert project_reservations(events, "A1")["res-1"].state == STATE_RETAINED
    # ONE append produced both effects — no AttemptCreditRetained was written, so there is
    # no interleaving in which the dispatch is unknown but the credits were let go.
    assert len(events) == before + 1
    assert "AttemptCreditRetained" not in [e.event_type for e in events]


def test_a_dispatch_within_the_timeout_is_left_alone(repo):
    # The timeout is conservative BY DESIGN: a still-running valid call must never be
    # marked before it could possibly have finished.
    _record_started(repo)
    assert reconcile_unknown(repo, problem_id="P1", attempt_id="A1", actor="exec",
                             clock=lambda: LATER, now=LATER, timeout_s=7200.0) == []
    assert "DispatchUnknown" not in [e.event_type for e in read(repo, "P1")]


def test_a_completed_dispatch_is_not_unknown(repo):
    sink = _sink(repo)
    sink.record(_started())
    sink.record(DispatchCompleted(route_id="r-1", candidate_index=0, candidate=CANDIDATE,
                                  reservation_id="res-1"))
    assert dangling_dispatches(read(repo, "P1"), attempt_id="A1", now=LATER,
                               timeout_s=60.0) == []


@pytest.mark.parametrize("outcome", ["advance", "abort", "skip"])
def test_a_terminal_candidate_outcome_is_a_known_result_not_an_unknown_one(repo, outcome):
    # A FAILED candidate is a known outcome. Only the absence of any resolution is unknown.
    sink = _sink(repo)
    sink.record(_started())
    sink.record(CandidateOutcome(route_id="r-1", candidate_index=0, candidate=CANDIDATE,
                                 outcome=outcome, reason="because"))
    assert dangling_dispatches(read(repo, "P1"), attempt_id="A1", now=LATER,
                               timeout_s=60.0) == []


def test_an_already_marked_dispatch_is_not_marked_twice(repo):
    sink = _sink(repo)
    sink.record(_started())
    sink.record(DispatchUnknown(route_id="r-1", candidate_index=0, candidate=CANDIDATE,
                                reservation_id="res-1"))
    assert dangling_dispatches(read(repo, "P1"), attempt_id="A1", now=LATER,
                               timeout_s=60.0) == []


def test_reconciliation_is_idempotent_on_re_run(repo):
    _record_started(repo)
    args = dict(problem_id="P1", attempt_id="A1", actor="exec", clock=lambda: LATER,
                now=LATER, timeout_s=60.0)
    assert reconcile_unknown(repo, **args) == ["r-1"]
    assert reconcile_unknown(repo, **args) == []
    assert len([e for e in read(repo, "P1") if e.event_type == "DispatchUnknown"]) == 1


def test_another_attempts_dispatch_is_untouched(repo):
    _record_started(repo, attempt="A2")
    assert reconcile_unknown(repo, problem_id="P1", attempt_id="A1", actor="exec",
                             clock=lambda: LATER, now=LATER, timeout_s=60.0) == []


def test_a_free_candidates_dangling_dispatch_reconciles_without_a_reservation(repo):
    # A free candidate reserves nothing, so its unknown dispatch carries no reservation and
    # must still reconcile rather than crash on a missing id.
    _record_started(repo, reservation=None)
    assert reconcile_unknown(repo, problem_id="P1", attempt_id="A1", actor="exec",
                             clock=lambda: LATER, now=LATER, timeout_s=60.0) == ["r-1"]
    events = read(repo, "P1")
    assert project_reservations(events, "A1") == {}


def test_reconciliation_leaves_a_second_open_reservation_alone(repo):
    led = AttemptCreditLedger(repo=repo, problem_id="P1", attempt_id="A1",
                              attempt_budget_credits=20.0, call_ceiling=56, actor="exec",
                              clock=lambda: TS)
    led.reserve(4.0, reservation_id="res-1", call_id="c1")
    led.reserve(4.0, reservation_id="res-2", call_id="c2")
    _record_started(repo, reservation="res-1")

    reconcile_unknown(repo, problem_id="P1", attempt_id="A1", actor="exec",
                      clock=lambda: LATER, now=LATER, timeout_s=60.0)
    res = project_reservations(read(repo, "P1"), "A1")
    assert res["res-1"].state == STATE_RETAINED and res["res-2"].state == STATE_OPEN


def test_a_naive_now_is_refused(repo):
    # Comparing a naive timestamp against tz-aware history would either raise deep inside
    # the comparison or silently offset the cutoff.
    _record_started(repo)
    with pytest.raises(ValueError, match="timezone"):
        dangling_dispatches(read(repo, "P1"), attempt_id="A1", now="2026-07-24T01:00:00",
                            timeout_s=60.0)
