"""Relative strength levels: track population, percentile cut-off, near-ties (spec 027 5.10, Task 12)."""

import random
from datetime import date, timedelta

import pytest

from llmxive.model_selection.policy import FUNDED_POLICY
from llmxive.model_selection.strength import (
    cutoff_index,
    level_qualifiers,
    publish_date_fresh,
    publish_date_invalid,
    repo_of,
    track_population,
)
from llmxive.model_selection.types import ArenaScore, ModelScores
from tests.helpers.funded import (
    CODING,
    FILLERS,
    PUBLISHED,
    REASONING,
    REPO_A,
    REPO_B,
    REPO_C,
    REPO_E,
)


def pop(table):
    return {repo: ArenaScore(*table[repo], PUBLISHED) for repo in table}


R, C_ = pop(REASONING), pop(CODING)
F = FILLERS


def test_repo_of_strips_the_provider_suffix():
    assert repo_of("acme/alpha-large:prov-a") == "acme/alpha-large"
    assert repo_of("acme/alpha-large") == "acme/alpha-large"


@pytest.mark.parametrize("n,pct,idx", [(20, 50, 9), (20, 30, 5), (20, 10, 1), (20, None, 0), (10, 30, 2), (1, 50, 0),
    (63, 50, 31), (63, 30, 18), (63, 10, 6), (3, 10, 0), (0, 50, 0),
    (2, 50, 0), (2, 30, 0), (2, 10, 0), (9, 50, 4), (9, 30, 2), (9, 10, 0), (11, 50, 5), (11, 30, 3), (11, 10, 1)])
def test_cutoff_index_is_integer_arithmetic(n, pct, idx):
    # (10, 30) -> 2: the cut-off is the ceil(30 * 10 / 100) = 3rd model, index 3 - 1 = 2;
    # dropping the "- 1" would wrongly give index 3.
    assert cutoff_index(n, pct) == idx


def test_level_qualifiers_on_the_reasoning_table():                   # near-ties at the boundary qualify (>=)
    def q(lvl):
        return level_qualifiers(R, lvl, FUNDED_POLICY)
    assert q("strongest") == {REPO_A, REPO_E}                         # E's upper 1400 >= A's lower 1395
    assert q("strong") == {REPO_A, REPO_E, F[0]}                      # F01 upper 1381 >= E lower 1380
    assert q("balanced") == {REPO_A, REPO_E, F[0], F[1], F[2], REPO_C, F[3]}    # F04 upper 1335 == C lower 1335
    assert q("economy") == q("balanced") | {F[4], F[5], REPO_B, F[6]}           # F07 upper 1295 == B lower 1295


def test_level_qualifiers_on_the_coding_table():
    def q(lvl):
        return level_qualifiers(C_, lvl, FUNDED_POLICY)
    assert q("strongest") == {REPO_B} and q("strong") == {REPO_B, REPO_A}
    assert q("balanced") == {REPO_B, REPO_A, *F[:5]} and q("economy") == {REPO_B, REPO_A, *F[:9]}


WEAKEST_FIRST = ("economy", "balanced", "strong", "strongest")


def _assert_nested(p):
    s = [level_qualifiers(p, lvl, FUNDED_POLICY) for lvl in WEAKEST_FIRST]
    assert s[3] <= s[2] <= s[1] <= s[0], s


def _constructed_tables():
    """Deterministic synthetic populations: assorted sizes, ties, zero-width and very
    wide intervals (including a top model whose interval swallows the whole table)."""
    rng = random.Random(20261123)
    tables = [R, C_]
    for n in (1, 2, 3, 5, 9, 10, 11, 20, 37, 63):
        for _ in range(6):
            t = {}
            for i in range(n):
                rating = float(rng.choice([rng.randint(1000, 1500), 1200]))      # some exact rating ties
                below, above = rng.choice([(0.0, 0.0), (5.0, 5.0), (rng.uniform(0, 300), rng.uniform(0, 300))])
                t[f"x/m{i:02d}"] = ArenaScore(rating, rating - below, rating + above, PUBLISHED)
            tables.append(t)
    return tables


@pytest.mark.parametrize("table", _constructed_tables())
def test_levels_nest(table):
    _assert_nested(table)


def test_a_wide_top_interval_cannot_make_strongest_admit_what_strong_rejects():
    # The top model's interval is so wide that its rating_lower (1100) is far below the
    # strong cut-off's rating_lower (1394, index 1 of 20). Under the un-nested rule
    # strongest would admit every model with rating_upper >= 1100, i.e. all 20.
    t = {"x/top": ArenaScore(1400.0, 1100.0, 1500.0, PUBLISHED),
         **{f"x/m{i:02d}": ArenaScore(1399.0 - 10 * i, 1394.0 - 10 * i, 1404.0 - 10 * i, PUBLISHED) for i in range(19)}}
    strongest, strong = (level_qualifiers(t, lvl, FUNDED_POLICY) for lvl in ("strongest", "strong"))
    assert t["x/top"].rating_lower < t["x/m00"].rating_lower                # the triggering condition
    assert strongest <= strong
    assert strongest == strong == {"x/top", "x/m00", "x/m01"}            # m01 upper 1394 >= 1394; m02 1384 is not
    assert "x/m10" not in strongest
    _assert_nested(t)


def test_zero_width_interval_and_rating_ties_are_deterministic():
    p = {"x/a": ArenaScore(1000.0, 1000.0, 1000.0, PUBLISHED), "x/b": ArenaScore(1000.0, 1000.0, 1000.0, PUBLISHED),
         "x/c": ArenaScore(999.0, 999.0, 999.0, PUBLISHED)}
    assert level_qualifiers(p, "strongest", FUNDED_POLICY) == {"x/a", "x/b"}
    assert level_qualifiers({}, "economy", FUNDED_POLICY) == frozenset()


def test_track_population_drops_stale_rows_and_other_tracks():
    def s(d):
        return ArenaScore(1300.0, 1290.0, 1310.0, d)
    scores = {"acme/a:p1": ModelScores(reasoning=s(date(2026, 11, 16))), "acme/a:p2": ModelScores(reasoning=s(date(2026, 11, 16))),
              "acme/b:p1": ModelScores(reasoning=s(date(2026, 11, 15))), "acme/d:p1": ModelScores(coding=s(PUBLISHED))}
    got = track_population(scores, "reasoning", today=date(2026, 11, 23), max_publish_age_days=7)
    assert set(got) == {"acme/a"}                                     # 7 days old is in, 8 is out, coding-only is out
    assert got["acme/a"] == s(date(2026, 11, 16))


@pytest.mark.parametrize("ahead,kept", [(0, True), (1, True), (2, False)])
def test_a_publish_date_more_than_one_day_ahead_is_invalid(ahead, kept):
    today = date(2026, 11, 23)
    assert publish_date_fresh(today + timedelta(days=ahead), today=today, max_publish_age_days=7) is kept
    assert publish_date_invalid(today + timedelta(days=ahead), today=today) is not kept
    scores = {"acme/a:p1": ModelScores(reasoning=ArenaScore(1300.0, 1290.0, 1310.0, today + timedelta(days=ahead))),
              "acme/b:p1": ModelScores(reasoning=ArenaScore(1200.0, 1190.0, 1210.0, today))}
    got = track_population(scores, "reasoning", today=today, max_publish_age_days=7)
    assert set(got) == ({"acme/a", "acme/b"} if kept else set())     # one invalid row: nobody qualifies
    assert level_qualifiers(got, "economy", FUNDED_POLICY) == ({"acme/a"} if kept else frozenset())
    # an invalid row on the OTHER track does not touch this track
    other = {**scores, "acme/c:p1": ModelScores(coding=ArenaScore(1.0, 1.0, 1.0, today + timedelta(days=9)))}
    assert track_population(other, "reasoning", today=today, max_publish_age_days=7) == got


def test_cutoff_index_avoids_float_rounding():                        # float ceil(0.07 * 100) is 8
    assert cutoff_index(100, 7) == 6


def test_track_population_rejects_conflicting_scores_for_one_repo():
    scores = {"acme/a:p1": ModelScores(reasoning=ArenaScore(1300.0, 1290.0, 1310.0, PUBLISHED)),
              "acme/a:p2": ModelScores(reasoning=ArenaScore(1301.0, 1290.0, 1310.0, PUBLISHED))}
    with pytest.raises(ValueError, match="conflicting reasoning scores"):
        track_population(scores, "reasoning", today=PUBLISHED, max_publish_age_days=7)
