"""Guard: the LLM-call resilience policy stays CENTRALIZED.

Every LLM call in the package must route through the central router entry points
(``router.reasoning_chat`` for a given backend, ``router.chat_with_fallback`` /
``router.chat_with_model_fallback`` for the backend-resolving path) so it
automatically gets peer-model fallback + retry+jitter+backoff + the per-model
circuit breaker + the per-request deadline + the deadline/302 fast-fail. A direct
``backend.chat(...)`` bypasses ALL of that.

This used to be re-implemented per module (7 copies of ``_chat_reasoning_safe``,
8 copies of ``_REASONING_MAX_TOKENS``). These tests convert the convention into an
enforced invariant so the duplication can't creep back.
"""

from __future__ import annotations

import ast
import pathlib
import re

_SRC = pathlib.Path(__file__).resolve().parents[2] / "src" / "llmxive"

# The ONLY place a raw ``<backend>.chat(...)`` invocation may appear: the router's
# ``_chat_one_model`` is the single adapter that actually pokes a backend (with
# signature degradation for stub/fake backends). Everything else routes through
# the router's public functions.
_ALLOWED_CHAT_CALL_FILES = {"backends/router.py"}


def _src_files() -> list[pathlib.Path]:
    return [p for p in _SRC.rglob("*.py") if "__pycache__" not in p.parts]


def _rel(p: pathlib.Path) -> str:
    return p.relative_to(_SRC).as_posix()


def test_no_direct_chat_call_outside_central_router() -> None:
    """No module may call ``.chat(...)`` directly (AST-level, so docstring/comment
    mentions don't count) except the allowlisted central adapter."""
    offenders: list[str] = []
    for py in _src_files():
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "chat"
            ):
                rel = _rel(py)
                if rel not in _ALLOWED_CHAT_CALL_FILES:
                    offenders.append(f"{rel}:{node.lineno}")
    assert not offenders, (
        "Direct `.chat(` LLM call(s) bypass the central resilience policy "
        "(fallback/retry/breaker/deadline). Route through "
        "router.reasoning_chat / chat_with_fallback / chat_with_model_fallback "
        f"instead. Offenders: {offenders}"
    )


def test_single_reasoning_budget_source_of_truth() -> None:
    """``REASONING_MAX_TOKENS`` is defined exactly ONCE (the router), and the old
    per-module ``_REASONING_MAX_TOKENS`` name is gone everywhere."""
    reasoning_defs: list[str] = []
    legacy_defs: list[str] = []
    for py in _src_files():
        for line in py.read_text(encoding="utf-8").splitlines():
            if re.match(r"\s*REASONING_MAX_TOKENS\s*=", line):
                reasoning_defs.append(_rel(py))
            if re.match(r"\s*_REASONING_MAX_TOKENS\s*=", line):
                legacy_defs.append(_rel(py))
    assert reasoning_defs == ["backends/router.py"], (
        f"REASONING_MAX_TOKENS must be defined once (in the router); found "
        f"{reasoning_defs}"
    )
    assert not legacy_defs, (
        f"the per-module `_REASONING_MAX_TOKENS` constant must not be "
        f"reintroduced — import REASONING_MAX_TOKENS from the router: {legacy_defs}"
    )


def test_no_per_module_reasoning_wrapper_reintroduced() -> None:
    """No module may redefine its own ``_chat_reasoning_safe`` wrapper — that was
    the duplicated policy this centralization removed."""
    bad = [
        _rel(py)
        for py in _src_files()
        if "def _chat_reasoning_safe" in py.read_text(encoding="utf-8")
    ]
    assert not bad, (
        "per-module `_chat_reasoning_safe` wrappers must not be reintroduced; "
        f"use router.reasoning_chat instead: {bad}"
    )
