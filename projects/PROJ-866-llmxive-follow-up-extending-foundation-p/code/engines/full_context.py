import json
import os
import sys
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from engines.oracle_policy import OraclePolicyEngine

class FullContextEngine:
    """
    Executes workflows with full context, validating each node against the Oracle Policy.
    """
    
    def __init__(self):
        self.oracle = OraclePolicyEngine()
    
    def execute(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow with full context.
        
        Args:
            workflow: The workflow to execute
        
        Returns:
            Execution log with validation results
        """
        workflow_id = workflow.get("id", "unknown")
        depth = workflow.get("depth", 0)
        nodes = workflow.get("nodes", [])
        metadata = workflow.get("metadata", {})
        
        # Check if workflow is marked as invalid
        is_valid = metadata.get("is_valid", True)
        
        # Handle edge cases
        if depth == 0 or len(nodes) <= 1:
            return {
                "workflow_id": workflow_id,
                "compression_depth": depth,
                "token_count": 0,
                "policy_violations": [],
                "context_reduction_pct": "[deferred]",
                "is_valid": is_valid,
                "status": "edge_case",
                "violation_details": []
            }
        
        # Execute each node
        violations = []
        violation_details = []
        
        for node in nodes:
            node_id = node.get("id")
            node_type = node.get("type")
            constraints = node.get("constraints", [])
            
            # Validate against Oracle
            is_node_valid, violation = self.oracle.validate(workflow, node)
            
            if not is_node_valid:
                violations.append(violation)
                if node_id and violation:
                    violation_details.append({
                        "node_id": node_id,
                        "rule_id": violation.get("rule_id", "unknown")
                    })
        
        # Calculate token count (simplified - in real implementation, use tiktoken)
        token_count = len(str(workflow)) // 4  # Rough estimate

        return {
            "workflow_id": workflow_id,
            "compression_depth": depth,
            "token_count": token_count,
            "policy_violations": violations,
            "context_reduction_pct": 0.0,  # Full context, no reduction
            "is_valid": is_valid and len(violations) == 0,
            "status": "normal" if len(violations) == 0 else "edge_case",
            "violation_details": violation_details
        }

def main():
    """
    CLI entry point for full context execution.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Execute workflows with full context")
    parser.add_argument("--workflow", type=str, required=True, help="Input workflow file path")
    parser.add_argument("--output", type=str, required=True, help="Output file path for execution logs")
    
    args = parser.parse_args()
    
    # Load workflows
    workflow_file = Path(args.workflow)
    if not workflow_file.exists():
        print(f"Error: Workflow file not found: {args.workflow}", file=sys.stderr)
        sys.exit(1)
    
    with open(workflow_file, 'r', encoding='utf-8') as f:
        workflows = json.load(f)
    
    if not isinstance(workflows, list):
        workflows = [workflows]
    
    # Execute each workflow
    engine = FullContextEngine()
    logs = []
    
    for workflow in workflows:
        log = engine.execute(workflow)
        logs.append(log)
    
    # Save logs
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)
    
    print(f"Executed {len(logs)} workflows")
    print(f"Saved logs to {args.output}")

if __name__ == "__main__":
    main()
