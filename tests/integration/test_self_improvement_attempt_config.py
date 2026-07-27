"""An Attempt's limits are DURABLE (spec 025 slice 1A, Task 13).

A restart, a config change, or a competing worker must not be able to raise (or lower) the
call ceiling or the credit budget. A durable count checked against a mutable bound is not a
durable cap.
"""

from __future__ import annotations

import math
import subprocess
import threading

import pytest

from llmxive.self_improvement.attempt_config import (
    AttemptConfigMismatch,
    bind_attempt_config,
    load_attempt_config,
    require_attempt_config,
)
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log, read


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


def _clock():
    return "2026-07-24T00:00:00+00:00"


_CFG = LaneLogConfig(remote="origin")


@pytest.fixture
def clone(tmp_path, bare_remote):
    c = _clone(bare_remote, tmp_path / "c")
    bootstrap_lane_log(c, config=_CFG)
    return c


def _bind(repo, *, ceiling=56, budget=50.0):
    return bind_attempt_config(repo, problem_id="P1", attempt_id="A1", call_ceiling=ceiling,
                               attempt_budget_credits=budget, actor="lane", clock=_clock,
                               config=_CFG)


def _records(repo):
    return [e for e in read(repo, "P1", config=_CFG) if e.event_type == "AttemptConfigured"]


def test_binding_is_idempotent_for_identical_limits(clone):
    first = _bind(clone)
    assert _bind(clone) == first
    assert len(_records(clone)) == 1  # ONE record, not two


def test_a_larger_ceiling_is_rejected(clone):
    # THE regression: this is the exact sequence that defeats a constructor-local cap.
    _bind(clone, ceiling=2)
    with pytest.raises(AttemptConfigMismatch, match="call_ceiling"):
        _bind(clone, ceiling=100)


def test_a_smaller_ceiling_is_also_rejected(clone):
    # Fail closed in BOTH directions: a lower bound would silently strand admitted work.
    _bind(clone, ceiling=56)
    with pytest.raises(AttemptConfigMismatch, match="call_ceiling"):
        _bind(clone, ceiling=2)


def test_a_different_credit_budget_is_rejected(clone):
    _bind(clone, budget=50.0)
    with pytest.raises(AttemptConfigMismatch, match="attempt_budget_credits"):
        _bind(clone, budget=500.0)


def test_a_second_clone_sees_the_bound_limits(tmp_path, bare_remote):
    # Cross-process, not just cross-object.
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    bootstrap_lane_log(c1, config=_CFG)
    _bind(c1, ceiling=2)
    assert require_attempt_config(read(c2, "P1", config=_CFG), "A1").call_ceiling == 2
    with pytest.raises(AttemptConfigMismatch):
        _bind(c2, ceiling=100)


def test_two_concurrent_binders_converge_on_one_record(tmp_path, bare_remote):
    c1 = _clone(bare_remote, tmp_path / "c1")
    c2 = _clone(bare_remote, tmp_path / "c2")
    bootstrap_lane_log(c1, config=_CFG)
    barrier = threading.Barrier(2, timeout=30)
    out, errors = {}, []

    def _go(name, repo):
        try:
            barrier.wait()
            out[name] = _bind(repo)
        except BaseException as exc:
            errors.append(exc)

    ts = [threading.Thread(target=_go, args=(n, c)) for n, c in (("a", c1), ("b", c2))]
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout=60)
    assert not errors, f"concurrent bind raised: {errors}"
    assert out["a"] == out["b"]
    assert len(_records(c1)) == 1


@pytest.mark.parametrize("budget", [
    float("nan"),  # THE dangerous one: `total + credits > nan` is False -> always admit
    float("inf"),  # an unbounded cap by another name
    float("-inf"),
    True,          # bool IS an int in Python, and a nonsense credit budget
    "50",          # not a number at all
])
def test_a_non_finite_or_non_numeric_budget_is_refused(clone, budget):
    # `value < 0` does NOT reject nan/inf. A NaN budget would silently disable the money
    # cap for the whole Attempt.
    with pytest.raises(ValueError):
        _bind(clone, budget=budget)
    assert _records(clone) == []


def test_a_nan_budget_would_have_defeated_the_cap():
    # The reason the check above is REQUIRED, asserted directly so the rationale cannot
    # rot: every comparison against NaN is False, so the admission test passes for any
    # amount.
    nan = float("nan")
    assert not (nan < 0)               # the naive guard lets it through
    assert not (10_000.0 + 1.0 > nan)  # ...and then the cap never denies anything
    assert not math.isfinite(nan)      # the check that actually catches it


@pytest.mark.parametrize("ceiling", [0, -1, True, 5.0, "56"])
def test_a_non_positive_or_non_int_ceiling_is_refused(clone, ceiling):
    with pytest.raises(ValueError):
        _bind(clone, ceiling=ceiling)
    assert _records(clone) == []


def test_a_zero_budget_is_legal(clone):
    # An Attempt allowed no paid spend at all is a meaningful configuration, distinct from
    # a malformed one.
    assert _bind(clone, budget=0.0).attempt_budget_credits == 0.0


def test_an_unconfigured_attempt_fails_closed(clone):
    assert load_attempt_config(read(clone, "P1", config=_CFG), "A1") is None
    with pytest.raises(AttemptConfigMismatch, match="not configured"):
        require_attempt_config(read(clone, "P1", config=_CFG), "A1")


def test_each_attempt_binds_its_own_limits(clone):
    _bind(clone, ceiling=2)
    other = bind_attempt_config(clone, problem_id="P1", attempt_id="A2", call_ceiling=90,
                                attempt_budget_credits=10.0, actor="lane", clock=_clock,
                                config=_CFG)
    assert other.call_ceiling == 90
    assert require_attempt_config(read(clone, "P1", config=_CFG), "A1").call_ceiling == 2
