"""Durable per-Attempt call admission (spec 025 slice 1A, Task 14).

The ceiling is per ATTEMPT and therefore durable and cross-process: a second process, or a
restarted one, must see the calls the first already spent. An in-memory counter would hand
each of them a fresh budget, which is exactly the runaway the ceiling exists to prevent.
"""

from __future__ import annotations

import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from llmxive.self_improvement.attempt_config import AttemptConfigMismatch
from llmxive.self_improvement.call_ledger import (
    LaneCallCeilingExceeded,
    LaneCallLedger,
    project_call_claims,
)
from llmxive.self_improvement.events import derive_route_id
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log, read

_CFG = LaneLogConfig(remote="origin")


def _git(repo, *a):
    subprocess.run(["git", *a], cwd=str(repo), check=True, capture_output=True, text=True)


@pytest.fixture
def bare_remote(tmp_path):
    r = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(r)], check=True)
    return r


def _clone(bare, dst):
    subprocess.run(["git", "clone", "-q", str(bare), str(dst)], check=True)
    _git(dst, "config", "user.email", "t@t")
    _git(dst, "config", "user.name", "t")
    return dst


@pytest.fixture
def clone(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=_CFG)
    return c


def _clock():
    return "2026-07-24T00:00:00+00:00"


def _ledger(repo, ceiling=3, attempt="A1"):
    # attempt_budget_credits is passed because ONE AttemptConfigured record binds BOTH
    # limits; this ledger reads back only the ceiling.
    return LaneCallLedger(repo=repo, problem_id="P1", attempt_id=attempt, call_ceiling=ceiling,
                          attempt_budget_credits=50.0, actor="lane", clock=_clock, config=_CFG)


def test_claim_charges_once_and_replays_the_same_route_id(clone):
    led = _ledger(clone)
    first = led.claim(operation_id="lens-a", leg="primary")
    again = led.claim(operation_id="lens-a", leg="primary")  # REPLAY, not a second call
    assert first == again == derive_route_id("A1", "lens-a", "primary")
    assert led.calls_used() == 1


def test_the_two_reroute_legs_are_distinct_claims(clone):
    led = _ledger(clone)
    primary = led.claim(operation_id="lens-a", leg="primary")
    fallback = led.claim(operation_id="lens-a", leg="fallback")
    assert primary != fallback and led.calls_used() == 2  # the ceiling counts BOTH legs


def test_ceiling_fails_closed(clone):
    led = _ledger(clone, ceiling=2)
    led.claim(operation_id="a")
    led.claim(operation_id="b")
    with pytest.raises(LaneCallCeilingExceeded):
        led.claim(operation_id="c")


def test_a_replay_still_works_at_the_ceiling(clone):
    # A retry of an ALREADY-admitted operation must not be refused just because the Attempt
    # is now full — it consumes nothing.
    led = _ledger(clone, ceiling=2)
    first = led.claim(operation_id="a")
    led.claim(operation_id="b")
    assert led.claim(operation_id="a") == first
    assert led.calls_used() == 2


def test_an_unknown_leg_is_rejected(clone):
    with pytest.raises(ValueError, match="leg"):
        _ledger(clone).claim(operation_id="a", leg="tertiary")


def test_a_restarted_process_does_not_get_a_fresh_ceiling(clone):
    # THE regression: the whole point of durability. A brand-new ledger object (a restart, a
    # retry on another runner, a duplicate worker) must observe the calls already spent.
    _ledger(clone, ceiling=2).claim(operation_id="a")
    _ledger(clone, ceiling=2).claim(operation_id="b")
    with pytest.raises(LaneCallCeilingExceeded):
        _ledger(clone, ceiling=2).claim(operation_id="c")


def test_a_second_clone_shares_the_same_ceiling(tmp_path, bare_remote):
    # Cross-PROCESS, not just cross-object: two clones of one remote, one Attempt budget.
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    bootstrap_lane_log(c1, config=_CFG)
    _ledger(c1, ceiling=2).claim(operation_id="a")
    _ledger(c2, ceiling=2).claim(operation_id="b")  # syncs c1's claim from the ref
    with pytest.raises(LaneCallCeilingExceeded):
        _ledger(c2, ceiling=2).claim(operation_id="c")


def test_a_larger_ceiling_cannot_reopen_a_spent_attempt(clone):
    # With a constructor-local ceiling this sequence admitted the third call. The limit is
    # bound durably, so the third LEDGER is refused at construction.
    _ledger(clone, ceiling=2).claim(operation_id="a")
    _ledger(clone, ceiling=2).claim(operation_id="b")
    with pytest.raises(AttemptConfigMismatch, match="call_ceiling"):
        _ledger(clone, ceiling=100)


def test_a_second_clone_cannot_present_a_different_ceiling(tmp_path, bare_remote):
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    bootstrap_lane_log(c1, config=_CFG)
    _ledger(c1, ceiling=2).claim(operation_id="a")
    with pytest.raises(AttemptConfigMismatch):
        _ledger(c2, ceiling=100)


def test_another_attempt_has_its_own_ceiling(clone):
    _ledger(clone, ceiling=2, attempt="A1").claim(operation_id="a")
    other = _ledger(clone, ceiling=2, attempt="A2")
    other.claim(operation_id="a")
    assert other.calls_used() == 1  # A1's spend is not charged to A2


def test_concurrent_claimers_never_exceed_the_ceiling(clone):
    # The panel's ThreadPoolExecutor shares ONE ledger; admission must be atomic.
    led = _ledger(clone, ceiling=4)
    ok, refused, errors = [], [], []
    lock = threading.Lock()

    def _take(i):
        try:
            route = led.claim(operation_id=f"op-{i}")
            with lock:
                ok.append(route)
        except LaneCallCeilingExceeded:
            with lock:
                refused.append(i)
        except BaseException as exc:
            with lock:
                errors.append(exc)

    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(_take, range(10)))

    assert not errors, f"claim raised something other than the ceiling error: {errors}"
    assert len(ok) == 4 and len(set(ok)) == 4  # exactly the ceiling, all distinct
    assert len(refused) == 6
    assert len(project_call_claims(read(clone, "P1", config=_CFG), "A1")) == 4


def test_the_claim_record_carries_the_derived_route_id(clone):
    # validate_lane_event recomputes this at the write boundary, so a claim whose route_id
    # was not derived from its own (attempt, operation, leg) could never be appended.
    led = _ledger(clone)
    led.claim(operation_id="lens-a", leg="fallback")
    claim = next(e for e in read(clone, "P1", config=_CFG) if e.event_type == "LaneCallClaimed")
    assert claim.payload["route_id"] == derive_route_id("A1", "lens-a", "fallback")
    assert claim.payload["leg"] == "fallback" and claim.attempt_id == "A1"
