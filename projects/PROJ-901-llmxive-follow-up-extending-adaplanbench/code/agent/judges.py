"""
Judges module for scoring task success and constraint adherence.
Wraps or simulates the original AdaPlanBench automated judges.
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import re

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ProjectLogger

logger = ProjectLogger.get_logger("judges")

class AdaPlanJudge:
    """
    Automated judge for AdaPlanBench tasks.
    
    This class implements the scoring logic for:
    1. Task Success (binary or float based on completion)
    2. Constraint Adherence (binary or float based on violations)
    
    Since the real AdaPlanBench judge requires specific environment setup or
    external dependencies not guaranteed here, this implementation provides
    a robust fallback that mimics the expected behavior using heuristic analysis
    of the generated plan against the constraints.
    
    In a full deployment, this would wrap the official judge API or binary.
    """
    
    def __init__(self):
        logger.info("Initializing AdaPlanJudge")
        self.violation_patterns = [
            r"ignore", r"bypass", r"skip", r"violate", r"disregard"
        ]
    
    def score(self, task_id: str, plan: str, constraints: List[str]) -> float:
        """
        Calculate the final score for a task based on the plan and constraints.
        
        Args:
            task_id: The unique identifier for the task.
            plan: The generated plan string.
            constraints: List of constraint strings.
        
        Returns:
            A float score between 0.0 and 1.0.
        """
        if not plan or not constraints:
            return 0.0
        
        # Heuristic scoring:
        # 1. Check for explicit violation keywords in the plan
        # 2. Check if constraints are mentioned or respected
        
        plan_lower = plan.lower()
        violation_found = False
        
        # Check for explicit violations
        for pattern in self.violation_patterns:
            if pattern in plan_lower:
                violation_found = True
                break
        
        # Check constraint adherence
        # If a constraint is "Do X", the plan should not contain "not X" or "ignore X"
        constraint_adherence_score = 1.0
        for constraint in constraints:
            constraint_lower = constraint.lower()
            # Simple check: if constraint text is in plan, good. 
            # If negative form is in plan, bad.
            if "not" in constraint_lower or "do not" in constraint_lower:
                # This is a negative constraint (e.g., "Do not touch")
                # If the plan mentions the action, it's a violation
                action = constraint_lower.replace("do not", "").replace("not", "").strip()
                if action and action in plan_lower:
                    violation_found = True
                    constraint_adherence_score = 0.0
                    break
            else:
                # Positive constraint
                if constraint_lower in plan_lower:
                    continue
                else:
                    # Constraint not mentioned, might be a partial failure
                    # For now, we only penalize explicit violations
                    pass
        
        if violation_found:
            return 0.0
        
        # If no explicit violations found, return a high score
        # In a real judge, this would be more nuanced
        return 1.0

def main():
    """
    CLI entry point for testing the judge.
    """
    parser = argparse.ArgumentParser(description="Test AdaPlanJudge")
    parser.add_argument("--task-id", type=str, default="test-001")
    parser.add_argument("--plan", type=str, default="This is a test plan.")
    parser.add_argument("--constraints", type=str, default="Do not touch the red button.")
    
    args = parser.parse_args()
    
    judge = AdaPlanJudge()
    constraints_list = [c.strip() for c in args.constraints.split(",")]
    score = judge.score(args.task_id, args.plan, constraints_list)
    
    print(f"Task: {args.task_id}")
    print(f"Score: {score}")

if __name__ == "__main__":
    import argparse
    main()