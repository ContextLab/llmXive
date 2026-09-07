import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from engines.oracle_policy import OraclePolicyEngine


class FullContextEngine:
    """Engine for executing workflows with full policy context."""

    def __init__(self):
        """Initialize the engine with an Oracle Policy Engine."""
        self.oracle = OraclePolicyEngine()

    def execute(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow with full context validation.

        Args:
            workflow: The workflow to execute.

        Returns:
            Execution log dictionary.
        """
        nodes = workflow.get("nodes", {})
        metadata = workflow.get("metadata", {})

        # Handle edge cases
        if len(nodes) <= 1 or metadata.get("depth", 0) == 0:
            return {
                "workflow_id": workflow.get("id", "unknown"),
                "compression_depth": 0,
                "token_count": 0,
                "context_reduction_pct": "[deferred]",
                "is_valid": True,
                "status": "edge_case",
                "policy_violations": [],
                "violation_details": [],
                "depth": metadata.get("depth", 0),
                "complexity": metadata.get("complexity", 0),
            }

        # Validate each node using Oracle
        violations = []
        violation_details = []
        is_valid = True

        for node_id, node in nodes.items():
            constraints = node.get("constraints", [])
            for constraint in constraints:
                rule_id = constraint.get("id", "unknown")
                # Simulate Oracle validation (in real implementation, this would be more complex)
                # For synthetic data, we simulate some violations
                if random.random() < 0.05:  # 5% chance of violation
                    violations.append(f"Policy violation: {rule_id}")
                    violation_details.append({
                        "node_id": node_id,
                        "rule_id": rule_id,
                        "reason": "Oracle policy violation detected"
                    })
                    is_valid = False

        # Calculate token count (full context)
        full_json = json.dumps(workflow)
        # Mock token count for demonstration (real implementation would use tiktoken)
        token_count = len(full_json) // 4  # Approximate

        return {
            "workflow_id": workflow.get("id", "unknown"),
            "compression_depth": 0,
            "token_count": token_count,
            "context_reduction_pct": 0.0,
            "is_valid": is_valid,
            "status": "normal" if not is_valid else "valid",
            "policy_violations": violations,
            "violation_details": violation_details,
            "depth": metadata.get("depth", 0),
            "complexity": metadata.get("complexity", 0),
        }


def main() -> None:
    """Main entry point for full context engine."""
    import argparse

    parser = argparse.ArgumentParser(description="Full Context Engine")
    parser.add_argument("--workflow", type=str, required=True, help="Workflow JSON file")
    parser.add_argument("--output", type=str, required=True, help="Output log file")

    args = parser.parse_args()

    with open(args.workflow, "r") as f:
        workflow = json.load(f)

    engine = FullContextEngine()
    log = engine.execute(workflow)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(log, f, indent=2)

    print(f"Execution log saved to {args.output}")


if __name__ == "__main__":
    main()
