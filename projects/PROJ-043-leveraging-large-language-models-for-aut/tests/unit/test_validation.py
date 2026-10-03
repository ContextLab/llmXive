import pytest
import yaml
import tempfile
import os
from pathlib import Path
from pydantic import ValidationError

# Import the functions to test
from utils.validation import (
    load_schema_from_yaml,
    schema_to_pydantic_model,
    validate_config,
    validate_output,
    validate
)

@pytest.fixture
def config_schema_content():
    return """
    type: object
    properties:
      HF_API_KEY:
        type: string
      RANDOM_SEED:
        type: integer
      MAX_ATTEMPTS:
        type: integer
      MIN_VALID_FUNCTIONS:
        type: integer
      TARGET_VALID_FUNCTIONS:
        type: integer
      BATCH_SIZE:
        type: integer
      BASELINE_TOLERANCE:
        type: number
    required:
      - HF_API_KEY
      - RANDOM_SEED
      - MAX_ATTEMPTS
      - MIN_VALID_FUNCTIONS
      - TARGET_VALID_FUNCTIONS
      - BATCH_SIZE
      - BASELINE_TOLERANCE
    """

@pytest.fixture
def output_schema_content():
    return """
    type: object
    properties:
      FunctionSample:
        type: object
        properties:
          code:
            type: string
          hash:
            type: string
          loc:
            type: integer
          nesting_depth:
            type: integer
          param_count:
            type: integer
          pep8_violations:
            type: integer
          pep8_adherence_score:
            type: number
          docstring_present:
            type: boolean
        required:
          - code
          - hash
          - loc
          - nesting_depth
          - param_count
          - pep8_violations
          - pep8_adherence_score
          - docstring_present
      MetricDelta:
        type: object
        properties:
          complexity_delta:
            type: number
          pylint_delta:
            type: number
          maintainability_delta:
            type: number
        required:
          - complexity_delta
          - pylint_delta
          - maintainability_delta
    required:
      - FunctionSample
      - MetricDelta
    """

@pytest.fixture
def temp_config_schema(config_schema_content):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_schema_content)
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def temp_output_schema(output_schema_content):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(output_schema_content)
        path = f.name
    yield path
    os.unlink(path)

def test_load_schema_from_yaml(temp_config_schema):
    schema = load_schema_from_yaml(temp_config_schema)
    assert schema['type'] == 'object'
    assert 'HF_API_KEY' in schema['properties']

def test_schema_to_pydantic_model_basic():
    schema = {
        'properties': {
            'name': {'type': 'string'},
            'age': {'type': 'integer'}
        },
        'required': ['name']
    }
    model = schema_to_pydantic_model(schema)
    instance = model(name="Test", age=25)
    assert instance.name == "Test"
    assert instance.age == 25

def test_validate_config_success(temp_config_schema):
    valid_config = {
        'HF_API_KEY': 'test_key',
        'RANDOM_SEED': 42,
        'MAX_ATTEMPTS': 400,
        'MIN_VALID_FUNCTIONS': 100,
        'TARGET_VALID_FUNCTIONS': 200,
        'BATCH_SIZE': 10,
        'BASELINE_TOLERANCE': 0.01
    }
    assert validate_config(valid_config, temp_config_schema) is True

def test_validate_config_failure(temp_config_schema):
    invalid_config = {
        'HF_API_KEY': 'test_key',
        # Missing required fields
    }
    with pytest.raises(ValidationError):
        validate_config(invalid_config, temp_config_schema)

def test_validate_output_success(temp_output_schema):
    valid_output = {
        'FunctionSample': {
            'code': 'def test(): pass',
            'hash': 'abc123',
            'loc': 1,
            'nesting_depth': 0,
            'param_count': 0,
            'pep8_violations': 0,
            'pep8_adherence_score': 1.0,
            'docstring_present': False
        },
        'MetricDelta': {
            'complexity_delta': 0.5,
            'pylint_delta': -0.2,
            'maintainability_delta': 1.0
        }
    }
    assert validate_output(valid_output, temp_output_schema) is True

def test_validate_output_failure(temp_output_schema):
    invalid_output = {
        'FunctionSample': {
            'code': 'def test(): pass',
            # Missing required fields
        }
    }
    with pytest.raises(ValidationError):
        validate_output(invalid_output, temp_output_schema)

def test_validate_generic_config(temp_config_schema):
    valid_config = {
        'HF_API_KEY': 'test_key',
        'RANDOM_SEED': 42,
        'MAX_ATTEMPTS': 400,
        'MIN_VALID_FUNCTIONS': 100,
        'TARGET_VALID_FUNCTIONS': 200,
        'BATCH_SIZE': 10,
        'BASELINE_TOLERANCE': 0.01
    }
    assert validate(valid_config, temp_config_schema, "config") is True

def test_validate_generic_output(temp_output_schema):
    valid_output = {
        'FunctionSample': {
            'code': 'def test(): pass',
            'hash': 'abc123',
            'loc': 1,
            'nesting_depth': 0,
            'param_count': 0,
            'pep8_violations': 0,
            'pep8_adherence_score': 1.0,
            'docstring_present': False
        },
        'MetricDelta': {
            'complexity_delta': 0.5,
            'pylint_delta': -0.2,
            'maintainability_delta': 1.0
        }
    }
    assert validate(valid_output, temp_output_schema, "output") is True