import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from config import Config

class SchemaValidator:
    """Validates data against schema definitions."""
    
    def __init__(self, schema_dir: Optional[str] = None):
        self.config = Config()
        self.schema_dir = Path(schema_dir) if schema_dir else self.config.contracts_dir
    
    def validate(self, data: Dict[str, Any], schema_type: str) -> Tuple[bool, List[str]]:
        """
        Validate data against a specific schema.
        
        Args:
            data: The data to validate
            schema_type: One of 'trace', 'metrics', 'benchmark_results', 'compressibility_analysis'
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if schema_type == 'trace':
            return TraceValidator().validate(data)
        elif schema_type == 'metrics':
            return MetricsValidator().validate(data)
        else:
            # Placeholder for other schema types
            return True, []

class TraceValidator:
    """Validates trace data structure."""
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        
        required_fields = ['session_id', 'exact_tool_sequence', 'ground_truth_state']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if 'exact_tool_sequence' in data:
            if not isinstance(data['exact_tool_sequence'], list):
                errors.append("exact_tool_sequence must be a list")
            else:
                for i, step in enumerate(data['exact_tool_sequence']):
                    if 'tool' not in step:
                        errors.append(f"Step {i} missing 'tool'")
                    if 'args' not in step:
                        errors.append(f"Step {i} missing 'args'")
        
        if 'ground_truth_state' in data:
            if not isinstance(data['ground_truth_state'], dict):
                errors.append("ground_truth_state must be a dict")
        
        return len(errors) == 0, errors

class MetricsValidator:
    """Validates metrics data structure."""
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        
        # Check for common metrics fields
        metric_fields = ['session_id', 'sequence_entropy', 'tool_repetition_freq', 'arg_semantic_variance']
        for field in metric_fields:
            if field not in data:
                errors.append(f"Missing metric field: {field}")
        
        return len(errors) == 0, errors
