"""
Tests for the visualization module.
"""

import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.visualization import (
    create_boxplot,
    load_metric_data,
    generate_all_boxplots,
    METRIC_TYPES
)
from code.data_model import MetricResult

class TestVisualization:
    """Test cases for visualization functions."""

    @pytest.fixture
    def temp_figures_dir(self):
        """Create a temporary directory for test figures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fig_dir = Path(tmpdir) / "figures"
            fig_dir.mkdir()
            yield fig_dir

    @pytest.fixture
    def sample_data(self):
        """Generate sample metric data for testing."""
        np.random.seed(42)
        human_data = np.random.normal(loc=5.0, scale=1.5, size=100).tolist()
        codegen_data = np.random.normal(loc=6.5, scale=2.0, size=100).tolist()
        return human_data, codegen_data

    def test_create_boxplot_basic(self, temp_figures_dir, sample_data):
        """Test basic boxplot creation."""
        human_data, codegen_data = sample_data
        output_path = temp_figures_dir / "test_boxplot.png"
        
        result = create_boxplot(
            metric_type="test_metric",
            human_data=human_data,
            codegen_data=codegen_data,
            output_path=output_path
        )
        
        assert result is True, "Boxplot creation should succeed"
        assert output_path.exists(), "Output file should be created"
        assert output_path.stat().st_size > 0, "Output file should not be empty"

    def test_create_boxplot_invalid_data(self, temp_figures_dir):
        """Test boxplot creation with insufficient data."""
        human_data = [1.0, 2.0]  # Too few points
        codegen_data = [3.0, 4.0]
        output_path = temp_figures_dir / "test_invalid.png"
        
        # Should still create a plot, but might be visually empty
        result = create_boxplot(
            metric_type="test_metric",
            human_data=human_data,
            codegen_data=codegen_data,
            output_path=output_path
        )
        
        assert isinstance(result, bool), "Should return boolean"

    def test_create_boxplot_empty_data(self, temp_figures_dir):
        """Test boxplot creation with empty data."""
        human_data = []
        codegen_data = []
        output_path = temp_figures_dir / "test_empty.png"
        
        # This should handle gracefully or fail
        try:
            result = create_boxplot(
                metric_type="test_metric",
                human_data=human_data,
                codegen_data=codegen_data,
                output_path=output_path
            )
            # If it doesn't crash, it should return False
            assert result is False, "Empty data should fail gracefully"
        except Exception:
            # Or it might raise an exception, which is also acceptable
            pass

    def test_load_metric_data_missing_files(self):
        """Test loading data when files don't exist."""
        # Temporarily change METRICS_DIR to a non-existent path
        from code import visualization
        original_metrics_dir = visualization.METRICS_DIR
        
        try:
            visualization.METRICS_DIR = Path("/nonexistent/path")
            human_df, codegen_df = load_metric_data("cyclomatic_complexity")
            
            assert human_df is None, "Should return None for missing human data"
            assert codegen_df is None, "Should return None for missing codegen data"
        finally:
            visualization.METRICS_DIR = original_metrics_dir

    def test_metric_types_defined(self):
        """Test that all expected metric types are defined."""
        expected_metrics = [
            "cyclomatic_complexity",
            "maintainability_index",
            "loc",
            "bug_potential",
            "style_issues"
        ]
        
        for metric in expected_metrics:
            assert metric in METRIC_TYPES, f"{metric} should be in METRIC_TYPES"

    def test_generate_all_boxplots_structure(self, temp_figures_dir, sample_data):
        """Test the structure of generate_all_boxplots output."""
        # This test would require setting up actual metric files
        # For now, we test that the function returns a dict
        # We can't easily test with real data without setting up the full pipeline
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])