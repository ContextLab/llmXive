"""FR-036: authoritative time. Lane runs execute on independent GitHub runners with
independent clocks, and every bound the lane enforces (heartbeat renewal, ``claim_expiry``,
``max_claim_hold_time``, ``streak_started_at``, ``cooldown_until``) is a DURATION. Comparing
runners' timestamps therefore requires one clock they share.

Rev 21 tried to validate a timestamp against "the appending process's own clock" — the same
process that generated it, so the comparison is vacuous — and to reject anything trailing
the ref's latest, which let one fast-skewed runner poison the ref and reject correctly-timed
runners indefinitely. Both are withdrawn. The authority here is GitHub's server clock, which
every lane run can already reach because the lane is GitHub-native.

**The local WALL clock is never read.** An anchor is fixed against ``time.monotonic()`` and
every later instant is that anchor plus monotonic elapsed, so a system-clock adjustment —
an NTP step, a resumed VM, a manual correction — can neither move emitted time backward nor
suppress a refresh. The anchor's own uncertainty is measured rather than assumed: the
request is bracketed, the instant is taken at the round-trip midpoint, and a sample whose
round trip exceeds ``max_sample_rtt_s`` is discarded rather than trusted.

``seq`` remains the SOLE ordering authority (FR-009). Nothing here orders events."""

from __future__ import annotations

import datetime as dt
import email.utils
import os
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from llmxive.self_improvement import policy

#: Read from an AUTHENTICATED response; ``/rate_limit`` is documented as not counting
#: against the rate limit, so a run that has not yet called the API pays nothing for it.
#: The request is never made unauthenticated — see `_github_token`.
RATE_LIMIT_URL = "https://api.github.com/rate_limit"

#: Policy Contract: re-measure each ``heartbeat_interval`` so a long run cannot drift. The
#: interval IS the heartbeat interval — imported, not restated, because a Policy Contract
#: value written down twice is a Policy Contract with two answers (Constitution I).
DEFAULT_REFRESH_INTERVAL_S = policy.HEARTBEAT_INTERVAL_S

#: Policy Contract ``max_sample_rtt``. A slower round trip means the midpoint estimate is
#: wider than the lane's safety margin can absorb, so the sample is worthless, not merely
#: imprecise.
DEFAULT_MAX_SAMPLE_RTT_S = float(policy.MAX_SAMPLE_RTT_S)

#: Attempts to land a sample inside the RTT budget before declaring no trusted time.
_SAMPLE_ATTEMPTS = 3

#: An RFC 7231 ``Date`` is whole seconds, so a header naming second N was true at or after
#: N and strictly before N + 1. That is a real uncertainty the anchor inherits no matter how
#: fast the round trip was, and it is the FLOOR on `sample_uncertainty_s` — a lane that
#: treated a 5 ms round trip as ±2.5 ms would be claiming a precision the wire format cannot
#: express.
_HTTP_DATE_RESOLUTION_S = 1.0

#: Centre of that interval. Added to the parsed header so the estimate is unbiased; without
#: it every anchor sits half a second EARLY, which biases toward evicting sooner.
_HTTP_DATE_CENTRE = dt.timedelta(seconds=_HTTP_DATE_RESOLUTION_S / 2)

#: How far the authority may move BACKWARD before the clock stops clamping and fails
#: closed. DERIVED from the skew allowance, not chosen: `max_clock_skew` is already the
#: disagreement the lane tolerates between two clocks, and a clamp of at most that long is
#: absorbed by the same padding every bound is computed with (`elapsed >= claim_expiry +
#: max_clock_skew`). A regression larger than the lane's own tolerance is not imprecision
#: to absorb — it is an authority fault, and freezing lane time behind it would stall
#: expiry, hold time and cooldown maturation for as long as the fault lasted.
MAX_CLOCK_REGRESSION_S = policy.MAX_CLOCK_SKEW_S


class NoTrustedTimeError(RuntimeError):
    """No authority-derived instant is available, so the run performs NO lane work.

    Deliberately fatal rather than degrading to the local clock: a silently-wrong anchor
    poisons every duration the lane derives, and the failure mode is EVICTING A LIVE
    CLAIM-HOLDER. A run that cannot establish time needs no special recovery — the claim it
    does not take cannot wedge, and a claim it already holds is recovered by ordinary
    expiry. Total loss of trusted time therefore PREVENTS reclaim; it never licenses a
    fallback liveness signal, because ``seq`` can show that a beat happened but not that an
    expected one is missing."""


class AuthoritativeClock(Protocol):
    """Satisfies the ``clock: Callable[[], str]`` contract every 1A entry point already
    takes, so this drops in without a parallel time API (Constitution I)."""

    def __call__(self) -> str: ...

    @property
    def sample_uncertainty_s(self) -> float:
        """Half the round trip of the anchoring sample. The reclaimer ADDS this to
        ``max_clock_skew`` so imprecision always pads toward not evicting a live holder."""


@dataclass(frozen=True)
class TimeSample:
    """An authority instant, the monotonic reading it is anchored to, and how wide the
    estimate is. Immutable so a refresh REPLACES the sample rather than mutating half of
    it — a torn update would pair a new instant with an old anchor."""

    instant: dt.datetime
    monotonic_at: float
    uncertainty_s: float


def parse_http_date(raw: str) -> dt.datetime:
    """Parse an RFC 7231 ``Date`` header into an aware UTC instant, or raise.

    Fails closed on anything unparseable: a header we cannot read is not a weaker
    authority, it is NO authority."""
    try:
        parsed = email.utils.parsedate_to_datetime(raw) if raw else None
    except (TypeError, ValueError):
        parsed = None
    if parsed is None:
        raise NoTrustedTimeError(f"unparseable Date header: {raw!r}")
    if parsed.tzinfo is None:
        # `-0000` parses to a NAIVE datetime, which would be read as local time on the way
        # to UTC — a silent offset of however far this runner sits from Greenwich.
        raise NoTrustedTimeError(f"Date header carries no usable offset: {raw!r}")
    return parsed.astimezone(dt.UTC)


def _github_token() -> str:
    """The token the time authority is read UNDER. No token, no trusted time.

    Maintainer decision (2026-08-02, open question 1): the clock is safety-critical — its
    output decides whether a live claim-holder is evicted — so it may not depend on the
    unauthenticated 60/hr per-IP allowance, which a busy shared runner can exhaust and
    which any other tenant of that IP can exhaust FOR us. An exhausted allowance would not
    look like an outage; it would look like a run with no time, at an unpredictable
    moment. FR-036 already says no trusted time ⇒ no lane work, so requiring the token is
    not a new failure mode, it is the existing one made deterministic.

    Offline and local work injects `FixedAnchorClock` instead — a real-logic double, not a
    mock — so nothing needs an unauthenticated escape hatch."""
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        token = os.environ.get(name)
        if token:
            return token
    raise NoTrustedTimeError(
        "no GITHUB_TOKEN/GH_TOKEN: the time authority must be read under an authenticated "
        "request, and a run that cannot establish trusted time performs NO lane work "
        "(FR-036). Inject FixedAnchorClock for offline or local runs.")


def _default_fetch() -> str:
    request = urllib.request.Request(
        RATE_LIMIT_URL,
        headers={"Authorization": f"Bearer {_github_token()}",
                 "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=10) as resp:
        header = resp.headers.get("Date")
    if not header:
        raise NoTrustedTimeError(f"{RATE_LIMIT_URL} returned no Date header")
    return header


class GitHubDateClock:
    """Authority-derived instants, anchored by a bracketed sample and extrapolated with a
    MONOTONIC source.

    Sampling an anchor (rather than fetching per event) keeps the clock cheap while still
    tracking real elapsed time: the monotonic source measures the interval, the authority
    fixes the origin. Because the monotonic source cannot jump, emitted time is monotonic
    by construction — the property the whole lane's duration arithmetic assumes."""

    def __init__(self, *, fetch_date_header: Callable[[], str] | None = None,
                 monotonic: Callable[[], float] | None = None,
                 refresh_interval_s: int = DEFAULT_REFRESH_INTERVAL_S,
                 max_sample_rtt_s: float = DEFAULT_MAX_SAMPLE_RTT_S) -> None:
        self._fetch = fetch_date_header or _default_fetch
        self._monotonic = monotonic or time.monotonic
        self._refresh_interval_s = refresh_interval_s
        self._max_sample_rtt_s = max_sample_rtt_s
        self._sample: TimeSample | None = None
        #: The highest instant this clock has EMITTED. Not the highest sampled: what the
        #: rest of the lane must never see decrease is what it was told.
        self._floor: dt.datetime | None = None
        #: The monotonic reading at which the clamp last ENGAGED, or None while emitted
        #: time is tracking the authority normally. See `_now` for why a clamp needs a
        #: duration bound and not only a magnitude bound.
        self._clamped_since: float | None = None

    @property
    def sample_uncertainty_s(self) -> float:
        """0.0 only before the first sample — and no lane work happens before then, because
        every entry point stamps a time first. After sampling this is never 0: the header's
        one-second resolution alone contributes 0.5 s."""
        return 0.0 if self._sample is None else self._sample.uncertainty_s

    def _take_sample(self) -> TimeSample:
        """One bracketed measurement, retried while the round trip is over budget.

        The stale sample is dropped BEFORE the attempt: "we had time once" is not "we have
        time now", and keeping it would let a failed refresh extrapolate indefinitely from
        an anchor the lane can no longer confirm."""
        self._sample = None
        last = ""
        for _ in range(_SAMPLE_ATTEMPTS):
            start = self._monotonic()
            try:
                header = self._fetch()
            except NoTrustedTimeError:
                raise
            except Exception as exc:  # network, HTTP, DNS — all mean the same thing here
                raise NoTrustedTimeError(
                    f"could not reach the time authority: {exc}") from exc
            end = self._monotonic()
            rtt = end - start
            if rtt > self._max_sample_rtt_s:
                last = (f"round trip {rtt:.3f}s exceeds max_sample_rtt "
                        f"{self._max_sample_rtt_s}s")
                continue
            # Two independent uncertainties, and both are charged.
            #
            # (1) The header was true somewhere inside [start, end]; the midpoint is the
            #     least-wrong estimate and is off by at most rtt/2 BY CONSTRUCTION.
            # (2) An RFC 7231 `Date` is WHOLE SECONDS, so "12:00:03" means the real instant
            #     lay at or after 03.0 and strictly before 04.0. The centre of that
            #     interval is +0.5 s and the half-width is 0.5 s. Taking the header at face
            #     value would bias every anchor 0.5 s early and understate the error —
            #     small, but it is a bias in the direction of evicting sooner, which is the
            #     one direction FR-036 forbids.
            return TimeSample(
                instant=parse_http_date(header) + _HTTP_DATE_CENTRE,
                monotonic_at=(start + end) / 2,
                uncertainty_s=rtt / 2 + _HTTP_DATE_RESOLUTION_S / 2,
            )
        raise NoTrustedTimeError(
            f"no sample inside the budget after {_SAMPLE_ATTEMPTS} attempts: {last}")

    def _now(self) -> dt.datetime:
        sample = self._sample
        if sample is None or (
            self._monotonic() - sample.monotonic_at
        ) > self._refresh_interval_s:
            sample = self._sample = self._take_sample()
        instant = sample.instant + dt.timedelta(
            seconds=self._monotonic() - sample.monotonic_at)
        # NON-REGRESSING ACROSS REFRESHES, but only up to a BOUND. Within one anchor the
        # monotonic source already guarantees this. Across anchors it does not: a fresh
        # sample is a new measurement of a remote clock, and an authority that moved
        # backward — or simply a sample whose error landed on the other side — installs an
        # origin behind the one already emitted.
        #
        # Clamping is right for a SMALL regression and wrong for a large one. While
        # clamped, emitted time stands still, so every duration the lane derives stands
        # still with it: expiry stops approaching, hold time stops accruing, cooldowns stop
        # maturing. An unbounded clamp therefore converts an authority fault into a
        # silently frozen lane, which is worse than the regression — the lane would look
        # healthy and make no progress. Past the bound this is not a clock with imprecision,
        # it is no trusted time, and FR-036 already says what to do about that.
        if self._floor is not None and instant < self._floor:
            behind = (self._floor - instant).total_seconds()
            if behind > MAX_CLOCK_REGRESSION_S:
                self._sample = None
                self._clamped_since = None
                raise NoTrustedTimeError(
                    f"the authority moved {behind:.1f}s backward, past the "
                    f"{MAX_CLOCK_REGRESSION_S}s tolerance — refusing to freeze lane time "
                    "behind a clock that cannot be trusted")
            # The clamp is bounded in DURATION as well as in magnitude, and the duration
            # is the bound the design's own argument actually needs. A magnitude bound
            # alone does not catch a STUCK authority: one that keeps serving the same
            # instant sits a CONSTANT distance behind the floor, never trips the size
            # check, and re-anchors to the same stale value on every refresh — so emitted
            # time stands still indefinitely while every call still succeeds. That is
            # exactly the "looks healthy and makes no progress" state the magnitude bound
            # was introduced to prevent, reached by a different route: standing still for
            # longer than the lane's own skew allowance is indistinguishable, from every
            # consumer's point of view, from having no time at all.
            now_mono = self._monotonic()
            if self._clamped_since is None:
                self._clamped_since = now_mono
            elif now_mono - self._clamped_since > MAX_CLOCK_REGRESSION_S:
                stalled = now_mono - self._clamped_since
                self._sample = None
                self._clamped_since = None
                raise NoTrustedTimeError(
                    f"emitted time has stood still for {stalled:.1f}s — longer than the "
                    f"{MAX_CLOCK_REGRESSION_S}s tolerance — because the authority is not "
                    "advancing; a lane whose durations never grow makes no progress while "
                    "appearing healthy")
            return self._floor
        self._clamped_since = None
        self._floor = instant
        return instant

    def __call__(self) -> str:
        return self._now().isoformat()


class FixedAnchorClock:
    """A REAL clock anchored to a known instant — for tests and for a runner whose anchor
    was established elsewhere. Not a stub: it runs the SAME extrapolation as
    :class:`GitHubDateClock`, it simply never fetches."""

    def __init__(self, *, anchor: dt.datetime,
                 monotonic: Callable[[], float] | None = None) -> None:
        self._monotonic = monotonic or time.monotonic
        self._sample = TimeSample(instant=anchor, monotonic_at=self._monotonic(),
                                  uncertainty_s=0.0)

    @property
    def sample_uncertainty_s(self) -> float:
        return 0.0

    def __call__(self) -> str:
        elapsed = self._monotonic() - self._sample.monotonic_at
        return (self._sample.instant + dt.timedelta(seconds=elapsed)).isoformat()


__all__ = [
    "DEFAULT_MAX_SAMPLE_RTT_S",
    "DEFAULT_REFRESH_INTERVAL_S",
    "MAX_CLOCK_REGRESSION_S",
    "RATE_LIMIT_URL",
    "AuthoritativeClock",
    "FixedAnchorClock",
    "GitHubDateClock",
    "NoTrustedTimeError",
    "TimeSample",
    "parse_http_date",
]
