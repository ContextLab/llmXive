"""
Unit tests for the Synthetic Trace Generator (T019).

Tests verify:
1. Correct generation of N=500 traces
2. Pre-determined logical patterns are present
3. Output file structure matches expectations
4. Metadata and ground truth rules are correctly formatted
"""

import json
import os
import pytest
from pathlib import Path
from typing import List, Dict, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.synthetic_trace_generator import SyntheticTraceGenerator, ControlTrace, TraceStep

@pytest.fixture
def generator():
    return SyntheticTraceGenerator(seed=42)

@pytest.fixture
def temp_output_path(tmp_path):
    return str(tmp_path / "test_traces.json")

def test_generator_initialization(generator):
    """Test that generator initializes with correct seed."""
    assert generator.seed == 42

def test_generate_linear_sequence(generator):
    """Test linear sequence pattern generation."""
    trace = generator._generate_linear_sequence("test_001", length=10)
    
    assert trace.pattern_type == "linear_sequence"
    assert len(trace.steps) == 10
    assert trace.ground_truth_rule.startswith("sequence(")
    assert trace.metadata["length"] == 10
    assert trace.metadata["deterministic"] is True

def test_generate_conditional_branch(generator):
    """Test conditional branch pattern generation."""
    trace = generator._generate_conditional_branch("test_002")
    
    assert trace.pattern_type == "conditional_branch"
    assert len(trace.steps) == 3
    assert "if" in trace.ground_truth_rule
    assert "then" in trace.ground_truth_rule
    assert "condition" in trace.metadata

def test_generate_loop_pattern(generator):
    """Test loop pattern generation."""
    trace = generator._generate_loop_pattern("test_003", iterations=5)
    
    assert trace.pattern_type == "loop_pattern"
    assert len(trace.steps) == 6  # 5 iterations + 1 exit
    assert "repeat" in trace.ground_truth_rule
    assert trace.metadata["iterations"] == 5

def test_generate_parallel_convergence(generator):
    """Test parallel convergence pattern generation."""
    trace = generator._generate_parallel_convergence("test_004")
    
    assert trace.pattern_type == "parallel_convergence"
    assert len(trace.steps) == 6
    assert "parallel" in trace.ground_truth_rule
    assert trace.metadata["branches"] == 2

def test_generate_batch(generator, temp_output_path):
    """Test batch generation of traces."""
    n = 100
    generator.generate_batch(n=n, output_path=temp_output_path)
    
    assert os.path.exists(temp_output_path)
    
    with open(temp_output_path, 'r') as f:
        traces = json.load(f)
    
    assert len(traces) == n
    
    # Verify structure of each trace
    for i, trace in enumerate(traces):
        assert "trace_id" in trace
        assert "pattern_type" in trace
        assert "steps" in trace
        assert "ground_truth_rule" in trace
        assert "metadata" in trace
        assert trace["trace_id"] == f"synthetic_control_{i:04d}"

def test_pattern_distribution(generator, temp_output_path):
    """Test that patterns are distributed correctly in batch."""
    n = 100  # Should be evenly distributed across 4 patterns
    generator.generate_batch(n=n, output_path=temp_output_path)
    
    with open(temp_output_path, 'r') as f:
        traces = json.load(f)
    
    pattern_counts = {}
    for trace in traces:
        pattern = trace["pattern_type"]
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
    
    # Each pattern should have approximately n/4 traces
    expected_per_pattern = n // 4
    for pattern, count in pattern_counts.items():
        assert abs(count - expected_per_pattern) <= 1, \
            f"Pattern {pattern} has {count} traces, expected ~{expected_per_pattern}"

def test_trace_step_structure(generator, temp_output_path):
    """Test that each step in a trace has the correct structure."""
    generator.generate_batch(n=10, output_path=temp_output_path)
    
    with open(temp_output_path, 'r') as f:
        traces = json.load(f)
    
    required_step_fields = ["step_id", "action", "observation", "reasoning", "next_state", "confidence"]
    
    for trace in traces:
        for step in trace["steps"]:
            for field in required_step_fields:
                assert field in step, f"Missing field {field} in step"
            assert isinstance(step["step_id"], int)
            assert isinstance(step["confidence"], float)
            assert 0.0 <= step["confidence"] <= 1.0

def test_ground_truth_rules(generator, temp_output_path):
    """Test that ground truth rules are properly formatted."""
    generator.generate_batch(n=50, output_path=temp_output_path)
    
    with open(temp_output_path, 'r') as f:
        traces = json.load(f)
    
    for trace in traces:
        rule = trace["ground_truth_rule"]
        assert isinstance(rule, str)
        assert len(rule) > 0
        # Verify rule contains pattern-specific keywords
        if trace["pattern_type"] == "linear_sequence":
            assert "sequence" in rule
        elif trace["pattern_type"] == "conditional_branch":
            assert "if" in rule
        elif trace["pattern_type"] == "loop_pattern":
            assert "repeat" in rule
        elif trace["pattern_type"] == "parallel_convergence":
            assert "parallel" in rule

def test_output_file_valid_json(temp_output_path):
    """Test that the output file is valid JSON."""
    generator = SyntheticTraceGenerator(seed=42)
    generator.generate_batch(n=10, output_path=temp_output_path)
    
    # Should not raise an exception
    with open(temp_output_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list)

def test_seed_reproducibility(temp_output_path):
    """Test that same seed produces same results."""
    path1 = str(Path(temp_output_path).parent / "run1.json")
    path2 = str(Path(temp_output_path).parent / "run2.json")
    
    gen1 = SyntheticTraceGenerator(seed=42)
    gen1.generate_batch(n=50, output_path=path1)
    
    gen2 = SyntheticTraceGenerator(seed=42)
    gen2.generate_batch(n=50, output_path=path2)
    
    with open(path1, 'r') as f:
        data1 = json.load(f)
    with open(path2, 'r') as f:
        data2 = json.load(f)
    
    assert data1 == data2, "Same seed should produce identical output"
