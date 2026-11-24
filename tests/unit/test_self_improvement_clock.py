"""FR-036 authoritative time. The lane compares durations across independent runners, so
every recorded instant must come from ONE authority — rev 21's check compared a writer's
timestamp against that same writer's clock, which cannot detect skew at all.

The wall clock is never consulted. These tests drive a fake MONOTONIC source; several of
them exist specifically because an earlier draft extrapolated from wall time and would have
emitted a backward-moving 'authoritative' clock on an ordinary NTP correction."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from llmxive.self_improvement import clock as clock_mod
from llmxive.self_improvement.clock import (
    MAX_CLOCK_REGRESSION_S,
    FixedAnchorClock,
    GitHubDateClock,
    NoTrustedTimeError,
    parse_http_date,
)

DATE_HDR = "Fri, 31 Jul 2026 12:00:00 GMT"
LATER_HDR = "Fri, 31 Jul 2026 13:00:00 GMT"
#: One minute behind DATE_HDR — a regression INSIDE `MAX_CLOCK_REGRESSION_S` (300 s), so
#: the clamp absorbs it. The hour-long step is the fail-closed case, not this one.
EARLIER_HDR = "Fri, 31 Jul 2026 11:59:00 GMT"


class Mono:
    """A controllable monotonic source. Real logic: it only ever advances."""

    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        assert seconds >= 0, "a monotonic source cannot go backward"
        self.t += seconds


def _clock(mono, headers, *, rtt=0.0, **kw):
    """A clock whose fetch consumes `headers` and burns `rtt` seconds of monotonic time,
    which is how the bracket sees a round trip at all."""
    seen = []

    def fetch():
        seen.append(1)
        mono.advance(rtt)
        return headers[min(len(seen) - 1, len(headers) - 1)]

    clock = GitHubDateClock(fetch_date_header=fetch, monotonic=mono, **kw)
    clock.fetch_count = lambda: len(seen)
    return clock


# ---- parsing ----


def test_parse_http_date_yields_an_aware_utc_instant():
    assert parse_http_date(DATE_HDR) == dt.datetime(
        2026, 7, 31, 12, 0, tzinfo=dt.UTC)


@pytest.mark.parametrize("bad", ["", "not a date", "Fri, 31 Jul 2026", "1753963200"])
def test_parse_http_date_refuses_anything_it_cannot_parse(bad):
    # Fail closed: a silently-wrong anchor poisons every duration in the lane.
    with pytest.raises(NoTrustedTimeError):
        parse_http_date(bad)


def test_parse_http_date_refuses_a_header_with_NO_usable_offset():
    """RFC 7231's `-0000` means "offset unknown", and `parsedate_to_datetime` returns a
    NAIVE datetime for it. Converting that to UTC would read it as LOCAL time — a silent
    error of however far this runner sits from Greenwich, in either direction."""
    with pytest.raises(NoTrustedTimeError, match="offset"):
        parse_http_date("Fri, 31 Jul 2026 12:00:00 -0000")


# ---- the authenticated fetch (maintainer decision 1) ----


def test_the_default_fetch_REQUIRES_a_token_and_never_calls_out_without_one(monkeypatch):
    # A safety-critical clock does not fall back to the unauthenticated 60/hr per-IP
    # allowance, which a co-tenant can exhaust for us. Asserting the network is never
    # reached is the point — an unauthenticated request that HAPPENS to succeed today is
    # the failure this refuses to depend on.
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        monkeypatch.delenv(name, raising=False)

    def _never(*a, **kw):
        raise AssertionError("the clock attempted an unauthenticated request")

    monkeypatch.setattr(clock_mod.urllib.request, "urlopen", _never)
    with pytest.raises(NoTrustedTimeError, match="GITHUB_TOKEN"):
        clock_mod._default_fetch()


def test_the_default_fetch_sends_the_token_it_found(monkeypatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "t0ken")
    sent = {}

    class _Resp:
        def __init__(self):
            self.headers = {"Date": DATE_HDR}

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def _capture(request, timeout=None):
        sent.update(request.headers)
        return _Resp()

    monkeypatch.setattr(clock_mod.urllib.request, "urlopen", _capture)
    assert clock_mod._default_fetch() == DATE_HDR
    # urllib title-cases header keys.
    assert sent["Authorization"] == "Bearer t0ken"


# ---- sampling ----


def test_the_clock_reports_authority_time_and_tracks_monotonic_elapsed():
    mono = Mono()
    clock = _clock(mono, [DATE_HDR])
    assert clock().startswith("2026-07-31T12:00:00")
    mono.advance(120)
    assert clock().startswith("2026-07-31T12:02:00")


def test_the_sample_is_taken_at_the_ROUND_TRIP_MIDPOINT():
    # A 10 s round trip means the header was true somewhere in that window; the midpoint is
    # the least-wrong estimate, and it is off by at most rtt/2 by construction.
    mono = Mono()
    clock = _clock(mono, [DATE_HDR], rtt=10.0, max_sample_rtt_s=30.0)
    stamped = dt.datetime.fromisoformat(clock())
    # 5 s of the round trip elapsed after the midpoint, so "now" is 12:00:05 — plus the
    # half-second that centres a whole-second header in the interval it names.
    assert stamped == dt.datetime(2026, 7, 31, 12, 0, 5, 500_000, tzinfo=dt.UTC)
    assert clock.sample_uncertainty_s == pytest.approx(5.5)


def test_uncertainty_never_drops_below_the_HEADER_RESOLUTION():
    """A 4 ms round trip does not make the anchor accurate to 2 ms: the header names a
    WHOLE SECOND, so half a second of the estimate is unknowable no matter how fast the
    wire is. Understating it would shrink the reclaim margin, which pads the one way
    FR-036 forbids."""
    mono = Mono()
    clock = _clock(mono, [DATE_HDR], rtt=0.004)
    clock()
    assert clock.sample_uncertainty_s == pytest.approx(0.502)
    assert clock.sample_uncertainty_s >= 0.5


def test_the_header_instant_is_CENTRED_not_taken_at_face_value():
    """`Date: 12:00:00` names the whole second beginning at 12:00:00. Anchoring at the left
    edge biases every stamp half a second early — always toward `elapsed` looking LARGER,
    i.e. toward evicting a live holder sooner."""
    mono = Mono()
    clock = _clock(mono, [DATE_HDR])
    stamped = dt.datetime.fromisoformat(clock())
    assert stamped == parse_http_date(DATE_HDR) + dt.timedelta(milliseconds=500)


def test_a_sample_whose_round_trip_blows_the_budget_is_discarded_and_retried():
    mono = Mono()
    rtts = [30.0, 0.2]

    def fetch():
        mono.advance(rtts.pop(0) if rtts else 0.2)
        return DATE_HDR

    clock = GitHubDateClock(fetch_date_header=fetch, monotonic=mono, max_sample_rtt_s=2.0)
    clock()
    assert not rtts, "the over-budget sample was accepted instead of retried"
    assert clock.sample_uncertainty_s <= 1.0


def test_a_clock_that_only_ever_samples_slowly_has_NO_trusted_time():
    mono = Mono()

    def fetch():
        mono.advance(30.0)
        return DATE_HDR

    clock = GitHubDateClock(fetch_date_header=fetch, monotonic=mono, max_sample_rtt_s=2.0)
    with pytest.raises(NoTrustedTimeError, match="round trip"):
        clock()


# ---- non-regression, and its bound ----


def test_emitted_time_never_moves_backward_across_a_refresh():
    # The authority itself steps BACKWARD by a minute (a load-balanced fleet with a
    # lagging node) — within tolerance, so it is absorbed rather than fatal. Emitted time
    # must not regress: the lane's durations would go negative.
    mono = Mono()
    # The third header is what makes this a STEPPED-BACK authority rather than a STOPPED
    # one: after the backward step it keeps ticking, so the next refresh reads a later
    # instant. A fake that repeats EARLIER_HDR forever models a clock that stopped, which
    # is a different fault with a different correct outcome — see
    # `test_an_authority_that_is_STUCK_fails_closed_once_the_stall_exceeds_the_tolerance`.
    recovered = "Fri, 31 Jul 2026 13:05:40 GMT"
    clock = _clock(mono, [DATE_HDR, EARLIER_HDR, recovered], refresh_interval_s=300)
    first = dt.datetime.fromisoformat(clock())
    mono.advance(400)
    second = dt.datetime.fromisoformat(clock())
    assert clock.fetch_count() == 2
    # Held at the floor, not advanced past it: the clamp is a floor on what was EMITTED,
    # and it is the only thing standing between a backward authority step and a negative
    # `since_beat`.
    assert second == first, f"authority time went backward: {first} -> {second}"
    # And the clamp RELEASES as soon as the authority is ahead of the floor again.
    mono.advance(4000)
    assert dt.datetime.fromisoformat(clock()) > second


def test_an_authority_that_is_STUCK_fails_closed_once_the_stall_exceeds_the_tolerance():
    """The magnitude bound alone does not cover this, and the gap is silent.

    An authority that keeps serving the SAME instant sits a CONSTANT distance behind the
    floor. It never trips the "moved too far backward" check, and every refresh re-anchors
    to the same stale value — so emitted time stands still indefinitely while every call
    still succeeds. Expiry stops approaching, hold time stops accruing, cooldowns stop
    maturing, and nothing raises. That is the "looks healthy and makes no progress" state
    the magnitude bound exists to prevent, reached by a route the magnitude bound cannot
    see, so the clamp is bounded in DURATION too."""
    mono = Mono()
    clock = _clock(mono, [DATE_HDR, EARLIER_HDR], refresh_interval_s=300)
    clock()
    mono.advance(400)
    assert clock()  # clamped, and legitimately so: 60 s is inside the tolerance
    mono.advance(MAX_CLOCK_REGRESSION_S + 1)
    with pytest.raises(NoTrustedTimeError, match="stood still"):
        clock()


def test_a_clamp_SHORTER_than_the_tolerance_is_absorbed_without_raising():
    """The complement: the duration bound must not turn an ordinary, brief clamp into a
    failure. A short stall is what the clamp is FOR.

    Note what sets the natural length of a clamp: the authority stepped back 60 s, so 60 s
    of monotonic elapsed carries the NEW anchor's extrapolation back past the floor and the
    clamp releases on its own. Advancing by less than that keeps it engaged, which is what
    this needs in order to observe a live clamp at all — advancing further would test the
    release, not the absorption."""
    mono = Mono()
    clock = _clock(mono, [DATE_HDR, EARLIER_HDR], refresh_interval_s=300)
    clock()
    mono.advance(400)
    held = dt.datetime.fromisoformat(clock())
    mono.advance(30)  # < the 60 s step, so still clamped; << the 300 s duration bound
    assert dt.datetime.fromisoformat(clock()) == held


def test_a_refresh_that_regresses_by_LESS_than_the_interval_is_still_clamped():
    """The case the 'a refresh only fires after 300 s, so small steps are absorbed'
    argument gets wrong. 300 s of elapsed time has already RAISED the emitted instant by
    300 s, so a new anchor must beat the old one plus 300 s — not merely the old one. A
    one-second backward step regresses emitted time, and only the floor stops it."""
    mono = Mono()
    clock = _clock(mono, [DATE_HDR, "Fri, 31 Jul 2026 11:59:59 GMT"],
                   refresh_interval_s=300)
    clock()
    mono.advance(299)
    mid = dt.datetime.fromisoformat(clock())  # still the first anchor: ~12:04:59.5
    assert clock.fetch_count() == 1
    mono.advance(2)
    after = dt.datetime.fromisoformat(clock())  # refresh: the authority is 1 s behind
    assert clock.fetch_count() == 2
    # Adopted naively, `after` would be ~11:59:59.5 — FIVE MINUTES behind `mid`, from an
    # authority that moved back by one second. Elapsed time since the new anchor is ~0.
    assert after == mid


def test_a_regression_PAST_THE_TOLERANCE_fails_closed_instead_of_freezing():
    """The clamp's own failure mode, bounded.

    While clamped, emitted time stands still — so expiry stops approaching, hold time
    stops accruing, and cooldowns stop maturing. That is the right trade for a small
    regression and the wrong one for a large one: an unbounded clamp turns an authority
    fault into a lane that looks healthy and makes no progress. Past the tolerance there
    is no trusted time, and FR-036 already says the run does no lane work."""
    mono = Mono()
    clock = _clock(mono, [LATER_HDR, DATE_HDR], refresh_interval_s=300)  # 1 h backward
    first = dt.datetime.fromisoformat(clock())
    mono.advance(400)
    with pytest.raises(NoTrustedTimeError, match="backward"):
        clock()
    # And it does not quietly recover from the poisoned sample: the next call re-samples.
    assert clock.fetch_count() == 2
    assert first is not None


def test_the_regression_tolerance_is_DERIVED_from_the_skew_allowance():
    from llmxive.self_improvement import policy

    assert clock_mod.MAX_CLOCK_REGRESSION_S == policy.MAX_CLOCK_SKEW_S
    src = Path(clock_mod.__file__).read_text()
    assert "MAX_CLOCK_REGRESSION_S = policy.MAX_CLOCK_SKEW_S" in src, (
        "the tolerance must be derived from the skew allowance, not written as a literal")


# ---- refresh scheduling + fail-closed ----


def test_refresh_scheduling_uses_monotonic_elapsed():
    mono = Mono()
    clock = _clock(mono, [DATE_HDR, LATER_HDR], refresh_interval_s=300)
    clock()
    mono.advance(299)
    clock()
    assert clock.fetch_count() == 1, "re-measured before the interval elapsed"
    mono.advance(2)
    clock()
    assert clock.fetch_count() == 2, "did not re-measure after the interval elapsed"


def test_the_module_never_reads_the_WALL_clock():
    """The design point the whole module rests on, asserted rather than trusted: an anchor
    re-derived from wall time inherits every wall-clock discontinuity, and a backward NTP
    step would move emitted authority time backward AND could suppress the refresh that
    would catch it."""
    src = Path(clock_mod.__file__).read_text()
    for forbidden in ("datetime.now", "utcnow", "time.time("):
        assert forbidden not in src, f"clock.py reads wall time via {forbidden!r}"


def test_a_clock_that_cannot_reach_the_authority_raises_and_never_falls_back():
    # The forbidden behavior is silently using the local clock: precisely the untrusted
    # input FR-036 exists to exclude.
    def boom():
        raise OSError("network down")

    with pytest.raises(NoTrustedTimeError):
        GitHubDateClock(fetch_date_header=boom, monotonic=Mono())()


def test_a_stale_anchor_is_not_reused_when_re_measurement_fails():
    mono = Mono()
    headers = [DATE_HDR]

    def fetch():
        if headers:
            return headers.pop()
        raise OSError("network down")

    clock = GitHubDateClock(fetch_date_header=fetch, monotonic=mono,
                            refresh_interval_s=300)
    assert clock().startswith("2026-07-31T12:00:00")
    mono.advance(400)
    with pytest.raises(NoTrustedTimeError):
        clock()  # refresh due, refresh failed -> no trusted time, NOT the stale anchor


# ---- the injectable real-logic double ----


def test_fixed_anchor_clock_is_a_real_implementation_not_a_stub():
    mono = Mono()
    clock = FixedAnchorClock(
        anchor=dt.datetime(2026, 7, 31, 12, 0, tzinfo=dt.UTC), monotonic=mono)
    assert clock().startswith("2026-07-31T12:00:00")
    mono.advance(90)
    assert clock().startswith("2026-07-31T12:01:30")
    assert clock.sample_uncertainty_s == 0.0


def test_both_clocks_satisfy_the_callable_contract_1A_entry_points_take():
    """`bind_attempt_config` and every other 1A entry point take `clock: Callable[[], str]`.
    Satisfying that exactly is what lets the authoritative clock drop in without a parallel
    time API (Constitution I)."""
    mono = Mono()
    fixed = FixedAnchorClock(
        anchor=dt.datetime(2026, 7, 31, 12, 0, tzinfo=dt.UTC), monotonic=mono)
    github = _clock(mono, [DATE_HDR])
    for clock in (fixed, github):
        stamped = clock()
        assert isinstance(stamped, str)
        assert dt.datetime.fromisoformat(stamped).tzinfo is not None
