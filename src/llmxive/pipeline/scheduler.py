"""Project scheduler — picks the next project to act on.

**Spec 011 / user-directed prioritization (2026-05-15):**

The previous FIFO-within-tier policy biased toward keeping early-stage
projects rotating slowly. The user wants the opposite: projects that
are FURTHER along the pipeline (closer to published papers) should get
priority for edits + advancement, and projects with MORE COMMENTS
(personality + reviewer contributions) should also be prioritized.

Implementation: a `priority_score()` function combines two factors:

  - **Stage-depth weight**: higher for stages closer to POSTED. We use
    the canonical stage progression (see `STAGE_PROGRESSION` below) and
    score each stage exponentially by its rank. The fall-off is gentle
    enough that early-stage projects still have a non-zero chance of
    being picked (so the queue keeps draining), but late-stage projects
    are typically picked first.
  - **Comment-count multiplier**: every personality / reviewer comment
    on the project increases its weight. We cap the bonus at 20 comments
    to prevent runaway popularity dominance (the bottom-of-queue must
    still get some attention).

Selection is **roulette-wheel** (probabilistic) over these weights, not
deterministic. Two reasons:

  1. The user explicitly asked for "probabilistically" prioritized.
  2. Deterministic picks let a single popular project monopolize every
     tick. Probabilistic picks give every project nonzero chance.

When `stage=` is provided, the pool is restricted to that stage and the
same probabilistic logic still applies (within-stage comment-count
weighting). When `stage=None`, the pool is every non-terminal,
non-locked project.

Locked projects (per `pipeline/lock.py`) and terminal stages
(human_input_needed / blocked / posted) are always excluded.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from llmxive.pipeline import lock as lockmod
from llmxive.state import project as project_store
from llmxive.types import Project, Stage

# Canonical stage progression — earliest → latest. The further down the
# list a stage is, the higher its base priority score (closer to a
# published paper = more valuable to advance).
#
# Stages not in this list (e.g. RESEARCH_REVIEW review-cycle states) get
# their own dedicated reviewer cron and are handled outside the standard
# scheduler.
STAGE_PROGRESSION: list[Stage] = [
    Stage.BRAINSTORMED,
    Stage.FLESH_OUT_COMPLETE,
    Stage.PROJECT_INITIALIZED,
    Stage.SPECIFIED,
    Stage.CLARIFIED,
    Stage.PLANNED,
    Stage.TASKED,
    Stage.ANALYZED,
    Stage.IN_PROGRESS,
    Stage.RESEARCH_COMPLETE,
    Stage.PAPER_DRAFTING_INIT,
    Stage.PAPER_SPECIFIED,
    Stage.PAPER_CLARIFIED,
    Stage.PAPER_PLANNED,
    Stage.PAPER_TASKED,
    Stage.PAPER_ANALYZED,
    Stage.PAPER_IN_PROGRESS,
    Stage.PAPER_COMPLETE,
    Stage.PAPER_REVIEW,
    Stage.PAPER_ACCEPTED,
]

# Backwards-compat alias for existing callers that imported `PRIORITY`.
PRIORITY: list[Stage] = STAGE_PROGRESSION


# Stages a project can sit at that should NEVER be picked by the
# scheduler: explicit human-only handoffs and terminal end states.
#
# Spec 015 T042 / FR-034: the 3 spec-012 transient stages
# (PAPER_REVISION_IN_PROGRESS, READY_FOR_IMPLEMENTATION,
# PAPER_REVISION_BLOCKED) were DELETED. The new generic
# :class:`Stage.AGENT_BLOCKED` replaces PAPER_REVISION_BLOCKED's
# "operator must edit action items" role and is the new failsafe sink.
# NOTE: HUMAN_INPUT_NEEDED is deliberately NOT in this set. It is a RETIRED
# resting state — the autonomous escalation + deterministic re-plan flow replaced
# every path that used to park there — so it stays SCHEDULABLE on purpose: a
# straggler still sitting at it gets auto-recovered into the pipeline
# (run_one_step routes HUMAN_INPUT_NEEDED -> PLANNED). The ONLY sanctioned human
# gate is publication sign-off (AWAITING_PUBLICATION_SIGNOFF, below).
_NEVER_PICK: set[Stage] = {
    Stage.BLOCKED,
    Stage.POSTED,
    # Spec 013: PUBLISH_BLOCKED is operator-action (5 consecutive Zenodo
    # failures). Cleared via `llmxive project republish`.
    Stage.PUBLISH_BLOCKED,
    # Spec 015 T042: AGENT_BLOCKED is the unified failsafe sink. Cleared
    # via `llmxive project unblock-agent` (operator must edit action
    # items first).
    Stage.AGENT_BLOCKED,
    # Spec 023 / FR-014: VALIDATOR_REJECTED is the honest idea-track
    # terminal (idea-retry cap exhausted; rejected to the backlog).
    Stage.VALIDATOR_REJECTED,
    # Spec 023 / FR-021: sign-off-parked papers consume ZERO scheduler
    # capacity — the signoff-poll lane (integrations.signoff_gate) owns
    # the stage: it opens/parses the maintainer vote and dispatches the
    # publisher itself on approval.
    Stage.AWAITING_PUBLICATION_SIGNOFF,
}


# Exponential-decay base for the stage-depth score. Larger values =
# *steeper* preference for late-stage projects. 1.5 gives roughly:
#   brainstormed         → 1.0x
#   project_initialized  → 3.4x
#   tasked               → 17x
#   in_progress          → 57x
#   paper_in_progress    → 1500x
# which approximates "papers close to publication get strong preference,
# but earlier-stage projects still get picked every several ticks."
STAGE_GROWTH_BASE: float = 1.5

# --- Spec 023 / FR-006: stage-allocation counterweights -------------------
#
# Pre-023 the roulette weighted PROJECTS individually by
# ``STAGE_GROWTH_BASE ** rank`` — so 92 paper-review projects each carrying
# ~1478x swamped 589 flesh_out_complete projects at 1.5x (the idea queue got
# ~2% of picks and effectively never drained; issue #303). Selection is now
# TWO-LEVEL: pick a STAGE by counterweighted roulette, then a project within
# that stage. The stage weight keeps the late-stage preference but bounds its
# dominance and counterbalances it with queue depth and staleness:
#
#   stage_weight = GROWTH^min(rank, STAGE_RANK_CAP)      (bounded preference)
#                  * (1 + log2(1 + queue_depth))          (deep queues matter)
#                  * (1 + min(stale_days, MAX) / DIVISOR)  (neglect matters)
#
# and every eligible stage is floored at MIN_STAGE_SHARE of the total — the
# FR-006 "non-vanishing share" guarantee is explicit, not emergent.
STAGE_RANK_CAP: int = 12
MIN_STAGE_SHARE: float = 0.05
STALENESS_DIVISOR_DAYS: float = 7.0
MAX_STALENESS_DAYS: float = 14.0

# Comment-count bonus: every personality/reviewer comment file in
# projects/<id>/reviews/research/ adds this much to the multiplier,
# capped at MAX_COMMENT_BONUS comments.
COMMENT_BONUS_PER: float = 0.10
MAX_COMMENT_BONUS: int = 20


def _comment_count(project_id: str, repo_root: Path) -> int:
    """Count personality / reviewer markdown files for a project."""
    reviews_dir = repo_root / "projects" / project_id / "reviews" / "research"
    if not reviews_dir.is_dir():
        return 0
    try:
        return sum(1 for _ in reviews_dir.glob("*.md"))
    except OSError:
        return 0


def priority_score(project: Project, *, repo_root: Path | None = None) -> float:
    """Compute the project's scheduling weight.

    Returns a non-negative float. Higher = more likely to be picked next.

    Composition:
      base = STAGE_GROWTH_BASE ** stage_depth_rank
      multiplier = 1 + COMMENT_BONUS_PER * min(comment_count, MAX_COMMENT_BONUS)
      score = base * multiplier

    Stages outside STAGE_PROGRESSION (review states, etc.) are scored as
    rank 0 (lowest). Terminal / human-input stages return 0 (never picked).
    """
    if project.current_stage in _NEVER_PICK:
        return 0.0
    try:
        rank = STAGE_PROGRESSION.index(project.current_stage)
    except ValueError:
        rank = 0  # unknown stage scores as low priority but non-zero
    base = STAGE_GROWTH_BASE ** rank

    rr = Path(repo_root) if repo_root is not None else Path.cwd()
    cc = _comment_count(project.id, rr)
    multiplier = 1.0 + COMMENT_BONUS_PER * min(cc, MAX_COMMENT_BONUS)
    return base * multiplier


def _eligible_candidates(
    *,
    repo_root: Path | None,
    stage: Stage | None,
) -> list[Project]:
    """Return projects eligible for scheduling: non-terminal, non-locked,
    and (if `stage` is given) at that exact stage."""
    projects = project_store.list_all(repo_root=repo_root)
    out: list[Project] = []
    for p in projects:
        if p.current_stage in _NEVER_PICK:
            continue
        if lockmod.is_locked(p.id, repo_root=repo_root):
            continue
        if stage is not None and p.current_stage != stage:
            continue
        out.append(p)
    return out


def _stage_rank(stage: Stage) -> int:
    try:
        return STAGE_PROGRESSION.index(stage)
    except ValueError:
        return 0


def stage_weight(
    stage: Stage, candidates: list[Project], *, now: datetime | None = None
) -> float:
    """Counterweighted scheduling weight for one stage's queue (FR-006)."""
    if not candidates:
        return 0.0
    now = now or datetime.now(UTC)
    pref = STAGE_GROWTH_BASE ** min(_stage_rank(stage), STAGE_RANK_CAP)
    depth_term = 1.0 + math.log2(1 + len(candidates))
    oldest = min(c.updated_at for c in candidates)
    stale_days = max(0.0, (now - oldest).total_seconds() / 86400.0)
    staleness_term = 1.0 + min(stale_days, MAX_STALENESS_DAYS) / STALENESS_DIVISOR_DAYS
    return pref * depth_term * staleness_term


#: Brainstorm is the funnel mouth; allow it to carry up to 25% MORE than the
#: per-stage target before the balancer starts draining it (user policy).
BRAINSTORM_HEADROOM: float = 1.25


def _stage_target(stage: Stage, base_target: float) -> float:
    """Per-stage target population for the load balancer."""
    return base_target * (BRAINSTORM_HEADROOM if stage == Stage.BRAINSTORMED else 1.0)


def _stage_weights_with_floor(
    by_stage: dict[Stage, list[Project]], *, now: datetime | None = None
) -> dict[Stage, float]:
    """LOAD-BALANCING stage weights (user policy): drive the project
    distribution toward UNIFORMITY across the WHOLE pipeline — an equal share
    of the active population in every column — with up to +25% headroom at
    `brainstormed`.

    A stage's weight is how far its queue exceeds its target — so the fullest
    stages drain first and the populations equalize across all columns. When
    every stage is at or under target (already balanced) we fall back to
    draining proportional to queue depth so flow still advances. The
    MIN_STAGE_SHARE floor keeps every eligible stage pickable so nothing is
    ever fully starved (FR-006); the within-stage pick (`priority_score`)
    handles staleness/oldest-first.

    The equal-share target is computed over the FULL pipeline breadth, not just
    the currently-occupied stages. If we divided ``total`` by the number of
    OCCUPIED stages, the target would float upward as the pipeline collapses
    onto a few lumpy columns (e.g. 11 occupied stages → target ~73 for an
    800-project population), so giant piles barely register as "over target"
    and the balancer under-drains them — the distribution stays lumpy instead
    of spreading toward uniform. Dividing by the full-pipeline breadth instead
    pins the target at the "uniform across all columns" level (~total / 20),
    so over-full stages drain hard toward it and the populations equalize.

    Denominator = ``max(len(by_stage), len(STAGE_PROGRESSION))``: the canonical
    20-stage ``STAGE_PROGRESSION`` is the SSoT for "all pipeline columns", and
    ``max`` keeps the target correct even if more distinct stages are occupied
    than the canonical progression lists (some advanceable stages, e.g.
    ``validated``, live outside ``STAGE_PROGRESSION``) — in that case the
    occupied count is the true breadth and yields the lower, fairer target.
    """
    counts = {s: len(c) for s, c in by_stage.items()}
    total = sum(counts.values())
    nstages = max(len(by_stage), len(STAGE_PROGRESSION))
    if total <= 0 or len(by_stage) == 0:
        return {s: 0.0 for s in by_stage}
    base_target = total / nstages
    over = {
        s: max(0.0, counts[s] - _stage_target(s, base_target)) for s in by_stage
    }
    if sum(over.values()) <= 0:  # already balanced → keep flow moving by depth
        over = {s: float(counts[s]) for s in by_stage}
    total_over = sum(over.values())
    if total_over <= 0:
        return over
    floor = MIN_STAGE_SHARE * total_over
    return {s: max(w, floor) for s, w in over.items()}


def _pick_within_stage(
    candidates: list[Project], *, repo_root: Path | None, rand,
) -> Project:
    weights = [priority_score(p, repo_root=repo_root) for p in candidates]
    total = sum(weights)
    if total <= 0:
        return sorted(candidates, key=lambda p: p.updated_at)[0]
    return rand.choices(candidates, weights=weights, k=1)[0]


def pick_next(
    *, repo_root: Path | None = None, stage: Stage | None = None,
    rng: random.Random | None = None,
) -> Project | None:
    """Pick the next project: stage by counterweighted roulette (FR-006),
    then a project within that stage.

    `rng` lets tests inject a seeded `random.Random` for determinism.
    Production callers should pass None (uses the module-level RNG).
    """
    candidates = _eligible_candidates(repo_root=repo_root, stage=stage)
    if not candidates:
        return None
    rand = rng if rng is not None else random
    if stage is not None:
        return _pick_within_stage(candidates, repo_root=repo_root, rand=rand)
    by_stage: dict[Stage, list[Project]] = defaultdict(list)
    for p in candidates:
        by_stage[p.current_stage].append(p)
    weights = _stage_weights_with_floor(by_stage)
    stages = list(by_stage)
    total = sum(weights[s] for s in stages)
    if total <= 0:
        candidates.sort(key=lambda p: p.updated_at)
        return candidates[0]
    chosen_stage = rand.choices(stages, weights=[weights[s] for s in stages], k=1)[0]
    return _pick_within_stage(
        by_stage[chosen_stage], repo_root=repo_root, rand=rand
    )


def pick_for_worker(
    worker_index: int,
    n_workers: int,
    *,
    repo_root: Path | None = None,
    now: datetime | None = None,
) -> Project | None:
    """DETERMINISTIC multi-worker selection (advance.yml matrix lane).

    Unlike the probabilistic :func:`pick_next` / :func:`pick_next_n`, this is a
    pure function of the repo state: N workers fan out across the top-weighted
    stages by round-robin, each taking a DISTINCT project, so the 6 concurrent
    matrix jobs at the same HEAD pick 6 distinct projects (no double-work).

    Algorithm:

    1. Gather eligible candidates (``_eligible_candidates(repo_root, stage=None)``)
       and group them by ``current_stage``.
    2. Score each occupied stage with the EXISTING :func:`stage_weight` (which
       already encodes the load-balance-the-biggest-piles + prefer-further-along
       + staleness policy).
    3. Rank occupied stages by weight DESC; deterministic tiebreak: pipeline
       depth DESC (further-along first, via ``_stage_rank``), then stage value
       (name) ASC → ``ranked_stages``.
    4. If no stages, return None. Else
       ``stage = ranked_stages[worker_index % len(ranked_stages)]`` and
       ``depth = worker_index // len(ranked_stages)`` (round-robin wraps to a
       deeper project in the same stage when there are more workers than stages).
    5. Within that stage, order projects by staleness — oldest ``updated_at``
       FIRST (furthest-waiting), tiebreak by ``id`` ASC. Return the ``depth``-th
       project, or None if ``depth >= count``.

    ``now`` lets tests pin the staleness reference; production passes None.
    """
    if n_workers <= 0:
        return None
    candidates = _eligible_candidates(repo_root=repo_root, stage=None)
    if not candidates:
        return None
    now = now or datetime.now(UTC)
    by_stage: dict[Stage, list[Project]] = defaultdict(list)
    for p in candidates:
        by_stage[p.current_stage].append(p)
    # Rank occupied stages: weight DESC, then depth DESC, then name ASC.
    ranked_stages = sorted(
        by_stage,
        key=lambda s: (
            -stage_weight(s, by_stage[s], now=now),
            -_stage_rank(s),
            s.value,
        ),
    )
    if not ranked_stages:
        return None
    stage = ranked_stages[worker_index % len(ranked_stages)]
    depth = worker_index // len(ranked_stages)
    in_stage = sorted(by_stage[stage], key=lambda p: (p.updated_at, p.id))
    if depth >= len(in_stage):
        return None
    return in_stage[depth]


def pick_next_n(
    n: int,
    *, repo_root: Path | None = None, stage: Stage | None = None,
    rng: random.Random | None = None,
) -> list[Project]:
    """Pick up to N distinct projects, weighted by `priority_score`.

    Used when a cron tick wants to advance several projects in one pass
    (FR-012 / PIPELINE_PARALLELISM). Sampling is without replacement:
    once a project is picked, it's removed from the pool before the next
    pick.
    """
    if n <= 0:
        return []
    candidates = _eligible_candidates(repo_root=repo_root, stage=stage)
    picked: list[Project] = []
    rand = rng if rng is not None else random
    while candidates and len(picked) < n:
        if stage is not None:
            choice = _pick_within_stage(candidates, repo_root=repo_root, rand=rand)
        else:
            by_stage: dict[Stage, list[Project]] = defaultdict(list)
            for p in candidates:
                by_stage[p.current_stage].append(p)
            weights = _stage_weights_with_floor(by_stage)
            stages = list(by_stage)
            total = sum(weights[s] for s in stages)
            if total <= 0:
                candidates.sort(key=lambda p: p.updated_at)
                picked.append(candidates.pop(0))
                continue
            chosen_stage = rand.choices(
                stages, weights=[weights[s] for s in stages], k=1
            )[0]
            choice = _pick_within_stage(
                by_stage[chosen_stage], repo_root=repo_root, rand=rand
            )
        picked.append(choice)
        candidates = [c for c in candidates if c.id != choice.id]
    return picked


__all__ = [
    "COMMENT_BONUS_PER",
    "MAX_COMMENT_BONUS",
    "MAX_STALENESS_DAYS",
    "MIN_STAGE_SHARE",
    "PRIORITY",
    "STAGE_GROWTH_BASE",
    "STAGE_PROGRESSION",
    "STAGE_RANK_CAP",
    "STALENESS_DIVISOR_DAYS",
    "pick_for_worker",
    "pick_next",
    "pick_next_n",
    "priority_score",
    "stage_weight",
]
