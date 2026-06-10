"""promptfoo python assertion — validates a reviewer response with the
PRODUCTION parser, not a parallel re-implementation (Constitution I).

A response passes iff it would survive
``research_reviewer.handle_response``'s deterministic validation chain:
frontmatter regex → YAML mapping → sane ``verdict``. Test cases that set
``expected_not_accept: true`` additionally fail if a deliberately flawed
artifact bundle is accepted (the quality gate from issue #294 Phase 2 /
issue #216).

promptfoo contract: ``get_assert(output, context) -> GradingResult dict``.
"""

from __future__ import annotations

VALID_VERDICTS = {"accept", "minor_revision", "full_revision", "reject"}


def get_assert(output: str, context: dict) -> dict:
    import yaml

    from llmxive.agents.research_reviewer import _FRONTMATTER_RE

    def fail(reason: str) -> dict:
        return {"pass": False, "score": 0.0, "reason": reason}

    text = (output or "").strip()
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return fail("response missing YAML frontmatter (--- delimiters)")
    try:
        front = yaml.safe_load(match.group("frontmatter"))
    except yaml.YAMLError as exc:
        return fail(f"frontmatter is not valid YAML: {exc}")
    if not isinstance(front, dict):
        return fail("frontmatter must be a YAML mapping")
    verdict = front.get("verdict")
    if verdict not in VALID_VERDICTS:
        return fail(f"verdict {verdict!r} not in {sorted(VALID_VERDICTS)}")
    if not match.group("body").strip():
        return fail("review body is empty")

    test_vars = (context or {}).get("vars") or {}
    if test_vars.get("expected_not_accept") and verdict == "accept":
        return fail(
            "deliberately flawed artifact bundle was accepted — "
            "reviewer quality regression"
        )
    return {
        "pass": True,
        "score": 1.0,
        "reason": f"valid review record shape (verdict={verdict})",
    }
