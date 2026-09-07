import json
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path


class OraclePolicyEngine:
    """Independent rule-based validator for policy compliance."""

    def __init__(self):
        """Initialize the Oracle Policy Engine."""
        self.rules = self._load_default_rules()

    def _load_default_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load default policy rules.

        Returns:
            Dictionary of policy rules.
        """
        return {
            "data_sovereignty": {
                "id": "data_sovereignty",
                "description": "Data must remain within jurisdiction",
                "severity": "high",
            },
            "access_control": {
                "id": "access_control",
                "description": "Access must be properly authenticated",
                "severity": "medium",
            },
            "audit_logging": {
                "id": "audit_logging",
                "description": "All actions must be logged",
                "severity": "low",
            },
        }

    def validate_node(
        self, node: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str]]:
        """Validate a single node against policy rules.

        Args:
            node: The node to validate.
            context: Optional execution context.

        Returns:
            Tuple of (is_valid, list_of_violations).
        """
        violations = []
        constraints = node.get("constraints", [])

        for constraint in constraints:
            rule_id = constraint.get("id")
            if rule_id and rule_id in self.rules:
                # In a real implementation, this would check actual compliance
                # For synthetic data, we simulate validation
                if constraint.get("compliant", True):
                    continue
                else:
                    violations.append(f"Policy violation: {rule_id}")

        return len(violations) == 0, violations

    def validate_workflow(
        self, workflow: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Validate an entire workflow against policy rules.

        Args:
            workflow: The workflow to validate.
            context: Optional execution context.

        Returns:
            Tuple of (is_valid, list_of_violation_details).
        """
        nodes = workflow.get("nodes", {})
        all_violations = []
        is_valid = True

        for node_id, node in nodes.items():
            node_valid, violations = self.validate_node(node, context)
            if not node_valid:
                is_valid = False
                for v in violations:
                    all_violations.append({
                        "node_id": node_id,
                        "rule_id": node.get("constraints", [{}])[0].get("id", "unknown") if node.get("constraints") else "unknown",
                        "message": v
                    })

        return is_valid, all_violations


def main() -> None:
    """Main entry point for Oracle Policy Engine."""
    import argparse

    parser = argparse.ArgumentParser(description="Oracle Policy Engine")
    parser.add_argument("--workflow", type=str, required=True, help="Workflow JSON file")

    args = parser.parse_args()

    with open(args.workflow, "r") as f:
        workflow = json.load(f)

    engine = OraclePolicyEngine()
    is_valid, violations = engine.validate_workflow(workflow)

    result = {
        "workflow_id": workflow.get("id"),
        "is_valid": is_valid,
        "violations": violations,
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
