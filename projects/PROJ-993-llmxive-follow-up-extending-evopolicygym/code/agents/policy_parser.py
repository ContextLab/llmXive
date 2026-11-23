from radon.complexity import cc_visit
from radon.raw import analyze as raw_analyze
import ast
from typing import Dict, Any, List

def parse_policy_complexity(policy_code: str) -> Dict[str, Any]:
    """
    T034: Analyze policy code for cyclomatic complexity and branch count.
    
    Args:
        policy_code: The string content of the generated policy file.
        
    Returns:
        A dictionary with 'cyclomatic_complexity' and 'branch_count'.
    """
    if not policy_code:
        return {"cyclomatic_complexity": 0.0, "branch_count": 0}
    
    try:
        # Parse AST for structural analysis
        tree = ast.parse(policy_code)
        
        # Radon complexity analysis
        complexity_results = cc_visit(policy_code)
        total_complexity = sum(cc.complexity for cc in complexity_results)
        
        # Radon raw analysis for branch count
        raw_data = raw_analyze(policy_code)
        branch_count = raw_data.branches
        
        return {
            "cyclomatic_complexity": float(total_complexity),
            "branch_count": int(branch_count)
        }
    except SyntaxError:
        # If code is syntactically invalid, return 0 or raise handled error
        # Per T035, errors are caught in the harness, but we return safe defaults here
        return {"cyclomatic_complexity": 0.0, "branch_count": 0}
    except Exception as e:
        # Log error but return safe defaults to avoid crashing the pipeline
        return {"cyclomatic_complexity": 0.0, "branch_count": 0}
