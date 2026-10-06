"""
Integration tests for the pipeline.
"""
import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from src.report import generate_stability_report

class TestAggregationHandlesMissingRepoGracefully:
    def test_aggregation_handles_missing_repo_gracefully(self):
        """Test that aggregation handles missing repository data gracefully."""
        # Simulate data with missing repo
        data = {
            "GEO": {"stability": 0.9},
            "TCGA": {},  # Missing data
            "ENCODE": {"stability": 0.85}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            # Should not raise
            generate_stability_report(data, output_path)
            assert output_path.exists()
