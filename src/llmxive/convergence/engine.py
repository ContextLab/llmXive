"""Generic convergence engine (spec 015 T022-T028, #239).

Implements the identify -> revise -> re-review protocol parameterized by a
``ReviewSpec``. Owns the round loop, the unanimous-accept test, per-round budget,
honest convergence reporting, and converge-or-kickback. Overflowing reviewer/reviser
inputs are routed through ``tools/summarize``. See contracts/convergence-engine.md.
"""

from __future__ import annotations

import os
import re
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

from llmxive.agents.citation_guard import (
    UNVERIFIED_MARKER_PREFIX,
    has_unverified_markers,
)
from llmxive.tools.summarize import estimate_tokens, summarize

from .kickback import route_kickback
from .types import (
    Concern,
    ConcernResponse,
    ConvergenceResult,
    Reviewer,
    ReviewSpec,
    Severity,
    Verdict,
)

# A hook the caller supplies to persist a per-round inspection record + run-log entry
# (FR-015/050/051). Signature: (round_index, concerns, responses, verdicts) -> None.
RoundHook = Callable[[int, list[Concern], list[ConcernResponse], list[Verdict]], None]

# Default upper bound on concurrent panel-lens calls. The panel lenses are
# independent (no cross-reviewer state), so the engine dispatches their long
# reasoning-model calls in parallel with a bounded pool — a pure wall-clock
# optimization that leaves results byte-for-byte identical to the serial path.
# Env-overridable via ``LLMXIVE_PANEL_MAX_CONCURRENCY`` for tuning/throttling.
_PANEL_MAX_CONCURRENCY = 8


def _panel_max_concurrency() -> int:
    """Resolve the concurrency cap, honoring ``LLMXIVE_PANEL_MAX_CONCURRENCY``.

    An unset / empty / non-positive / unparsable override falls back to the
    module default. The pool is always additionally bounded by the panel size
    at the call site, so a tiny panel never spins up idle workers."""
    raw = os.environ.get("LLMXIVE_PANEL_MAX_CONCURRENCY")
    if raw:
        try:
            val = int(raw)
        except ValueError:
            return _PANEL_MAX_CONCURRENCY
        if val > 0:
            return val
    return _PANEL_MAX_CONCURRENCY


_T = TypeVar("_T")


def _map_indices(n: int, fn: Callable[[int], _T]) -> list[_T]:
    """Call ``fn(i)`` for ``i`` in ``range(n)``, returning results in INDEX
    order — independent of which call finishes first.

    The panel lenses are independent, so the (long reasoning-model) calls are
    dispatched concurrently with a bounded ``ThreadPoolExecutor``; results are
    collected keyed by index and re-assembled in order, so the engine's output
    (concern/verdict ordering, dedupe, convergence outcome) is identical to the
    prior serial behavior. If any call raises, the first exception (by index) is
    re-raised AFTER the pool drains — never swallowed, never a partial result —
    so the circuit-breaker's run-abort path stays intact.

    ``n`` of 0 or 1 runs inline (no pool) — the serial path — so tiny panels
    never depend on the executor."""
    if n <= 0:
        return []
    if n == 1:
        return [fn(0)]

    max_workers = min(n, _panel_max_concurrency())
    if max_workers <= 1:
        return [fn(i) for i in range(n)]

    results: list[_T | None] = [None] * n
    errors: list[BaseException | None] = [None] * n
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fn, i): i for i in range(n)}
        for fut in futures:
            idx = futures[fut]
            try:
                results[idx] = fut.result()
            except BaseException as exc:  # propagate below in index order
                errors[idx] = exc
    # Propagate the FIRST error in index order (deterministic), matching the
    # serial path where the earliest-panel-index failure aborts the phase.
    for err in errors:
        if err is not None:
            raise err
    return [r for r in results]  # type: ignore[misc]  # all populated (no errors)


def _map_reviewers(
    subset: Sequence[Reviewer], fn: Callable[[Reviewer], _T]
) -> list[_T]:
    """Apply ``fn`` to each reviewer in ``subset``, returning results in INPUT
    (panel) order. Thin wrapper over :func:`_map_indices` so R1 ``identify`` and
    R3 ``rereview`` share the same bounded-pool, ordered, exception-propagating
    dispatch."""
    return _map_indices(len(subset), lambda i: fn(subset[i]))


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


def _is_doc_artifact_key(key: str) -> bool:
    """A scannable produced-doc key, vs a sentinel/control input.

    The artifacts dict mixes two key kinds (see ``project_runner``): real
    repo-relative doc PATHS (the produced documents) and ``__sentinel__``
    control/context inputs wrapped in double underscores (``__constitution__``,
    ``__idea_md__``, ...). Only the produced docs are gated for unverified
    markers — a marker echoed inside a context input is not the doc this stage
    is publishing."""
    return not (key.startswith("__") and key.endswith("__"))


def _unverified_marker_concerns(
    artifacts: dict[str, str], *, stage: str, reviewer: str
) -> list[Concern]:
    """Synthesize a blocking :class:`Concern` per produced-doc artifact that
    still carries an ``[UNRESOLVED-CLAIM: ...]`` marker — the unified marker the
    claim-verification layer (and F-18/F-19 as resolvers within it) renders for
    any citation or factual claim it could not resolve to a verified value or a
    signed execution receipt (spec 016, FR-017/FR-019).

    A fabricated / unverifiable reference or claim is a factual (scientific)
    defect, so each concern is :attr:`Severity.SCIENCE` — the strongest factual
    lens the enum provides whose kickback routing points at an earlier *content*
    stage (``clarified`` / ``brainstormed`` / ``flesh_out_in_progress`` depending
    on the stage's ``kickback_routing`` table) rather than an in-loop re-edit.
    Each concern names the offending artifact path and the marker bodies so the
    kickback record (and the next worker) sees exactly what was unresolved."""
    concerns: list[Concern] = []
    for idx, path in enumerate(sorted(artifacts)):
        if not _is_doc_artifact_key(path):
            continue
        content = artifacts[path]
        if not has_unverified_markers(content):
            continue
        # Capture the FULL verbatim markers (prefix + body + ``]``) so the
        # synthesized concern text carries them intact — the kickback reason
        # re-extracts them via the same ``find_unverified_markers`` helper.
        full_markers = re.findall(
            re.escape(UNVERIFIED_MARKER_PREFIX) + r"[^\]]*\]", content
        )
        joined = " ".join(full_markers) if full_markers else "(unparsable marker)"
        concerns.append(
            Concern(
                # 12-char deterministic id (Concern has no length cap, but the
                # persisted records elsewhere expect short ids; keep parity).
                id=f"unverif{idx:05d}"[:12].ljust(12, "0"),
                reviewer=reviewer,
                severity=Severity.SCIENCE,
                artifact=path,
                location="",
                text=(
                    f"Unverifiable/fabricated reference(s) or claim(s) remain in "
                    f"'{path}': {joined}. The claim-verification layer could not "
                    f"resolve these against a primary source or a signed execution "
                    f"receipt; the document must not advance until every reference "
                    f"and claim is verified or removed (Constitution Principle II)."
                ),
                round=1,
            )
        )
    return concerns


def _spec_quality_concerns(
    artifacts: dict[str, str], *, stage: str, reviewer: str
) -> list[Concern]:
    """Synthesize a blocking :class:`Concern` per spec-quality defect the
    deterministic scanner (:func:`llmxive.speckit._spec_quality.scan_spec_quality`)
    finds in a ``spec.md`` produced-doc artifact.

    The panel lenses catch consistency/coverage/scope issues but reliably MISS
    mechanical regressions (a surviving ``[NEEDS CLARIFICATION: …]`` marker, an
    unfilled ``[DATE]``/``[link]``/branch-name placeholder, a leftover
    ``/speckit-…`` instruction line, or a duplicate FR). This pure scan is the
    reliable backstop, mirroring ``_unverified_marker_concerns``: each finding
    becomes a blocking concern appended to ``open_concerns`` before the
    converged check, so the reviser MUST resolve it within the cap (and a
    converged spec is guaranteed to carry none).

    Only runs at the spec stage (``clarified``) and only over ``spec.md`` doc
    artifacts — the scanner's FR/placeholder grammar is spec-specific. A
    duplicate-FR or surviving-clarification defect is a ``requirement``-class
    concern (the FR set itself is broken); its kickback routing points at an
    earlier spec/content stage per the spec's ``kickback_routing`` table."""
    if stage != "clarified":
        return []
    from llmxive.speckit._spec_quality import scan_spec_quality

    concerns: list[Concern] = []
    idx = 0
    for path in sorted(artifacts):
        if not _is_doc_artifact_key(path):
            continue
        if not path.replace("\\", "/").endswith("spec.md"):
            continue
        for finding in scan_spec_quality(artifacts[path]):
            concerns.append(
                Concern(
                    id=f"specqual{idx:04d}"[:12].ljust(12, "0"),
                    reviewer=reviewer,
                    severity=Severity.REQUIREMENT,
                    artifact=path,
                    location="",
                    text=(
                        f"[{finding.kind}] {finding.reason} in '{path}': "
                        f"{finding.text!r}. A converged spec must not carry this; "
                        f"the reviser must resolve it before the spec advances."
                    ),
                    round=1,
                )
            )
            idx += 1
    return concerns


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
    # The lenses are independent, so dispatch ``identify`` concurrently; results
    # are merged in PANEL order (not completion order) so ``open_concerns`` is
    # assembled identically to the serial path.
    seen = _present(artifacts)
    open_concerns: list[Concern] = []
    r1_results = _map_reviewers(
        panel, lambda r: r.identify(seen, constitution=const, advisory=advisory)
    )
    for concerns in r1_results:
        for c in concerns:
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
        # Select the re-reviewing subset FIRST, in panel order, applying the
        # skip-accepter optimization (an R1-accepter with no own concerns is
        # skipped when R2 changed nothing -> no rereview call dispatched for it,
        # exactly as the serial path). Capture each reviewer's own concerns so
        # assembly below stays panel-ordered after the concurrent dispatch.
        rereviewers: list[Reviewer] = []
        own_by_reviewer: list[list[Concern]] = []
        for r in panel:
            own = [c for c in open_concerns if c.reviewer == r.name]
            if not own and not r2_changed_artifacts:
                continue  # accepter + nothing changed -> no wasted re-review
            rereviewers.append(r)
            own_by_reviewer.append(own)

        def _rereview_one(
            idx: int,
            *,
            _revs: list[Reviewer] = rereviewers,
            _owns: list[list[Concern]] = own_by_reviewer,
            _responses: list[ConcernResponse] = responses,
            _seen: dict[str, str] = seen,
        ) -> list[Verdict]:
            # Per-round state is bound as default args (not captured by closure)
            # so each worker reads THIS round's slice — no late-binding hazard.
            r = _revs[idx]
            own = _owns[idx]
            own_responses = [resp for resp in _responses
                             if any(resp.concern_id == c.id for c in own)]
            return r.rereview(_seen, own, own_responses,
                              constitution=const, advisory=advisory)

        # Dispatch the independent rereview calls concurrently; results come
        # back in subset (== panel) order so verdict/next_open assembly is
        # identical to the serial path. We map over indices (not the reviewer
        # objects) so each worker reads its OWN ``own``/responses slice — no
        # shared mutable closure state across threads.
        verdict_lists = _map_indices(len(rereviewers), _rereview_one)

        # FR-018 honesty: a concern the reviser left UNADDRESSED — a padded
        # ``"<missing>"`` response (the reviser call failed, or its output parsed
        # to zero artifacts) — is NOT resolved, no matter what a lenient
        # re-reviewer LLM says. Force it open deterministically so an unaddressed
        # concern can never be marked a pass → false convergence. (This is the
        # masking that hid the PROJ-552 plan-stage reviser failure: 26 padded
        # ``<missing>`` responses were re-reviewed as ``pass``.)
        unaddressed = {
            resp.concern_id for resp in responses if resp.response == "<missing>"
        }
        for own, verdicts in zip(own_by_reviewer, verdict_lists, strict=True):
            round_verdicts.extend(verdicts)
            judged = {v.concern_id: v for v in verdicts}
            for c in own:
                v = judged.get(c.id)
                if c.id in unaddressed or v is None or not _resolved(v):
                    next_open.append(c)  # unresolved (unaddressed, failed, stale, self-review, or unjudged)
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

    # F-18 universal citation hard-block: BEFORE declaring convergence, scan the
    # FINAL produced-doc artifacts for unresolved ``[UNVERIFIED: ...]`` markers.
    # If any remain, the stage MUST NOT converge — a fabricated/unverifiable
    # reference is a blocking factual defect. We synthesize SCIENCE-severity
    # concern(s) (one per offending artifact, naming the marker bodies), append
    # them to ``open_concerns`` so the kickback record carries the reason, and
    # fall through to the kickback path. This only ever flips converged->False:
    # the reviser must remove the bad ref to clear it; if it can't within the
    # cap, the (correct) kickback routes the defect to an earlier content stage.
    # Spec 016 FR-017/FR-019: ``_unverified_marker_concerns`` now scans for the
    # unified ``[UNRESOLVED-CLAIM: ...]`` marker (the F-18 ``UNVERIFIED`` names
    # alias the unified gate via ``claims.gate``), so this single pass blocks on
    # both unresolved citations AND any other unresolved factual claim the
    # claim-verification layer could not resolve to a verified value/receipt.
    _guard_reviewer = panel[0].name if panel else "claim_guard"
    # Deterministic backstops (Constitution Principle II): the unified
    # ``[UNRESOLVED-CLAIM: …]`` marker gate AND the spec-quality scanner
    # (surviving [NEEDS CLARIFICATION] / unfilled placeholder / duplicate FR).
    # Both synthesize blocking concerns the reviser must resolve within the cap.
    marker_concerns = _unverified_marker_concerns(
        artifacts, stage=spec.stage, reviewer=_guard_reviewer
    ) + _spec_quality_concerns(
        artifacts, stage=spec.stage, reviewer=_guard_reviewer
    )
    if marker_concerns:
        existing_ids = {c.id for c in open_concerns}
        for c in marker_concerns:
            if c.id not in existing_ids:
                open_concerns.append(c)
                existing_ids.add(c.id)
            if c.id not in {h.id for h in concern_history}:
                concern_history.append(c)

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
