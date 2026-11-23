"""Relative strength levels: track population, percentile cut-off, near-ties (spec 027 5.10, Task 12)."""

from datetime import date

import pytest

from llmxive.model_selection.policy import FUNDED_POLICY
from llmxive.model_selection.strength import (
    cutoff_index,
    level_qualifiers,
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
    (63, 50, 31), (63, 30, 18), (63, 10, 6), (3, 10, 0), (0, 50, 0)])
def test_cutoff_index_is_integer_arithmetic(n, pct, idx):            # Review Focus 2: ceil(0.3*10) would give 3, not 2
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


def test_levels_nest_on_both_tables():
    for p in (R, C_):
        s = [level_qualifiers(p, lvl, FUNDED_POLICY) for lvl in ("strongest", "strong", "balanced", "economy")]
        assert s[0] <= s[1] <= s[2] <= s[3]


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


def test_cutoff_index_avoids_float_rounding():                        # float ceil(0.07 * 100) is 8
    assert cutoff_index(100, 7) == 6


def test_track_population_rejects_conflicting_scores_for_one_repo():
    scores = {"acme/a:p1": ModelScores(reasoning=ArenaScore(1300.0, 1290.0, 1310.0, PUBLISHED)),
              "acme/a:p2": ModelScores(reasoning=ArenaScore(1301.0, 1290.0, 1310.0, PUBLISHED))}
    with pytest.raises(ValueError, match="conflicting reasoning scores"):
        track_population(scores, "reasoning", today=PUBLISHED, max_publish_age_days=7)
