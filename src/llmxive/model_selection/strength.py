"""Relative strength levels for funded selection (spec 027, section 5.10).

Pure arithmetic, no I/O and no clock (``today`` is an argument):

- :func:`track_population` — the day's scored population for one track: every
  repo with a score on that track whose leaderboard publish date is at most
  ``max_publish_age_days`` old.
- :func:`cutoff_index` — the population index of the model sitting at a level's
  percentile cut-off, in integer arithmetic only.
- :func:`level_qualifiers` — the repos that qualify for a level under the
  near-tie rule: ``rating_upper`` at or above the ``rating_lower`` of the model at
  the cut-off (for ``strongest``, the top model). A leaderboard row without both
  bounds reaches this module as a zero-width :class:`ArenaScore`
  (``rating_lower == rating == rating_upper``), so it needs no special case here.

Population order is ``rating`` descending, then repo id ascending, so equal
ratings resolve the same way on every run.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from llmxive.model_selection.policy import FundedPolicy
from llmxive.model_selection.types import ArenaScore, ModelScores, StrengthLevel, Track


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
    """Map each repo scored on ``track`` to its score, keeping only rows with
    ``(today - publish_date).days <= max_publish_age_days``.

    ``scores`` is keyed by provider-qualified model id; ids of the same repo
    collapse to one entry. Two ids of one repo carrying DIFFERENT scores is a
    broken join and raises ``ValueError`` (Fail Fast) rather than picking one.
    """
    population: dict[str, ArenaScore] = {}
    for model_id, model_scores in scores.items():
        score = model_scores.for_track(track)
        if score is None or (today - score.publish_date).days > max_publish_age_days:
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
    repo at ``level``'s cut-off. An empty population qualifies nothing."""
    if not population:
        return frozenset()
    ordered = sorted(population, key=lambda repo: (-population[repo].rating, repo))
    cutoff_repo = ordered[cutoff_index(len(ordered), policy.level_top_percent[level])]
    floor = population[cutoff_repo].rating_lower
    return frozenset(repo for repo, score in population.items() if score.rating_upper >= floor)
