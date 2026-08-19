"""
Integration test for uncertainty inflation stability (US3).

This test verifies that systematic uncertainty inflation (as implemented in
code/robustness/uncertainty.py) does not cause significant shifts in the
Bayes factor, ensuring result stability under systematic error variations.

Requirement: Bayes factor changes must be < 0.1 log-units when covariance
matrix is inflated by the configured factor.
"""
import json
import logging
import os
import sys
import unittest
from pathlib import Path
from typing import Dict, Any

import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import ProjectConfig, get_logger, setup_logging
from data.state_manager import read_state, check_bootstrap_flag
from models.likelihood import load_covariance_matrix, log_likelihood_yukawa, log_likelihood_newtonian
from inference.nested import load_harmonized_data, run_nested_sampling
from robustness.uncertainty import inflate_uncertainties

# Configure logging
setup_logging()
logger = get_logger(__name__)


class TestUncertaintyInflationStability(unittest.TestCase):
    """Integration test for uncertainty inflation stability."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.config = ProjectConfig()
        cls.project_root = Path(__file__).resolve().parents[2]
        cls.data_dir = cls.project_root / "data"
        cls.processed_dir = cls.data_dir / "processed"
        cls.results_dir = cls.data_dir / "results"
        
        # Ensure directories exist
        cls.processed_dir.mkdir(parents=True, exist_ok=True)
        cls.results_dir.mkdir(parents=True, exist_ok=True)

        # Load harmonized data
        logger.info("Loading harmonized dataset...")
        cls.harmonized_data = load_harmonized_data(cls.processed_dir)
        if cls.harmonized_data is None:
            raise RuntimeError(
                "Failed to load harmonized dataset. "
                "Please ensure T014 (harmonization) has been completed."
            )

        logger.info(f"Loaded {len(cls.harmonized_data['separation'])} data points")

    def test_uncertainty_inflation_stability(self):
        """
        Test that uncertainty inflation does not significantly change Bayes factor.
        
        This test:
        1. Loads the baseline covariance matrix
        2. Inflates uncertainties by the configured factor
        3. Runs nested sampling for both Newtonian and Yukawa models
        4. Computes Bayes factor for both baseline and inflated cases
        5. Verifies the change is < 0.1 log-units
        """
        logger.info("Starting uncertainty inflation stability test...")
        
        # Get inflation factor from config
        inflation_factor = self.config.get("SYSTEMATIC_INFLATION_FACTOR", 1.1)
        logger.info(f"Using inflation factor: {inflation_factor}")

        # Load baseline covariance matrix
        cov_matrix_path = self.processed_dir / "covariance_matrix.npy"
        if not cov_matrix_path.exists():
            self.fail(
                f"Covariance matrix not found at {cov_matrix_path}. "
                "Please ensure T015-COV (covariance construction) has been completed."
            )
        
        baseline_cov = load_covariance_matrix(self.processed_dir)
        self.assertIsNotNone(baseline_cov, "Failed to load baseline covariance matrix")
        
        # Run nested sampling for baseline
        logger.info("Running baseline nested sampling (Newtonian)...")
        baseline_newtonian_result = run_nested_sampling(
            self.harmonized_data, 
            model="newtonian",
            output_dir=self.results_dir,
            seed=42
        )
        
        logger.info("Running baseline nested sampling (Yukawa)...")
        baseline_yukawa_result = run_nested_sampling(
            self.harmonized_data, 
            model="yukawa",
            output_dir=self.results_dir,
            seed=42
        )
        
        if baseline_newtonian_result is None or baseline_yukawa_result is None:
            self.fail("Baseline nested sampling failed to complete")
        
        baseline_log_evidence_newtonian = baseline_newtonian_result.get("log_evidence", 0.0)
        baseline_log_evidence_yukawa = baseline_yukawa_result.get("log_evidence", 0.0)
        baseline_bayes_factor = baseline_log_evidence_yukawa - baseline_log_evidence_newtonian
        
        logger.info(f"Baseline Bayes factor (log units): {baseline_bayes_factor:.4f}")

        # Inflate uncertainties
        logger.info(f"Inflating uncertainties by factor {inflation_factor}...")
        inflated_cov = inflate_uncertainties(baseline_cov, inflation_factor)
        
        # Save inflated covariance for verification
        inflated_cov_path = self.processed_dir / "covariance_matrix_inflated.npy"
        np.save(str(inflated_cov_path), inflated_cov)
        logger.info(f"Saved inflated covariance matrix to {inflated_cov_path}")

        # Create temporary harmonized data with inflated covariance
        # (We need to temporarily replace the covariance in the data dict)
        original_cov = self.harmonized_data.get("covariance_matrix")
        self.harmonized_data["covariance_matrix"] = inflated_cov

        try:
            # Run nested sampling for inflated case
            logger.info("Running inflated nested sampling (Newtonian)...")
            inflated_newtonian_result = run_nested_sampling(
                self.harmonized_data, 
                model="newtonian",
                output_dir=self.results_dir,
                seed=42,
                use_inflated_cov=True
            )
            
            logger.info("Running inflated nested sampling (Yukawa)...")
            inflated_yukawa_result = run_nested_sampling(
                self.harmonized_data, 
                model="yukawa",
                output_dir=self.results_dir,
                seed=42,
                use_inflated_cov=True
            )
            
            if inflated_newtonian_result is None or inflated_yukawa_result is None:
                self.fail("Inflated nested sampling failed to complete")
            
            inflated_log_evidence_newtonian = inflated_newtonian_result.get("log_evidence", 0.0)
            inflated_log_evidence_yukawa = inflated_yukawa_result.get("log_evidence", 0.0)
            inflated_bayes_factor = inflated_log_evidence_yukawa - inflated_log_evidence_newtonian
            
            logger.info(f"Inflated Bayes factor (log units): {inflated_bayes_factor:.4f}")

            # Calculate change in Bayes factor
            bayes_factor_change = abs(inflated_bayes_factor - baseline_bayes_factor)
            logger.info(f"Bayes factor change: {bayes_factor_change:.4f} log units")

            # Check stability threshold (0.1 log-units)
            stability_threshold = 0.1
            is_stable = bayes_factor_change < stability_threshold
            
            logger.info(f"Stability threshold: {stability_threshold} log units")
            logger.info(f"Test result: {'PASS' if is_stable else 'FAIL'}")

            # Save results
            results = {
                "test_name": "uncertainty_inflation_stability",
                "inflation_factor": inflation_factor,
                "baseline_bayes_factor": float(baseline_bayes_factor),
                "inflated_bayes_factor": float(inflated_bayes_factor),
                "bayes_factor_change": float(bayes_factor_change),
                "stability_threshold": stability_threshold,
                "is_stable": is_stable,
                "timestamp": str(self.config.get_timestamp()),
                "pass": is_stable
            }

            results_path = self.results_dir / "uncertainty_inflation_stability.json"
            with open(results_path, "w") as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Results saved to {results_path}")

            # Assert stability
            self.assertTrue(
                is_stable,
                f"Bayes factor change ({bayes_factor_change:.4f}) exceeds stability "
                f"threshold ({stability_threshold}). This indicates the results are "
                "sensitive to systematic uncertainty variations."
            )

        finally:
            # Restore original covariance
            self.harmonized_data["covariance_matrix"] = original_cov

    def test_covariance_matrix_positive_definite_after_inflation(self):
        """
        Test that the inflated covariance matrix remains positive definite.
        
        This is a prerequisite for valid likelihood calculations.
        """
        logger.info("Testing positive definiteness of inflated covariance...")
        
        cov_matrix_path = self.processed_dir / "covariance_matrix.npy"
        if not cov_matrix_path.exists():
            self.skipTest("Covariance matrix not found")
        
        baseline_cov = load_covariance_matrix(self.processed_dir)
        inflation_factor = self.config.get("SYSTEMATIC_INFLATION_FACTOR", 1.1)
        
        inflated_cov = inflate_uncertainties(baseline_cov, inflation_factor)
        
        # Check positive definiteness via eigenvalues
        eigenvalues = np.linalg.eigvalsh(inflated_cov)
        min_eigenvalue = np.min(eigenvalues)
        
        logger.info(f"Minimum eigenvalue of inflated covariance: {min_eigenvalue:.6e}")
        
        self.assertTrue(
            min_eigenvalue > 0,
            f"Inflated covariance matrix is not positive definite. "
            f"Minimum eigenvalue: {min_eigenvalue}"
        )


def run_tests():
    """Run the integration test suite."""
    logger.info("Running uncertainty inflation stability integration tests...")
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUncertaintyInflationStability)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)