from radon.complexity import cc_visit
from radon.raw import analyze as raw_analyze
import ast
from typing import Dict, Any, List

def parse_policy_complexity(policy_code: str) -> Dict[str, Any]:
    """
    Parses Python policy code to calculate cyclomatic complexity and branch count.
    """
    try:
        # Parse AST for branch count
        tree = ast.parse(policy_code)
        branch_count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.ExceptHandler)):
                branch_count += 1
            elif isinstance(node, ast.BoolOp):
                branch_count += len(node.values) - 1
        
        # Use radon for cyclomatic complexity
        # radon might raise SyntaxError if code is invalid, which is handled by caller
        try:
            complexity_results = cc_visit(policy_code)
            if complexity_results:
                # Get the max complexity of any function in the code
                max_cc = max([res.cc for res in complexity_results])
            else:
                max_cc = 1.0 # Default for simple scripts
        except Exception:
            # If radon fails (e.g. non-Python content), fallback to 1.0
            max_cc = 1.0

        return {
            "complexity": max_cc,
            "branches": branch_count
        }
    except SyntaxError as e:
        # T035: Catch syntactically invalid code
        raise e
    except Exception as e:
        raise e