import json
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

class OraclePolicyEngine:
    """
    Independent rule-based validator (Oracle) for workflow execution.
    
    Defines ground-truth validity for each step in a workflow.
    Separate from execution engines.
    
    Rules:
    1. Data sovereignty: Confidential/Restricted data cannot be processed at public nodes.
    2. Audit requirement: Nodes with 'audit_required' tag must have a valid audit trail.
    3. Rate limiting: Process nodes exceeding rate limit thresholds are invalid.
    4. Retry policy: Decision nodes must have valid retry paths.
    """

    def __init__(self):
        """Initialize the Oracle Policy Engine."""
        self.violation_types = [
            "data_sovereignty_violation",
            "audit_missing",
            "rate_limit_exceeded",
            "invalid_retry_path"
        ]

    def validate_node(self, node: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a single node against the policy rules.
        
        Args:
            node (Dict[str, Any]): The node to validate.
            context (Dict[str, Any]): Execution context (available data, audit trails, etc.).
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_violations)
        """
        violations = []
        node_type = node.get("node_type")
        policy_tags = node.get("policy_tags", [])
        data_req = node.get("data_requirements", {})
        
        # Rule 1: Data sovereignty
        if node_type in ["process", "decision"]:
            data_level = data_req.get("sovereignty_level", "public")
            context_level = context.get("data_sovereignty_level", "public")
            
            sovereignty_map = {
                "public": 0,
                "internal": 1,
                "confidential": 2,
                "restricted": 3
            }
            
            if sovereignty_map.get(data_level, 0) > sovereignty_map.get(context_level, 0):
                violations.append("data_sovereignty_violation")
        
        # Rule 2: Audit requirement
        if "audit_required" in policy_tags:
            if not context.get("has_valid_audit_trail", False):
                violations.append("audit_missing")
        
        # Rule 3: Rate limiting
        if "rate_limit" in policy_tags:
            if context.get("current_rate", 0) > context.get("max_rate", float("inf")):
                violations.append("rate_limit_exceeded")
        
        # Rule 4: Retry policy
        if "retry_policy" in policy_tags and node_type == "decision":
            if not context.get("has_retry_path", False):
                violations.append("invalid_retry_path")
        
        return len(violations) == 0, violations

    def validate_workflow(self, workflow: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an entire workflow against the policy rules.
        
        Args:
            workflow (Dict[str, Any]): The workflow to validate.
            context (Dict[str, Any]): Execution context.
            
        Returns:
            Dict[str, Any]: Validation result with per-node violations.
        """
        nodes = workflow.get("nodes", [])
        results = {
            "workflow_id": workflow.get("workflow_id"),
            "is_valid": True,
            "node_results": [],
            "total_violations": 0
        }
        
        for node in nodes:
            is_valid, violations = self.validate_node(node, context)
            
            node_result = {
                "node_id": node.get("node_id"),
                "is_valid": is_valid,
                "violations": violations
            }
            results["node_results"].append(node_result)
            
            if not is_valid:
                results["is_valid"] = False
                results["total_violations"] += len(violations)
        
        return results

    def validate_edge(self, edge: Dict[str, Any], workflow: Dict[str, Any]) -> bool:
        """
        Validate a single edge in the workflow.
        
        Args:
            edge (Dict[str, Any]): The edge to validate.
            workflow (Dict[str, Any]): The parent workflow.
            
        Returns:
            bool: True if edge is valid.
        """
        # Check if source and target nodes exist
        source_id = edge.get("source_node_id")
        target_id = edge.get("target_node_id")
        
        node_ids = {n["node_id"] for n in workflow.get("nodes", [])}
        
        if source_id not in node_ids or target_id not in node_ids:
            return False
        
        # Check for cycles (simplified: just check depth ordering)
        nodes_map = {n["node_id"]: n for n in workflow.get("nodes", [])}
        source_depth = nodes_map.get(source_id, {}).get("depth", 0)
        target_depth = nodes_map.get(target_id, {}).get("depth", 0)
        
        if source_depth >= target_depth:
            return False  # Invalid edge (would create cycle or backward link)
        
        return True

def main():
    """
    CLI entry point for testing the Oracle Policy Engine.
    
    Usage:
        python -m engines.oracle_policy --workflow WORKFLOW_FILE --context CONTEXT_FILE
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Oracle Policy Engine")
    parser.add_argument("--workflow", type=str, required=True, help="Workflow JSON file")
    parser.add_argument("--context", type=str, default=None, help="Context JSON file (optional)")
    
    args = parser.parse_args()
    
    # Load workflow
    with open(args.workflow, 'r') as f:
        workflow = json.load(f)
    
    # Load or create context
    if args.context and Path(args.context).exists():
        with open(args.context, 'r') as f:
            context = json.load(f)
    else:
        # Default context
        context = {
            "data_sovereignty_level": "internal",
            "has_valid_audit_trail": True,
            "current_rate": 100,
            "max_rate": 1000,
            "has_retry_path": True
        }
    
    # Validate
    oracle = OraclePolicyEngine()
    result = oracle.validate_workflow(workflow, context)
    
    print(json.dumps(result, indent=2))
    
    return 0 if result["is_valid"] else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
