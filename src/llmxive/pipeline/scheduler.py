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
import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from llmxive.pipeline import advance_ledger
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
    # External-paper intake triage (spec 024): ingested papers land here and are
    # reprocessed into the pipeline (code -> in_progress; no-code -> brainstormed).
    # First slot = lowest stage-depth weight; the deep ingest queue is drained by
    # its overflow weight, not an inflated late-stage preference.
    Stage.PAPER_INGESTED,
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
    # Reviewed-Preprints (2026-07-01): a review-only ingested paper is terminal —
    # the original is never modified; it only carries llmXive review artifacts.
    Stage.REVIEWED_PREPRINT,
    # Spec 023 / FR-021: sign-off-parked papers consume ZERO scheduler
    # capacity — the signoff-poll lane (integrations.signoff_gate) owns
    # the stage: it opens/parses the maintainer vote and dispatches the
    # publisher itself on approval.
    Stage.AWAITING_PUBLICATION_SIGNOFF,
}

# Transient pass-through / recovery stages have NO agent — run_one_step /
# _decide_next_stage routes them forward in a single cheap tick (full_revision
# -> in_progress, rejected -> brainstormed, fundamental_flaws -> brainstormed,
# accepted -> awaiting_signoff, the retired human_input_needed -> planned). They
# are usually SPARSE (1-2 projects), so the load-balanced stage weight ranks them
# BELOW the worker count and `pick_for_worker` (which fans the N workers across
# the top-N ranked stages) never reaches them — stranding the project forever
# (PROJ-604 parked at research_full_revision: review correctly flagged it, it
# routed to research_full_revision, then no worker ever picked that floor-weight
# stage to apply the -> in_progress routing). Float these to the FRONT of the
# worker rotation every tick: routing them is free and unblocks a stuck project.
_PRIORITY_DRAIN_STAGES: frozenset[Stage] = frozenset({
    Stage.RESEARCH_FULL_REVISION,
    Stage.RESEARCH_REJECTED,
    Stage.PAPER_FUNDAMENTAL_FLAWS,
    Stage.PAPER_ACCEPTED,
    Stage.HUMAN_INPUT_NEEDED,
})


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
    NOT on an advance-error hold, and (if `stage` is given) at that exact stage.

    The advance-error hold (issue #1139, defect D5) is the fix for the every-tick
    re-pick of a permanently-failing project: a project whose typed ledger record
    (:mod:`llmxive.pipeline.advance_ledger`) is still active for its CURRENT stage
    is skipped while it is inside a transient backoff window or held in a
    ``rerouted``/``terminal`` disposition awaiting a re-plan / operator. A record
    for a different stage is stale (the project advanced past the failing step) and
    is ignored, so a hold can never permanently strand a project. Terminal STAGES
    (``_NEVER_PICK``) and locks are still honoured exactly as before."""
    projects = project_store.list_all(repo_root=repo_root)
    out: list[Project] = []
    for p in projects:
        if p.current_stage in _NEVER_PICK:
            continue
        if lockmod.is_locked(p.id, repo_root=repo_root):
            continue
        if stage is not None and p.current_stage != stage:
            continue
        if advance_ledger.is_on_hold(p, repo_root=repo_root):
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

#: Ceiling on the fraction of the worker matrix any ONE stage may hold in a single
#: tick (:func:`_apportion_workers`). The biggest pile SHOULD get most of the
#: workers — that is the whole point of load-balancing — but never all of them: the
#: remaining share keeps the upstream stages that feed it flowing, and stops one
#: blocked pile from stalling the entire pipeline for a tick. FR-006 (nothing is
#: ever fully starved) is enforced HERE for the deterministic matrix lane.
MAX_STAGE_WORKER_SHARE: float = 2.0 / 3.0


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
       (name) ASC → ``ranked_stages``, with the sparse priority-drain stages
       floated to the front so they never strand.
    4. APPORTION the N workers across those stages in PROPORTION to their weight
       (:func:`_apportion_workers`), capped by each stage's pile size.
    5. Worker ``i`` takes the ``i``-th slot; its depth is the number of earlier
       slots on the same stage. Within a stage, projects are ordered by staleness
       — oldest ``updated_at`` FIRST — tiebreak ``id`` ASC. Distinct (stage, depth)
       per worker ⇒ distinct projects ⇒ no double-work.

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
    # Float transient pass-through / recovery stages to the FRONT so a worker
    # always reaches them this tick (they are sparse, so the load-balanced rank
    # otherwise leaves them below the worker count → never picked → stranded).
    priority = [s for s in ranked_stages if s in _PRIORITY_DRAIN_STAGES]
    if priority:
        rest = [s for s in ranked_stages if s not in _PRIORITY_DRAIN_STAGES]
        ranked_stages = priority + rest
    slots = _apportion_workers(ranked_stages, by_stage, n_workers, now=now)
    if worker_index >= len(slots):
        return None
    stage = slots[worker_index]
    depth = slots[:worker_index].count(stage)
    in_stage = _order_within_stage(stage, by_stage[stage], repo_root=repo_root)
    if depth >= len(in_stage):
        return None
    return in_stage[depth]


#: Stages whose completion needs MANY sequential ticks (the implementer drains a
#: batch of tasks per tick, and a project carries 30-70 tasks).
_IMPLEMENT_STAGES: frozenset[Stage] = frozenset({
    Stage.IN_PROGRESS, Stage.PAPER_IN_PROGRESS,
})


def _remaining_tasks(project: Project, *, repo_root: Path | None) -> int:
    """Open (``[ ]``) + under-review (``[~]``) task count for an implement project.

    Resolved through the SSoT ``feature_dir_for`` (honours the ``speckit_*_dir``
    pointer) so a stale lower-numbered ``specs/*`` dir can never shadow the real one.
    An unreadable/absent tasks.md sorts LAST (a large sentinel) rather than first —
    "no tasks file" must not masquerade as "almost finished".
    """
    rr = Path(repo_root) if repo_root is not None else Path.cwd()
    track = "paper" if project.current_stage == Stage.PAPER_IN_PROGRESS else "research"
    try:
        fdir = project_store.feature_dir_for(
            rr / "projects" / project.id, track=track
        )
        if fdir is None:
            return _NO_TASKS_SENTINEL
        text = (fdir / "tasks.md").read_text(encoding="utf-8")
    except OSError:
        return _NO_TASKS_SENTINEL
    # Count real checkbox LINES, not any `- [ ]` substring — the tasks.md's own
    # "## Format: `- [ ] T### …`" header contains the literal example and must not
    # read as an open task (same phantom-marker bug that stranded PROJ-148; see
    # graph._TASK_LINE_RE). Anchored per-line, indent allowed for subtasks.
    return len(_OPEN_TASK_RE.findall(text))


#: A real OPEN or under-review checkbox line (see _remaining_tasks).
_OPEN_TASK_RE = re.compile(r"^\s*-\s*\[[ ~]\]\s", re.MULTILINE)


#: Sorts a project with no readable tasks.md to the BACK of its implement queue.
_NO_TASKS_SENTINEL = 1 << 30


def _order_within_stage(
    stage: Stage, projects: list[Project], *, repo_root: Path | None
) -> list[Project]:
    """Order a stage's queue for the matrix workers.

    Implement stages are served SHORTEST-REMAINING-FIRST: the project closest to
    done goes first. Everywhere else, oldest-waiting first (staleness) — there is no
    "remaining work" to be short of.

    Why implement is different: draining a project takes SEVERAL ticks (~38 tasks at
    ~10/tick). Ordering by staleness made that a strict ROUND-ROBIN — working on a
    project refreshes its ``updated_at`` and sends it to the back of the queue, so
    each project waited for all 434 others between touches. Every project crept
    forward and NONE ever finished: classic processor-sharing starvation, and the
    reason zero projects had EVER crossed research_complete. Serving the shortest
    remaining queue first turns the same compute into COMPLETED projects (it is
    optimal for mean completion time), and it cannot starve the long ones: a finished
    project LEAVES the stage, so the queue steadily advances to them.

    Staleness remains the tiebreak, so equal-remaining projects still go
    oldest-first.
    """
    if stage in _IMPLEMENT_STAGES:
        return sorted(
            projects,
            key=lambda p: (_effective_remaining(p, repo_root=repo_root), p.updated_at, p.id),
        )
    return sorted(projects, key=lambda p: (p.updated_at, p.id))


#: How many tasks' worth of "distance from done" each FAILED execution attempt adds.
#: A project stuck in the execution fix-loop is NOT nearly done — it has an unresolved
#: blocker — but a failed run re-opens only a handful of tasks, so on raw open-task
#: count it looks like the closest thing to finished and got re-picked EVERY tick.
#: Twelve such churners ate ~4,000 of one day's 5,111 implementer calls (one took 843)
#: while 400 projects got none. The penalty is deliberately moderate: it moves a
#: churner behind healthy work without banishing it, because it still needs attempts
#: to reach the re-plan cap and be honestly rejected.
EXEC_CHURN_PENALTY: int = 3


def _effective_remaining(project: Project, *, repo_root: Path | None) -> int:
    """Distance-from-done for an implement project: open tasks PLUS a penalty for
    every execution attempt it has already burned (see :data:`EXEC_CHURN_PENALTY`)."""
    from llmxive.state import execution_status

    remaining = _remaining_tasks(project, repo_root=repo_root)
    if remaining >= _NO_TASKS_SENTINEL:
        return remaining
    attempts = execution_status.total_attempts(project.id, repo_root=repo_root)
    return remaining + EXEC_CHURN_PENALTY * attempts


def _apportion_workers(
    ranked_stages: list[Stage],
    by_stage: dict[Stage, list[Project]],
    n_workers: int,
    *,
    now: datetime | None = None,
) -> list[Stage]:
    """Hand out the N worker slots across stages IN PROPORTION to stage weight.

    This is what makes the load-balance policy real. The previous assignment was
    ``ranked_stages[worker_index % len(ranked_stages)]`` — a flat round-robin that
    used the weights only to ORDER the stages and then threw their MAGNITUDE away.
    Every occupied stage got exactly one worker, so a stage holding 433 projects
    (in_progress: 41% of the fleet) was served no harder than a stage holding 1,
    and any worker whose round-robin slot landed on a 1-project stage at depth>=1
    picked nothing at all and idled. The biggest pile could never drain.

    Apportionment is D'Hondt (the standard highest-averages method): repeatedly give
    the next slot to the stage maximizing ``weight / (slots_already_held + 1)``. That
    yields whole-worker counts proportional to weight, is deterministic (ties break
    by ``ranked_stages`` order), and self-corrects — as a pile drains its weight
    falls and its share follows.

    The weights are :func:`_stage_weights_with_floor` — the LOAD-BALANCING policy
    (how far a stage exceeds its equal-share target, with a MIN_STAGE_SHARE floor)
    — NOT the raw :func:`stage_weight` used for ranking. That distinction matters:
    raw weight grows exponentially with pipeline depth, so apportioning on it would
    hand nearly every worker to the deepest pile and starve the upstream stages that
    feed it. The floor is what guarantees no stage is ever fully starved (FR-006).

    Three further guards:
      * every priority-drain stage is seeded a slot FIRST (they are sparse, transient
        and must never strand),
      * a stage is capped at its pile size, so no slot is wasted on an empty depth, and
      * NO stage may take more than :data:`MAX_STAGE_WORKER_SHARE` of the workers.
        Without that cap a pile as lopsided as in_progress (433 of 1064) simply takes
        EVERY worker, which starves the upstream stages that feed it — a monoculture
        tick that also stalls the whole pipeline if the pile happens to be blocked.
        FR-006 requires that nothing is ever fully starved; the cap is what enforces
        it here (the MIN_STAGE_SHARE floor alone cannot: against an overflow of 380 a
        floor weight rounds to zero whole slots).
    """
    balance = _stage_weights_with_floor(by_stage, now=now)
    weights = {s: max(balance.get(s, 0.0), 0.0) for s in ranked_stages}
    counts: dict[Stage, int] = dict.fromkeys(ranked_stages, 0)
    slots: list[Stage] = []
    # Ceil, and never below 1, so a single-worker matrix still schedules.
    max_share = max(1, math.ceil(n_workers * MAX_STAGE_WORKER_SHARE))

    def _capacity(s: Stage) -> int:
        return min(len(by_stage[s]), max_share)

    def _take(stage: Stage) -> None:
        slots.append(stage)
        counts[stage] += 1

    # Seed the sparse priority-drain stages so they are always reached this tick.
    for s in ranked_stages:
        if len(slots) >= n_workers:
            break
        if s in _PRIORITY_DRAIN_STAGES and counts[s] < _capacity(s):
            _take(s)
    # Seed the TOP-RANKED stage (raw stage_weight: prefer-further-along + depth +
    # staleness) so worker 0 always lands there — the "finish what's started before
    # starting more" policy, which the overflow-based apportionment below would
    # otherwise override in favour of whichever pile is merely the most over target.
    for s in ranked_stages:
        if len(slots) >= n_workers:
            break
        if counts[s] < _capacity(s):
            _take(s)
        break
    # Apportion the rest by highest-averages, capped by pile size AND max_share.
    while len(slots) < n_workers:
        best: Stage | None = None
        best_score = -1.0
        for s in ranked_stages:  # ranked order ⇒ deterministic tiebreak
            if counts[s] >= _capacity(s):
                continue  # pile exhausted or at its share cap
            score = weights[s] / (counts[s] + 1)
            if score > best_score:
                best_score, best = score, s
        if best is None:
            break  # every pile exhausted / capped
        _take(best)
    # The share cap exists to stop one stage crowding OUT the others — never to idle
    # a worker. If slots remain because every stage is at its cap (e.g. in_progress is
    # the only occupied stage), hand them out ignoring the cap, bounded only by pile
    # size. Otherwise a 1-stage repo would leave a third of the matrix doing nothing.
    while len(slots) < n_workers:
        best = None
        best_score = -1.0
        for s in ranked_stages:
            if counts[s] >= len(by_stage[s]):
                continue  # a worker here would pick nothing
            score = weights[s] / (counts[s] + 1)
            if score > best_score:
                best_score, best = score, s
        if best is None:
            break  # genuinely fewer projects than workers
        _take(best)
    return slots


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
