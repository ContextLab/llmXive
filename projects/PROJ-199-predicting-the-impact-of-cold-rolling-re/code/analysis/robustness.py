"""
Robustness analysis module for evaluating model stability under data sparsity.

This module implements sensitivity analysis by sweeping interpolation tolerance
over a specific set of values and quantifying the impact on model performance (R²).
It also supports variance decomposition to quantify residual variance from missing
microstructural variables.

FR-007: Sensitivity analysis must sweep interpolation tolerance over {0.01, 0.05, 0.1}.
US-4 Scenario 2: Verify R² variation remains ≤ 0.02 across swept tolerances.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Import local utilities
from utils.logging import get_logger
from config import get_reductions, get_seed

logger = get_logger(__name__)

# Mandated tolerance set from FR-007
MANDATED_TOLERANCES = [0.01, 0.05, 0.1]

class RobustnessAnalysis:
    """
    Performs sensitivity analysis and variance decomposition for predictive models.
    """

    def __init__(self, model_class, feature_columns: List[str], target_column: str):
        """
        Initialize the robustness analyzer.

        Args:
            model_class: The sklearn model class to use for training.
            feature_columns: List of column names to use as features.
            target_column: Name of the target column.
        """
        self.model_class = model_class
        self.feature_columns = feature_columns
        self.target_column = target_column
        self.scaler = StandardScaler()
        self.results: Dict[str, Any] = {}

    def run_sensitivity_analysis(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        tolerances: Optional[List[float]] = None,
        n_iterations: int = 10
    ) -> Dict[str, List[float]]:
        """
        Run sensitivity analysis by sweeping interpolation tolerance.

        This simulates the effect of data sparsity or interpolation errors
        by adding noise to the features based on the tolerance level.

        Args:
            X: Feature DataFrame.
            y: Target Series.
            tolerances: List of tolerance values to test. Defaults to MANDATED_TOLERANCES.
            n_iterations: Number of Monte Carlo iterations per tolerance.

        Returns:
            Dictionary mapping each tolerance to a list of R² scores.
        """
        if tolerances is None:
            tolerances = MANDATED_TOLERANCES

        logger.info(f"Running sensitivity analysis for tolerances: {tolerances}")

        # Split data once
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=get_seed()
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        results = {t: [] for t in tolerances}

        for tol in tolerances:
            logger.debug(f"Processing tolerance {tol}")
            for i in range(n_iterations):
                # Simulate interpolation error/noise based on tolerance
                # This is a proxy for the "interpolation tolerance" mentioned in the spec.
                # In a real physical context, this might represent uncertainty in grain boundary
                # orientation or reduction level measurement.
                noise = np.random.normal(0, tol, size=X_train_scaled.shape)
                X_train_noisy = X_train_scaled + noise

                # Train model
                model = self.model_class()
                model.fit(X_train_noisy, y_train)

                # Evaluate
                y_pred = model.predict(X_test_scaled)
                r2 = r2_score(y_test, y_pred)
                results[tol].append(r2)

            logger.info(f"Completed tolerance {tol}: Mean R² = {np.mean(results[tol]):.4f}")

        self.results['sensitivity'] = results
        return results

    def calculate_r2_variation(self, sensitivity_results: Dict[str, List[float]]) -> float:
        """
        Calculate the variation (max - min) of mean R² scores across tolerances.

        Args:
            sensitivity_results: Output from run_sensitivity_analysis.

        Returns:
            The variation in R² scores.
        """
        if not sensitivity_results:
            raise ValueError("No sensitivity results provided.")

        mean_scores = [np.mean(scores) for scores in sensitivity_results.values()]
        variation = max(mean_scores) - min(mean_scores)

        logger.info(f"R² variation across tolerances: {variation:.4f}")
        return variation

    def check_variation_threshold(self, variation: float, threshold: float = 0.02) -> bool:
        """
        Check if the R² variation is within the acceptable threshold.

        Args:
            variation: The calculated R² variation.
            threshold: The maximum allowed variation (default 0.02 per US-4 Scenario 2).

        Returns:
            True if variation <= threshold, False otherwise.
        """
        is_pass = variation <= threshold
        status = "PASS" if is_pass else "FAIL"
        logger.info(f"Variation check: {status} (Variation: {variation:.4f}, Threshold: {threshold})")
        return is_pass

    def run_variance_decomposition(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        missing_variables: List[str]
    ) -> Dict[str, float]:
        """
        Perform variance decomposition to quantify residual variance from missing variables.

        This is a simplified implementation using hierarchical modeling concepts.
        In a full implementation, Shapley values or more complex hierarchical
        modeling would be used.

        Args:
            X: Feature DataFrame.
            y: Target Series.
            missing_variables: List of variable names considered "missing".

        Returns:
            Dictionary with variance attribution.
        """
        logger.info(f"Running variance decomposition for missing variables: {missing_variables}")

        # Simple proxy: Compare model performance with and without synthetic noise
        # representing the missing variables.
        # This is a placeholder for a more rigorous statistical method.
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=get_seed()
        )

        model_full = self.model_class()
        model_full.fit(X_train, y_train)
        r2_full = model_full.score(X_test, y_test)

        # Simulate missing variables by adding noise to features
        # This is a heuristic approximation.
        noise_factor = 0.1
        X_test_noisy = X_test + np.random.normal(0, noise_factor, size=X_test.shape)
        r2_noisy = model_full.score(X_test_noisy, y_test)

        variance_attributed = r2_full - r2_noisy

        result = {
            "r2_full_model": r2_full,
            "r2_with_missing_noise": r2_noisy,
            "attributed_variance": variance_attributed,
            "missing_variables": missing_variables
        }

        self.results['variance_decomposition'] = result
        return result

def run_sensitivity_analysis(
    model_class,
    X: pd.DataFrame,
    y: pd.Series,
    feature_columns: List[str],
    target_column: str,
    tolerances: Optional[List[float]] = None,
    n_iterations: int = 10
) -> Dict[str, Any]:
    """
    Convenience function to run sensitivity analysis.

    Args:
        model_class: Sklearn model class.
        X: Feature DataFrame.
        y: Target Series.
        feature_columns: List of feature column names.
        target_column: Target column name.
        tolerances: List of tolerances to test.
        n_iterations: Number of iterations per tolerance.

    Returns:
        Dictionary containing results and variation metrics.
    """
    analyzer = RobustnessAnalysis(model_class, feature_columns, target_column)
    sensitivity_results = analyzer.run_sensitivity_analysis(
        X[feature_columns], y[target_column] if isinstance(y, pd.Series) else y,
        tolerances=tolerances,
        n_iterations=n_iterations
    )

    variation = analyzer.calculate_r2_variation(sensitivity_results)
    passed = analyzer.check_variation_threshold(variation)

    return {
        "sensitivity_results": sensitivity_results,
        "variation": variation,
        "passed_threshold": passed,
        "threshold": 0.02
    }

def main():
    """
    Main entry point for running robustness analysis from the command line.
    """
    logger.info("Starting Robustness Analysis")

    # Example usage (would be replaced with actual data loading in a real run)
    # This is a placeholder to demonstrate the interface.
    # In a real scenario, data would be loaded from data/processed/descriptors.csv
    # and models from code/models/train.py.

    try:
        from sklearn.linear_model import Ridge
        # Mock data for demonstration
        np.random.seed(42)
        n_samples = 100
        X_mock = pd.DataFrame(np.random.rand(n_samples, 2), columns=['feat1', 'feat2'])
        y_mock = pd.Series(np.random.rand(n_samples), name='target')

        result = run_sensitivity_analysis(
            model_class=Ridge,
            X=X_mock,
            y=y_mock,
            feature_columns=['feat1', 'feat2'],
            target_column='target',
            tolerances=MANDATED_TOLERANCES,
            n_iterations=5
        )

        print(f"Analysis Result: {result}")

        if not result['passed_threshold']:
            logger.warning(f"R² variation {result['variation']:.4f} exceeds threshold 0.02")
            sys.exit(1)
        else:
            logger.info("Robustness check passed.")

    except Exception as e:
        logger.error(f"Error during robustness analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()