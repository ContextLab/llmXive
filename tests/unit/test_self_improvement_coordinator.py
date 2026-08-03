"""The LaneCoordinator projection (spec 025 slice 1A, Task 4).

The fold is the lane's recovery authority: after a crash, whoever picks the lane up
re-derives ownership from these events alone. So every test here is about refusing a
history that would answer the ownership question wrongly, not merely about happy paths.
"""

from __future__ import annotations

import pytest

from llmxive.self_improvement.coordinator import EMPTY_COORDINATOR, project_coordinator
from llmxive.self_improvement.events import COORDINATOR_STREAM, Event

_MERGED_AT = "2026-07-24T00:00:00+00:00"


def _ev(eid, etype, payload, seq, *, attempt_id="A1"):
    return Event(event_id=eid, event_type=etype, problem_id=COORDINATOR_STREAM, actor="coord",
                 payload=payload, timestamp="2026-07-24T00:00:00+00:00", attempt_id=attempt_id,
                 expected_lane_revision=seq, resulting_lane_revision=seq + 1, seq=seq)


def _claim(eid, seq, problem="P1", attempt="A1"):
    return _ev(eid, "ClaimAcquired", {"problem_id": problem, "attempt_id": attempt}, seq,
               attempt_id=attempt)


def _release(eid, seq, problem="P1", attempt="A1"):
    return _ev(eid, "ClaimReleased", {"problem_id": problem, "attempt_id": attempt}, seq,
               attempt_id=attempt)


def test_empty_is_genesis():
    assert project_coordinator([]) == EMPTY_COORDINATOR


def test_claim_sets_active():
    c = project_coordinator([_claim("e1", 0)])
    assert c.active_problem_id == "P1" and c.active_attempt_id == "A1" and c.lane_revision == 1


def test_claim_then_release_returns_idle():
    c = project_coordinator([_claim("e1", 0), _release("e2", 1)])
    assert c.lane_revision == 2 and c.active_problem_id is None and c.active_attempt_id is None


def test_the_lane_can_be_reclaimed_after_a_release():
    # The singleton is a lock, not a one-shot: releasing must leave the lane usable.
    c = project_coordinator([_claim("e1", 0), _release("e2", 1), _claim("e3", 2, "P2", "A2")])
    assert (c.active_problem_id, c.active_attempt_id, c.lane_revision) == ("P2", "A2", 3)


def test_projection_rejects_unknown_event_type():
    bad = _ev("x", "SomethingFromTheFuture", {}, 0)
    with pytest.raises(ValueError, match="unknown coordinator event"):
        project_coordinator([bad])


@pytest.mark.parametrize("history, why", [
    ([_release("e1", 0)], "ClaimReleased while idle"),
    ([_claim("e1", 0), _claim("e2", 1, "P2", "A2")], "ClaimAcquired while active"),
    ([_claim("e1", 0), _release("e2", 1, "PX", "AX")], "non-owner"),
])
def test_projection_rejects_illegal_transitions(history, why):
    # The projection is the recovery authority: an illegal history must RAISE, never be
    # folded into a plausible-looking answer.
    with pytest.raises(ValueError, match=why):
        project_coordinator(history)


def test_a_release_naming_the_right_problem_but_the_wrong_attempt_is_a_non_owner():
    # Ownership is the PAIR. A retry from an earlier Attempt on the same Problem must not
    # clear the current one's claim.
    with pytest.raises(ValueError, match="non-owner"):
        project_coordinator([_claim("e1", 0, "P1", "A1"), _release("e2", 1, "P1", "A2")])


def test_events_out_of_seq_order_are_refused():
    # ORDER decides ownership here. A caller that sorted by timestamp — the exact mistake
    # the seq design exists to prevent — would otherwise get a confidently wrong answer.
    reversed_history = [_release("e2", 1), _claim("e1", 0)]
    with pytest.raises(ValueError, match="out of order"):
        project_coordinator(reversed_history)


def test_a_payload_missing_the_field_the_fold_reads_fails_closed():
    # validate_lane_event rejects this at the write boundary; the fold must still refuse
    # rather than raise KeyError if it is ever handed an unvalidated event.
    with pytest.raises(ValueError, match="payload lacks 'attempt_id'"):
        project_coordinator([_ev("e1", "ClaimAcquired", {"problem_id": "P1"}, 0)])


def test_monitor_started_accumulates_in_order():
    c = project_coordinator([
        # The payloads are what `validate_lane_event` would accept (spec rev 24 made
        # `problem_id` and `merged_at` required); the fold reads only `attempt_id` today —
        # `last_autonomous_merge_at` and the ownership check come with Task 12.
        _ev("e1", "MonitorStarted",
            {"problem_id": "P1", "attempt_id": "A1", "merged_at": _MERGED_AT}, 0),
        _ev("e2", "MonitorStarted",
            {"problem_id": "P2", "attempt_id": "A2", "merged_at": _MERGED_AT}, 1,
            attempt_id="A2"),
    ])
    assert c.monitored_attempts == ("A1", "A2") and c.lane_revision == 2


def test_promotion_flag_and_policy_version_track_the_last_record():
    c = project_coordinator([
        _ev("e1", "PromotionEnabledSet", {"promotion_enabled": True, "policy_version": 3}, 0,
            attempt_id=None),
        _ev("e2", "PromotionEnabledSet", {"promotion_enabled": False}, 1, attempt_id=None),
    ])
    # the second record carries no version, so the previous one stands
    assert c.promotion_enabled is False and c.policy_version == 3


def test_a_non_bool_promotion_flag_is_refused_rather_than_coerced():
    # bool("false") is True: coercion here would OPEN the autonomous-merge gate that the
    # record was written to close.
    bad = _ev("e1", "PromotionEnabledSet", {"promotion_enabled": "false"}, 0, attempt_id=None)
    with pytest.raises(ValueError, match="must be a bool"):
        project_coordinator([bad])
