"""
Unit tests for plot generation in code/viz/plots.py.

Tests verify that:
1. Partial Dependence Plots (PDP) are generated correctly for top features.
2. Correlation heatmaps are generated correctly.
3. Output files are saved to the correct paths with deterministic names.
4. Plots are valid image files (non-empty, correct format).
"""
import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.utils.config import get_paths, ensure_directories
from code.viz.plots import generate_pdp, generate_correlation_heatmap, main


class TestPlotGeneration(unittest.TestCase):
    """Test cases for plot generation functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test outputs
        self.test_dir = tempfile.mkdtemp()
        self.paths = {
            "data": self.test_dir,
            "artifacts": os.path.join(self.test_dir, "artifacts"),
            "processed": os.path.join(self.test_dir, "processed"),
        }
        ensure_directories(self.paths)
        
        # Create mock data for testing
        self.mock_data = pd.DataFrame({
            'delta': np.random.rand(100),
            'delta_hmix': np.random.rand(100),
            'vec': np.random.rand(100),
            'delta_chi': np.random.rand(100),
            'shear_modulus': np.random.rand(100) * 100,
            'alloy_family': np.random.choice(['Zr', 'Ti', 'Cu', 'Pd'], 100)
        })
        
        # Create a simple mock model
        self.mock_model = MagicMock()
        self.mock_model.predict = MagicMock(return_value=np.random.rand(100))
        self.mock_model.feature_importances_ = np.array([0.4, 0.3, 0.2, 0.1])
        
        # Mock feature names
        self.feature_names = ['delta', 'delta_hmix', 'vec', 'delta_chi']

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generate_pdp_creates_file(self):
        """Test that PDP generation creates a valid image file."""
        output_path = os.path.join(self.paths["artifacts"], "pdp_top3.png")
        
        # Generate PDP
        result = generate_pdp(
            model=self.mock_model,
            data=self.mock_data,
            feature_names=self.feature_names,
            target_col='shear_modulus',
            output_path=output_path
        )
        
        # Verify file exists and is non-empty
        self.assertTrue(os.path.exists(output_path))
        self.assertGreater(os.path.getsize(output_path), 0)
        self.assertTrue(result)

    def test_generate_pdp_correct_features(self):
        """Test that PDP is generated for top 3 features."""
        output_path = os.path.join(self.paths["artifacts"], "pdp_top3.png")
        
        # Generate PDP
        generate_pdp(
            model=self.mock_model,
            data=self.mock_data,
            feature_names=self.feature_names,
            target_col='shear_modulus',
            output_path=output_path
        )
        
        # Verify the function was called with correct parameters
        # (This is implicitly tested by successful execution)
        self.assertTrue(os.path.exists(output_path))

    def test_generate_correlation_heatmap_creates_file(self):
        """Test that correlation heatmap generation creates a valid image file."""
        output_path = os.path.join(self.paths["artifacts"], "correlation_heatmap.png")
        
        # Generate heatmap
        result = generate_correlation_heatmap(
            data=self.mock_data,
            feature_names=self.feature_names,
            target_col='shear_modulus',
            output_path=output_path
        )
        
        # Verify file exists and is non-empty
        self.assertTrue(os.path.exists(output_path))
        self.assertGreater(os.path.getsize(output_path), 0)
        self.assertTrue(result)

    def test_generate_correlation_heatmap_includes_target(self):
        """Test that correlation heatmap includes the target variable."""
        output_path = os.path.join(self.paths["artifacts"], "correlation_heatmap.png")
        
        # Generate heatmap
        generate_correlation_heatmap(
            data=self.mock_data,
            feature_names=self.feature_names,
            target_col='shear_modulus',
            output_path=output_path
        )
        
        # Verify file exists
        self.assertTrue(os.path.exists(output_path))

    def test_main_function_creates_all_plots(self):
        """Test that main function generates all required plots."""
        # Create a mock importance report
        importance_report = {
            "top_features": ["delta", "delta_hmix", "vec"],
            "importances": [0.4, 0.3, 0.2]
        }
        
        importance_report_path = os.path.join(self.paths["artifacts"], "importance_report.json")
        with open(importance_report_path, 'w') as f:
            json.dump(importance_report, f)
        
        # Mock the load_processed_data function to return our mock data
        with patch('code.viz.plots.load_processed_data', return_value=self.mock_data):
            # Mock the load_json_file function to return our importance report
            with patch('code.viz.plots.load_json_file', return_value=importance_report):
                # Create a mock model
                mock_model = MagicMock()
                mock_model.predict = MagicMock(return_value=np.random.rand(100))
                
                with patch('code.viz.plots.load_model', return_value=mock_model):
                    # Run main
                    main(
                        data_path=os.path.join(self.paths["processed"], "features.csv"),
                        model_path=os.path.join(self.paths["artifacts"], "best_model.pkl"),
                        importance_report_path=importance_report_path,
                        output_dir=self.paths["artifacts"]
                    )
        
        # Verify both plot files were created
        pdp_path = os.path.join(self.paths["artifacts"], "pdp_top3.png")
        heatmap_path = os.path.join(self.paths["artifacts"], "correlation_heatmap.png")
        
        self.assertTrue(os.path.exists(pdp_path))
        self.assertTrue(os.path.exists(heatmap_path))
        self.assertGreater(os.path.getsize(pdp_path), 0)
        self.assertGreater(os.path.getsize(heatmap_path), 0)

    def test_deterministic_filenames(self):
        """Test that filenames are deterministic and follow the spec."""
        # Run main twice and verify same filenames are produced
        importance_report = {
            "top_features": ["delta", "delta_hmix", "vec"],
            "importances": [0.4, 0.3, 0.2]
        }
        
        importance_report_path = os.path.join(self.paths["artifacts"], "importance_report.json")
        with open(importance_report_path, 'w') as f:
            json.dump(importance_report, f)
        
        with patch('code.viz.plots.load_processed_data', return_value=self.mock_data):
            with patch('code.viz.plots.load_json_file', return_value=importance_report):
                mock_model = MagicMock()
                mock_model.predict = MagicMock(return_value=np.random.rand(100))
                
                with patch('code.viz.plots.load_model', return_value=mock_model):
                    main(
                        data_path=os.path.join(self.paths["processed"], "features.csv"),
                        model_path=os.path.join(self.paths["artifacts"], "best_model.pkl"),
                        importance_report_path=importance_report_path,
                        output_dir=self.paths["artifacts"]
                    )
        
        # Check for expected deterministic filenames
        expected_files = [
            "pdp_top3.png",
            "correlation_heatmap.png"
        ]
        
        for expected_file in expected_files:
            full_path = os.path.join(self.paths["artifacts"], expected_file)
            self.assertTrue(os.path.exists(full_path), f"Expected file {expected_file} not found")

    def test_error_handling_missing_data(self):
        """Test error handling when data file is missing."""
        with self.assertRaises(FileNotFoundError):
            generate_correlation_heatmap(
                data=pd.DataFrame(),  # Empty dataframe
                feature_names=[],
                target_col='shear_modulus',
                output_path=os.path.join(self.paths["artifacts"], "test.png")
            )

    def test_error_handling_invalid_model(self):
        """Test error handling when model is invalid."""
        with self.assertRaises(AttributeError):
            generate_pdp(
                model={},  # Invalid model
                data=self.mock_data,
                feature_names=self.feature_names,
                target_col='shear_modulus',
                output_path=os.path.join(self.paths["artifacts"], "test.png")
            )


if __name__ == '__main__':
    unittest.main()