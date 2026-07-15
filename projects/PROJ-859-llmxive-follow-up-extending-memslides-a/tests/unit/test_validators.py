"""
Unit tests for schema validators.
"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import yaml

from code.utils.validators import TraceValidator, MetricsValidator


@pytest.fixture
def mock_trace_schema():
    return {
        "required": ["trace_id", "exact_tool_sequence", "raw_arg_variance"],
        "properties": {
            "trace_id": {"type": "string"},
            "exact_tool_sequence": {"type": "array"},
            "raw_arg_variance": {"type": "number"}
        }
    }


@pytest.fixture
def mock_metrics_schema():
    return {
        "required": ["trace_id", "sequence_entropy"],
        "properties": {
            "trace_id": {"type": "string"},
            "sequence_entropy": {"type": "number"},
            "tool_repetition_freq": {"type": "number"},
            "arg_semantic_variance": {"type": "number"},
            "compressibility_score": {"type": "number", "minimum": 0, "maximum": 1}
        }
    }


@pytest.fixture
def temp_contract_dir(mock_trace_schema, mock_metrics_schema):
    """Create temporary contracts directory with schemas."""
    with tempfile.TemporaryDirectory() as tmpdir:
        contracts_dir = Path(tmpdir) / "contracts"
        contracts_dir.mkdir()
        
        with open(contracts_dir / "trace.schema.yaml", "w") as f:
            yaml.dump(mock_trace_schema, f)
        
        with open(contracts_dir / "metrics.schema.yaml", "w") as f:
            yaml.dump(mock_metrics_schema, f)
        
        yield contracts_dir


class TestTraceValidator:
    def test_valid_trace(self, temp_contract_dir):
        config = MagicMock()
        config.root = str(temp_contract_dir.parent)
        validator = TraceValidator(config)
        
        valid_data = {
            "trace_id": "test-001",
            "exact_tool_sequence": [
                {"tool_name": "edit", "arguments": {"x": 1}}
            ],
            "raw_arg_variance": 0.5
        }
        
        is_valid, errors = validator.validate(valid_data)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_required_field(self, temp_contract_dir):
        config = MagicMock()
        config.root = str(temp_contract_dir.parent)
        validator = TraceValidator(config)
        
        invalid_data = {
            "trace_id": "test-001",
            "exact_tool_sequence": []
            # missing raw_arg_variance
        }
        
        is_valid, errors = validator.validate(invalid_data)
        assert is_valid is False
        assert "Missing required field: raw_arg_variance" in errors

    def test_invalid_tool_sequence_type(self, temp_contract_dir):
        config = MagicMock()
        config.root = str(temp_contract_dir.parent)
        validator = TraceValidator(config)
        
        invalid_data = {
            "trace_id": "test-001",
            "exact_tool_sequence": "not_a_list",
            "raw_arg_variance": 0.5
        }
        
        is_valid, errors = validator.validate(invalid_data)
        assert is_valid is False
        assert any("must be a list" in e for e in errors)

    def test_negative_variance(self, temp_contract_dir):
        config = MagicMock()
        config.root = str(temp_contract_dir.parent)
        validator = TraceValidator(config)
        
        invalid_data = {
            "trace_id": "test-001",
            "exact_tool_sequence": [],
            "raw_arg_variance": -0.5
        }
        
        is_valid, errors = validator.validate(invalid_data)
        assert is_valid is False
        assert any("cannot be negative" in e for e in errors)


class TestMetricsValidator:
    def test_valid_metrics(self, temp_contract_dir):
        config = MagicMock()
        config.root = str(temp_contract_dir.parent)
        validator = MetricsValidator(config)
        
        valid_data = {
            "trace_id": "test-001",
            "sequence_entropy": 1.2,
            "tool_repetition_freq": 0.8,
            "arg_semantic_variance": 0.3,
            "compressibility_score": 0.7
        }
        
        is_valid, errors = validator.validate(valid_data)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_required_field(self, temp_contract_dir):
        config = MagicMock()
        config.root = str(temp_contract_dir.parent)
        validator = MetricsValidator(config)
        
        invalid_data = {
            "trace_id": "test-001"
            # missing sequence_entropy
        }
        
        is_valid, errors = validator.validate(invalid_data)
        assert is_valid is False
        assert "Missing required field: sequence_entropy" in errors

    def test_invalid_numeric_type(self, temp_contract_dir):
        config = MagicMock()
        config.root = str(temp_contract_dir.parent)
        validator = MetricsValidator(config)
        
        invalid_data = {
            "trace_id": "test-001",
            "sequence_entropy": "not_a_number",
            "tool_repetition_freq": 0.8
        }
        
        is_valid, errors = validator.validate(invalid_data)
        assert is_valid is False
        assert any("must be numeric" in e for e in errors)

    def test_compressibility_out_of_range(self, temp_contract_dir):
        config = MagicMock()
        config.root = str(temp_contract_dir.parent)
        validator = MetricsValidator(config)
        
        invalid_data = {
            "trace_id": "test-001",
            "sequence_entropy": 1.2,
            "compressibility_score": 1.5  # > 1
        }
        
        is_valid, errors = validator.validate(invalid_data)
        assert is_valid is False
        assert any("must be in [0, 1]" in e for e in errors)
