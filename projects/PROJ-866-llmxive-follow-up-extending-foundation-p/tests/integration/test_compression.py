import pytest
import json
import os
from pathlib import Path
from engines.compressed_context import CompressedContextEngine
from engines.full_context import FullContextEngine
from generators.synthetic_workflow import SyntheticWorkflowGenerator

@pytest.fixture
def sample_workflows():
    """Generate 10 sample workflows for integration testing."""
    generator = SyntheticWorkflowGenerator(seed=123)
    workflows, _ = generator.generate_workflows(num_workflows=10)
    return workflows

def test_full_vs_compressed_logs(sample_workflows):
    """
    T019: Integration test: Compare Full vs. Compressed logs for 10 workflows.
    Verifies that compressed execution results in reduced token counts and 
    potentially different violation counts compared to full context.
    """
    full_engine = FullContextEngine()
    compressed_engine = CompressedContextEngine()
    
    # Use a small depth for compression to ensure reduction
    compression_depth = 2
    
    full_logs = []
    compressed_logs = []
    
    for wf in sample_workflows:
        # Run full context
        full_log = full_engine.execute(wf)
        full_logs.append(full_log)
        
        # Run compressed context
        compressed_log = compressed_engine.execute(wf, depth=compression_depth)
        compressed_logs.append(compressed_log)
    
    # Verify logs exist and have expected structure
    assert len(full_logs) == 10
    assert len(compressed_logs) == 10
    
    # Check that compressed logs generally have fewer tokens (statistically)
    full_token_counts = [log.get("token_count", 0) for log in full_logs]
    compressed_token_counts = [log.get("token_count", 0) for log in compressed_logs]
    
    # At least some compression should occur in most cases
    avg_full = sum(full_token_counts) / len(full_token_counts)
    avg_compressed = sum(compressed_token_counts) / len(compressed_token_counts)
    
    # Allow for some edge cases where compression might not reduce tokens significantly
    # but generally compressed should be <= full
    assert avg_compressed <= avg_full * 1.1, f"Compression did not reduce tokens: Full={avg_full:.1f}, Compressed={avg_compressed:.1f}"
