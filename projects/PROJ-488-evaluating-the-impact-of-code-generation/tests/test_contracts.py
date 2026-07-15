"""
Tests for the contracts module.

Validates that contract checking works correctly for data, API, and validation contracts.
"""

import pytest
import math
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts.data_contracts import (
    CodeSnippetContract, 
    MetricScoreContract, 
    DatasetGroupContract, 
    MetricResultContract
)
from contracts.validation_contracts import (
    ContractViolationError,
    validate_preconditions,
    validate_postconditions,
    run_contract_check
)
from data_model import CodeSnippet, MetricScore, DatasetGroup, MetricResult


class TestDataContracts:
    """Tests for data contract validation."""
    
    def test_valid_code_snippet(self):
        """Test validation of a valid CodeSnippet."""
        data = {
            'id': 'test-123',
            'source': 'codesearchnet',
            'code': 'def hello():\n    return "world"',
            'length': 30,
            'language': 'python'
        }
        assert CodeSnippetContract.validate(data) is True
    
    def test_invalid_code_snippet_missing_field(self):
        """Test validation fails on missing field."""
        data = {
            'id': 'test-123',
            'source': 'codesearchnet',
            'code': 'def hello():\n    return "world"',
            'length': 30
            # missing 'language'
        }
        with pytest.raises(ValueError):
            CodeSnippetContract.validate(data)
    
    def test_invalid_code_snippet_wrong_type(self):
        """Test validation fails on wrong type."""
        data = {
            'id': 123,  # should be string
            'source': 'codesearchnet',
            'code': 'def hello():\n    return "world"',
            'length': 30,
            'language': 'python'
        }
        with pytest.raises(ValueError):
            CodeSnippetContract.validate(data)
    
    def test_valid_metric_score(self):
        """Test validation of a valid MetricScore."""
        data = {
            'snippet_id': 'test-123',
            'metric_type': 'cyclomatic_complexity',
            'score': 5.0,
            'timestamp': '2024-01-01T00:00:00'
        }
        assert MetricScoreContract.validate(data) is True
    
    def test_invalid_metric_score_nan(self):
        """Test validation fails on NaN score."""
        data = {
            'snippet_id': 'test-123',
            'metric_type': 'cyclomatic_complexity',
            'score': float('nan'),
            'timestamp': '2024-01-01T00:00:00'
        }
        with pytest.raises(ValueError):
            MetricScoreContract.validate(data)
    
    def test_valid_metric_result(self):
        """Test validation of a valid MetricResult."""
        data = {
            'snippet_id': 'test-123',
            'metric_type': 'cyclomatic_complexity',
            'value': 5.0,
            'group_label': 'human',
            'timestamp': '2024-01-01T00:00:00'
        }
        assert MetricResultContract.validate(data) is True
    
    def test_object_conversion(self):
        """Test conversion between objects and dictionaries."""
        snippet = CodeSnippet(
            id='test-123',
            source='codesearchnet',
            code='def hello():\n    return "world"',
            length=30,
            language='python'
        )
        
        # Convert to dict
        data = CodeSnippetContract.to_dict(snippet)
        assert data['id'] == 'test-123'
        assert data['length'] == 30
        
        # Convert back to object
        reconstructed = CodeSnippetContract.from_dict(data)
        assert reconstructed.id == snippet.id
        assert reconstructed.length == snippet.length


class TestValidationContracts:
    """Tests for validation contract functionality."""
    
    def test_precondition_success(self):
        """Test successful precondition validation."""
        preconditions = {
            'not_empty': lambda s: len(s.get('data', [])) > 0
        }
        state = {'data': [1, 2, 3]}
        
        assert validate_preconditions('test_func', preconditions, state) is True
    
    def test_precondition_failure(self):
        """Test precondition failure raises exception."""
        preconditions = {
            'not_empty': lambda s: len(s.get('data', [])) > 0
        }
        state = {'data': []}
        
        with pytest.raises(ContractViolationError):
            validate_preconditions('test_func', preconditions, state)
    
    def test_postcondition_success(self):
        """Test successful postcondition validation."""
        postconditions = {
            'positive_result': lambda i, o: o > 0
        }
        input_state = {'x': 5}
        output = 10
        
        assert validate_postconditions('test_func', postconditions, input_state, output) is True
    
    def test_postcondition_failure(self):
        """Test postcondition failure raises exception."""
        postconditions = {
            'positive_result': lambda i, o: o > 0
        }
        input_state = {'x': 5}
        output = -10
        
        with pytest.raises(ContractViolationError):
            validate_postconditions('test_func', postconditions, input_state, output)
    
    def test_run_contract_check_success(self):
        """Test run_contract_check with successful contracts."""
        def add_numbers(a, b):
            return a + b
        
        preconditions = {
            'positive_inputs': lambda s: s['args'][0] > 0 and s['args'][1] > 0
        }
        postconditions = {
            'positive_result': lambda i, o: o > 0
        }
        
        result = run_contract_check(
            'add_numbers',
            add_numbers,
            preconditions,
            postconditions,
            5,
            10
        )
        
        assert result == 15
    
    def test_run_contract_check_precondition_failure(self):
        """Test run_contract_check with failing precondition."""
        def add_numbers(a, b):
            return a + b
        
        preconditions = {
            'positive_inputs': lambda s: s['args'][0] > 0 and s['args'][1] > 0
        }
        postconditions = {}
        
        with pytest.raises(ContractViolationError):
            run_contract_check(
                'add_numbers',
                add_numbers,
                preconditions,
                postconditions,
                -5,
                10
            )
    
    def test_run_contract_check_postcondition_failure(self):
        """Test run_contract_check with failing postcondition."""
        def subtract_numbers(a, b):
            return a - b
        
        preconditions = {}
        postconditions = {
            'positive_result': lambda i, o: o > 0
        }
        
        with pytest.raises(ContractViolationError):
            run_contract_check(
                'subtract_numbers',
                subtract_numbers,
                preconditions,
                postconditions,
                5,
                10
            )

class TestContractErrors:
    """Tests for ContractViolationError."""
    
    def test_error_attributes(self):
        """Test ContractViolationError has correct attributes."""
        error = ContractViolationError(
            'precondition',
            'Test violation',
            {'detail': 'more info'}
        )
        
        assert error.contract_type == 'precondition'
        assert error.message == 'Test violation'
        assert error.details == {'detail': 'more info'}
        assert error.timestamp is not None
        assert 'precondition' in str(error)
        assert 'Test violation' in str(error)