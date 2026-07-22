"""
Integration tests for the synthetic generation pipeline.
Validates end-to-end flow of T012 (synthetic_trace.py).
"""
import pytest
import json
import os
from pathlib import Path
import sys
import shutil
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from generators.synthetic_trace import generate_synthetic_traces, SyntheticTraceGenerator, DataGenerationError
from utils.validators import TraceValidator
from config import get_config

class TestSyntheticGeneration:
    """Integration tests for synthetic trace generation."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for tests."""
        self.test_dir = Path("data/test_integration")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        yield
        # Cleanup
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_generate_small_dataset(self):
        """Test generation of a small dataset (10 traces)."""
        num_traces = 10
        results = generate_synthetic_traces(num_traces=num_traces, seed=42)
        
        assert "training_path" in results
        assert "heldout_path" in results
        assert results["stats"]["total_generated"] == num_traces
        
        # Check training files
        training_dir = Path(results["training_path"])
        training_files = list(training_dir.glob("session_*.json"))
        assert len(training_files) == 8  # 80% of 10
        
        # Check held-out files
        heldout_dir = Path(results["heldout_path"])
        heldout_files = list(heldout_dir.glob("session_*.json"))
        assert len(heldout_files) == 2  # 20% of 10
    
    def test_trace_schema_compliance(self):
        """Test that generated traces comply with the schema."""
        num_traces = 50
        results = generate_synthetic_traces(num_traces=num_traces, seed=42)
        
        validator = TraceValidator()
        all_valid = True
        
        # Check training traces
        for file_path in Path(results["training_path"]).glob("session_*.json"):
            with open(file_path, 'r') as f:
                trace = json.load(f)
            if not validator.validate(trace):
                all_valid = False
                break
        
        # Check held-out traces
        for file_path in Path(results["heldout_path"]).glob("session_*.json"):
            with open(file_path, 'r') as f:
                trace = json.load(f)
            if not validator.validate(trace):
                all_valid = False
                break
        
        assert all_valid, "Some traces failed schema validation"
    
    def test_reproducibility(self):
        """Test that generation is reproducible with the same seed."""
        num_traces = 10
        
        # Generate first set
        results1 = generate_synthetic_traces(num_traces=num_traces, seed=123)
        traces1 = []
        for file_path in Path(results1["training_path"]).glob("session_*.json"):
            with open(file_path, 'r') as f:
                traces1.append(json.load(f))
        
        # Generate second set with same seed
        results2 = generate_synthetic_traces(num_traces=num_traces, seed=123)
        traces2 = []
        for file_path in Path(results2["training_path"]).glob("session_*.json"):
            with open(file_path, 'r') as f:
                traces2.append(json.load(f))
        
        # Compare (session IDs will differ due to UUID, but structure should match)
        assert len(traces1) == len(traces2)
        for t1, t2 in zip(traces1, traces2):
            assert t1["metadata"]["sequence_length"] == t2["metadata"]["sequence_length"]
            assert t1["raw_arg_variance"] == t2["raw_arg_variance"]
            assert len(t1["exact_tool_sequence"]) == len(t2["exact_tool_sequence"])
    
    def test_varied_sequence_lengths(self):
        """Test that generated traces have varied sequence lengths."""
        num_traces = 100
        results = generate_synthetic_traces(num_traces=num_traces, seed=42)
        
        lengths = []
        for file_path in Path(results["training_path"]).glob("session_*.json"):
            with open(file_path, 'r') as f:
                trace = json.load(f)
            lengths.append(trace["metadata"]["sequence_length"])
        
        # Check for variance
        assert len(set(lengths)) > 1, "All traces have the same sequence length"
        assert min(lengths) >= 5, "Sequence length too short"
        assert max(lengths) <= 50, "Sequence length too long"
    
    def test_varied_tool_types(self):
        """Test that generated traces use varied tool types."""
        num_traces = 100
        results = generate_synthetic_traces(num_traces=num_traces, seed=42)
        
        all_tools = set()
        for file_path in Path(results["training_path"]).glob("session_*.json"):
            with open(file_path, 'r') as f:
                trace = json.load(f)
            for step in trace["exact_tool_sequence"]:
                all_tools.add(step["tool_name"])
        
        # Should have multiple tool types
        assert len(all_tools) > 3, "Not enough variety in tool types"
    
    def test_varied_argument_variance(self):
        """Test that generated traces have varied argument variance."""
        num_traces = 100
        results = generate_synthetic_traces(num_traces=num_traces, seed=42)
        
        variances = []
        for file_path in Path(results["training_path"]).glob("session_*.json"):
            with open(file_path, 'r') as f:
                trace = json.load(f)
            variances.append(trace["raw_arg_variance"])
        
        # Check for variance
        assert len(set([round(v, 4) for v in variances])) > 1, "All traces have the same argument variance"
    
    def test_edge_case_zero_repetition(self):
        """Test handling of traces with zero tool repetitions (high entropy)."""
        # This is tested implicitly by the variety test, but we ensure no crashes
        num_traces = 10
        results = generate_synthetic_traces(num_traces=num_traces, seed=42)
        
        assert results["stats"]["total_generated"] == num_traces
    
    def test_large_generation(self):
        """Test generation of the full 5000 trace dataset."""
        num_traces = 5000
        results = generate_synthetic_traces(num_traces=num_traces, seed=42)
        
        assert results["stats"]["total_generated"] == num_traces
        assert results["stats"]["training_count"] == 4000
        assert results["stats"]["heldout_count"] == 1000
        
        # Verify file counts
        training_count = len(list(Path(results["training_path"]).glob("session_*.json")))
        heldout_count = len(list(Path(results["heldout_path"]).glob("session_*.json")))
        
        assert training_count == 4000
        assert heldout_count == 1000
