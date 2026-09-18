import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from engines.oracle_policy import OraclePolicyEngine


class FullContextEngine:
    """Executes workflows with full context."""

    def __init__(self):
        self.oracle = OraclePolicyEngine()

    def execute(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow with full context.

        Args:
            workflow: Workflow dictionary.

        Returns:
            Execution log dictionary.
        """
        workflow_id = workflow["id"]
        nodes = workflow["nodes"]
        edges = workflow["edges"]
        metadata = workflow["metadata"]

        # Check for edge cases
        if len(nodes) <= 1 or metadata.get("depth", 0) == 0:
            return {
                "workflow_id": workflow_id,
                "compression_depth": 0,
                "token_count": 0,
                "policy_violations": [],
                "context_reduction_pct": "[deferred]",
                "is_valid": True,
                "status": "edge_case"
            }

        violations = []
        valid = True

        # Validate each node against Oracle
        for node_id, node_data in nodes.items():
            result = self.oracle.validate(workflow, node_data)
            if not result["compliant"]:
                violations.append({
                    "node_id": node_id,
                    "rule_id": result.get("rule_id", "unknown"),
                    "details": result.get("details", "Constraint violation")
                })
                valid = False

        # Calculate token count (mock for now, replaced by T022 integration)
        # Using a simple heuristic based on node count and constraints
        token_count = len(str(workflow)) * 4  # Rough estimate

        return {
            "workflow_id": workflow_id,
            "compression_depth": 0,
            "token_count": token_count,
            "policy_violations": violations,
            "context_reduction_pct": 0.0,
            "is_valid": valid and len(violations) == 0,
            "status": "normal" if valid else "violation_detected"
        }


def main() -> None:
    """Main entry point for full context execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Full Context Engine")
    parser.add_argument("--workflow", type=str, required=True, help="Input workflow file")
    parser.add_argument("--output", type=str, required=True, help="Output log file")

    args = parser.parse_args()

    engine = FullContextEngine()
    
    with open(args.workflow, 'r') as f:
        workflow = json.load(f)
    
    log = engine.execute(workflow)
    
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(log, f, indent=2)
    
    print(f"Executed {args.workflow} -> {args.output}")


if __name__ == "__main__":
    main()
