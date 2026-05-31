"""Reviser self-consistency pass — code-level R2 second pass (spec 015 FR-011).

FR-011 (issue §1): "the step's reviser MUST address every R1 concern, run a
self-consistency pass, and emit a structured response + change-log per
concern." The revisers in this package already do address-concerns +
change-log; this module adds the **self-consistency pass** as a CODE-LEVEL
second pass that every reviser runs after its first pass.

The flow each reviser shares (via :func:`run_with_self_consistency`):

1. The reviser produces its first-pass ``(updated_artifacts, responses)``.
2. :func:`self_consistency_pass` makes ONE extra LLM call asking the model to
   audit its OWN revision (resolution / no-new-contradiction / no-unrelated-
   deletion). It parses the structured YAML reply into a list of problems.
3. If problems are reported, the reviser's OWN LLM is re-invoked ONCE (a
   corrective re-pass) with the flagged problems appended to its task; the
   corrected output replaces the first-pass output. The loop runs AT MOST
   once — never infinite.
4. Whichever output is returned, the per-concern change-log is still complete
   (one ``ConcernResponse`` per concern), because the corrective re-pass goes
   through the same ``_parse_response`` padding path as the first pass.

CRITICAL robustness contract (also correct production behaviour): the
self-consistency check must NEVER block or crash the revision. A flaky check
that itself errors (network blip, unparseable reply, an in-test fake backend
that ran out of canned responses) must fall back to the first-pass output.
:func:`self_consistency_pass` therefore catches ALL exceptions from its own
backend call + parsing and returns ``SelfConsistencyResult(ok=True,
problems=[])`` on ANY failure, logging a warning. This is what keeps the
~50 existing single-response-fake reviser tests passing unchanged: their
fake backend has only one queued reply, so the 2nd (self-consistency) call
raises → caught → first-pass output returned.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from llmxive.agents.prompts import load_prompt
from llmxive.backends.base import ChatMessage

from ..types import Concern, ConcernResponse

logger = logging.getLogger(__name__)

_SELF_CONSISTENCY_BLOCK_PATH = "agents/prompts/_shared/reviser_self_consistency_block.md"


@dataclass(slots=True)
class SelfConsistencyResult:
    """Outcome of the self-consistency audit.

    ``ok`` is ``True`` when the revision passed (or when the check itself
    failed and we fell back — a failed check must never block the pipeline).
    ``problems`` lists concrete issues the model flagged; it is empty iff
    ``ok`` is ``True``.
    """

    ok: bool
    problems: list[str] = field(default_factory=list)


def _render_concerns(concerns: list[Concern]) -> str:
    return "\n".join(
        f"- [concern {c.id}] severity={c.severity.value} reviewer={c.reviewer} "
        f"location={c.location or '(unstated)'}\n  {c.text}"
        for c in concerns
    ) or "(no panel concerns this round)"


def _render_responses(responses: list[ConcernResponse]) -> str:
    return "\n".join(
        f"- [response {r.concern_id}] {r.response}\n"
        f"  what_changed: {r.what_changed}\n"
        f"  artifacts_changed: {', '.join(r.artifacts_changed) or '(none)'}"
        for r in responses
    ) or "(the reviser produced no per-concern responses)"


def _render_revised_artifacts(revised_artifacts: dict[str, str]) -> str:
    # Skip sentinel/context keys (``__comments_block__`` etc.) — they are
    # inputs, not artifacts the reviser produced.
    parts = [
        f"## {path}\n\n{text}"
        for path, text in revised_artifacts.items()
        if not (path.startswith("__") and path.endswith("__"))
    ]
    return "\n\n".join(parts) or "(no revised artifacts)"


def _parse_self_consistency_reply(text: str) -> SelfConsistencyResult:
    """Parse the model's YAML audit reply into a :class:`SelfConsistencyResult`.

    Raises on anything it cannot honestly interpret; the caller catches and
    falls back. We deliberately do NOT paper over a malformed reply here —
    fallback (treat as OK) is the caller's explicit policy, applied uniformly
    to every failure mode.
    """
    raw = (text or "").strip()
    # Strip a leading ```yaml / ``` fence if present.
    if raw.startswith("```"):
        lines = raw.splitlines()
        # drop the opening fence line and any trailing fence line
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()

    obj = yaml.safe_load(raw)
    if not isinstance(obj, dict):
        raise ValueError(
            f"self-consistency reply is not a YAML mapping: {type(obj).__name__}"
        )

    # A genuine audit document MUST carry an ``ok`` flag and/or a ``problems``
    # list. Anything else (notably a revision-shaped payload — see
    # ``_looks_like_revision``) is NOT an audit; reject it so the caller falls
    # back rather than mis-reading a stray payload as a clean audit.
    if "ok" not in obj and "problems" not in obj:
        raise ValueError(
            "self-consistency reply has neither 'ok' nor 'problems' key; "
            f"not an audit document (keys={sorted(obj)!r})"
        )

    problems_raw = obj.get("problems") or []
    problems: list[str] = []
    if isinstance(problems_raw, list):
        problems = [str(p).strip() for p in problems_raw if str(p).strip()]

    ok_field = obj.get("ok")
    # ``ok`` and ``problems`` must agree; ``problems`` wins when they conflict
    # (a non-empty problem list is the load-bearing signal for the re-pass).
    ok = bool(ok_field) if ok_field is not None else not problems
    if problems:
        ok = False
    return SelfConsistencyResult(ok=ok, problems=problems)


# qwen3.5-122b (the default panel/reviser model) is a *reasoning* model: its
# hidden chain-of-thought tokens count against the response budget, so the
# OpenAI-shaped 512-token default is fully consumed by reasoning → empty content
# + finish_reason=length → TransientBackendError. Reviser/self-consistency calls
# go straight to ``backend.chat`` (not the router), so they must pass an adequate
# budget themselves. 131072 matches ``chat_with_fallback``'s default and leaves
# ample input room within qwen's 256K context.
_REASONING_MAX_TOKENS = 131_072


def _chat_reasoning_safe(
    backend: Any, messages: list[ChatMessage], model: str | None
) -> Any:
    """``backend.chat`` with a reasoning-safe ``max_tokens``, degrading
    gracefully for backends / test fakes whose signature omits the kwargs."""
    kwargs: dict[str, Any] = {"max_tokens": _REASONING_MAX_TOKENS}
    if model is not None:
        kwargs["model"] = model
    try:
        return backend.chat(messages, **kwargs)
    except TypeError:
        # Fake/legacy signature: retry without max_tokens, then bare.
        kwargs.pop("max_tokens", None)
        try:
            return backend.chat(messages, **kwargs)
        except TypeError:
            return backend.chat(messages)


def invoke_reviser_backend(reviser: Any, messages: list[ChatMessage]) -> str:
    """Shared backend call for a reviser's revision turn.

    Every reviser's ``_call_backend`` delegates here so the model-or-no-model
    ``backend.chat`` branch is written once. Returns the response text (or ""
    when the backend yields no text).
    """
    model = getattr(reviser, "_model", None)
    response = _chat_reasoning_safe(reviser._backend, messages, model)
    return getattr(response, "text", "") or ""


def self_consistency_pass(
    *,
    backend: Any,
    model: str | None,
    revised_artifacts: dict[str, str],
    concerns: list[Concern],
    responses: list[ConcernResponse],
    repo_root: Path,
) -> SelfConsistencyResult:
    """Make ONE LLM call asking the model to audit its OWN revision.

    Returns a :class:`SelfConsistencyResult`. On ANY failure (backend error,
    exhausted fake-backend queue, empty/unparseable reply, missing prompt
    block, or a reply that isn't a well-formed audit document) returns
    ``SelfConsistencyResult(ok=True, problems=[])`` and logs a warning — a
    self-consistency check that itself fails must NEVER block or crash the
    revision (FR-011 robustness + correct production behaviour).
    """
    try:
        block = load_prompt(_SELF_CONSISTENCY_BLOCK_PATH, repo_root=repo_root)
        system_text = (
            "You are auditing a revision you just produced, for self-consistency.\n\n"
            + block
        )
        user_text = (
            "# Concerns the revision was meant to address\n\n"
            f"{_render_concerns(concerns)}\n\n"
            "# Your per-concern change-log (what you claimed you did)\n\n"
            f"{_render_responses(responses)}\n\n"
            "# Your revised artifact(s) (the actual text to audit)\n\n"
            f"{_render_revised_artifacts(revised_artifacts)}\n\n"
            "# Task\n\n"
            "Audit the revision per the self-consistency contract above and "
            "return the single YAML document it specifies."
        )
        messages = [
            ChatMessage(role="system", content=system_text),
            ChatMessage(role="user", content=user_text),
        ]
        response = _chat_reasoning_safe(backend, messages, model)
        reply_text = getattr(response, "text", "") or ""
        if not reply_text.strip():
            raise ValueError("self-consistency reply was empty")
        # _parse_self_consistency_reply REQUIRES an `ok`/`problems` audit
        # document; any other payload (e.g. a stray revision-shaped reply)
        # raises here and is caught below → safe OK fallback.
        return _parse_self_consistency_reply(reply_text)
    except Exception as exc:  # deliberate catch-all (see docstring)
        logger.warning(
            "self_consistency_pass: check failed (%s: %s); falling back to "
            "first-pass output (treating as OK)",
            type(exc).__name__,
            exc,
        )
        return SelfConsistencyResult(ok=True, problems=[])


def corrective_instructions(problems: list[str]) -> str:
    """Render the flagged problems into a task-appendix for the corrective pass."""
    bullet = "\n".join(f"- {p}" for p in problems)
    return (
        "\n\n# Self-consistency corrective pass (REQUIRED)\n\n"
        "Your previous revision was audited and the following problems were "
        "found. Produce a CORRECTED revision that fixes every one of them while "
        "STILL addressing every original concern (one response per concern):\n\n"
        f"{bullet}\n"
    )


def run_with_self_consistency(
    *,
    backend: Any,
    model: str | None,
    repo_root: Path,
    concerns: list[Concern],
    first_pass: tuple[dict[str, str], list[ConcernResponse]],
    redo: Callable[[str], tuple[dict[str, str], list[ConcernResponse]]],
) -> tuple[dict[str, str], list[ConcernResponse]]:
    """Wrap a reviser's first pass with FR-011's self-consistency second pass.

    ``first_pass`` is the reviser's just-produced ``(updated_artifacts,
    responses)``. ``redo`` re-runs the reviser's OWN pass with an extra
    instruction string appended to its task (used for the single corrective
    re-pass). Returns whichever output is final.

    The corrective loop runs AT MOST once: even if a hypothetical second audit
    would still complain, the corrected output is returned as-is. The
    self-consistency call is fully exception-guarded inside
    :func:`self_consistency_pass`, so a flaky check never blocks the revision.
    """
    updated, responses = first_pass
    result = self_consistency_pass(
        backend=backend,
        model=model,
        revised_artifacts=updated,
        concerns=concerns,
        responses=responses,
        repo_root=repo_root,
    )
    if result.ok or not result.problems:
        return _clean_citations(updated, backend=backend, model=model, repo_root=repo_root), responses

    logger.info(
        "self-consistency flagged %d problem(s); running ONE corrective re-pass",
        len(result.problems),
    )
    # ONE corrective re-pass. If the re-pass itself raises, that is a genuine
    # reviser failure (not a self-consistency-check failure) and must surface
    # — the engine maps it to non-convergence.
    corrected, corrected_responses = redo(corrective_instructions(result.problems))
    return _clean_citations(corrected, backend=backend, model=model, repo_root=repo_root), corrected_responses


def _clean_citations(
    artifacts: dict[str, str], *, backend: Any, model: str | None, repo_root: Path
) -> dict[str, str]:
    """Run the citation + claim-verification guards on the reviser's final artifacts.

    1. F-18 :func:`_strip_unresolvable_citations` — network-free structural pass
       (flags malformed/unresolvable references).
    2. Spec 016 :func:`_verify_claims` — the claim-verification layer (extract →
       resolve → re-render with the verified value or a unified
       ``[UNRESOLVED-CLAIM: ...]`` marker). This SUPERSEDES F-19
       ``_ground_factual_claims``: the two layers use conflicting text-mutation
       models (F-19 appends ``[UNVERIFIED]`` markers in place; 016 then
       re-extracts those marker reasons as new "claims" and garbles the prose —
       PROJ-552 root cause 2). 016 is the single source of truth now, so only it
       runs here. ``_ground_factual_claims`` remains defined for any other
       importer but is no longer invoked in the reviser chokepoint.
    """
    cleaned = _strip_unresolvable_citations(artifacts)
    return _verify_claims(cleaned, backend=backend, model=model, repo_root=repo_root)


def _verify_claims(
    artifacts: dict[str, str], *, backend: Any, model: str | None, repo_root: Path
) -> dict[str, str]:
    """Spec 016 (T038/FR-002): run the claim-verification layer on the reviser's
    final artifacts each round — the EARLIEST interception, before the panel
    re-reviews. Each produced-doc artifact is processed by
    :func:`claims.service.process_document`, which extracts every check-worthy
    claim, resolves it (external source or signed execution receipt), and
    re-renders the doc with the verified value (or the unified
    ``[UNRESOLVED-CLAIM: ...]`` marker the engine then hard-blocks on).

    Mirrors :func:`_ground_factual_claims`: gated ON by ``LLMXIVE_CLAIM_LAYER=1``
    (set by the pipeline entrypoint) and OFF by default so the offline
    single-response reviser unit tests stay network-free. Sentinel/context keys
    and non-text artifacts are skipped; any failure is swallowed (logged) so the
    guard never crashes a revision. The verified-value cache keeps the repeated
    per-round passes cheap (FR-015)."""
    import os

    if backend is None:
        logger.info("claim layer: no backend available; skipping claim-verification pass")
        return artifacts
    if os.environ.get("LLMXIVE_CLAIM_LAYER", "0") != "1":
        logger.debug("claim layer: LLMXIVE_CLAIM_LAYER!=1; skipping claim-verification pass")
        return artifacts

    from llmxive.claims.resolve import _extract_project_id
    from llmxive.claims.service import process_document

    cleaned: dict[str, str] = dict(artifacts)
    for path, body in artifacts.items():
        if path.startswith("__") and path.endswith("__"):
            continue
        if not isinstance(body, str) or not body:
            continue
        project_id = _extract_project_id(path)
        if not project_id:
            continue
        try:
            rendered, _claims, gate = process_document(
                body,
                artifact_path=path,
                project_id=project_id,
                backend=backend,
                model=model,
                repo_root=repo_root,
            )
        except Exception as exc:  # never block a revision on the claim layer
            logger.warning(
                "claim layer failed on %s (%s: %s); leaving body untouched",
                path, type(exc).__name__, exc,
            )
            continue
        if rendered != body:
            logger.info(
                "claim layer rewrote %s (blocked=%s)", path, getattr(gate, "blocked", "?")
            )
            cleaned[path] = rendered
    return cleaned


def _ground_factual_claims(
    artifacts: dict[str, str], *, backend: Any, model: str | None, repo_root: Path
) -> dict[str, str]:
    """F-19 factual-grounding guard for the reviser path (LLM + real HTTP).

    Runs :func:`grounding_guard.verify_grounding_and_clean` on every produced
    artifact body so a reviser-introduced fabricated number (e.g. the PROJ-552
    ``1,296`` attached to a free-text "Kauffman & Lambropoulou 2004" citation) is
    marked ``[UNVERIFIED]`` BEFORE the next convergence panel round — breaking the
    fabrication cascade at its source.

    The extraction call is exception-guarded inside the grounding module: with a
    single-response fake backend (the offline reviser tests) the extra extraction
    call exhausts the fake queue → caught → no claims → no-op (no HTTP), so the
    offline reviser tests stay network-free. With a real backend, claims are
    extracted and grounded against their cited sources via real HTTP.

    Sentinel/context keys (``__x__``) and non-text artifacts are skipped. Any
    failure is swallowed (logged) — the guard must never crash a revision. A
    claim skipped for lack of a backend is logged, not silently dropped.
    """
    import os

    from llmxive.agents.grounding_guard import verify_grounding_and_clean

    if backend is None:
        logger.info("grounding guard: no backend available; skipping factual-grounding pass")
        return artifacts
    # The grounding pass makes a REAL LLM extraction call + REAL HTTP grounding
    # calls. It is gated ON in production by the pipeline entrypoint
    # (``cli.run`` sets ``LLMXIVE_GROUNDING_GUARD=1``) and OFF by default so the
    # ~50 offline single-response reviser unit tests — which assert EXACT
    # ``backend.chat`` call counts and run network-free — are unaffected. The
    # real-call F-19 test sets the flag explicitly.
    if os.environ.get("LLMXIVE_GROUNDING_GUARD", "0") != "1":
        logger.debug(
            "grounding guard: LLMXIVE_GROUNDING_GUARD!=1; skipping factual-grounding pass"
        )
        return artifacts

    cleaned: dict[str, str] = dict(artifacts)
    for path, body in artifacts.items():
        if path.startswith("__") and path.endswith("__"):
            continue
        if not isinstance(body, str) or not body:
            continue
        try:
            new_body, report = verify_grounding_and_clean(
                body, backend=backend, model=model, repo_root=repo_root
            )
        except Exception as exc:  # never block a revision on the guard
            logger.warning(
                "grounding guard failed on %s (%s: %s); leaving body untouched",
                path, type(exc).__name__, exc,
            )
            continue
        if report.flagged_count:
            logger.info(
                "grounding guard flagged %d ungrounded claim(s) in %s: %s",
                report.flagged_count, path, report.flagged_values,
            )
            cleaned[path] = new_body
    return cleaned


def _strip_unresolvable_citations(artifacts: dict[str, str]) -> dict[str, str]:
    """F-18 citation guard for the reviser path (network-free).

    Every reviser routes its final output through here (via
    :func:`run_with_self_consistency`), so a reviser-introduced fabricated /
    malformed reference (e.g. ``arXiv:2402.13``) is marked ``[UNVERIFIED]``
    BEFORE the next convergence panel round sees it — breaking the
    fabrication cascade at its source (Constitution Principle II, #239).

    Only STRUCTURALLY unresolvable references are flagged here (no HTTP): a
    malformed arXiv id can be judged fabricated with zero network I/O, which
    keeps the loop fast and offline reviser tests network-free. Full HTTP
    verification runs at the stage-production point
    (``slash_command._validate_artifact_citations`` → ``verify_and_clean``).

    Sentinel/context keys (``__comments_block__`` etc.) and non-text artifacts
    are skipped. Any failure here is swallowed — the guard must never crash a
    revision.
    """
    from llmxive.agents.citation_guard import strip_unresolvable_offline

    cleaned: dict[str, str] = dict(artifacts)
    for path, body in artifacts.items():
        if path.startswith("__") and path.endswith("__"):
            continue
        if not isinstance(body, str) or not body:
            continue
        try:
            new_body, report = strip_unresolvable_offline(body)
        except Exception as exc:  # never block a revision on the guard
            logger.warning(
                "citation guard failed on %s (%s: %s); leaving body untouched",
                path, type(exc).__name__, exc,
            )
            continue
        if report.flagged_count:
            logger.info(
                "citation guard flagged %d unresolvable reference(s) in %s: %s",
                report.flagged_count, path, report.flagged_values,
            )
            cleaned[path] = new_body
    return cleaned


__all__ = [
    "SelfConsistencyResult",
    "corrective_instructions",
    "invoke_reviser_backend",
    "run_with_self_consistency",
    "self_consistency_pass",
]
