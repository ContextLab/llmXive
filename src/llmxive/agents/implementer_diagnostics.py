"""Implementer failsafe diagnostic mode (spec 015 T042 / FR-034).

When the implementer agent's per-round failsafe trips (e.g. N consecutive
zero-success rounds), the legacy behavior was simply to halt at the
deleted ``PAPER_REVISION_BLOCKED`` stage. This module replaces that
behavior with a **learning loop**:

  1. :func:`classify_failure` reads the implementer's error logs and
     decides what KIND of failure the round encountered: broken LaTeX
     compile / missing tool / model error / parse error / unknown.
  2. :func:`failure_to_concern` synthesizes a :class:`Concern` carrying
     the diagnosis (severity = METHODOLOGY for syntactic/parsing failures
     that the next round can plausibly retry, SCIENCE for capability
     gaps that require richer tooling).
  3. The implementer's failsafe block calls
     :func:`llmxive.convergence.revision_adapter.kickback_to_revision_spec`
     with a synthetic KickbackRecord wrapping that Concern. The next
     round's auto-revisions tasks.md then encodes the diagnosed problem
     as WORK to be done, rather than as a halt.

Only when :func:`classify_failure` returns ``UNKNOWN`` does the project
reach the new generic :class:`Stage.AGENT_BLOCKED` failsafe — the operator
clears that via ``llmxive project unblock-agent`` once they've edited the
action items.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from llmxive.convergence.types import (
    Concern,
    KickbackRecord,
    Severity,
)


class FailureClass(StrEnum):
    """The diagnostic-mode failure classes the failsafe can recover from.

    ``UNKNOWN`` is the ONE class that escalates to ``Stage.AGENT_BLOCKED``.
    Every other class produces a synthetic Concern that the next round
    of work can act on."""

    BROKEN_LATEX = "broken_latex"
    MISSING_TOOL = "missing_tool"
    MODEL_ERROR = "model_error"
    PARSE_ERROR = "parse_error"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FailureClassification:
    """The diagnostic verdict for one failing round."""

    cls: FailureClass
    evidence: str  # the line(s) of error text the classifier matched on
    suggested_severity: Severity


# --- pattern catalogue --------------------------------------------------

# Order matters: more specific patterns precede more general ones so a
# LaTeX error caused by a missing package is BROKEN_LATEX (the user
# action is "fix the package import"), not MISSING_TOOL.
#
# Each entry: (pattern, FailureClass, suggested severity for the Concern).

_PATTERNS: Final[tuple[tuple[re.Pattern[str], FailureClass, Severity], ...]] = (
    # --- BROKEN_LATEX (syntactic LaTeX failures — METHODOLOGY) ----------
    (re.compile(r"!\s*LaTeX Error:", re.IGNORECASE),
     FailureClass.BROKEN_LATEX, Severity.METHODOLOGY),
    (re.compile(r"^\s*!\s+Undefined control sequence", re.IGNORECASE | re.MULTILINE),
     FailureClass.BROKEN_LATEX, Severity.METHODOLOGY),
    (re.compile(r"^\s*!\s+Missing\s+\\?[\w]+", re.IGNORECASE | re.MULTILINE),
     FailureClass.BROKEN_LATEX, Severity.METHODOLOGY),
    (re.compile(r"lualatex\s+(?:failed|exited\s+with|non-zero)", re.IGNORECASE),
     FailureClass.BROKEN_LATEX, Severity.METHODOLOGY),
    (re.compile(r"Emergency\s+stop", re.IGNORECASE),
     FailureClass.BROKEN_LATEX, Severity.METHODOLOGY),
    # --- MISSING_TOOL (executable / API / module not available — SCIENCE) -
    (re.compile(
        r"command not found|No such file or directory.*?(?:lualatex|pdflatex|bibtex|biber)",
        re.IGNORECASE),
     FailureClass.MISSING_TOOL, Severity.SCIENCE),
    (re.compile(r"ModuleNotFoundError", re.IGNORECASE),
     FailureClass.MISSING_TOOL, Severity.SCIENCE),
    (re.compile(r"ImportError", re.IGNORECASE),
     FailureClass.MISSING_TOOL, Severity.SCIENCE),
    (re.compile(r"executable\s+not\s+found", re.IGNORECASE),
     FailureClass.MISSING_TOOL, Severity.SCIENCE),
    # --- MODEL_ERROR (backend / model / timeout — SCIENCE) ---------------
    (re.compile(r"timeout|TimeoutError|read\s+timed\s+out", re.IGNORECASE),
     FailureClass.MODEL_ERROR, Severity.SCIENCE),
    (re.compile(r"(?:HTTP|http)\s+(?:5\d\d|429)", re.IGNORECASE),
     FailureClass.MODEL_ERROR, Severity.SCIENCE),
    (re.compile(r"rate.?limit|throttl", re.IGNORECASE),
     FailureClass.MODEL_ERROR, Severity.SCIENCE),
    (re.compile(r"context(?:_length)?(?:_exceeded|\s+exceeded)", re.IGNORECASE),
     FailureClass.MODEL_ERROR, Severity.SCIENCE),
    (re.compile(r"LLM call failed", re.IGNORECASE),
     FailureClass.MODEL_ERROR, Severity.SCIENCE),
    # --- PARSE_ERROR (the model emitted unparseable output — METHODOLOGY) -
    (re.compile(r"did\s+not\s+emit\s+a\s+parseable\s+JSON\s+edit", re.IGNORECASE),
     FailureClass.PARSE_ERROR, Severity.METHODOLOGY),
    (re.compile(r"JSONDecodeError|json\.decoder\.JSONDecodeError", re.IGNORECASE),
     FailureClass.PARSE_ERROR, Severity.METHODOLOGY),
    (re.compile(r"yaml\.YAMLError|yaml\.scanner\.ScannerError", re.IGNORECASE),
     FailureClass.PARSE_ERROR, Severity.METHODOLOGY),
    (re.compile(r"ambiguous:\s+search\s+string\s+matches", re.IGNORECASE),
     FailureClass.PARSE_ERROR, Severity.METHODOLOGY),
    (re.compile(r"no-match:\s+search\s+string\s+not\s+found", re.IGNORECASE),
     FailureClass.PARSE_ERROR, Severity.METHODOLOGY),
)


def classify_failure(
    error_log_text: str, last_command: str | None = None,
) -> FailureClassification:
    """Classify a failing implementer round's error text.

    Returns a :class:`FailureClassification` whose ``cls`` is ``UNKNOWN``
    only when no pattern matches — that's the signal to halt at
    :class:`Stage.AGENT_BLOCKED`.

    Parameters
    ----------
    error_log_text : str
        The aggregated error context the implementer accumulated this
        round — model_response_excerpts, lualatex log tails,
        FileNotFoundError messages, etc.
    last_command : str | None
        The last subprocess command run (e.g. ``lualatex``,
        ``python script.py``); used as a hint when the patterns
        otherwise tie (e.g. "no such file or directory" → MISSING_TOOL
        when the command was a build tool, PARSE_ERROR otherwise).
    """
    if not error_log_text and not last_command:
        return FailureClassification(
            cls=FailureClass.UNKNOWN,
            evidence="(no error log text supplied)",
            suggested_severity=Severity.FATAL,
        )

    haystack = error_log_text or ""
    if last_command:
        haystack = f"$ {last_command}\n{haystack}"

    for pat, cls, sev in _PATTERNS:
        m = pat.search(haystack)
        if m is not None:
            # Capture a window of evidence around the match (±80 chars)
            # so the synthesized Concern carries enough context for the
            # next round to be actionable.
            start = max(0, m.start() - 80)
            end = min(len(haystack), m.end() + 80)
            return FailureClassification(
                cls=cls,
                evidence=haystack[start:end].strip(),
                suggested_severity=sev,
            )

    return FailureClassification(
        cls=FailureClass.UNKNOWN,
        evidence=haystack[-300:].strip(),
        suggested_severity=Severity.FATAL,
    )


# --- concern synthesis --------------------------------------------------

_CLASS_TO_HINT: Final[dict[FailureClass, str]] = {
    FailureClass.BROKEN_LATEX: (
        "The previous implementer round's edit produced a non-compiling "
        "manuscript. Diagnose the LaTeX error in the captured evidence "
        "and re-emit the smallest edit that fixes it without changing "
        "the intended semantics. Verify with `lualatex` before claiming "
        "the task is done."
    ),
    FailureClass.MISSING_TOOL: (
        "The implementer's environment is missing a tool or module the "
        "task depends on. Either swap to an available equivalent (and "
        "record the substitution in the spec) or, if the tool is "
        "necessary, mark the task as ``needs-external-data`` so the "
        "operator can provision it."
    ),
    FailureClass.MODEL_ERROR: (
        "The backend call failed (timeout / rate-limit / context-length / "
        "5xx). Retry with the centralised retry-with-backoff path or, if "
        "the context exceeds budget, reduce the artifact view via the "
        "SSoT summarizer (``llmxive.tools.summarize``) before re-emitting "
        "the edit."
    ),
    FailureClass.PARSE_ERROR: (
        "The previous implementer round emitted output that the parser "
        "could not consume (malformed JSON edit / ambiguous search / "
        "no-match). Re-emit a SINGLE, well-formed edit per the implementer "
        "prompt's contract — anchor the search to a uniquely-occurring "
        "substring and supply the FULL new file content for diff edits."
    ),
}


def failure_to_concern(
    classification: FailureClassification,
    *,
    artifact_path: str,
    reviewer: str = "implementer_diagnostics",
    round_num: int = 0,
) -> Concern:
    """Synthesize a :class:`Concern` carrying the diagnosis.

    The concern's ``text`` includes the classifier's hint + the captured
    evidence, so the next round's revised tasks.md is concrete enough to
    actually act on.
    """
    if classification.cls == FailureClass.UNKNOWN:
        raise ValueError(
            "failure_to_concern() refuses to synthesize a concern for "
            "FailureClass.UNKNOWN — the caller should halt at "
            "Stage.AGENT_BLOCKED instead. Got: "
            f"{classification.evidence!r}"
        )
    hint = _CLASS_TO_HINT[classification.cls]
    text = (
        f"[failsafe-diagnostic:{classification.cls.value}] {hint} "
        f"Captured evidence: {classification.evidence!r}"
    )[:500]  # ActionItem text field is bounded to 500 chars; mirror that.
    # Deterministic concern id derived from class + evidence so the SAME
    # diagnosed failure across consecutive rounds collapses to ONE id
    # (lets the implementer's anti-duplicate logic dedupe properly).
    digest = hashlib.sha1(
        f"{classification.cls.value}::{classification.evidence}".encode()
    ).hexdigest()[:12]
    return Concern(
        id=digest,
        reviewer=reviewer,
        severity=classification.suggested_severity,
        artifact=artifact_path,
        location="",
        text=text,
        round=round_num,
    )


def synth_kickback_from_failure(
    classification: FailureClassification,
    *,
    project_id: str,
    artifact_path: str,
    round_num: int,
) -> KickbackRecord:
    """Build a synthetic :class:`KickbackRecord` from a diagnosed failure.

    Used by the implementer's failsafe to invoke
    :func:`llmxive.convergence.revision_adapter.kickback_to_revision_spec`
    without going through the full convergence engine."""
    concern = failure_to_concern(
        classification, artifact_path=artifact_path, round_num=round_num,
    )
    return KickbackRecord(
        from_stage="paper_review",  # the failsafe was reached in paper-review-driven implementation
        to_stage="paper_review",    # next round's implementer pass picks the spec back up
        worst_severity=concern.severity,
        unresolved_concerns=[concern],
        artifact_links=[artifact_path],
        reason=(
            f"[implementer failsafe diagnostic: {classification.cls.value}] "
            f"project={project_id} round={round_num}; routed back to next "
            f"implementer pass with a synthesized work-item rather than "
            f"halting at Stage.AGENT_BLOCKED."
        ),
    )


__all__ = [
    "FailureClass",
    "FailureClassification",
    "classify_failure",
    "failure_to_concern",
    "synth_kickback_from_failure",
]
