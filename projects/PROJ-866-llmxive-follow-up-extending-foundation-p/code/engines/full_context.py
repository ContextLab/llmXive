import json
import os
import sys
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from engines.oracle_policy import OraclePolicyEngine


class FullContextEngine:
    """Executes workflows with full context."""

    def __init__(self):
        self.oracle = OraclePolicyEngine()
        self._verify_oracle_isolation()

    def _verify_oracle_isolation(self) -> None:
        """Runtime check to ensure Oracle is used only for validation.
        
        This enforces Constitution Principle VI: The Oracle must remain the
        independent ground truth. This check verifies that no execution logic
        is implemented directly in this engine that should belong to the Oracle.
        
        Raises:
            RuntimeError: If the engine attempts to implement policy logic itself.
        """
        # Get the source code of this class
        source = inspect.getsource(self.__class__)
        
        # Define forbidden patterns that indicate policy logic implementation
        forbidden_patterns = [
            "if node_data.get('budget')",
            "if node_data.get('sovereignty')",
            "if node_data.get('latency')",
            "node_data['budget'] <",
            "node_data['sovereignty'] >=",
            "node_data['latency'] >=",
            "budget_limit =",
            "sovereignty_check =",
            "latency_threshold =",
            "self._check_budget",
            "self._check_sovereignty",
            "self._check_latency"
        ]
        
        violations = []
        for pattern in forbidden_patterns:
            if pattern in source:
                violations.append(pattern)
        
        if violations:
            raise RuntimeError(
                f"Constitution Principle VI Violation: FullContextEngine contains "
                f"policy logic that should be in OraclePolicyEngine. "
                f"Detected forbidden patterns: {violations}"
            )
        
        # Verify that we are using the Oracle for validation
        if "self.oracle.validate" not in source:
            raise RuntimeError(
                "Constitution Principle VI Violation: FullContextEngine must use "
                "OraclePolicyEngine for validation. No call to self.oracle.validate found."
            )

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
