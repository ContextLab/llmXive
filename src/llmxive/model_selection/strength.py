"""Relative strength levels for funded selection (spec 027, section 5.10).

Pure arithmetic, no I/O and no clock (``today`` is an argument):

- :func:`publish_date_invalid` / :func:`publish_date_fresh` — THE publish-date
  rule, shared with ``select``'s whole-leaderboard check: a date more than
  :data:`MAX_FUTURE_PUBLISH_DAYS` in the future is invalid; otherwise a date is
  fresh when at most ``max_publish_age_days`` old.
- :func:`track_population` — the day's scored population for one track: every
  repo with a fresh score on that track (empty when any row on the track carries
  an invalid future date: the leaderboard is then unavailable).
- :func:`cutoff_index` — the population index of the model sitting at a level's
  percentile cut-off, in integer arithmetic only.
- :func:`level_qualifiers` — the repos that qualify for a level under the
  near-tie rule: ``rating_upper`` at or above the ``rating_lower`` of the model at
  the cut-off (for ``strongest``, the top model), AND the same for every weaker
  level, so levels nest. A leaderboard row missing either bound reaches this
  module as a zero-width :class:`ArenaScore`
  (``rating_lower == rating == rating_upper``; ``leaderboard._parse_row``), so it
  needs no special case here.

Population order is ``rating`` descending, then repo id ascending, so equal
ratings resolve the same way on every run.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from llmxive.model_selection.policy import FundedPolicy
from llmxive.model_selection.types import (
    STRENGTH_LEVELS,
    ArenaScore,
    ModelScores,
    StrengthLevel,
    Track,
)

#: A publish date up to this many days ahead of ``today`` is accepted (time zones:
#: the leaderboard may already be on tomorrow's date); further ahead is invalid.
MAX_FUTURE_PUBLISH_DAYS = 1


def publish_date_invalid(publish_date: date, *, today: date) -> bool:
    """True when ``publish_date`` is more than :data:`MAX_FUTURE_PUBLISH_DAYS` after ``today``."""
    return (publish_date - today).days > MAX_FUTURE_PUBLISH_DAYS


def publish_date_fresh(publish_date: date, *, today: date, max_publish_age_days: int) -> bool:
    """True when ``publish_date`` is valid and at most ``max_publish_age_days`` old."""
    return not publish_date_invalid(publish_date, today=today) and (
        (today - publish_date).days <= max_publish_age_days
    )


def repo_of(model_id: str) -> str:
    """The Hub repo of a provider-qualified id: ``"acme/alpha-large:prov-a"`` →
    ``"acme/alpha-large"`` (an id without a provider suffix is returned as is)."""
    return model_id.split(":", 1)[0]


def track_population(
    scores: Mapping[str, ModelScores],
    track: Track,
    *,
    today: date,
    max_publish_age_days: int,
) -> dict[str, ArenaScore]:
    """Map each repo scored on ``track`` to its score, keeping only rows whose
    publish date is :func:`publish_date_fresh`. When ANY row on the track carries
    an invalid (future) publish date the leaderboard is unavailable and the
    population is empty, so nobody qualifies.

    ``scores`` is keyed by provider-qualified model id; ids of the same repo
    collapse to one entry. Two ids of one repo carrying DIFFERENT scores is a
    broken join and raises ``ValueError`` (Fail Fast) rather than picking one.
    """
    population: dict[str, ArenaScore] = {}
    for model_id, model_scores in scores.items():
        score = model_scores.for_track(track)
        if score is None:
            continue
        if publish_date_invalid(score.publish_date, today=today):
            return {}
        if not publish_date_fresh(score.publish_date, today=today, max_publish_age_days=max_publish_age_days):
            continue
        repo = repo_of(model_id)
        seen = population.get(repo)
        if seen is not None and seen != score:
            raise ValueError(f"conflicting {track} scores for repo {repo!r}: {seen} vs {score}")
        population[repo] = score
    return population


def cutoff_index(n: int, top_percent: int | None) -> int:
    """Index (in population order) of the model at the ``top_percent`` cut-off of
    a population of ``n``: ``max(0, ceil(top_percent * n / 100) - 1)``, computed
    with integers only (in floats ``ceil(0.07 * 100)`` is 8, not 7). ``None`` means
    the top-scoring model, index 0."""
    if top_percent is None:
        return 0
    return max(0, -(-top_percent * n // 100) - 1)


def level_qualifiers(
    population: Mapping[str, ArenaScore],
    level: StrengthLevel,
    policy: FundedPolicy,
) -> frozenset[str]:
    """Repos whose ``rating_upper`` is at or above the ``rating_lower`` of the
    repo at the cut-off of ``level`` AND of every weaker level. The effective floor
    is therefore the maximum of those cut-off ``rating_lower`` values, so a wide
    interval on the top model can never make ``strongest`` admit a model that
    ``strong`` rejects. An empty population qualifies nothing."""
    if not population:
        return frozenset()
    ordered = sorted(population, key=lambda repo: (-population[repo].rating, repo))
    floor = max(
        population[ordered[cutoff_index(len(ordered), policy.level_top_percent[lvl])]].rating_lower
        for lvl in STRENGTH_LEVELS[: STRENGTH_LEVELS.index(level) + 1]
    )
    return frozenset(repo for repo, score in population.items() if score.rating_upper >= floor)
