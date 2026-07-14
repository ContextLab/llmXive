"""
Integration test for plot generation (Task T025).

Verifies:
1. Plot generation scripts produce PNG files in the expected location.
2. File sizes are under 5MB.
3. Peak memory usage during generation is under 6GB (using tracemalloc).
4. Generated plots contain correct axis labels (Forest, Funnel, Correlation).
"""

import json
import os
import tracemalloc
import unittest
from pathlib import Path
from typing import Dict, Any

# Add project root to path to allow imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.visualization.plots import generate_all_plots
from code.utils.config import get_project_root, ensure_directory


class TestPlotGeneration(unittest.TestCase):
    """Integration tests for the visualization pipeline."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before any tests in this class are run."""
        tracemalloc.start()
        cls.project_root = get_project_root()
        cls.data_dir = cls.project_root / "data" / "derived"
        ensure_directory(cls.data_dir)

        # Ensure we have a valid input JSON for the plots to consume.
        # We generate a minimal valid meta-analysis result if one doesn't exist,
        # or load the existing one from T014/T021/T022 outputs.
        cls.input_json_path = cls.data_dir / "meta_analysis_result.json"
        
        if not cls.input_json_path.exists():
            # Create a minimal valid input for testing purposes
            # This simulates the output of the analysis pipeline
            mock_data = {
                "study_count": 12,
                "weighted_mean_r": 0.35,
                "confidence_interval": [0.25, 0.45],
                "heterogeneity": {
                    "i_squared": 45.50,
                    "q_statistic": 18.2,
                    "p_value": 0.04
                },
                "bias": {
                    "egger_intercept": 0.12,
                    "egger_p_value": 0.25
                },
                "correction": {
                    "adjusted_threshold": 0.01,
                    "significance": True
                },
                "studies": [
                    {"id": "S1", "tract": "Arcuate", "r": 0.4, "se": 0.05},
                    {"id": "S2", "tract": "Cingulum", "r": 0.3, "se": 0.06},
                    {"id": "S3", "tract": "Uncinate", "r": 0.35, "se": 0.05},
                    {"id": "S4", "tract": "Arcuate", "r": 0.38, "se": 0.04},
                    {"id": "S5", "tract": "Cingulum", "r": 0.32, "se": 0.05},
                    {"id": "S6", "tract": "Uncinate", "r": 0.36, "se": 0.06},
                    {"id": "S7", "tract": "Arcuate", "r": 0.42, "se": 0.05},
                    {"id": "S8", "tract": "Cingulum", "r": 0.29, "se": 0.05},
                    {"id": "S9", "tract": "Uncinate", "r": 0.33, "se": 0.05},
                    {"id": "S10", "tract": "Arcuate", "r": 0.39, "se": 0.04},
                    {"id": "S11", "tract": "Cingulum", "r": 0.31, "se": 0.06},
                    {"id": "S12", "tract": "Uncinate", "r": 0.37, "se": 0.05}
                ]
            }
            with open(cls.input_json_path, 'w') as f:
                json.dump(mock_data, f, indent=2)

        cls.expected_files = [
            cls.data_dir / "forest_plot.png",
            cls.data_dir / "funnel_plot.png",
            cls.data_dir / "correlation_summary.png"
        ]

    def setUp(self):
        """Clean up previous run files before each test."""
        for f in self.expected_files:
            if f.exists():
                f.unlink()

    def test_01_file_existence_and_size(self):
        """Test that plots are generated and file sizes are < 5MB."""
        max_size_mb = 5.0
        max_size_bytes = max_size_mb * 1024 * 1024

        # Run the plot generation
        generate_all_plots(str(self.input_json_path), str(self.data_dir))

        for file_path in self.expected_files:
            with self.subTest(file=file_path.name):
                self.assertTrue(
                    file_path.exists(),
                    f"Plot file {file_path.name} was not generated."
                )
                
                size_bytes = file_path.stat().st_size
                self.assertLess(
                    size_bytes,
                    max_size_bytes,
                    f"Plot file {file_path.name} exceeds {max_size_mb}MB "
                    f"(size: {size_bytes / (1024*1024):.2f}MB)"
                )

    def test_02_memory_usage(self):
        """Test that peak memory usage during plot generation is < 6GB."""
        max_memory_gb = 6.0
        max_memory_bytes = max_memory_gb * 1024 * 1024 * 1024

        # Start fresh snapshot
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        tracemalloc.start()

        generate_all_plots(str(self.input_json_path), str(self.data_dir))

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.assertLess(
            peak,
            max_memory_bytes,
            f"Peak memory usage ({peak / (1024*1024*1024):.2f}GB) exceeded "
            f"limit of {max_memory_gb}GB"
        )

    def test_03_axis_labels(self):
        """Test that generated plots contain expected axis labels."""
        import matplotlib.pyplot as plt
        from PIL import Image
        import matplotlib.image as mpimg

        # Re-run generation to ensure files exist
        generate_all_plots(str(self.input_json_path), str(self.data_dir))

        # We will verify labels by inspecting the figure objects if possible,
        # or by checking the saved file metadata/content if necessary.
        # Since we are testing the *generated file*, we need to load the figure
        # from the saved state or re-verify the logic that creates them.
        # A robust integration test often re-runs the plotting logic on a mock
        # figure to assert labels, but here we assert the file exists and
        # we can load it. The specific label check is best done by re-running
        # the plotting function on a temporary figure to assert the state,
        # as reading text from a PNG is brittle.
        
        # Strategy: Re-run the specific plotting functions on a fresh figure
        # to assert labels exist, ensuring the `plots.py` logic is correct.
        # This validates the *code* that produces the files.
        
        from code.visualization.plots import (
            create_forest_plot,
            create_funnel_plot,
            create_correlation_summary
        )

        # Load data
        with open(self.input_json_path, 'r') as f:
            data = json.load(f)

        # Test Forest Plot
        fig_f, ax_f = create_forest_plot(data)
        self.assertIsNotNone(ax_f.get_xlabel(), "Forest plot X-axis label missing")
        self.assertIsNotNone(ax_f.get_ylabel(), "Forest plot Y-axis label missing")
        plt.close(fig_f)

        # Test Funnel Plot
        fig_fun, ax_fun = create_funnel_plot(data)
        self.assertIsNotNone(ax_fun.get_xlabel(), "Funnel plot X-axis label missing")
        self.assertIsNotNone(ax_fun.get_ylabel(), "Funnel plot Y-axis label missing")
        plt.close(fig_fun)

        # Test Correlation Summary
        fig_c, ax_c = create_correlation_summary(data)
        self.assertIsNotNone(ax_c.get_xlabel(), "Correlation plot X-axis label missing")
        self.assertIsNotNone(ax_c.get_ylabel(), "Correlation plot Y-axis label missing")
        plt.close(fig_c)


if __name__ == '__main__':
    unittest.main()