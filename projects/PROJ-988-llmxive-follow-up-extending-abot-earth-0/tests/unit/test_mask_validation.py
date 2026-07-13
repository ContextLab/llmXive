"""
Unit tests for cloud mask validation logic.
Specifically verifies the Kolmogorov-Smirnov (KS) test implementation
used to compare synthetic cloud mask distributions against real reference masks.
"""
import os
import sys
import unittest
import json
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
from scipy import stats

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from lib.logging_config import get_logger

logger = get_logger(__name__)


class MockDataLoader:
    """Mock loader to simulate reading mask data for testing without external dependencies."""

    @staticmethod
    def generate_synthetic_mask_distribution(n_samples: int = 1000, mean: float = 0.2, std: float = 0.05) -> np.ndarray:
        """Generate a normal distribution of cloud coverage fractions."""
        return np.random.normal(loc=mean, scale=std, size=n_samples)

    @staticmethod
    def generate_real_reference_distribution(n_samples: int = 1000, mean: float = 0.22, std: float = 0.06) -> np.ndarray:
        """Generate a slightly shifted normal distribution to simulate real reference data."""
        return np.random.normal(loc=mean, scale=std, size=n_samples)


class TestCloudMaskValidation(unittest.TestCase):
    """Test suite for cloud mask validation logic (KS-test implementation)."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_loader = MockDataLoader()
        self.knobs = {
            "synthetic_mean": 0.20,
            "synthetic_std": 0.05,
            "real_mean": 0.22,
            "real_std": 0.06,
            "sample_size": 1000
        }

    def test_ks_test_import_and_execution(self):
        """
        Verify that the Kolmogorov-Smirnov test is correctly imported from scipy.stats
        and can be executed on two distributions.
        """
        synthetic_data = self.mock_loader.generate_synthetic_mask_distribution(
            n_samples=self.knobs["sample_size"],
            mean=self.knobs["synthetic_mean"],
            std=self.knobs["synthetic_std"]
        )
        real_data = self.mock_loader.generate_real_reference_distribution(
            n_samples=self.knobs["sample_size"],
            mean=self.knobs["real_mean"],
            std=self.knobs["real_std"]
        )

        # Perform the KS test
        result = stats.ks_2samp(synthetic_data, real_data)

        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'statistic'))
        self.assertTrue(hasattr(result, 'pvalue'))
        self.assertIsInstance(result.statistic, float)
        self.assertIsInstance(result.pvalue, float)
        self.assertGreaterEqual(result.statistic, 0.0)
        self.assertLessEqual(result.statistic, 1.0)
        self.assertGreaterEqual(result.pvalue, 0.0)
        self.assertLessEqual(result.pvalue, 1.0)

        logger.info(f"KS Test Executed: Statistic={result.statistic:.4f}, p-value={result.pvalue:.4f}")

    def test_mask_similarity_threshold_logic(self):
        """
        Verify the logic that determines if the synthetic mask distribution
        is sufficiently similar to the real distribution based on the p-value.
        """
        synthetic_data = self.mock_loader.generate_synthetic_mask_distribution(
            n_samples=self.knobs["sample_size"],
            mean=self.knobs["synthetic_mean"],
            std=self.knobs["synthetic_std"]
        )
        # Create a very similar distribution (same params)
        real_data = self.mock_loader.generate_synthetic_mask_distribution(
            n_samples=self.knobs["sample_size"],
            mean=self.knobs["synthetic_mean"],
            std=self.knobs["synthetic_std"]
        )

        result = stats.ks_2samp(synthetic_data, real_data)

        # Define threshold (e.g., p > 0.05 implies we cannot reject null hypothesis of same distribution)
        similarity_threshold = 0.05
        is_similar = result.pvalue > similarity_threshold

        self.assertTrue(is_similar, "Identical distributions should be considered similar (p > 0.05)")
        logger.info(f"Similarity Check: p-value={result.pvalue:.4f} > {similarity_threshold} -> {is_similar}")

    def test_mask_similarity_failure_logic(self):
        """
        Verify that significantly different distributions are correctly identified as dissimilar.
        """
        synthetic_data = self.mock_loader.generate_synthetic_mask_distribution(
            n_samples=self.knobs["sample_size"],
            mean=0.10,  # Low cloud cover
            std=0.02
        )
        real_data = self.mock_loader.generate_real_reference_distribution(
            n_samples=self.knobs["sample_size"],
            mean=0.80,  # High cloud cover
            std=0.10
        )

        result = stats.ks_2samp(synthetic_data, real_data)
        
        # With such different means, p-value should be very low
        self.assertLess(result.pvalue, 0.001, "Very different distributions should yield low p-value")

    def test_validation_report_structure(self):
        """
        Verify that the validation logic produces a report structure compatible
        with the expected output format for T016 (mask_similarity_score.json).
        """
        synthetic_data = self.mock_loader.generate_synthetic_mask_distribution(
            n_samples=self.knobs["sample_size"],
            mean=self.knobs["synthetic_mean"],
            std=self.knobs["synthetic_std"]
        )
        real_data = self.mock_loader.generate_real_reference_distribution(
            n_samples=self.knobs["sample_size"],
            mean=self.knobs["real_mean"],
            std=self.knobs["real_std"]
        )

        ks_result = stats.ks_2samp(synthetic_data, real_data)

        report = {
            "test_method": "Kolmogorov-Smirnov (KS) 2-sample test",
            "statistic": float(ks_result.statistic),
            "p_value": float(ks_result.pvalue),
            "threshold": 0.05,
            "passed": bool(ks_result.pvalue > 0.05),
            "description": "Comparison of synthetic vs real cloud mask coverage distributions"
        }

        # Verify JSON serializability
        try:
            json_str = json.dumps(report)
            loaded_report = json.loads(json_str)
            self.assertEqual(loaded_report["test_method"], report["test_method"])
            self.assertEqual(loaded_report["passed"], report["passed"])
            logger.info(f"Report structure validated: {json_str}")
        except (TypeError, ValueError) as e:
            self.fail(f"Report structure is not JSON serializable: {e}")

    def test_edge_case_empty_samples(self):
        """Verify behavior with empty or single-sample inputs (should raise error or handle gracefully)."""
        with self.assertRaises(ValueError):
            stats.ks_2samp([], [])

        # Single sample might work but is statistically weak, check it doesn't crash unexpectedly
        try:
            stats.ks_2samp([0.5], [0.5])
        except Exception as e:
            # Depending on scipy version, this might raise or return 0.0
            logger.warning(f"Single sample KS test behavior: {e}")


if __name__ == "__main__":
    unittest.main()