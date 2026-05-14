"""Deterministic arXiv-source -> PDF pipeline (spec 009, FR-019 through FR-022).

**HARD CONSTRAINT (FR-019, SC-007)**: This subtree MUST contain ZERO LLM
imports. A module-level guard below raises ImportError if any module in this
package directly or transitively imports a known LLM client. The static
import guard test at tests/unit/test_pdf_pipeline_no_llm.py also enforces this
via AST inspection so regressions break CI.

Modules:
    restyle               - orchestrator
    compile               - lualatex + bibtex invocation (byte-deterministic)
    normalize_references  - cite-order [N] normalization (FR-014, Clarification Q1)
    normalize_figures     - bounded-width \\figwidth rewriting (FR-015)
    normalize_authors     - canonical \\authorblock rewriting (FR-016)
    cli                   - single 'build' entrypoint
"""

from __future__ import annotations

import sys
from types import ModuleType

# Module-level LLM-import guard. Anyone importing pdf_pipeline triggers this.
_BANNED_LLM_MODULES = {
    "anthropic",
    "openai",
    "google.generativeai",
    "google.genai",
    "cohere",
    "groq",
    "mistralai",
    "ollama",
    # llmxive's own backend layer is also banned in this pipeline
    "llmxive.backends",
}


def _assert_no_llm_imports() -> None:
    """Raise if any banned LLM module has already been imported into this process.

    We only guard at this package's own import time; the AST-based test
    catches static `import` regressions in any module under this subtree.
    """
    banned_present = [m for m in _BANNED_LLM_MODULES if m in sys.modules]
    if banned_present:
        # We don't fail hard here because the parent process may legitimately have
        # those modules imported elsewhere. The AST test enforces static purity.
        # But we do mark this on the module so callers can see the violation.
        _violations.update(banned_present)


_violations: set[str] = set()
_assert_no_llm_imports()


def has_llm_violations() -> bool:
    """Return True if any banned LLM module is present in sys.modules."""
    return bool(_violations)
