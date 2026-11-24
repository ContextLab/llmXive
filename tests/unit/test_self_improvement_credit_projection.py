"""The AttemptCreditLedger reservation projection (spec 025 slice 1A, Task 6).

This fold decides how much of an Attempt's budget is committed, so the tests are about
what it REFUSES as much as what it counts: a number produced from an illegal history would
be a spending decision made on a lie.
"""

from __future__ import annotations

import pytest

from llmxive.self_improvement.credit_ledger import (
    STATE_OPEN,
    STATE_RECONCILED,
    STATE_RELEASED,
    STATE_RETAINED,
    counting_total,
    project_reservations,
)
from llmxive.self_improvement.events import Event


def _ev(eid, etype, rid, seq, attempt="A1", credits=2.5, call_id="c1"):
    payload = {} if rid is None else {"reservation_id": rid}
    if etype == "AttemptCreditReserved":
        payload |= {"call_id": call_id, "reserved_credits": credits}
    return Event(event_id=eid, event_type=etype, problem_id="P1", actor="exec", payload=payload,
                 timestamp="2026-07-24T00:00:00+00:00", attempt_id=attempt,
                 expected_problem_revision=seq, resulting_problem_revision=seq + 1, seq=seq)


def test_reserve_retain_reconcile_advances():
    events = [_ev("e1", "AttemptCreditReserved", "r1", 0),
              _ev("e2", "AttemptCreditRetained", "r1", 1),
              _ev("e3", "AttemptCreditReconciled", "r1", 2)]
    assert project_reservations(events, "A1")["r1"].state == STATE_RECONCILED


def test_a_fresh_reservation_is_open_and_counts():
    res = project_reservations([_ev("e1", "AttemptCreditReserved", "r1", 0, credits=7.5)], "A1")
    assert res["r1"].state == STATE_OPEN
    assert (res["r1"].call_id, res["r1"].reserved_credits) == ("c1", 7.5)
    assert counting_total(res) == 7.5


def test_a_negative_reservation_would_have_reopened_the_budget():
    # WHY Task 2 validates reserved_credits > 0, asserted directly so the rationale cannot
    # rot: counting_total SUMS the amounts, so a negative one hands back budget that was
    # already spent. The event validator makes this unreachable through the real write
    # path; this test pins the consequence it prevents.
    honest = [_ev("e1", "AttemptCreditReserved", "r1", 0, credits=40.0)]
    poisoned = [*honest, _ev("e2", "AttemptCreditReserved", "r2", 1, credits=-30.0)]
    assert counting_total(project_reservations(honest, "A1")) == 40.0
    assert counting_total(project_reservations(poisoned, "A1")) == 10.0  # 30 credits back


def test_released_excluded_from_counting():
    events = [_ev("e1", "AttemptCreditReserved", "r1", 0, credits=10.0),
              _ev("e2", "AttemptCreditReserved", "r2", 1, credits=5.0),
              _ev("e3", "AttemptCreditReleased", "r2", 2)]
    res = project_reservations(events, "A1")
    assert res["r2"].state == STATE_RELEASED and counting_total(res) == 10.0


@pytest.mark.parametrize("state_events, why", [
    ([], "an open reservation is money already committed"),
    ([("AttemptCreditRetained",)], "a retained one was dispatched"),
    ([("AttemptCreditRetained",), ("AttemptCreditReconciled",)], "a reconciled one was billed"),
])
def test_every_state_but_released_keeps_counting(state_events, why):
    events = [_ev("e0", "AttemptCreditReserved", "r1", 0, credits=12.0)]
    for i, (etype,) in enumerate(state_events, start=1):
        events.append(_ev(f"e{i}", etype, "r1", i))
    assert counting_total(project_reservations(events, "A1")) == 12.0, why


def test_dispatch_unknown_retains_the_reservation():
    # The atomic reconcile effect: an unknown dispatch may have spent the money, so the
    # reservation is RETAINED (still counting), never released.
    events = [_ev("e1", "AttemptCreditReserved", "r1", 0),
              _ev("e2", "DispatchUnknown", "r1", 1)]  # payload carries reservation_id
    assert project_reservations(events, "A1")["r1"].state == STATE_RETAINED


def test_dispatch_unknown_is_idempotent_because_reconciliation_may_repeat():
    events = [_ev("e1", "AttemptCreditReserved", "r1", 0),
              _ev("e2", "DispatchUnknown", "r1", 1),
              _ev("e3", "DispatchUnknown", "r1", 2)]
    assert project_reservations(events, "A1")["r1"].state == STATE_RETAINED


def test_a_free_candidates_dispatch_unknown_carries_no_reservation():
    # A free candidate spends nothing, so its unknown dispatch has no reservation to
    # retain — the ONLY type whose reservation_id is legitimately absent.
    events = [_ev("e1", "AttemptCreditReserved", "r1", 0),
              _ev("e2", "DispatchUnknown", None, 1)]
    assert project_reservations(events, "A1")["r1"].state == STATE_OPEN


@pytest.mark.parametrize("history, why", [
    ([("AttemptCreditRetained", "ghost")], "unknown reservation"),
    ([("AttemptCreditReserved", "r1"), ("AttemptCreditReserved", "r1")], "illegal"),
    ([("AttemptCreditReserved", "r1"), ("AttemptCreditReleased", "r1"),
      ("AttemptCreditRetained", "r1")], "illegal"),
    ([("AttemptCreditReserved", "r1"), ("AttemptCreditReconciled", "r1")], "illegal"),
    ([("AttemptCreditReserved", "r1"), ("AttemptCreditRetained", "r1"),
      ("AttemptCreditReleased", "r1")], "illegal"),
    ([("AttemptCreditReserved", "r1"), ("AttemptCreditRetained", "r1"),
      ("AttemptCreditReconciled", "r1"), ("AttemptCreditReconciled", "r1")], "illegal"),
])
def test_projection_rejects_illegal_transitions(history, why):
    events = [_ev(f"e{i}", etype, rid, i) for i, (etype, rid) in enumerate(history)]
    with pytest.raises(ValueError, match=why):
        project_reservations(events, "A1")


def test_a_dispatched_reservation_can_never_be_released():
    # The edge that matters most for money: once a call was dispatched the spend is real,
    # so there is no path back to `released` that would hand the credits back.
    events = [_ev("e1", "AttemptCreditReserved", "r1", 0, credits=9.0),
              _ev("e2", "DispatchUnknown", "r1", 1)]
    with pytest.raises(ValueError, match="illegal transition"):
        project_reservations([*events, _ev("e3", "AttemptCreditReleased", "r1", 2)], "A1")


def test_a_credit_transition_missing_its_reservation_id_fails_closed():
    # Skipping it would leave a released reservation counting against the budget forever.
    events = [_ev("e1", "AttemptCreditReserved", "r1", 0),
              _ev("e2", "AttemptCreditReleased", None, 1)]
    with pytest.raises(ValueError, match="payload lacks 'reservation_id'"):
        project_reservations(events, "A1")


def test_other_attempts_events_are_not_folded_in():
    events = [_ev("e1", "AttemptCreditReserved", "r1", 0, credits=10.0),
              _ev("e2", "AttemptCreditReserved", "r9", 1, attempt="A2", credits=99.0)]
    res = project_reservations(events, "A1")
    assert set(res) == {"r1"} and counting_total(res) == 10.0


def test_unrelated_event_types_are_ignored():
    events = [_ev("e1", "AttemptCreditReserved", "r1", 0, credits=3.0),
              _ev("e2", "DispatchStarted", "r1", 1)]  # an audit mirror, not a transition
    assert project_reservations(events, "A1")["r1"].state == STATE_OPEN
