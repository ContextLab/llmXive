import json
import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Import from project
from generators.synthetic_trace import SyntheticTraceGenerator, generate_synthetic_traces
from config import get_config

class TestSyntheticTraceGeneration:
    """Unit tests for synthetic trace generation logic."""

    def test_generator_initialization(self):
        """Test that generator initializes with correct seed and parameters."""
        gen = SyntheticTraceGenerator(seed=42, variance_multiplier=1.0)
        assert gen.seed == 42
        assert gen.variance_multiplier == 1.0
        assert len(gen.tool_types) > 0

    def test_trace_generation_structure(self):
        """Test that generated traces have the required structure."""
        gen = SyntheticTraceGenerator(seed=42)
        trace = gen.generate_trace()
        
        assert "trace_id" in trace
        assert "tool_sequence" in trace
        assert "arguments" in trace
        assert "final_state" in trace
        assert "metadata" in trace
        assert trace["metadata"]["seed"] == 42
        assert len(trace["tool_sequence"]) >= 5  # min_length

    def test_trace_generation_length_variance(self):
        """Test that variance_multiplier affects sequence length distribution."""
        gen_std = SyntheticTraceGenerator(seed=42, variance_multiplier=1.0)
        gen_high = SyntheticTraceGenerator(seed=42, variance_multiplier=2.0)
        
        # Generate multiple traces to see distribution shift
        lengths_std = []
        lengths_high = []
        
        for _ in range(50):
            t1 = gen_std.generate_trace()
            t2 = gen_high.generate_trace()
            lengths_std.append(len(t1["tool_sequence"]))
            lengths_high.append(len(t2["tool_sequence"]))
        
        # High variance should generally produce longer sequences
        avg_std = sum(lengths_std) / len(lengths_std)
        avg_high = sum(lengths_high) / len(lengths_high)
        
        assert avg_high >= avg_std, "High variance should produce longer or equal sequences"

    def test_integrity_log_generation(self):
        """Test that integrity log is populated correctly."""
        gen = SyntheticTraceGenerator(seed=42)
        gen.generate_trace()
        gen.generate_trace()
        
        log = gen.get_integrity_log()
        assert len(log) == 2
        assert "tool_sequence" in log[0]
        assert "sequence_entropy" in log[0]
        assert "tool_repetition_freq" in log[0]
        assert "arg_semantic_variance" in log[0]

    def test_generate_synthetic_traces_writes_files(self):
        """Test that the batch generation function writes files to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            count = 10
            
            generate_synthetic_traces(
                count=count,
                output_dir=tmpdir,
                seed=42,
                variance_multiplier=1.0,
                log_path=log_path
            )
            
            # Verify files exist
            files = list(Path(tmpdir).glob("*.json"))
            assert len(files) == count
            
            # Verify log exists
            assert os.path.exists(log_path)
            with open(log_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == count

    def test_reproducibility_with_seed(self):
        """Test that same seed produces identical results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test1.log")
            generate_synthetic_traces(
                count=5,
                output_dir=tmpdir,
                seed=42,
                variance_multiplier=1.0,
                log_path=log_path
            )
            
            # Read first file content
            files = sorted(Path(tmpdir).glob("*.json"))
            with open(files[0], 'r') as f:
                content1 = f.read()
            
            # Regenerate with same seed
            generate_synthetic_traces(
                count=5,
                output_dir=tmpdir,
                seed=42,
                variance_multiplier=1.0,
                log_path=log_path
            )
            
            # Read again (should overwrite)
            with open(files[0], 'r') as f:
                content2 = f.read()
            
            assert content1 == content2, "Same seed should produce identical traces"

    def test_metrics_calculation(self):
        """Test that metrics are calculated correctly in the generator."""
        gen = SyntheticTraceGenerator(seed=42)
        trace = gen.generate_trace()
        
        # Check that metrics are present in log
        log = gen.get_integrity_log()
        assert len(log) > 0
        
        entry = log[0]
        assert entry["sequence_entropy"] >= 0
        assert 0 <= entry["tool_repetition_freq"] <= 1
        assert entry["arg_semantic_variance"] >= 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])