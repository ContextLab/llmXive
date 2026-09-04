import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import Oracle engine for validation
from engines.oracle_policy import OraclePolicyEngine

class FullContextEngine:
    """
    Executes workflows with full policy graphs.
    Invokes oracle_policy.py to validate each step and record specific 'policy-violation' flags.
    """

    def __init__(self, oracle_engine: Optional[OraclePolicyEngine] = None):
        self.oracle_engine = oracle_engine or OraclePolicyEngine()
        self.execution_logs: List[Dict[str, Any]] = []

    def _is_edge_case(self, workflow: Dict[str, Any]) -> bool:
        """
        Detect edge cases: single-node graphs or depth=0.
        """
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])
        
        # Check for single node
        if len(nodes) == 1:
            return True
        
        # Check for depth 0 (no edges, or only self-loops which count as depth 0 in DAG context)
        if len(edges) == 0:
            return True
        
        # Calculate actual depth if possible
        # For a DAG, depth is the longest path. If no edges, depth is 0.
        # If only 1 node, depth is 0.
        return False

    def execute(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single workflow with full context.
        
        Returns an execution log containing:
        - workflow_id
        - status: 'success', 'failed', 'edge_case'
        - context_reduction_pct: percentage reduction (or '[deferred]' for edge cases)
        - policy_violations: list of violations
        - steps: list of step logs
        """
        workflow_id = workflow.get("id", "unknown")
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])
        
        # Check for edge cases first
        is_edge = self._is_edge_case(workflow)
        
        if is_edge:
            # Handle edge case as per T016 requirements
            log_entry = {
                "workflow_id": workflow_id,
                "status": "edge_case",
                "context_reduction_pct": "[deferred]",
                "policy_violations": [],
                "steps": [],
                "message": "Edge case detected: single-node graph or depth=0"
            }
            self.execution_logs.append(log_entry)
            return log_entry

        # Normal execution path
        steps = []
        violations = []
        
        # Simulate execution of each node in topological order (simplified)
        # In a real implementation, we would compute topological sort
        executed_nodes = set()
        
        for node in nodes:
            node_id = node.get("id")
            if node_id in executed_nodes:
                continue
            
            # Validate against Oracle
            is_valid, violation_msg = self.oracle_engine.validate_node(node, workflow)
            
            step_log = {
                "node_id": node_id,
                "status": "executed" if is_valid else "blocked",
                "details": node.get("details", {})
            }
            
            if not is_valid:
                violations.append({
                    "node_id": node_id,
                    "reason": violation_msg
                })
                step_log["status"] = "policy_violation"
            
            steps.append(step_log)
            executed_nodes.add(node_id)
        
        # Calculate context reduction (0% for full context)
        context_reduction_pct = 0.0
        
        # Determine overall status
        if violations:
            status = "failed"
        else:
            status = "success"
        
        log_entry = {
            "workflow_id": workflow_id,
            "status": status,
            "context_reduction_pct": context_reduction_pct,
            "policy_violations": violations,
            "steps": steps,
            "message": "Full context execution completed"
        }
        
        self.execution_logs.append(log_entry)
        return log_entry

    def execute_batch(self, workflows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute a batch of workflows.
        """
        results = []
        for workflow in workflows:
            result = self.execute(workflow)
            results.append(result)
        return results

    def get_logs(self) -> List[Dict[str, Any]]:
        """
        Return all execution logs.
        """
        return self.execution_logs

    def save_logs(self, output_path: str) -> None:
        """
        Save execution logs to a JSON file.
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.execution_logs, f, indent=2)

def main():
    """
    Main entry point for testing the FullContextEngine.
    """
    # Create sample workflow for testing edge cases
    edge_case_workflow = {
        "id": "edge-test-001",
        "nodes": [{"id": "node1", "type": "compute", "policy": "allow"}],
        "edges": []
    }
    
    normal_workflow = {
        "id": "normal-test-001",
        "nodes": [
            {"id": "node1", "type": "compute", "policy": "allow"},
            {"id": "node2", "type": "compute", "policy": "allow"}
        ],
        "edges": [{"source": "node1", "target": "node2"}]
    }
    
    engine = FullContextEngine()
    
    print("Testing edge case (single node)...")
    edge_log = engine.execute(edge_case_workflow)
    print(f"Edge case result: {json.dumps(edge_log, indent=2)}")
    
    print("\nTesting normal workflow...")
    normal_log = engine.execute(normal_workflow)
    print(f"Normal result: {json.dumps(normal_log, indent=2)}")
    
    # Verify edge case handling
    assert edge_log["status"] == "edge_case", f"Expected edge_case, got {edge_log['status']}"
    assert edge_log["context_reduction_pct"] == "[deferred]", f"Expected '[deferred]', got {edge_log['context_reduction_pct']}"
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    main()