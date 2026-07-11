import json
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

class OraclePolicyEngine:
    """
    Independent rule-based validator for workflow policies.
    Defines ground-truth validity; separate from execution engines.
    """

    def __init__(self):
        # Define policy rules
        self.policy_rules = {
            'default': self._validate_default,
            'data_sovereignty': self._validate_data_sovereignty,
            'compliance': self._validate_compliance,
            'security': self._validate_security
        }

    def validate_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single node against its policy.
        
        Args:
            node: Dictionary containing node definition
            
        Returns:
            Dictionary with 'valid' boolean and 'message' if invalid
        """
        policy_type = node.get('policy', 'default')
        validator = self.policy_rules.get(policy_type, self._validate_default)
        
        return validator(node)

    def _validate_default(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Default validation - always passes unless explicitly marked invalid."""
        if node.get('invalid', False):
            return {'valid': False, 'message': 'Node explicitly marked as invalid'}
        return {'valid': True, 'message': None}

    def _validate_data_sovereignty(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data sovereignty policy.
        Ensures data stays within allowed regions.
        """
        region = node.get('region', 'global')
        allowed_regions = node.get('allowed_regions', ['global'])
        
        if region not in allowed_regions and 'global' not in allowed_regions:
            return {
                'valid': False, 
                'message': f'Data sovereignty violation: region {region} not in allowed regions {allowed_regions}'
            }
        
        return {'valid': True, 'message': None}

    def _validate_compliance(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Validate compliance policy."""
        compliance_level = node.get('compliance_level', 0)
        required_level = node.get('required_compliance_level', 0)
        
        if compliance_level < required_level:
            return {
                'valid': False,
                'message': f'Compliance violation: level {compliance_level} below required {required_level}'
            }
        
        return {'valid': True, 'message': None}

    def _validate_security(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Validate security policy."""
        security_level = node.get('security_level', 0)
        required_level = node.get('required_security_level', 0)
        
        if security_level < required_level:
            return {
                'valid': False,
                'message': f'Security violation: level {security_level} below required {required_level}'
            }
        
        return {'valid': True, 'message': None}

    def validate_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an entire workflow.
        
        Args:
            workflow: Dictionary containing workflow definition
            
        Returns:
            Dictionary with overall validity and list of violations
        """
        nodes = workflow.get('nodes', [])
        violations = []
        
        for node in nodes:
            result = self.validate_node(node)
            if not result['valid']:
                violations.append(result['message'])
        
        return {
            'valid': len(violations) == 0,
            'violations': violations,
            'message': '; '.join(violations) if violations else None
        }

def main():
    """
    Main entry point for testing the OraclePolicyEngine.
    """
    oracle = OraclePolicyEngine()
    
    # Test various node types
    test_nodes = [
        {'id': 'node1', 'policy': 'default'},
        {'id': 'node2', 'policy': 'data_sovereignty', 'region': 'eu', 'allowed_regions': ['eu', 'us']},
        {'id': 'node3', 'policy': 'compliance', 'compliance_level': 3, 'required_compliance_level': 2},
        {'id': 'node4', 'policy': 'security', 'security_level': 1, 'required_security_level': 2}
    ]
    
    for node in test_nodes:
        result = oracle.validate_node(node)
        print(f"Node {node['id']}: {result}")

if __name__ == '__main__':
    main()
