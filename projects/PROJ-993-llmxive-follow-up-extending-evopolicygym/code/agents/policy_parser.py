"""
Policy parser for calculating cyclomatic complexity and conditional branch counts.
"""
from radon.complexity import cc_visit
from radon.raw import analyze as raw_analyze
import ast
from typing import Dict, Any, List

def parse_policy_complexity(policy_code: str) -> Dict[str, Any]:
    """
    Parse a policy's source code to calculate complexity metrics.

    Args:
        policy_code: The source code of the policy as a string.

    Returns:
        Dictionary containing cyclomatic complexity and branch count.
    """
    try:
        # Parse AST for syntax check
        tree = ast.parse(policy_code)

        # Calculate cyclomatic complexity using radon
        complexity_results = cc_visit(policy_code)
        max_cc = max([r.complexity for r in complexity_results]) if complexity_results else 0

        # Calculate raw metrics
        raw_metrics = raw_analyze(policy_code)

        return {
            "cyclomatic_complexity": max_cc,
            "branches": raw_metrics.branches,
            "loc": raw_metrics.loc,
            "sloc": raw_metrics.sloc
        }
    except SyntaxError as e:
        return {
            "cyclomatic_complexity": -1,
            "branches": -1,
            "loc": -1,
            "sloc": -1,
            "error": f"SyntaxError: {str(e)}"
        }