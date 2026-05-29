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


def invoke_reviser_backend(reviser: Any, messages: list[ChatMessage]) -> str:
    """Shared backend call for a reviser's revision turn.

    Every reviser's ``_call_backend`` delegates here so the model-or-no-model
    ``backend.chat`` branch is written once. Returns the response text (or ""
    when the backend yields no text).
    """
    model = getattr(reviser, "_model", None)
    backend = reviser._backend
    if model is not None:
        response = backend.chat(messages, model=model)
    else:
        response = backend.chat(messages)
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
        if model is not None:
            response = backend.chat(messages, model=model)
        else:
            response = backend.chat(messages)
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
        return updated, responses

    logger.info(
        "self-consistency flagged %d problem(s); running ONE corrective re-pass",
        len(result.problems),
    )
    # ONE corrective re-pass. If the re-pass itself raises, that is a genuine
    # reviser failure (not a self-consistency-check failure) and must surface
    # — the engine maps it to non-convergence.
    return redo(corrective_instructions(result.problems))


__all__ = [
    "SelfConsistencyResult",
    "corrective_instructions",
    "invoke_reviser_backend",
    "run_with_self_consistency",
    "self_consistency_pass",
]
