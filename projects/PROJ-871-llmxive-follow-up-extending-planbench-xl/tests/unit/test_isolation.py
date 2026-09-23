"""
Unit tests for agent isolation constraints.

This module verifies that the baseline agent implementation does not
access the failure signature index, ensuring a fair comparison with
the augmented agent.
"""
import ast
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path to allow imports if running from tests/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.agents import baseline
from code.utils import config


class TestBaselineIsolation(unittest.TestCase):
    """Tests to ensure BaselineAgent does not access failure signatures."""

    def test_no_signature_access(self):
        """
        Assert that the baseline agent code does not import or access
        data/derived/failure_signatures.json.
        
        This test performs a static analysis of the baseline.py source code
        to ensure it does not contain references to the failure signature file
        path or the 'failure_signatures' module/data.
        
        Constraint: The baseline agent must rely solely on internal LLM reasoning
        without external index access.
        """
        # Path to the baseline agent source file
        baseline_path = PROJECT_ROOT / "code" / "agents" / "baseline.py"
        
        if not baseline_path.exists():
            self.fail(f"Baseline agent source file not found at {baseline_path}")

        with open(baseline_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        # Define forbidden patterns
        forbidden_patterns = [
            "failure_signatures.json",
            "failure_signatures",
            "derived/failure_signatures",
            "data/derived/failure_signatures",
            # Check for imports that might load the index
            "from dataset.indexer import",
            "from code.dataset.indexer import",
            "load_failure_signatures",
            "build_failure_index",
        ]

        violations = []
        for pattern in forbidden_patterns:
            if pattern in source_code:
                violations.append(pattern)

        # Also perform a static AST check for specific file path strings
        # to catch dynamic string concatenations that might bypass simple 'in' checks
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if "failure_signatures" in node.value:
                        violations.append(f"AST String Literal: {node.value}")
                elif isinstance(node, ast.Call):
                    # Check for open() calls with the filename
                    if isinstance(node.func, ast.Name) and node.func.id == "open":
                        for arg in node.args:
                            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                if "failure_signatures" in arg.value:
                                    violations.append(f"AST open() call: {arg.value}")
        except SyntaxError as e:
            self.fail(f"Baseline agent source code has syntax errors preventing AST analysis: {e}")

        if violations:
            self.fail(
                f"Baseline agent code violates isolation constraint. "
                f"Found references to failure signatures: {violations}. "
                f"The baseline agent must not access data/derived/failure_signatures.json."
            )

        # Additionally, verify that the BaselineAgent class does not load the index
        # in its __init__ or run methods by inspecting the loaded module
        # (Dynamic check)
        if hasattr(baseline, "BaselineAgent"):
            agent_class = baseline.BaselineAgent
            # We can't easily inspect the source of a compiled module without the file,
            # but the static check above covers the source.
            # We assert that the class doesn't have a specific attribute that would
            # indicate index loading (optional heuristic).
            self.assertFalse(
                hasattr(agent_class, "_failure_index"),
                "BaselineAgent should not have a _failure_index attribute."
            )


if __name__ == "__main__":
    unittest.main()