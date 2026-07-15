import json
import os
from pathlib import Path
import pytest

from code.generators.synthetic_trace import SyntheticTraceGenerator, generate_synthetic_traces
from code.config import Config
from code.utils.validators import TraceValidator

def test_generator_initialization():
    """Test that the generator initializes with the correct seed."""
    gen = SyntheticTraceGenerator(seed=42)
    assert gen.seed == 42
    assert isinstance(gen.config, Config)

def test_generate_session_structure():
    """Test that a generated session has the required fields."""
    gen = SyntheticTraceGenerator(seed=42)
    trace = gen.generate_session("test-uuid")

    required_fields = ["session_id", "exact_tool_sequence", "raw_arg_variance", "tool_calls", "final_state"]
    for field in required_fields:
        assert field in trace, f"Missing required field: {field}"

def test_exact_tool_sequence_format():
    """Test that exact_tool_sequence is a list of (tool, arg_count) tuples."""
    gen = SyntheticTraceGenerator(seed=42)
    trace = gen.generate_session("test-uuid")

    assert isinstance(trace["exact_tool_sequence"], list)
    assert len(trace["exact_tool_sequence"]) > 0

    for item in trace["exact_tool_sequence"]:
        assert isinstance(item, (list, tuple))
        assert len(item) == 2
        assert isinstance(item[0], str)
        assert isinstance(item[1], int)

def test_raw_arg_variance_calculation():
    """Test that raw_arg_variance is a non-negative number."""
    gen = SyntheticTraceGenerator(seed=42)
    trace = gen.generate_session("test-uuid")

    assert isinstance(trace["raw_arg_variance"], (int, float))
    assert trace["raw_arg_variance"] >= 0

def test_trace_validation():
    """Test that generated traces pass the TraceValidator."""
    gen = SyntheticTraceGenerator(seed=42)
    trace = gen.generate_session("test-uuid")

    config = Config()
    validator = TraceValidator(config)
    assert validator.validate(trace)

def test_generate_synthetic_traces_writes_files(tmp_path):
    """Test that generate_synthetic_traces writes JSON files to disk."""
    output_dir = tmp_path / "test_output"
    files = generate_synthetic_traces(str(output_dir), count=3, seed=42)

    assert len(files) == 3
    for file_path in files:
        assert os.path.exists(file_path)
        with open(file_path, 'r') as f:
            data = json.load(f)
            assert "session_id" in data
            assert "exact_tool_sequence" in data
            assert "raw_arg_variance" in data