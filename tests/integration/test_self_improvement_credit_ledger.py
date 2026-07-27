"""AttemptCreditLedger reserve/release/mark_retained/reconcile (spec 025 slice 1A, T7-T9).

Real git repositories and real threads. The two layers of protection cover different
races, so both are exercised directly: an in-process panel sharing ONE ledger instance,
and two clones of one bare remote racing the same last credits.
"""

from __future__ import annotations

import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from llmxive.self_improvement.credit_ledger import (
    STATE_OPEN,
    STATE_RECONCILED,
    STATE_RELEASED,
    STATE_RETAINED,
    AttemptCreditLedger,
    counting_total,
    project_reservations,
)
from llmxive.self_improvement.lane_log import (
    LaneLogConfig,
    bootstrap_lane_log,
    read,
)

TS = "2026-07-24T00:00:00+00:00"


def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    bootstrap_lane_log(tmp_path, config=LaneLogConfig())
    return tmp_path


def _ledger(repo, budget=10.0, *, config=None, attempt="A1"):
    return AttemptCreditLedger(repo=repo, problem_id="P1", attempt_id=attempt,
                               attempt_budget_credits=budget, call_ceiling=56, actor="exec",
                               clock=lambda: TS, config=config)


def _reservations(repo, config=None, attempt="A1"):
    return project_reservations(read(repo, "P1", config=config), attempt)


def _state(repo, rid, config=None):
    return _reservations(repo, config)[rid].state


# ---- T7: amount validation ----


@pytest.mark.parametrize("bad", [-1.0, 0.0, float("nan"), float("inf"), float("-inf"), True, "5"])
def test_a_malformed_amount_raises_and_writes_nothing(repo, bad):
    # ValueError, not False: False is the answer to an ORDINARY budget denial, so a
    # malformed request reported that way would read as a routine skip.
    led = _ledger(repo, budget=10.0)
    with pytest.raises(ValueError, match="finite number > 0"):
        led.reserve(bad, reservation_id="r1", call_id="c1")
    assert _reservations(repo) == {}
    # and the budget is untouched — an honest reservation for the FULL amount still fits
    assert led.reserve(10.0, reservation_id="r1", call_id="c1") is True


# ---- T7: budget admission ----


def test_within_budget_reserves_and_over_budget_denies(repo):
    led = _ledger(repo, budget=10.0)
    assert led.reserve(6.0, reservation_id="r1", call_id="c1") is True
    assert led.reserve(5.0, reservation_id="r2", call_id="c2") is False  # only 4 left
    assert counting_total(_reservations(repo)) == 6.0


def test_a_reservation_that_exactly_fills_the_budget_is_admitted(repo):
    led = _ledger(repo, budget=10.0)
    assert led.reserve(6.0, reservation_id="r1", call_id="c1") is True
    assert led.reserve(4.0, reservation_id="r2", call_id="c2") is True  # at budget, not over
    assert counting_total(_reservations(repo)) == 10.0


def test_reserve_is_idempotent_for_the_same_identity(repo):
    led = _ledger(repo)
    assert led.reserve(3.0, reservation_id="r1", call_id="c1") is True
    assert led.reserve(3.0, reservation_id="r1", call_id="c1") is True  # re-invoked
    assert len(_reservations(repo)) == 1 and counting_total(_reservations(repo)) == 3.0


@pytest.mark.parametrize("credits, call_id", [(4.0, "c1"), (3.0, "c2")])
def test_the_same_reservation_id_with_a_different_identity_is_an_integrity_violation(
    repo, credits, call_id
):
    led = _ledger(repo)
    led.reserve(3.0, reservation_id="r1", call_id="c1")
    with pytest.raises(ValueError, match="COLLISION"):
        led.reserve(credits, reservation_id="r1", call_id=call_id)


def test_releasing_frees_the_budget_for_a_later_reservation(repo):
    led = _ledger(repo, budget=10.0)
    led.reserve(8.0, reservation_id="r1", call_id="c1")
    assert led.reserve(5.0, reservation_id="r2", call_id="c2") is False
    led.release("r1")
    assert led.reserve(5.0, reservation_id="r2", call_id="c2") is True


# ---- T7: concurrency ----


def test_an_in_process_panel_sharing_one_ledger_admits_only_what_the_budget_covers(repo):
    # US1 scenario 5: several reviewers, ONE ledger instance. Note this passes on the
    # ref-CAS alone — the lock is a contention measure, not the guarantee. Verified by
    # removing the lock: this test and the two-clone race both still hold.
    led = _ledger(repo, budget=10.0)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(led.reserve, 6.0, reservation_id=f"r{i}", call_id=f"c{i}")
                   for i in range(2)]
        results = [f.result() for f in futures]
    assert sorted(results) == [False, True]  # exactly one fit
    assert counting_total(_reservations(repo)) == 6.0


def test_two_clones_racing_the_last_credits_cannot_both_win(tmp_path):
    # The lock cannot help here — these are separate processes' worth of state. What makes
    # it safe is the ref-CAS plus the budget precondition recomputed against the events the
    # winner committed.
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
    results, lock = [], threading.Lock()

    def _worker(clone, tag):
        led = _ledger(clone, budget=10.0, config=cfg)
        barrier.wait()
        outcome = led.reserve(6.0, reservation_id=f"r-{tag}", call_id=f"c-{tag}")
        with lock:
            results.append(outcome)

    ts = [threading.Thread(target=_worker, args=(c, t))
          for c, t in zip(clones, ("a", "b"), strict=True)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout=60)

    assert sorted(results) == [False, True], f"both clones reserved 6.0 of a 10.0 budget: {results}"
    assert counting_total(_reservations(clones[0], cfg)) == 6.0


# ---- T8: release / mark_retained ----


def test_release_frees_budget_retain_keeps_it(repo):
    led = _ledger(repo, budget=20.0)
    led.reserve(6.0, reservation_id="r1", call_id="c1")
    led.release("r1")
    assert _state(repo, "r1") == STATE_RELEASED
    led.reserve(6.0, reservation_id="r2", call_id="c2")
    led.mark_retained("r2")
    assert _state(repo, "r2") == STATE_RETAINED
    assert counting_total(_reservations(repo)) == 6.0  # only the retained one counts


def test_dispatched_reservation_is_never_released(repo):
    # FR-033: once the call went out the spend is real, so release must not refund it.
    led = _ledger(repo)
    led.reserve(3.0, reservation_id="r1", call_id="c1")
    led.mark_retained("r1")
    led.release("r1")
    assert _state(repo, "r1") == STATE_RETAINED  # release was a no-op


def test_release_and_retain_are_idempotent(repo):
    led = _ledger(repo)
    led.reserve(3.0, reservation_id="r1", call_id="c1")
    led.release("r1")
    led.release("r1")
    assert _state(repo, "r1") == STATE_RELEASED
    assert len([e for e in read(repo, "P1") if e.event_type == "AttemptCreditReleased"]) == 1


def test_a_transition_on_an_unknown_reservation_is_a_no_op(repo):
    led = _ledger(repo)
    led.release("never-reserved")
    led.mark_retained("never-reserved")
    # No credit event at all — the stream still holds the ledger's own AttemptConfigured
    # binding, which construction writes.
    assert [e.event_type for e in read(repo, "P1")] == ["AttemptConfigured"]


def test_release_versus_retain_race_exactly_one_transition_lands(repo):
    # Two concurrent operations on ONE open reservation through the SHARED ledger. The
    # lock serializes them; the loser sees the reservation is no longer `open` and no-ops
    # per its contract, rather than raising or forcing a second transition.
    led = _ledger(repo)
    led.reserve(3.0, reservation_id="r1", call_id="c1")
    barrier = threading.Barrier(2, timeout=30)

    def _release():
        barrier.wait()
        led.release("r1")

    def _retain():
        barrier.wait()
        led.mark_retained("r1")

    ts = [threading.Thread(target=_release), threading.Thread(target=_retain)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout=60)

    final = _state(repo, "r1")
    assert final in (STATE_RELEASED, STATE_RETAINED)
    kinds = [e.event_type for e in read(repo, "P1") if e.event_type.startswith("AttemptCredit")]
    expected = "AttemptCreditReleased" if final == STATE_RELEASED else "AttemptCreditRetained"
    assert kinds == ["AttemptCreditReserved", expected]


# ---- T9: reconcile ----


def test_reconcile_moves_only_the_settled_retained_ids(repo):
    led = _ledger(repo, budget=30.0)
    for rid in ("r1", "r2"):
        led.reserve(3.0, reservation_id=rid, call_id=f"c-{rid}")
        led.mark_retained(rid)
    led.reserve(3.0, reservation_id="r3", call_id="c-r3")  # still open

    assert led.reconcile({"r1", "r3"}) == ["r1"]  # r3 is open, not retained
    assert _state(repo, "r1") == STATE_RECONCILED
    assert _state(repo, "r2") == STATE_RETAINED
    assert _state(repo, "r3") == STATE_OPEN


def test_reconcile_is_idempotent(repo):
    led = _ledger(repo)
    led.reserve(3.0, reservation_id="r1", call_id="c1")
    led.mark_retained("r1")
    assert led.reconcile({"r1"}) == ["r1"]
    assert led.reconcile({"r1"}) == []  # already reconciled → not moved again
    assert len([e for e in read(repo, "P1") if e.event_type == "AttemptCreditReconciled"]) == 1


def test_reconciled_credits_still_count(repo):
    # Reconciled means BILLED, so the money is gone — the only state that gives credits
    # back is `released`.
    led = _ledger(repo, budget=10.0)
    led.reserve(7.0, reservation_id="r1", call_id="c1")
    led.mark_retained("r1")
    led.reconcile({"r1"})
    assert counting_total(_reservations(repo)) == 7.0
    assert led.reserve(4.0, reservation_id="r2", call_id="c2") is False


def test_a_second_ledger_with_a_different_budget_is_rejected(repo):
    # The credit budget guards MONEY; it must not be re-openable by a worker that simply
    # passes a bigger number. Refused at CONSTRUCTION, before a single reservation.
    from llmxive.self_improvement.attempt_config import AttemptConfigMismatch

    _ledger(repo, budget=50.0)  # binds
    with pytest.raises(AttemptConfigMismatch, match="attempt_budget_credits"):
        _ledger(repo, budget=500.0)


def test_a_restarted_ledger_enforces_the_budget_already_spent(repo):
    # A fresh ledger object must see the reservations the previous one made — the durable
    # budget is the point, not the constructor argument.
    _ledger(repo, budget=10.0).reserve(8.0, reservation_id="r1", call_id="c1")
    assert _ledger(repo, budget=10.0).reserve(5.0, reservation_id="r2", call_id="c2") is False


def test_another_attempts_ledger_sees_its_own_budget(repo):
    # The stream is per-Problem but the budget is per-ATTEMPT: one Attempt's spend must
    # not consume another's headroom.
    a1 = _ledger(repo, budget=10.0, attempt="A1")
    a2 = _ledger(repo, budget=10.0, attempt="A2")
    assert a1.reserve(9.0, reservation_id="r1", call_id="c1") is True
    assert a2.reserve(9.0, reservation_id="r2", call_id="c2") is True
    assert counting_total(_reservations(repo, attempt="A1")) == 9.0
    assert counting_total(_reservations(repo, attempt="A2")) == 9.0
