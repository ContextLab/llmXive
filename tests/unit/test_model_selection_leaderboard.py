"""LMArena leaderboard: real local HTTP paging, parsing and strict name matching."""

import json
from datetime import date
from pathlib import Path

import pytest

from llmxive.model_selection import leaderboard
from llmxive.model_selection.leaderboard import (
    TRACK_CATEGORY,
    LeaderboardError,
    fetch_arena_category,
    fetch_arena_scores,
    join_scores,
    normalise_name,
    normalise_repo,
    parse_arena_rows,
)
from llmxive.model_selection.types import ArenaScore, ModelScores
from tests.helpers.replay_server import ReplayServer

_FIX = Path(__file__).parents[1] / "fixtures" / "hf_funded"
D = date(2026, 11, 22)


def _load(name):
    return json.loads((_FIX / name).read_text())


@pytest.fixture(autouse=True)
def _fast_retry(monkeypatch):
    monkeypatch.setattr(leaderboard, "RETRY_BACKOFF_SECONDS", 0.0)


def _row(name, rating, category="overall", lower="same", upper="same", published="2026-11-22"):
    return {
        "model_name": name, "organization": "x", "license": "y", "rating": rating,
        "rating_lower": rating if lower == "same" else lower,
        "rating_upper": rating if upper == "same" else upper,
        "variance": 1.0, "vote_count": 100.0, "rank": 1.0, "category": category,
        "leaderboard_publish_date": published,
    }


@pytest.mark.parametrize(
    "raw,norm",
    [
        ("Gemini 4 Carbon (High)", "gemini4carbon"),
        ("gpt-oss-120b", "gptoss120b"),
        ("Claude Opus 4.6", "claudeopus46"),
        ("DeepSeek-V3.2 (thinking) (beta) ", "deepseekv32"),
        ("  ", ""),
    ],
)
def test_normalise_name(raw, norm):
    assert normalise_name(raw) == norm


def test_normalise_repo_uses_the_part_after_the_org():
    assert normalise_repo("openai/gpt-oss-120b") == "gptoss120b" == normalise_name("gpt-oss-120b")


def test_parse_rows_highest_variant_wins_bounds_default_and_bad_rows_drop():
    rows = [
        _row("Alpha Large (High)", 1300.0, lower=1290.0, upper=1310.0),
        _row("Alpha Large", 1250.0),
        _row("Beta Mini", 1200.0, lower=None, upper=None),
        _row("Gamma", None),
        _row("Delta", 1100.0, lower=1120.0, upper=1130.0),
        _row("Eps", 1000.0, published="yesterday"),
        _row("(only a group)", 900.0),
        _row("Inf", float("inf")),
    ]
    got = parse_arena_rows(rows, category="overall")
    assert got == {
        "alphalarge": ArenaScore(1300.0, 1290.0, 1310.0, D),
        "betamini": ArenaScore(1200.0, 1200.0, 1200.0, D),
    }
    with pytest.raises(LeaderboardError):
        parse_arena_rows([_row("Z", 1.0, category="coding")], category="overall")


def test_join_matches_by_normalised_repo_name_and_drops_ambiguous():
    s1, s2, s3 = (ArenaScore(r, r, r, D) for r in (1300.0, 1500.0, 1250.0))
    arena = {"reasoning": {"alphalarge": s1, "zetadup": s2}, "coding": {"alphalarge": s3}}
    scores, ambiguous = join_scores(
        ["acme/alpha-large", "acme/zeta-dup", "other-lab/zeta-dup", "acme/unlisted"], arena
    )
    assert scores == {"acme/alpha-large": ModelScores(reasoning=s1, coding=s3)}
    assert ambiguous == ("zetadup",)


def test_join_ignores_shared_names_the_arena_does_not_list():
    arena = {"reasoning": {}, "coding": {}}
    assert join_scores(["a/same", "b/same"], arena) == ({}, ())


def _split_idx(n):
    """Realistic whole-split index of the n-th filtered row: starts at 505, irregular gaps."""
    return 505 + 2 * n + n // 7


def _pager(rows, *, total=None, stop_after=None):
    def respond(req):
        off, ln = int(req["query"]["offset"]), int(req["query"]["length"])
        page = [] if stop_after is not None and off >= stop_after else rows[off:off + ln]
        return 200, {
            "features": [],
            # filtered query: row_idx indexes the whole split (starts mid-way, has gaps)
            "rows": [{"row_idx": _split_idx(off + i), "row": r, "truncated_cells": []} for i, r in enumerate(page)],
            "num_rows_total": len(rows) if total is None else total,
            "num_rows_per_page": 100,
            "partial": False,
        }

    return respond


def test_fetch_pages_until_num_rows_total_without_a_key():
    rows = [_row(f"M{i}", 1000.0 + i, "coding") for i in range(250)]
    with ReplayServer({("GET", "/filter"): _pager(rows)}) as srv:
        got = fetch_arena_category("coding", base_url=srv.base_url + "/filter")
    assert got == rows and [r["query"]["offset"] for r in srv.requests] == ["0", "100", "200"]
    q = srv.requests[0]["query"]
    assert (q["dataset"], q["config"], q["split"], q["where"], q["length"]) == (
        "lmarena-ai/leaderboard-dataset", "text", "latest", "\"category\"='coding'", "100")
    assert all("authorization" not in r["headers"] for r in srv.requests)


def test_short_or_inconsistent_paging_fails_closed():
    rows = [_row(f"M{i}", 1000.0 + i, "coding") for i in range(250)]
    for route in (
        _pager(rows, stop_after=100),
        lambda req: (500, {"error": "x"}),
        lambda req: (422, {"error": "length too large"}),
        lambda req: (200, {"rows": [], "num_rows_total": 5, "partial": True}),
        lambda req: (200, {"rows": []}),
        lambda req: (200, b"not json"),
    ):
        with ReplayServer({("GET", "/filter"): route}) as srv:
            with pytest.raises(LeaderboardError):
                fetch_arena_category("coding", base_url=srv.base_url + "/filter")


def _envelope(rows, start, total):
    return 200, {
        "rows": [{"row_idx": _split_idx(start + i), "row": r, "truncated_cells": []} for i, r in enumerate(rows)],
        "num_rows_total": total, "partial": False,
    }


def test_filtered_numbering_with_gaps_passes_but_non_integer_or_backwards_idx_fails():
    rows = [_row(f"M{i}", 1000.0 + i, "coding") for i in range(120)]
    with ReplayServer({("GET", "/filter"): _pager(rows)}) as srv:
        assert fetch_arena_category("coding", base_url=srv.base_url + "/filter") == rows
    def bad(idx_for):
        def route(req):
            status, body = _pager(rows)(req)
            for i, item in enumerate(body["rows"]):
                item["row_idx"] = idx_for(int(req["query"]["offset"]) + i)
            return status, body
        return route
    for idx_for in (lambda n: "x", lambda n: None, lambda n: 1000 - n):
        with ReplayServer({("GET", "/filter"): bad(idx_for)}) as srv:
            with pytest.raises(LeaderboardError):
                fetch_arena_category("coding", base_url=srv.base_url + "/filter")


def test_inconsistent_pages_fail_closed():
    rows = [_row(f"M{i}", 1000.0 + i, "coding") for i in range(250)]
    good = _pager(rows)

    def changing_total(req):
        status, body = good(req)
        if req["query"]["offset"] != "0":
            body["num_rows_total"] = 251
        return status, body

    def repeated_page(req):  # the server ignores offset
        return _envelope(rows[:100], 0, 250)

    def oversized(req):
        return _envelope(rows[:101], int(req["query"]["offset"]), 250)

    def overshoot(req):  # pages deliver more rows than the total says
        return _envelope(rows[:100], int(req["query"]["offset"]), 50)

    for route in (changing_total, repeated_page, oversized, overshoot, lambda req: _envelope([], 0, 0)):
        with ReplayServer({("GET", "/filter"): route}) as srv:
            with pytest.raises(LeaderboardError):
                fetch_arena_category("coding", base_url=srv.base_url + "/filter")
    with ReplayServer({("GET", "/filter"): lambda req: _envelope([], 0, 0)}) as srv:
        with pytest.raises(LeaderboardError, match="empty"):
            fetch_arena_category("coding", base_url=srv.base_url + "/filter")
        assert fetch_arena_scores(base_url=srv.base_url + "/filter") is None


def test_row_missing_category_fails_closed():
    row = _row("M", 1000.0)
    del row["category"]
    with pytest.raises(LeaderboardError):
        parse_arena_rows([row], category="overall")


def test_transient_5xx_is_retried_then_succeeds_and_persistent_5xx_is_bounded():
    rows = [_row("M0", 1000.0, "coding")]
    ok = _pager(rows)
    with ReplayServer({("GET", "/filter"): [(502, {}), (500, {}), (200, ok({"query": {"offset": "0", "length": "100"}})[1])]}) as srv:
        assert fetch_arena_category("coding", base_url=srv.base_url + "/filter") == rows
        assert len(srv.requests) == 3
    with ReplayServer({("GET", "/filter"): [(503, {})]}) as srv:
        with pytest.raises(LeaderboardError, match="unavailable"):
            fetch_arena_category("coding", base_url=srv.base_url + "/filter")
        assert len(srv.requests) == leaderboard.MAX_RETRIES + 1
    with ReplayServer({("GET", "/filter"): [(422, {})]}) as srv:
        with pytest.raises(LeaderboardError):
            fetch_arena_category("coding", base_url=srv.base_url + "/filter")
        assert len(srv.requests) == 1  # a 4xx is not retried


def test_fetch_arena_scores_maps_categories_to_tracks_and_returns_none_on_failure():
    by_cat = {"overall": [_row("Alpha Large", 1300.0)], "coding": [_row("Alpha Large", 1250.0, "coding")]}

    def route(req):
        return _pager(by_cat["coding" if "coding" in req["query"]["where"] else "overall"])(req)

    with ReplayServer({("GET", "/filter"): route}) as srv:
        got = fetch_arena_scores(base_url=srv.base_url + "/filter")
    assert got["reasoning"]["alphalarge"].rating == 1300.0 and got["coding"]["alphalarge"].rating == 1250.0
    with ReplayServer({("GET", "/filter"): lambda req: (503, {})}) as srv:
        assert fetch_arena_scores(base_url=srv.base_url + "/filter") is None
    assert fetch_arena_scores(base_url="http://127.0.0.1:9/filter") is None  # connection refused


def test_recorded_fixtures_join_to_the_recorded_catalog():
    repos = {m["id"] for m in _load("router_models.json")["payload"]["data"]}
    arena = {
        t: parse_arena_rows(_load(f"lmarena_text_{c}.json")["payload"]["rows"], category=c)
        for t, c in TRACK_CATEGORY.items()
    }
    scores, ambiguous = join_scores(repos, arena)
    assert sum(s.reasoning is not None for s in scores.values()) >= 50
    assert sum(s.coding is not None for s in scores.values()) >= 50
    assert ambiguous == ()
