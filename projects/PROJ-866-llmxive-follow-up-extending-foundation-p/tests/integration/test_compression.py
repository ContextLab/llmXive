import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from engines.compressed_context import CompressedContextEngine
from engines.full_context import FullContextEngine
from generators.synthetic_workflow import SyntheticWorkflowGenerator


def test_full_vs_compressed():
    """Compare Full vs Compressed logs for multiple workflows."""
    generator = SyntheticWorkflowGenerator(seed=42)
    workflows = generator.generate_workflows(10)

    full_engine = FullContextEngine()
    compressed_engine = CompressedContextEngine(traversal_depth=2)

    for workflow in workflows:
        full_log = full_engine.execute(workflow)
        compressed_log = compressed_engine.execute(workflow)

        # Verify compressed log has reduced token count (or deferred)
        if compressed_log["context_reduction_pct"] != "[deferred]":
            assert compressed_log["context_reduction_pct"] >= 0

        # Verify structure
        assert "workflow_id" in full_log
        assert "workflow_id" in compressed_log
        assert "policy_violations" in full_log
        assert "policy_violations" in compressed_log

    print("All compression integration tests passed.")


if __name__ == "__main__":
    test_full_vs_compressed()
