"""Unit tests for parallel panel dispatch in the convergence engine.

The panel's lens reviewers are independent: each ``identify``/``rereview`` call
is a long reasoning-model call with no cross-reviewer dependency. The engine
dispatches them concurrently with a bounded pool, but the OBSERVABLE result
(concern ordering, verdicts, convergence outcome, skip-accepter optimization,
exception propagation) MUST be byte-for-byte identical to the prior serial
behavior. These tests pin that contract using deterministic fake reviewers
(real test doubles implementing the Reviewer interface — no mocks).
"""

from __future__ import annotations

import threading
import time

import pytest

from llmxive.convergence import engine as engine_mod
from llmxive.convergence.engine import run_convergence
from llmxive.convergence.types import ConcernResponse

# Reuse the existing real test doubles so the parallel tests drive the SAME
# reviewer interface the rest of the suite pins (Constitution I / SSoT).
from tests.unit.test_convergence_engine import (
    FakeReviewer,
    FakeReviser,
    _c,
    _spec,
)


def test_identify_concern_order_matches_panel_order():
    """R1 ``open_concerns`` must be assembled in PANEL order regardless of which
    worker thread finishes first. Reviewer 0 sleeps longest so, if results were
    appended from worker threads, its concern would land LAST — proving order is
    re-imposed by panel index, not completion time."""

    class SleepyReviewer(FakeReviewer):
        def __init__(self, name, cid, sleep):
            super().__init__(name=name, r1=[_c(cid, reviewer=name)])
            self._sleep = sleep

        def identify(self, artifacts, *, constitution, advisory):
            time.sleep(self._sleep)
            return super().identify(artifacts, constitution=constitution, advisory=advisory)

    panel = [
        SleepyReviewer("r0", "c0", 0.30),  # finishes last
        SleepyReviewer("r1", "c1", 0.05),
        SleepyReviewer("r2", "c2", 0.01),  # finishes first
    ]
    # max_rounds=0 -> identify only, then kickback; concern_history preserves R1 order.
    res = run_convergence(_spec(panel, FakeReviser(), max_rounds=0), {"a.md": "x"})
    ids = [c.id for c in res.concern_history]
    assert ids == ["c0", "c1", "c2"], ids


def test_identify_runs_concurrently():
    """Five reviewers that each sleep ~0.3s in ``identify`` must complete in
    roughly 1x (not 5x) wall-clock — proving the calls are dispatched in
    parallel, not serially."""
    sleep_s = 0.3
    n = 5

    class SleepyReviewer(FakeReviewer):
        def identify(self, artifacts, *, constitution, advisory):
            time.sleep(sleep_s)
            return super().identify(artifacts, constitution=constitution, advisory=advisory)

    panel = [SleepyReviewer(name=f"r{i}", r1=[]) for i in range(n)]
    t0 = time.monotonic()
    res = run_convergence(_spec(panel, FakeReviser()), {"a.md": "x"})
    elapsed = time.monotonic() - t0
    assert res.converged is True
    # Serial would be ~n*sleep_s; parallel ~sleep_s. Require well under 60% of serial.
    assert elapsed < sleep_s * n * 0.6, (
        f"identify took {elapsed:.2f}s; expected ~{sleep_s:.2f}s parallel, "
        f"not ~{sleep_s * n:.2f}s serial"
    )


def test_identify_exception_propagates_and_does_not_hang():
    """If one reviewer's ``identify`` raises, the engine call must raise (not
    swallow, not return partial convergence, not hang)."""

    class Boom(RuntimeError):
        pass

    class ExplodingReviewer(FakeReviewer):
        def identify(self, artifacts, *, constitution, advisory):
            raise Boom("backend unavailable")

    panel = [
        FakeReviewer(name="ok0", r1=[_c("c0", reviewer="ok0")]),
        ExplodingReviewer(name="boom", r1=[]),
        FakeReviewer(name="ok1", r1=[_c("c1", reviewer="ok1")]),
    ]
    with pytest.raises(Boom):
        run_convergence(_spec(panel, FakeReviser()), {"a.md": "x"})


def test_rereview_exception_propagates():
    """An exception raised in R3 ``rereview`` must propagate out of the phase
    (keeps the circuit-breaker's run-abort behavior intact)."""

    class Boom(RuntimeError):
        pass

    class ExplodingOnRereview(FakeReviewer):
        def rereview(self, artifacts, own_concerns, responses, *, constitution, advisory):
            raise Boom("transient backend error")

    # Both dissenters raise R1 concerns so both re-review in R3.
    panel = [
        FakeReviewer(name="ok", r1=[_c("c0", reviewer="ok")]),
        ExplodingOnRereview(name="boom", r1=[_c("c1", reviewer="boom")]),
    ]
    with pytest.raises(Boom):
        run_convergence(_spec(panel, FakeReviser()), {"a.md": "x"})


def test_rereview_runs_concurrently():
    """In R3, the per-reviewer ``rereview`` calls are dispatched in parallel.
    Two dissenters that each sleep ~0.3s in rereview must take ~1x, not 2x."""
    sleep_s = 0.3

    class SleepyRereview(FakeReviewer):
        def rereview(self, artifacts, own_concerns, responses, *, constitution, advisory):
            time.sleep(sleep_s)
            return super().rereview(
                artifacts, own_concerns, responses,
                constitution=constitution, advisory=advisory,
            )

    panel = [
        SleepyRereview(name="a", r1=[_c("ca", reviewer="a")]),  # passes round 1
        SleepyRereview(name="b", r1=[_c("cb", reviewer="b")]),  # passes round 1
    ]
    t0 = time.monotonic()
    res = run_convergence(_spec(panel, FakeReviser()), {"a.md": "x"})
    elapsed = time.monotonic() - t0
    assert res.converged is True
    assert elapsed < sleep_s * 2 * 0.6, f"rereview took {elapsed:.2f}s; expected ~parallel"


def test_skip_accepter_preserved_under_parallel_dispatch():
    """An R1-accepter (no own concerns) with a no-op revision (nothing changed)
    must NOT be re-reviewed, exactly as in the serial path — no rereview call is
    dispatched for it."""

    class _NoOpReviser:
        def __init__(self):
            self.calls = 0

        def revise(self, artifacts, concerns):
            self.calls += 1
            return dict(artifacts), [
                ConcernResponse(concern_id=c.id, response="no edit", what_changed="none")
                for c in concerns
            ]

    dissenter = FakeReviewer(name="A", r1=[_c("c1", reviewer="A")], pass_at={"c1": 99})
    accepter = FakeReviewer(name="B", r1=[])
    res = run_convergence(
        _spec([dissenter, accepter], _NoOpReviser(), max_rounds=3), {"a.md": "x"}
    )
    assert accepter.rereview_calls == 0  # never dispatched
    assert res.converged is False


def test_rereview_verdict_and_next_open_order_matches_panel_order():
    """``round_verdicts`` and the recomputed ``open_concerns`` must follow panel
    order even when later panelists finish first. r0 (sleeps longest) raises c0,
    r1 raises c1; both stay open (pass_at high) so they re-review every round and
    surface in panel order in concern_history."""

    class SleepyRereview(FakeReviewer):
        def __init__(self, name, cid, sleep):
            super().__init__(name=name, r1=[_c(cid, reviewer=name)], pass_at={cid: 99})
            self._sleep = sleep

        def rereview(self, artifacts, own_concerns, responses, *, constitution, advisory):
            time.sleep(self._sleep)
            return super().rereview(
                artifacts, own_concerns, responses,
                constitution=constitution, advisory=advisory,
            )

    panel = [
        SleepyRereview("r0", "c0", 0.15),  # last to finish R3
        SleepyRereview("r1", "c1", 0.01),
    ]
    res = run_convergence(_spec(panel, FakeReviser(), max_rounds=2), {"a.md": "x"})
    assert res.converged is False
    # Both concerns appear, in panel order (c0 before c1) in history.
    ids = [c.id for c in res.concern_history if c.id in {"c0", "c1"}]
    assert ids[:2] == ["c0", "c1"], ids


def test_single_reviewer_panel_uses_serial_path():
    """A panel of one must behave exactly like the serial path (no crash on a
    pool that would be size 1)."""
    rev = FakeReviewer(name="solo", r1=[_c("c1", reviewer="solo")])
    res = run_convergence(_spec([rev], FakeReviser()), {"a.md": "x"})
    assert res.converged is True
    assert res.rounds_used == 1


def test_pool_is_bounded_by_max_concurrency():
    """The pool size is capped at ``_PANEL_MAX_CONCURRENCY``: with a panel larger
    than the cap, no more than the cap reviewers run at once."""
    assert hasattr(engine_mod, "_PANEL_MAX_CONCURRENCY")
    cap = engine_mod._PANEL_MAX_CONCURRENCY

    active = 0
    peak = 0
    lock = threading.Lock()

    class CountingReviewer(FakeReviewer):
        def identify(self, artifacts, *, constitution, advisory):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            time.sleep(0.05)
            with lock:
                active -= 1
            return super().identify(artifacts, constitution=constitution, advisory=advisory)

    panel = [CountingReviewer(name=f"r{i}", r1=[]) for i in range(cap + 4)]
    run_convergence(_spec(panel, FakeReviser()), {"a.md": "x"})
    assert peak <= cap, f"peak concurrency {peak} exceeded cap {cap}"
