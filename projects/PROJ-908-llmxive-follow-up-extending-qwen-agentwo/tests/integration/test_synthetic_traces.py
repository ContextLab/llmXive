"""
Integration tests for T019: Synthetic Control Traces Generation.

Verifies that the generated traces:
1. Exist at the correct path.
2. Contain exactly N=500 traces.
3. Have the required structure (trace_id, pattern_id, steps, etc.).
4. Contain valid logical patterns as defined in the generator.
"""
import json
import os
from pathlib import Path
import pytest

from code.analysis.synthetic_trace_generator import SyntheticTraceGenerator, NUM_TRACES

OUTPUT_PATH = Path("data/raw/synthetic_control_traces.json")

@pytest.fixture(scope="module")
def synthetic_traces():
    """Generate traces before running tests if they don't exist."""
    if not OUTPUT_PATH.exists():
        generator = SyntheticTraceGenerator(seed=42)
        generator.generate_dataset(NUM_TRACES, OUTPUT_PATH)
    
    with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

class TestSyntheticTraceGeneration:
    def test_file_exists(self):
        """Verify the output file exists."""
        assert OUTPUT_PATH.exists(), f"File {OUTPUT_PATH} was not created."

    def test_trace_count(self, synthetic_traces):
        """Verify exactly N=500 traces are generated."""
        assert len(synthetic_traces) == NUM_TRACES, \
            f"Expected {NUM_TRACES} traces, got {len(synthetic_traces)}"

    def test_trace_structure(self, synthetic_traces):
        """Verify each trace has the required fields."""
        required_fields = {"trace_id", "pattern_id", "task_description", "steps", "expected_outcome", "metadata"}
        
        for i, trace in enumerate(synthetic_traces):
            missing = required_fields - set(trace.keys())
            assert not missing, f"Trace {i} missing fields: {missing}"
            
            # Verify steps is a list
            assert isinstance(trace["steps"], list), f"Trace {i}: 'steps' must be a list"
            assert len(trace["steps"]) > 0, f"Trace {i}: 'steps' cannot be empty"

    def test_pattern_validity(self, synthetic_traces):
        """Verify pattern IDs match the defined set."""
        valid_patterns = {"P01", "P02", "P03", "P04", "P05"}
        patterns_found = set(t["pattern_id"] for t in synthetic_traces)
        
        invalid_patterns = patterns_found - valid_patterns
        assert not invalid_patterns, f"Found invalid pattern IDs: {invalid_patterns}"
        
        # Ensure all patterns are represented
        missing_patterns = valid_patterns - patterns_found
        assert not missing_patterns, f"Missing expected patterns: {missing_patterns}"

    def test_step_structure(self, synthetic_traces):
        """Verify each step within a trace has required fields."""
        required_step_fields = {"step_id", "thought", "action"}
        
        for i, trace in enumerate(synthetic_traces):
            for j, step in enumerate(trace["steps"]):
                missing = required_step_fields - set(step.keys())
                assert not missing, \
                    f"Trace {i}, Step {j} missing fields: {missing}"

    def test_determinism(self):
        """Verify that running the generator again produces the same file."""
        # Save current file hash (simulated by re-generating and comparing)
        generator = SyntheticTraceGenerator(seed=42)
        temp_path = Path("data/raw/synthetic_control_traces_temp.json")
        
        try:
            generator.generate_dataset(NUM_TRACES, temp_path)
            
            with open(OUTPUT_PATH, 'r') as f1, open(temp_path, 'r') as f2:
                content1 = f1.read()
                content2 = f2.read()
            
            assert content1 == content2, "Regenerated traces do not match original (determinism failed)"
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_metadata_consistency(self, synthetic_traces):
        """Verify metadata contains expected keys."""
        for trace in synthetic_traces:
            assert "complexity" in trace["metadata"], "Metadata missing 'complexity'"
            assert "steps_count" in trace["metadata"], "Metadata missing 'steps_count'"
            
            # Verify steps_count matches actual length
            assert trace["metadata"]["steps_count"] == len(trace["steps"]), \
                f"Metadata steps_count mismatch for trace {trace['trace_id']}"
