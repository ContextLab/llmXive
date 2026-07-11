import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from engines.oracle_policy import OraclePolicyEngine

class FullContextEngine:
    """
    Executes workflows with full policy graphs.
    Invokes oracle_policy.py to validate each step and record 'policy-violation' flags.
    """

    def __init__(self, oracle_engine: Optional[OraclePolicyEngine] = None):
        self.oracle_engine = oracle_engine or OraclePolicyEngine()

    def execute(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single workflow with full context.
        
        Args:
            workflow: Dictionary containing workflow definition (nodes, edges, metadata)
            
        Returns:
            Execution log dictionary
        """
        workflow_id = workflow.get('id', 'unknown')
        nodes = workflow.get('nodes', [])
        edges = workflow.get('edges', [])
        depth = workflow.get('depth', 0)
        complexity = workflow.get('complexity', 0)
        
        # Check for edge cases first
        is_edge_case = self._check_edge_cases(nodes, depth)
        
        # Check if workflow is logically valid (possible to execute)
        is_valid = self._check_workflow_validity(nodes, edges)
        
        execution_log = {
            'workflow_id': workflow_id,
            'execution_status': 'edge_case' if is_edge_case else 'success',
            'timestamp': None,  # Would be set by actual execution time
            'is_valid': is_valid,
            'context_reduction_pct': '[deferred]' if is_edge_case else '0.0',
            'node_count': len(nodes),
            'depth': depth,
            'complexity': complexity,
            'policy_violations': [],
            'error_message': None,
            'metadata': {}
        }
        
        if not is_valid:
            execution_log['execution_status'] = 'failed'
            execution_log['error_message'] = 'Workflow is logically impossible to execute'
            return execution_log
        
        if is_edge_case:
            # For edge cases, we still mark them as valid if they are logically sound
            # but set status to edge_case as per T016 requirements
            return execution_log
        
        # Validate each step using Oracle
        violations = self._validate_workflow_steps(workflow)
        
        if violations:
            execution_log['execution_status'] = 'policy_violation'
            execution_log['policy_violations'] = violations
        else:
            execution_log['execution_status'] = 'success'
        
        return execution_log

    def _check_edge_cases(self, nodes: List[Dict], depth: int) -> bool:
        """Check for single-node graphs or depth=0 edge cases."""
        if depth == 0 or len(nodes) <= 1:
            return True
        return False

    def _check_workflow_validity(self, nodes: List[Dict], edges: List[Dict]) -> bool:
        """
        Check if a workflow is logically possible to execute.
        Returns False if:
        - Circular dependencies exist
        - Required nodes are missing
        - Graph structure is invalid
        """
        if not nodes:
            return False
        
        # Build adjacency list
        adj = {node['id']: [] for node in nodes}
        in_degree = {node['id']: 0 for node in nodes}
        
        for edge in edges:
            src = edge['source']
            dst = edge['target']
            if src in adj and dst in adj:
                adj[src].append(dst)
                in_degree[dst] += 1
        
        # Check for cycles using topological sort
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        visited_count = 0
        
        while queue:
            node = queue.pop(0)
            visited_count += 1
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # If we didn't visit all nodes, there's a cycle
        if visited_count != len(nodes):
            return False
        
        return True

    def _validate_workflow_steps(self, workflow: Dict[str, Any]) -> List[str]:
        """
        Validate each step in the workflow using the Oracle Policy Engine.
        Returns a list of policy violation messages.
        """
        violations = []
        nodes = workflow.get('nodes', [])
        
        for node in nodes:
            node_id = node.get('id', 'unknown')
            # Simulate oracle validation for each node
            # In a real implementation, this would check specific policy rules
            oracle_result = self.oracle_engine.validate_node(node)
            
            if not oracle_result.get('valid', True):
                violation_msg = oracle_result.get('message', f'Policy violation at node {node_id}')
                violations.append(violation_msg)
        
        return violations

def main():
    """
    Main entry point for testing the FullContextEngine.
    """
    # Create a simple test workflow
    test_workflow = {
        'id': 'test_workflow_1',
        'nodes': [
            {'id': 'node1', 'type': 'start', 'policy': 'default'},
            {'id': 'node2', 'type': 'process', 'policy': 'data_sovereignty'},
            {'id': 'node3', 'type': 'end', 'policy': 'default'}
        ],
        'edges': [
            {'source': 'node1', 'target': 'node2'},
            {'source': 'node2', 'target': 'node3'}
        ],
        'depth': 2,
        'complexity': 3
    }
    
    engine = FullContextEngine()
    result = engine.execute(test_workflow)
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
