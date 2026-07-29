"""EventStoreRouteAudit + unknown-dispatch reconciliation (spec 025 slice 1A, T10-T12).

The sink is exercised through the real slice-0 dataclasses and the real ``emit_audit``
path, because the contract that matters is the one ``execute`` depends on: durable before
return, idempotent on a byte-identical replay, fatal on a conflicting payload.
"""

from __future__ import annotations

import subprocess
import threading
from datetime import UTC, datetime

import pytest

from llmxive.model_selection.attempt_hooks import (
    CandidateOutcome,
    ChainResolved,
    DispatchCompleted,
    DispatchStarted,
    DispatchUnknown,
    RouteAuditError,
    SelectionFailure,
    emit_audit,
)
from llmxive.model_selection.types import ModelRef, SnapshotProvenance
from llmxive.self_improvement.audit_sink import (
    RECONCILE_SAFETY_FACTOR,
    EventStoreRouteAudit,
    dangling_dispatches,
    reconcile_timeout_s,
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
#: A REAL datetime, as `snapshot.py` builds. See test_record_projects_nested_audit_types.
OBSERVED = datetime(2026, 7, 24, tzinfo=UTC)
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
    # `observed_at` is a REAL datetime here, which is what `snapshot.py` actually
    # constructs. It used to be the string TS, and that is why this test passed while a
    # real ChainResolved could not be written at all: `SnapshotProvenance`'s projection
    # hand-built its dict instead of recursing, so the datetime slipped past `_jsonable`'s
    # unknown-type guard and only exploded downstream at `json.dumps` — a TypeError
    # nothing normalizes into a RouteAuditError. The dataclass is not runtime-typed, so
    # feeding it a str made a whole class of failure invisible.
    sink = _sink(repo)
    sink.record(ChainResolved(
        route_id="r-1", requirement_digest="d1", prompt_digest="d2", context_digest="d3",
        snapshot_digest="d4",
        snapshot_provenance={"catalog": SnapshotProvenance(source="live", observed_at=OBSERVED,
                                                           age_s=0.0)},
        selection_policy_version=1, resolved_at=TS, explanation=("because",),
        candidates=(CANDIDATE,),
    ))
    payload = read(repo, "P1")[0].payload
    assert payload["candidates"] == [{"backend": "dartmouth", "serving_endpoint": "chat",
                                      "model_id": "m1", "model_family": "f", "vendor": "v"}]
    assert payload["snapshot_provenance"] == {
        "catalog": {"source": "live", "observed_at": OBSERVED.isoformat(), "age_s": 0.0}
    }
    assert payload["explanation"] == ["because"]
    # ISO-8601, so the recorded instant round-trips rather than freezing as a repr.
    assert datetime.fromisoformat(
        payload["snapshot_provenance"]["catalog"]["observed_at"]
    ) == OBSERVED


def test_a_selection_failures_real_provenance_is_writable(repo):
    # The OTHER event carrying snapshot_provenance. `build_invocation_identity` (Task 6)
    # joins a reroute to this record for FR-002's primary_failure, so if it cannot be
    # written, the degradation path has no provenance to join to.
    sink = _sink(repo)
    sink.record(SelectionFailure(
        route_id="r-1", exception_type="ModelUnavailable", message="none live",
        requirement_digest="rq-1",
        snapshot_provenance={"catalog": SnapshotProvenance(source="last_known_good",
                                                           observed_at=OBSERVED, age_s=42.5)},
    ))
    payload = read(repo, "P1")[0].payload
    assert payload["snapshot_provenance"]["catalog"] == {
        "source": "last_known_good", "observed_at": OBSERVED.isoformat(), "age_s": 42.5
    }


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


# ---- terminal disposition is exclusive ----


def _terminals(repo, config=None):
    return sorted(e.event_type for e in read(repo, "P1", config=config)
                  if e.event_type in ("DispatchCompleted", "DispatchUnknown"))


def test_a_completion_after_an_unknown_is_refused(repo):
    # The reverse race. Recording a completion over a dispatch already marked unknown would
    # leave two contradictory final dispositions for one dispatch.
    sink = _sink(repo)
    sink.record(_started())
    sink.record(DispatchUnknown(route_id="r-1", candidate_index=0, candidate=CANDIDATE,
                                reservation_id="res-1"))
    with pytest.raises(RouteAuditError):
        emit_audit(sink, DispatchCompleted(route_id="r-1", candidate_index=0,
                                           candidate=CANDIDATE, reservation_id="res-1"))
    assert _terminals(repo) == ["DispatchUnknown"]


def test_an_unknown_after_a_completion_is_refused(repo):
    sink = _sink(repo)
    sink.record(_started())
    sink.record(DispatchCompleted(route_id="r-1", candidate_index=0, candidate=CANDIDATE,
                                  reservation_id="res-1"))
    with pytest.raises(RouteAuditError):
        emit_audit(sink, DispatchUnknown(route_id="r-1", candidate_index=0,
                                         candidate=CANDIDATE, reservation_id="res-1"))
    assert _terminals(repo) == ["DispatchCompleted"]


def test_a_terminal_outcome_blocks_a_later_unknown(repo):
    sink = _sink(repo)
    sink.record(_started())
    sink.record(CandidateOutcome(route_id="r-1", candidate_index=0, candidate=CANDIDATE,
                                 outcome="advance", reason="fell through"))
    with pytest.raises(RouteAuditError):
        emit_audit(sink, DispatchUnknown(route_id="r-1", candidate_index=0,
                                         candidate=CANDIDATE, reservation_id="res-1"))


def test_a_byte_identical_terminal_replay_is_still_idempotent(repo):
    # The precondition must not refuse a record its OWN committed copy already satisfies.
    sink = _sink(repo)
    sink.record(_started())
    done = DispatchCompleted(route_id="r-1", candidate_index=0, candidate=CANDIDATE,
                             reservation_id="res-1")
    sink.record(done)
    _sink(repo, clock=lambda: LATER).record(done)  # replay from a later clock
    assert _terminals(repo) == ["DispatchCompleted"]


def test_a_terminal_record_does_not_block_a_different_candidate(repo):
    sink = _sink(repo)
    sink.record(_started(index=0))
    sink.record(_started(index=1))
    sink.record(DispatchCompleted(route_id="r-1", candidate_index=0, candidate=CANDIDATE,
                                  reservation_id="res-1"))
    sink.record(DispatchUnknown(route_id="r-1", candidate_index=1, candidate=CANDIDATE,
                                reservation_id="res-1"))
    assert _terminals(repo) == ["DispatchCompleted", "DispatchUnknown"]


def test_completion_and_reconciliation_racing_from_one_parent_yield_one_disposition(tmp_path):
    # THE race: both workers sync to the same parent, then one records a completion while
    # the other reconciles the same dispatch as unknown. Exactly one may become
    # authoritative — a dispatch cannot be both completed and unknown.
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
    _sink(clones[0], config=cfg).record(_started())

    barrier = threading.Barrier(2, timeout=30)
    outcomes, lock = [], threading.Lock()

    def _complete():
        barrier.wait()
        try:
            _sink(clones[0], clock=lambda: LATER, config=cfg).record(
                DispatchCompleted(route_id="r-1", candidate_index=0, candidate=CANDIDATE,
                                  reservation_id="res-1"))
            with lock:
                outcomes.append("completed")
        except Exception:
            with lock:
                outcomes.append("completion-refused")

    def _reconcile():
        barrier.wait()
        moved = reconcile_unknown(clones[1], problem_id="P1", attempt_id="A1", actor="exec",
                                  clock=lambda: LATER, now=LATER, timeout_s=60.0, config=cfg)
        with lock:
            outcomes.append("marked-unknown" if moved else "reconcile-skipped")

    ts = [threading.Thread(target=_complete), threading.Thread(target=_reconcile)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout=60)

    terminals = _terminals(clones[0], cfg)
    assert len(terminals) == 1, f"contradictory terminal history {terminals} from {outcomes}"
    # and the loser reported losing rather than claiming success
    assert ("completed" in outcomes) != ("marked-unknown" in outcomes), outcomes


# ---- resolution is scoped to the requested Attempt ----


def test_another_attempts_completion_does_not_resolve_this_attempts_dispatch(repo):
    # Route ids are caller-supplied at this layer, so an identically keyed dispatch under
    # A2 must not suppress reconciliation of A1's dangling one.
    _record_started(repo, attempt="A1")
    _sink(repo, attempt="A2").record(
        DispatchCompleted(route_id="r-1", candidate_index=0, candidate=CANDIDATE,
                          reservation_id="res-1"))
    dangling = dangling_dispatches(read(repo, "P1"), attempt_id="A1", now=LATER, timeout_s=60.0)
    assert [d["route_id"] for d in dangling] == ["r-1"]


def test_this_attempts_completion_does_not_resolve_another_attempts_dispatch(repo):
    _record_started(repo, attempt="A2")
    _sink(repo, attempt="A1").record(
        DispatchCompleted(route_id="r-1", candidate_index=0, candidate=CANDIDATE,
                          reservation_id="res-1"))
    dangling = dangling_dispatches(read(repo, "P1"), attempt_id="A2", now=LATER, timeout_s=60.0)
    assert [d["route_id"] for d in dangling] == ["r-1"]


def test_two_attempts_can_record_the_same_route_key(repo):
    # The slice-0 event_id is `route_id:candidate_index:kind` with no Attempt in it, so the
    # lane id has to add one. Without that, A2's record derives A1's lane id with a
    # different payload and dies on the append-only guard — the Attempt-scoped contract
    # would be unenforceable at the storage layer, not merely unenforced in the queries.
    _sink(repo, attempt="A1").record(_started(reservation="res-a1"))
    _sink(repo, attempt="A2").record(_started(reservation="res-a2"))
    started = [e for e in read(repo, "P1") if e.event_type == "DispatchStarted"]
    assert sorted(e.attempt_id for e in started) == ["A1", "A2"]


def test_claim_dispatch_is_scoped_to_its_attempt(repo):
    # A different Attempt IS a different dispatch, so it gets its own claim; a replay within
    # one Attempt still refuses.
    assert _sink(repo, attempt="A1").claim_dispatch(_started()) is True
    assert _sink(repo, attempt="A2").claim_dispatch(_started()) is True
    assert _sink(repo, attempt="A1").claim_dispatch(_started()) is False


def test_an_identically_keyed_dispatch_in_another_attempt_can_also_be_marked(repo):
    # Two Attempts, same caller-supplied route key: each owns its own terminal disposition,
    # so marking one must not block the other.
    _record_started(repo, attempt="A1")
    _record_started(repo, attempt="A2")
    args = dict(problem_id="P1", actor="exec", clock=lambda: LATER, now=LATER, timeout_s=60.0)
    assert reconcile_unknown(repo, attempt_id="A1", **args) == ["r-1"]
    assert reconcile_unknown(repo, attempt_id="A2", **args) == ["r-1"]
    assert _terminals(repo) == ["DispatchUnknown", "DispatchUnknown"]


# ---- the timeout must be able to bound something ----


@pytest.mark.parametrize("bad", [0, -1.0, float("nan"), float("inf"), True, "60"])
def test_a_timeout_that_cannot_bound_anything_is_refused(repo, bad):
    # Zero or negative marks a still-running dispatch unknown the instant it starts — the
    # opposite of the conservative guarantee the API promises.
    _record_started(repo)
    with pytest.raises(ValueError, match="timeout_s"):
        dangling_dispatches(read(repo, "P1"), attempt_id="A1", now=LATER, timeout_s=bad)
    with pytest.raises(ValueError, match="timeout_s"):
        reconcile_unknown(repo, problem_id="P1", attempt_id="A1", actor="exec",
                          clock=lambda: LATER, now=LATER, timeout_s=bad)


def test_the_derived_timeout_covers_the_whole_retry_envelope():
    # deadline * (retries + 1) * margin — the derivation is the reviewed one, so a caller
    # cannot arrive at a plausible-looking number by another route.
    assert reconcile_timeout_s(deadline_s=30.0, retries=3) == 30.0 * 4 * RECONCILE_SAFETY_FACTOR
    assert reconcile_timeout_s(deadline_s=30.0, retries=0) == 30.0 * 1 * RECONCILE_SAFETY_FACTOR
    # strictly longer than the worst case it must not preempt
    assert reconcile_timeout_s(deadline_s=30.0, retries=3) > 30.0 * 4


def test_an_unbounded_call_cannot_yield_a_conservative_timeout():
    # deadline_s=None is route_chat's DEFAULT, so this is the common case, not a corner:
    # with no worst case there is no timeout that proves the dispatch could not still be
    # running, and inventing one would only look conservative.
    with pytest.raises(ValueError, match="unbounded"):
        reconcile_timeout_s(deadline_s=None, retries=3)


@pytest.mark.parametrize("deadline, retries", [
    (0.0, 3), (-1.0, 3), (float("inf"), 3), (float("nan"), 3), (True, 3),
    (30.0, -1), (30.0, True), (30.0, 1.5),
])
def test_a_malformed_envelope_is_refused(deadline, retries):
    with pytest.raises(ValueError):
        reconcile_timeout_s(deadline_s=deadline, retries=retries)


def test_a_naive_now_is_refused(repo):
    # Comparing a naive timestamp against tz-aware history would either raise deep inside
    # the comparison or silently offset the cutoff.
    _record_started(repo)
    with pytest.raises(ValueError, match="timezone"):
        dangling_dispatches(read(repo, "P1"), attempt_id="A1", now="2026-07-24T01:00:00",
                            timeout_s=60.0)
