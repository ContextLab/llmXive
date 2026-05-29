"""Spec 009 T033 / FR-009 / FR-010: real-only guard for speckit emitters.

Before any speckit command commits an artifact, it MUST call
``assert_real_or_raise(path)`` to confirm the artifact passes the
template-vs-real auditor. On failure the guard raises ``TemplateRefused``
with an actionable error naming the rule(s) that fired and what context
appears to be missing; the caller MUST NOT increment project progression
points on refusal (per FR-009, SC-004).

Constitution Principle V (Fail Fast): the guard inspects the file in place
before any further pipeline state mutation.
"""

from __future__ import annotations

import logging as _logging_module
from collections.abc import Sequence
from pathlib import Path
from typing import Final


class TemplateRefused(RuntimeError):
    """Raised by assert_real_or_raise when an artifact would commit as template/partial."""

    def __init__(self, path: Path, classification: str, rules_fired: Sequence[object], missing_context: str):
        self.path = path
        self.classification = classification
        self.rules_fired = rules_fired
        self.missing_context = missing_context
        rule_summary = "; ".join(
            f"{getattr(r, 'rule_id', '?')}={getattr(r, 'evidence_snippet', '?')[:120]}"
            for r in rules_fired
        )
        msg = (
            f"speckit refused to emit a {classification!r} artifact at {path}.\n"
            f"  Rules fired: {rule_summary}\n"
            f"  Missing context: {missing_context}\n"
            f"  Project progression points are NOT incremented.\n"
            f"  Fix by supplying the missing inputs and re-running, or by abstaining cleanly."
        )
        super().__init__(msg)


DEFAULT_TEMPLATES_DIR: Final[str] = ".specify/templates"


def assert_real_or_raise(path: Path | str, *, repo_root: Path | str = ".",
                          templates_dir: Path | str | None = None) -> None:
    """Classify ``path`` against the auditor; raise TemplateRefused on template/partial.

    Caller contract: invoke BEFORE incrementing any project progression points or
    committing further downstream actions. On TemplateRefused, the caller MUST
    log the failure (so maintainers can see what context was missing) and abort.
    """
    from llmxive.audit.template_vs_real import classify

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"speckit guard cannot inspect missing file: {path}")

    tmpl = Path(templates_dir) if templates_dir else Path(repo_root) / DEFAULT_TEMPLATES_DIR
    classification, rules = classify(path, templates_dir=tmpl)

    if classification == "real":
        return  # ok

    # Build an actionable "missing context" hint per FR-010
    rule_ids = {getattr(r, "rule_id", "") for r in rules}
    if "action_required_marker_present" in rule_ids:
        missing = "Template ACTION REQUIRED markers remain — fill in the bracketed sections."
    elif "literal_template_phrases>=3" in rule_ids:
        missing = "Multiple literal template placeholders remain (e.g. [FEATURE NAME], [DATE], [Brief Title]) — substitute concrete values."
    elif "unfilled_bracket_density" in rule_ids:
        missing = "High density of [bracketed] placeholders — likely never filled in by the emitter; ensure the emitter received real project context."
    elif "body_density_short>=60pct" in rule_ids:
        missing = "Most section bodies are essentially empty — the emitter produced headings without prose."
    else:
        missing = "Unknown trigger — check rules_fired for details."

    raise TemplateRefused(
        path=path,
        classification=classification,
        rules_fired=rules,
        missing_context=missing,
    )


def is_real(path: Path | str, *, repo_root: Path | str = ".",
            templates_dir: Path | str | None = None) -> bool:
    """Non-raising variant — returns True iff the artifact would pass the guard."""
    try:
        assert_real_or_raise(path, repo_root=repo_root, templates_dir=templates_dir)
        return True
    except TemplateRefused:
        return False


def guard_emit(path: Path | str, *, repo_root: Path | str = ".",
               templates_dir: Path | str | None = None,
               unlink_on_fail: bool = True,
               logger: _logging_module.Logger | None = None) -> None:
    """Convenience: assert_real_or_raise + on-fail unlink + structured log.

    Used at every speckit emit site as a one-liner per FR-009. On failure the
    file is removed (so the offending stub doesn't pollute the tree) and the
    actionable error is logged BEFORE the exception propagates so callers see
    the missing-context hint even if they catch the exception.
    """
    import logging
    log = logger or logging.getLogger(__name__)
    path = Path(path)
    try:
        assert_real_or_raise(path, repo_root=repo_root, templates_dir=templates_dir)
    except TemplateRefused as exc:
        log.error("speckit guard refused emission: %s", exc)
        if unlink_on_fail and path.exists():
            path.unlink()
        raise
