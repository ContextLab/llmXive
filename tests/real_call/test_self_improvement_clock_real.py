"""The authority is real: GitHub actually serves a usable Date header (Constitution III).

These are the tests that would catch a policy value chosen against an imagined network
rather than the one the lane runs on.
"""

from __future__ import annotations

import datetime as dt
import os

import pytest

from llmxive.self_improvement.clock import (
    GitHubDateClock,
    NoTrustedTimeError,
    parse_http_date,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1", reason="real-call suite")


def _clock() -> GitHubDateClock:
    """A clock against the live authority. Skips — rather than fails — without a token,
    because "no token" is a missing precondition for this suite, not a defect in the
    clock; the OFFLINE suite is where the no-token path is asserted to fail closed."""
    if not (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")):
        pytest.skip("needs GITHUB_TOKEN/GH_TOKEN: the authority is read authenticated")
    return GitHubDateClock()


def test_github_serves_a_parseable_date_header_close_to_local_time():
    stamped = dt.datetime.fromisoformat(_clock()())
    assert stamped.tzinfo is not None
    drift = abs((stamped - dt.datetime.now(dt.UTC)).total_seconds())
    # 5 min is max_clock_skew: if a healthy developer machine exceeds it against the real
    # authority, the policy value is wrong and this test is the place to find out.
    assert drift < 300, f"local clock differs from GitHub by {drift}s"


def test_a_real_round_trip_fits_inside_the_sampling_budget():
    # The 2 s max_sample_rtt is only a safe bound if real samples clear it comfortably.
    # The floor here is 0.5 s (the header's whole-second resolution) no matter how fast the
    # network is, so anything under 1.0 s means the round trip contributed under 0.5 s.
    clock = _clock()
    clock()
    assert 0.5 <= clock.sample_uncertainty_s < 1.0, (
        f"real GitHub round trip gave +/-{clock.sample_uncertainty_s}s of uncertainty")


def test_the_raw_header_is_what_we_think_it_is():
    raw = _clock()._fetch()
    assert parse_http_date(raw).tzinfo == dt.UTC


def test_an_UNAUTHENTICATED_run_has_no_trusted_time_against_the_REAL_authority(monkeypatch):
    """The offline suite proves the code refuses without a token. This proves the refusal
    is not hiding a working unauthenticated path — against the real endpoint, with the
    token removed, the clock must still raise rather than quietly succeed."""
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(NoTrustedTimeError, match="GITHUB_TOKEN"):
        GitHubDateClock()()
