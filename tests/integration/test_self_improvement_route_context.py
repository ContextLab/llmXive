"""The lane route context (spec 025 slice 1B, Task 2).

Backed by the DURABLE call ledger, so these run against real git repos — an in-memory
counter is precisely what this design replaced. The audit/reservation doubles are real
objects implementing the protocols, not mocks.
"""

from __future__ import annotations

import subprocess
import sys
import threading

import pytest

from llmxive.model_selection.attempt_hooks import RouteAuditError
from llmxive.self_improvement.call_ledger import LaneCallCeilingExceeded, LaneCallLedger
from llmxive.self_improvement.events import derive_route_id
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log, read
from llmxive.self_improvement.route_context import (
    IMPL_REGEN_RETRIES,
    LaneRouteContext,
    attempt_call_ceiling,
    patch_call_ceiling,
    proposal_call_ceiling,
)

_BUDGET = 50.0  # ONE AttemptConfigured record binds this together with the call ceiling,
# so every ledger for this Attempt must present the SAME pair.


def _clock():
    return "2026-07-25T00:00:00+00:00"


class _Sink:
    """A real in-memory RouteAudit: records, and always claims."""

    def __init__(self):
        self.events = []

    def record(self, event) -> None:
        self.events.append(event)

    def claim_dispatch(self, event) -> bool:
        self.events.append(event)
        return True


class _Budget:
    """A real in-memory ReservationAuthority."""

    def reserve(self, credits, *, reservation_id, call_id) -> bool:
        return True

    def release(self, reservation_id) -> None:
        pass

    def mark_retained(self, reservation_id) -> None:
        pass


def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    bootstrap_lane_log(tmp_path, config=LaneLogConfig())
    return tmp_path


def _ledger(repo, ceiling=4):
    return LaneCallLedger(repo=repo, problem_id="P1", attempt_id="A1", call_ceiling=ceiling,
                          attempt_budget_credits=_BUDGET, actor="reviewer", clock=_clock,
                          config=LaneLogConfig())


def _ctx(repo, ceiling=4, *, config=None):
    return LaneRouteContext(
        repo=repo, problem_id="P1", attempt_id="A1", actor="reviewer", clock=_clock,
        route_audit=_Sink(), reservation_authority=_Budget(),
        call_ledger=_ledger(repo, ceiling), config=config,
    )


# ---- the ceiling arithmetic ----


def test_stage_components_match_the_spec_formulas():
    # Policy Contract line 313: proposal = 4N + R(2N + 2) (the reroute doubles every
    # reviewer term); patch = 2N + R(N + 2) (single-route, fail closed).
    assert proposal_call_ceiling(5, 3) == 56
    assert proposal_call_ceiling(1, 1) == 4 * 1 + 1 * (2 * 1 + 2) == 8
    assert patch_call_ceiling(5, 3) == 31
    assert patch_call_ceiling(1, 1) == 2 * 1 + 1 * (1 + 2) == 5


def test_the_attempt_ceiling_is_the_whole_line_313_expression():
    # This -- not a stage component -- is what AttemptConfigured binds.
    total = attempt_call_ceiling(proposal_panel=5, patch_panel=5, max_rounds=3)
    assert total == 1 + 2 + 56 + 31 == 90
    # and it is STRICTLY larger than any one stage: binding a component would both starve
    # the other stages and permanently lock out the real figure, since the record is
    # immutable for the Attempt.
    assert total > proposal_call_ceiling(5, 3) and total > patch_call_ceiling(5, 3)


def test_impl_regen_retries_moves_the_attempt_ceiling():
    assert IMPL_REGEN_RETRIES == 1  # Policy Contract line 312 (hard max 1)
    assert attempt_call_ceiling(proposal_panel=5, patch_panel=5, max_rounds=3,
                                impl_regen_retries=0) == 89


# ---- durable route admission ----


def test_each_operation_leg_gets_a_distinct_durable_route_id(repo):
    ctx = _ctx(repo, ceiling=3)
    a = ctx.claim_route(operation_id="lens-a")
    b = ctx.claim_route(operation_id="lens-b")
    c = ctx.claim_route(operation_id="lens-a", leg="fallback")
    assert len({a, b, c}) == 3 and ctx.calls_used() == 3


def test_a_replayed_operation_reuses_its_route_id_and_is_not_recharged(repo):
    # Retry-stability: a fresh context (a restart) claiming the SAME logical operation must
    # get the SAME route id back — that is what lets the dispatch gate recognize the retry
    # instead of dispatching twice.
    ctx = _ctx(repo, ceiling=3)
    first = ctx.claim_route(operation_id="lens-a")
    assert _ctx(repo, ceiling=3).claim_route(operation_id="lens-a") == first
    assert first == derive_route_id("A1", "lens-a", "primary")
    assert ctx.calls_used() == 1


def test_a_duplicate_worker_replays_instead_of_double_dispatching(repo):
    # This is the ONLY way a fresh process legitimately re-presents an existing attempt_id:
    # a crashed Attempt is a FAILED Attempt, and a retry gets a new attempt_id. The zombie
    # must land on the SAME route_id so the dispatch gate reports a replay.
    first = _ctx(repo, ceiling=5)
    rid = first.claim_route(operation_id=first.next_operation_id("lens-a:identify:deadbeef"))

    zombie = _ctx(repo, ceiling=5)  # a second process for the SAME attempt
    zid = zombie.claim_route(operation_id=zombie.next_operation_id("lens-a:identify:deadbeef"))

    assert zid == rid, "the duplicate worker minted a NEW route — it would dispatch twice"
    assert zombie.calls_used() == 1, "the replay consumed a second call from the ceiling"


def test_next_operation_id_separates_in_process_repeats_but_not_restarts(repo):
    # The engine re-invokes revise() with byte-identical arguments after a malformed reply;
    # that is a NEW logical call and must not replay the first claim.
    ctx = _ctx(repo, ceiling=5)
    a = ctx.next_operation_id("reviser:abc")
    b = ctx.next_operation_id("reviser:abc")
    assert a == "reviser:abc" and b == "reviser:abc#1" and a != b
    assert ctx.claim_route(operation_id=a) != ctx.claim_route(operation_id=b)
    assert ctx.calls_used() == 2
    # a RESTART starts the sequence over, so the bare base replays the original claim
    fresh = _ctx(repo, ceiling=5)
    assert fresh.next_operation_id("reviser:abc") == "reviser:abc"
    assert fresh.claim_route(operation_id="reviser:abc") == ctx.claim_route(operation_id=a)
    assert fresh.calls_used() == 2  # the replay charged nothing


def test_concurrent_repeats_of_one_base_all_get_distinct_ids(repo):
    """The context is SHARED across the panel's thread pool, so the uniqueness this method
    promises must not depend on callers happening to use different keys: two threads that
    read the same count would both return the bare base, and the second call would replay
    the first's claim and be refused at the dispatch gate.

    The switch interval is dropped to make the scheduler adversarial. At the default
    interval the read-modify-write never interleaves — an unlocked version passes this test
    100% of the time, which would make it worthless as a guard. At 1e-6 the unlocked
    version fails ~12% of ROUNDS, so 200 rounds detect it with probability ~1 - 1e-10.
    """
    ctx = _ctx(repo, ceiling=64)
    workers, rounds = 32, 200
    original_interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    try:
        for round_index in range(rounds):
            barrier = threading.Barrier(workers, timeout=30)
            ids, lock = [], threading.Lock()

            def _take(_barrier=barrier, _ids=ids, _lock=lock, _round=round_index):
                _barrier.wait()
                oid = ctx.next_operation_id(f"reviser:round-{_round}")
                with _lock:
                    _ids.append(oid)

            threads = [threading.Thread(target=_take) for _ in range(workers)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=60)

            assert len(ids) == workers
            assert len(set(ids)) == workers, (
                f"round {round_index}: duplicate operation ids under concurrency "
                f"({workers - len(set(ids))} collisions) — a replayed claim would be "
                f"refused at the dispatch gate"
            )
    finally:
        sys.setswitchinterval(original_interval)


def test_a_restarted_context_does_not_get_a_fresh_ceiling(repo):
    # An in-memory counter would let every new context spend anew.
    _ctx(repo, ceiling=2).claim_route(operation_id="a")
    _ctx(repo, ceiling=2).claim_route(operation_id="b")
    with pytest.raises(LaneCallCeilingExceeded):
        _ctx(repo, ceiling=2).claim_route(operation_id="c")


def test_hooks_are_required(repo):
    # A lane context CANNOT be built without the audit sink, the reservation authority, AND
    # the call ledger — no unaudited, unbudgeted, or unadmitted lane call.
    with pytest.raises(TypeError):
        LaneRouteContext(repo=repo, problem_id="P1", attempt_id="A1", actor="a", clock=_clock)


# ---- the explicit degradation record ----


def _reroute(ctx, operation_id="op-1", **kw):
    args = dict(
        operation_id=operation_id, lens="worthwhile-improvement",
        primary_route_id=derive_route_id("A1", operation_id, "primary"),
        fallback_route_id=derive_route_id("A1", operation_id, "fallback"),
        exception_type="ModelUnavailable", message="no independent family live",
    )
    args.update(kw)
    return ctx.record_reroute(**args)


def _rerouted(repo, config=None):
    return [e for e in read(repo, "P1", config=config) if e.event_type == "ReviewRerouted"]


def test_record_reroute_persists_the_explicit_event(repo):
    ctx = _ctx(repo)
    _reroute(ctx)
    rerouted = _rerouted(repo)
    assert len(rerouted) == 1
    payload = rerouted[0].payload
    assert payload["relaxed_constraints"] == ["family_independence", "snapshot_freshness"]
    assert payload["primary_profile"] == "independent_review"
    assert payload["fallback_profile"] == "deep_review"
    assert payload["primary_failure"]["exception_type"] == "ModelUnavailable"


def test_recording_the_same_reroute_twice_is_a_no_op(repo):
    ctx = _ctx(repo)
    _reroute(ctx)
    _reroute(ctx)
    assert len(_rerouted(repo)) == 1  # not a second degradation record


def test_a_reroute_naming_underived_route_ids_is_refused(repo):
    # The write-time validator recomputes both legs from the envelope attempt_id, so a
    # context cannot persist a record whose ids were not actually claimed for it.
    ctx = _ctx(repo)
    with pytest.raises(RouteAuditError):
        _reroute(ctx, primary_route_id="not-a-derived-id")
    assert _rerouted(repo) == []


def test_a_reroute_persistence_failure_is_route_fatal(tmp_path):
    # A REAL failure, not a patched one: the context points at a remote whose lane ref was
    # never bootstrapped, so sync_and_verify fails closed with GitLogAuthError. That escapes
    # as a raw transport error unless record_reroute normalizes it — and the lane entry
    # point does not classify transport errors, so it would bypass the fail-closed contract.
    bare = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
    clone = tmp_path / "c"
    subprocess.run(["git", "clone", "-q", str(bare), str(clone)], check=True)
    _git(clone, "config", "user.email", "t@t")
    _git(clone, "config", "user.name", "t")
    bootstrap_lane_log(clone, config=LaneLogConfig())  # LOCAL only — the remote has no ref

    ctx = LaneRouteContext(
        repo=clone, problem_id="P1", attempt_id="A1", actor="reviewer", clock=_clock,
        route_audit=_Sink(), reservation_authority=_Budget(),
        call_ledger=_ledger(clone), config=LaneLogConfig(remote="origin"),
    )
    with pytest.raises(RouteAuditError, match="must not run"):
        _reroute(ctx)
