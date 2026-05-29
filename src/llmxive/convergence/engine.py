"""Generic convergence engine (spec 015 T022-T028, #239).

Implements the identify -> revise -> re-review protocol parameterized by a
``ReviewSpec``. Owns the round loop, the unanimous-accept test, per-round budget,
honest convergence reporting, and converge-or-kickback. Overflowing reviewer/reviser
inputs are routed through ``tools/summarize``. See contracts/convergence-engine.md.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from llmxive.tools.summarize import estimate_tokens, summarize

from .kickback import route_kickback
from .types import (
    Concern,
    ConcernResponse,
    ConvergenceResult,
    ReviewSpec,
    Verdict,
)

# A hook the caller supplies to persist a per-round inspection record + run-log entry
# (FR-015/050/051). Signature: (round_index, concerns, responses, verdicts) -> None.
RoundHook = Callable[[int, list[Concern], list[ConcernResponse], list[Verdict]], None]


def _resolved(v: Verdict) -> bool:
    """A concern is resolved ONLY by a current, first-hand pass (FR-018): a stale
    verdict or a self-review never counts as a pass."""
    return v.status == "pass" and not v.stale and not v.self_review


def _maybe_reduce(artifacts: dict[str, str], *, goal: str, model: str,
                  budget: int) -> dict[str, str]:
    """Route any oversized artifact through the SSoT summarizer (FR-006) so no
    reviewer/reviser input silently overflows the model context."""
    out: dict[str, str] = {}
    for path, content in artifacts.items():
        if estimate_tokens(content) > budget:
            out[path] = summarize(content, goal=goal, model=model, token_budget=budget)
        else:
            out[path] = content
    return out


def run_convergence(
    spec: ReviewSpec,
    artifacts: dict[str, str],
    *,
    constitution: str | None = None,
    advisory: list[str] | None = None,
    producer: str | None = None,
    model: str = "qwen.qwen3.5-122b",
    reviewer_token_budget: int | None = None,
    max_rounds: int | None = None,
    per_round_budget_s: float | None = None,
    on_round: RoundHook | None = None,
) -> ConvergenceResult:
    """Run the convergence cycle for one reviewable step.

    ``artifacts`` maps repo-relative path -> content. ``producer`` (if given) is the
    agent that authored the artifacts; reviewers whose lens name equals it are excluded
    (self-review prevention, FR-018). Returns an honest ``ConvergenceResult``:
    ``converged`` is True iff every panelist's concerns are resolved within the cap.
    """
    if spec.exempt:
        raise ValueError(f"stage '{spec.stage}' is EXEMPT; do not run convergence on it")

    advisory = advisory or []
    cap = max_rounds if max_rounds is not None else spec.max_rounds
    const = constitution if spec.constitution_input else None
    # Self-review prevention: a reviewer may not review work it produced.
    panel = [r for r in spec.reviewers if producer is None or r.name != producer]
    if not panel:
        raise ValueError(f"stage '{spec.stage}' has no eligible reviewers (producer={producer!r})")

    budget = reviewer_token_budget
    if budget is None:
        from llmxive.tools.summarize import _usable_budget  # SSoT budget resolution
        budget = _usable_budget(model, None)

    def _present(arts: dict[str, str]) -> dict[str, str]:
        return _maybe_reduce(arts, goal=spec.overflow_goal, model=model, budget=budget)

    concern_history: list[Concern] = []
    response_history: list[ConcernResponse] = []
    verdict_history: list[Verdict] = []

    # --- R1: identify ---
    seen = _present(artifacts)
    open_concerns: list[Concern] = []
    for r in panel:
        for c in r.identify(seen, constitution=const, advisory=advisory):
            open_concerns.append(c)
    concern_history.extend(open_concerns)
    if on_round is not None:
        on_round(1, list(open_concerns), [], [])

    rounds_used = 0
    while open_concerns and rounds_used < cap:
        rounds_used += 1
        t0 = time.monotonic()

        # --- R2: revise (the reviser addresses EVERY open concern) ---
        if spec.reviser is None:
            break  # nothing can resolve the concerns -> kickback
        prev_artifacts = artifacts
        new_arts, responses = spec.reviser.revise(artifacts, list(open_concerns))
        artifacts = {**artifacts, **new_arts}
        response_history.extend(responses)
        seen = _present(artifacts)

        # Which artifact keys did R2 actually change? (FR-012: an
        # R1-accepter re-reviews ONLY if R2 changed an artifact relevant
        # to its lens.) Every panel lens reviews the whole artifact set
        # (there is no per-lens artifact restriction), so "relevant to
        # its lens" == "any artifact content changed". When R2 is a
        # no-op (nothing changed), accepters are skipped — no wasted
        # re-reviews, satisfying the design's optimization.
        r2_changed_artifacts = any(
            prev_artifacts.get(k) != v for k, v in new_arts.items()
        )

        # --- R3: re-review ---
        # Dissenters (panelists with open concerns) ALWAYS re-review,
        # judging their OWN concerns against the R2 change-log. An
        # R1-accepter (no open concerns this round) re-reviews ONLY when
        # R2 changed an artifact — to catch NEW breakage the revision
        # introduced in its lens (FR-012 "no new breakage"). Without
        # this, a revision made to satisfy a dissenter could silently
        # violate an accepter's lens and the engine would still report
        # `converged`.
        round_verdicts: list[Verdict] = []
        next_open: list[Concern] = []
        for r in panel:
            own = [c for c in open_concerns if c.reviewer == r.name]
            if not own and not r2_changed_artifacts:
                continue  # accepter + nothing changed -> no wasted re-review
            own_responses = [resp for resp in responses
                             if any(resp.concern_id == c.id for c in own)]
            verdicts = r.rereview(seen, own, own_responses,
                                  constitution=const, advisory=advisory)
            round_verdicts.extend(verdicts)
            judged = {v.concern_id: v for v in verdicts}
            for c in own:
                v = judged.get(c.id)
                if v is None or not _resolved(v):
                    next_open.append(c)  # unresolved (failed, stale, self-review, or unjudged)
            for v in verdicts:
                next_open.extend(v.new_concerns)
        verdict_history.extend(round_verdicts)
        # dedupe by concern id, preserving order
        deduped: list[Concern] = []
        ids: set[str] = set()
        for c in next_open:
            if c.id not in ids:
                ids.add(c.id)
                deduped.append(c)
        for c in deduped:
            if c.id not in {h.id for h in concern_history}:
                concern_history.append(c)
        open_concerns = deduped

        if on_round is not None:
            on_round(rounds_used + 1, list(open_concerns), list(responses), list(round_verdicts))

        if per_round_budget_s is not None and (time.monotonic() - t0) > per_round_budget_s:
            break  # per-round wall-clock budget exceeded -> stop, kickback

    converged = not open_concerns
    if converged:
        return ConvergenceResult(
            stage=spec.stage,
            converged=True,
            rounds_used=rounds_used,
            concern_history=concern_history,
            response_history=response_history,
            verdict_history=verdict_history,
            next_stage=spec.advance_stage,
        )
    kickback = route_kickback(spec, open_concerns)
    return ConvergenceResult(
        stage=spec.stage,
        converged=False,
        rounds_used=rounds_used,
        concern_history=concern_history,
        response_history=response_history,
        verdict_history=verdict_history,
        kickback=kickback,
    )


__all__ = ["run_convergence"]
