"""T014: enforce FR-019 (no LLM in PDF pipeline) via AST inspection.

Walks every module under src/llmxive/pipeline/pdf_pipeline/ and verifies its
import list does NOT contain any banned LLM client. This is a STATIC test
that catches regressions even if the LLM module is never actually called.

If this test fails, do NOT remove the assertion — find and remove the LLM
import. The PDF pipeline must remain deterministic per SC-007.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


BANNED_PREFIXES = (
    "anthropic",
    "openai",
    "google.generativeai",
    "google.genai",
    "cohere",
    "groq",
    "mistralai",
    "ollama",
    "llmxive.backends",
)


def _is_banned(modname: str) -> bool:
    if not modname:
        return False
    parts = modname.split(".")
    head1 = parts[0]
    head2 = ".".join(parts[:2]) if len(parts) >= 2 else ""
    full = modname
    for b in BANNED_PREFIXES:
        if full == b or head1 == b or head2 == b:
            return True
    return False


class TestPdfPipelineLlmFree(unittest.TestCase):
    def test_no_llm_imports(self):
        repo_root = Path(__file__).resolve().parents[2]
        pipeline_dir = repo_root / "src" / "llmxive" / "pipeline" / "pdf_pipeline"
        self.assertTrue(pipeline_dir.exists(), f"missing: {pipeline_dir}")

        bad: list[tuple[str, str, int]] = []
        for py in pipeline_dir.rglob("*.py"):
            try:
                tree = ast.parse(py.read_text())
            except SyntaxError as e:
                self.fail(f"syntax error in {py}: {e}")
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if _is_banned(alias.name):
                            bad.append((str(py), alias.name, node.lineno))
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    if _is_banned(mod):
                        bad.append((str(py), mod, node.lineno))

        if bad:
            msg = "\n".join(
                f"  {p}:{ln} — `{m}` is a banned LLM module per FR-019 / SC-007"
                for p, m, ln in bad
            )
            self.fail(f"FR-019 violation — LLM imports in PDF pipeline:\n{msg}")


if __name__ == "__main__":
    unittest.main()
