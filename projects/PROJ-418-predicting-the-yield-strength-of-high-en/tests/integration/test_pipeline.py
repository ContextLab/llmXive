"""
Integration tests for the full HEA yield strength prediction pipeline.

This module tests the end-to-end flow from data download (or loading from disk),
preprocessing, descriptor calculation, model training, evaluation, and report generation.
It verifies that all components work together and produce the expected output artifacts.
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.download import download_dataset
from code.data.preprocess import preprocess_data, normalize_units
from code.data.descriptors import calculate_descriptors, filter_missing_properties
from code.data.pipeline import run_pipeline
from code.data.status_writer import write_data_status
from code.models.train import run_training_pipeline
from code.models.evaluate import run_evaluation_pipeline
from code.models.metrics_writer import write_metrics_json
from code.models.power_analysis import write_power_analysis
from code.models.report_generator import main as generate_report_main
from code.utils.config import get_config
from code.utils.logging import get_logger, set_seeds

logger = get_logger(__name__)


class TestPipelineIntegration(unittest.TestCase):
    """Integration tests for the full HEA prediction pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test outputs
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, "data")
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.data_dir)
        os.makedirs(self.output_dir)

        # Set deterministic seeds
        set_seeds(42)

        # Mock config to use test directories
        self.original_config = None

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_mock_dataset(self, n_samples=100):
        """Create a mock dataset for integration testing."""
        np.random.seed(42)

        # Create mock elemental composition data
        elements = ["Fe", "Cr", "Ni", "Co", "Mn", "Al", "Ti", "Cu"]
        compositions = []

        for _ in range(n_samples):
            # Random composition that sums to 1
            raw = np.random.rand(len(elements))
            norm = raw / raw.sum()
            comp = dict(zip(elements, norm))
            compositions.append(comp)

        # Create DataFrame with required columns
        data = {
            "composition": compositions,
            "yield_strength": np.random.uniform(200, 1000, n_samples),  # MPa
            "temperature": np.random.uniform(20, 25, n_samples),  # Room temp
            "phase": np.random.choice(["single", "multi"], n_samples, p=[0.8, 0.2]),
            "source": ["mock_source"] * n_samples,
        }

        return pd.DataFrame(data)

    def test_full_pipeline_integration(self):
        """Test the full pipeline from data to report generation."""
        # Create mock data file
        mock_data_path = os.path.join(self.data_dir, "mock_hea_data.csv")
        mock_df = self._create_mock_dataset(n_samples=100)
        mock_df.to_csv(mock_data_path, index=False)

        # Patch the download function to use our mock data
        with patch('code.data.download.download_dataset') as mock_download:
            mock_download.return_value = mock_df

            # Run the full pipeline
            try:
                processed_df = run_pipeline(
                    input_path=mock_data_path,
                    output_dir=self.data_dir,
                    temp_dir=self.test_dir
                )

                # Verify processed data exists and has expected columns
                self.assertIsNotNone(processed_df)
                self.assertGreater(len(processed_df), 0)

                # Check for descriptor columns
                expected_descriptors = ["delta", "delta_chi", "VEC", "entropy", "melting_var"]
                for col in expected_descriptors:
                    self.assertIn(col, processed_df.columns)

                # Filter out rows with missing properties
                filtered_df = filter_missing_properties(processed_df)
                self.assertGreater(len(filtered_df), 0)

                # Write status
                status_path = os.path.join(self.output_dir, "data_status.json")
                write_data_status(filtered_df, status_path)

                self.assertTrue(os.path.exists(status_path))
                with open(status_path, 'r') as f:
                    status = json.load(f)
                self.assertIn('count', status)

                # Run training pipeline
                model_results = run_training_pipeline(
                    data_path=mock_data_path,
                    output_dir=self.output_dir,
                    test_size=0.2,
                    cv_folds=3,  # Reduced for faster testing
                    random_state=42
                )

                self.assertIsNotNone(model_results)
                self.assertIn('linear', model_results)
                self.assertIn('rf', model_results)
                self.assertIn('gb', model_results)

                # Run evaluation pipeline
                eval_results = run_evaluation_pipeline(
                    model_results=model_results,
                    data_path=mock_data_path,
                    output_dir=self.output_dir,
                    n_permutations=10,  # Reduced for faster testing
                    n_bootstrap=10,    # Reduced for faster testing
                    n_sensitivity=3
                )

                self.assertIsNotNone(eval_results)

                # Write metrics
                metrics_path = os.path.join(self.output_dir, "metrics.json")
                write_metrics_json(model_results, metrics_path)
                self.assertTrue(os.path.exists(metrics_path))

                # Write power analysis
                power_path = os.path.join(self.output_dir, "power_analysis.json")
                write_power_analysis(len(filtered_df), power_path)
                self.assertTrue(os.path.exists(power_path))

                # Generate report
                report_path = os.path.join(self.output_dir, "report.md")
                generate_report_main(
                    output_dir=self.output_dir,
                    report_path=report_path
                )
                self.assertTrue(os.path.exists(report_path))

                # Verify report contains disclaimers
                with open(report_path, 'r') as f:
                    report_content = f.read()
                self.assertIn("Associational analysis only", report_content)

            except Exception as e:
                logger.error(f"Pipeline integration test failed: {e}")
                raise

    def test_data_processing_chain(self):
        """Test the data processing chain: download -> preprocess -> descriptors."""
        mock_df = self._create_mock_dataset(n_samples=50)

        with patch('code.data.download.download_dataset') as mock_download:
            mock_download.return_value = mock_df

            # Test preprocessing
            processed = preprocess_data(mock_df)
            self.assertIsNotNone(processed)
            self.assertIn("yield_strength_mpa", processed.columns)

            # Test unit normalization
            normalized = normalize_units(processed)
            self.assertEqual(normalized["yield_strength_mpa"].dtype, np.float64)

            # Test descriptor calculation
            with_descriptors = calculate_descriptors(normalized)
            self.assertIn("delta", with_descriptors.columns)
            self.assertIn("VEC", with_descriptors.columns)

            # Test filtering missing properties
            filtered = filter_missing_properties(with_descriptors)
            self.assertGreater(len(filtered), 0)

    def test_model_training_and_evaluation(self):
        """Test model training and evaluation pipeline."""
        mock_df = self._create_mock_dataset(n_samples=50)
        mock_df.to_csv(os.path.join(self.data_dir, "test_data.csv"), index=False)

        # Train models
        results = run_training_pipeline(
            data_path=os.path.join(self.data_dir, "test_data.csv"),
            output_dir=self.output_dir,
            test_size=0.2,
            cv_folds=3,
            random_state=42
        )

        self.assertIn('linear', results)
        self.assertIn('rf', results)
        self.assertIn('gb', results)

        # Evaluate models
        eval_results = run_evaluation_pipeline(
            model_results=results,
            data_path=os.path.join(self.data_dir, "test_data.csv"),
            output_dir=self.output_dir,
            n_permutations=5,
            n_bootstrap=5,
            n_sensitivity=3
        )

        self.assertIn('metrics', eval_results)
        self.assertIn('vif', eval_results)
        self.assertIn('permutation', eval_results)

    def test_error_handling_insufficient_data(self):
        """Test pipeline behavior with insufficient data (N < 50)."""
        mock_df = self._create_mock_dataset(n_samples=30)  # Below threshold

        with patch('code.data.download.download_dataset') as mock_download:
            mock_download.return_value = mock_df

            processed = preprocess_data(mock_df)
            with_descriptors = calculate_descriptors(processed)
            filtered = filter_missing_properties(with_descriptors)

            # Write power analysis for small dataset
            power_path = os.path.join(self.output_dir, "power_analysis.json")
            write_power_analysis(len(filtered), power_path)

            self.assertTrue(os.path.exists(power_path))
            with open(power_path, 'r') as f:
                power_status = json.load(f)

            self.assertEqual(power_status['status'], 'insufficient_power')

    def test_parallel_execution_compatibility(self):
        """Test that pipeline components can run independently (for parallel execution)."""
        mock_df = self._create_mock_dataset(n_samples=50)

        # Test individual components independently
        processed = preprocess_data(mock_df)
        self.assertIsNotNone(processed)

        with_descriptors = calculate_descriptors(processed)
        self.assertIsNotNone(with_descriptors)

        filtered = filter_missing_properties(with_descriptors)
        self.assertIsNotNone(filtered)

        # Each component should be callable independently
        self.assertTrue(hasattr(preprocess_data, '__call__'))
        self.assertTrue(hasattr(calculate_descriptors, '__call__'))
        self.assertTrue(hasattr(filter_missing_properties, '__call__'))


if __name__ == '__main__':
    unittest.main()