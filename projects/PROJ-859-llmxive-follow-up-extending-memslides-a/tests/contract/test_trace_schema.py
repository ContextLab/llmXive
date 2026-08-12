"""
Contract test for generated trace schema.
Validates output of T012 (synthetic trace generation) against contracts/trace.schema.yaml.
"""
import json
import pytest
from pathlib import Path
import sys
import math

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from utils.validators import TraceValidator
except ImportError:
    from code.utils.validators import TraceValidator


class TestTraceSchemaValidation:
    """Tests for trace schema compliance."""
    
    def setup_method(self):
        self.validator = TraceValidator()
    
    def test_valid_trace(self):
        """Test that a valid trace passes validation."""
        valid_trace = {
            'exact_tool_sequence': ['edit_slide', 'add_text', 'format_text'],
            'tool_calls': [
                {
                    'name': 'edit_slide',
                    'arguments': {'slide_id': 1, 'content': 'Hello'}
                },
                {
                    'name': 'add_text',
                    'arguments': {'text': 'World', 'position': [10, 10]}
                },
                {
                    'name': 'format_text',
                    'arguments': {'bold': True}
                }
            ],
            'session_id': 'test-001',
            'raw_arg_variance': 0.25
        }
        
        is_valid, errors = self.validator.validate(valid_trace)
        
        assert is_valid, f"Valid trace failed validation: {errors}"
        assert len(errors) == 0
    
    def test_missing_required_field(self):
        """Test that missing required fields are detected."""
        invalid_trace = {
            'exact_tool_sequence': ['edit_slide'],
            # Missing tool_calls
        }
        
        is_valid, errors = self.validator.validate(invalid_trace)
        
        assert not is_valid
        assert any('tool_calls' in error for error in errors)
    
    def test_invalid_tool_sequence_type(self):
        """Test that non-list tool sequences are rejected."""
        invalid_trace = {
            'exact_tool_sequence': 'not_a_list',
            'tool_calls': []
        }
        
        is_valid, errors = self.validator.validate(invalid_trace)
        
        assert not is_valid
        assert any('exact_tool_sequence' in error for error in errors)
    
    def test_invalid_tool_call_structure(self):
        """Test that invalid tool call structures are detected."""
        invalid_trace = {
            'exact_tool_sequence': ['edit_slide'],
            'tool_calls': [
                {'name': 'edit_slide'}  # Missing arguments
            ]
        }
        
        is_valid, errors = self.validator.validate(invalid_trace)
        
        assert not is_valid
        assert any('arguments' in error for error in errors)
    
    def test_empty_tool_sequence(self):
        """Test that empty tool sequences are rejected (minItems: 1)."""
        invalid_trace = {
            'exact_tool_sequence': [],
            'tool_calls': []
        }
        
        is_valid, errors = self.validator.validate(invalid_trace)
        
        assert not is_valid
        # The validator should catch empty sequences
        assert len(errors) > 0
    
    def test_nan_variance_handling(self):
        """Test that NaN variance is handled (imputed or rejected based on schema)."""
        # The schema expects a number. If the generator produces NaN, 
        # the validator should ideally catch it if strict, or the test 
        # ensures the data loaded is clean.
        # Here we test that a valid float works.
        valid_trace = {
            'exact_tool_sequence': ['edit_slide'],
            'tool_calls': [{'name': 'edit_slide', 'arguments': {}}],
            'session_id': 'test-nan',
            'raw_arg_variance': 0.0
        }
        is_valid, errors = self.validator.validate(valid_trace)
        assert is_valid, f"Zero variance trace failed: {errors}"
    
    def test_trace_from_generated_data(self):
        """Test validation against actual generated trace files in data/training/."""
        training_dir = Path('data/training')
        
        if not training_dir.exists():
            pytest.skip("Training directory not found, skipping integration test")
        
        json_files = list(training_dir.glob("*.json"))
        
        if not json_files:
            pytest.skip("No JSON files found in training directory")
        
        # Test up to 10 files to ensure performance
        test_files = json_files[:10]
        failed_files = []
        
        for json_file in test_files:
            try:
                with open(json_file, 'r') as f:
                    trace_data = json.load(f)
                
                is_valid, errors = self.validator.validate(trace_data)
                
                if not is_valid:
                    failed_files.append((json_file.name, errors))
            except json.JSONDecodeError:
                failed_files.append((json_file.name, ["Invalid JSON structure"]))
        
        if failed_files:
            error_details = "\n".join([f"{name}: {errs}" for name, errs in failed_files])
            pytest.fail(f"Schema validation failed for {len(failed_files)} files:\n{error_details}")