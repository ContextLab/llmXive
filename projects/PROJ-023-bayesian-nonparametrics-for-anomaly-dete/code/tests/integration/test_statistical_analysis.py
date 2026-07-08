"""
Integration tests for statistical analysis in User Story 3.

This module verifies the end-to-end statistical analysis pipeline including:
- Evaluation of anomaly detection metrics (F1, AUC, Bootstrap CI)
- Statistical significance testing (Wilcoxon signed-rank, paired t-test)
- Multiple hypothesis correction (Bonferroni)
- Threshold sensitivity analysis

Prerequisites:
- T015: bayesian_gp.py must have generated data/results/bayesian_predictions.csv
- T020-T022: Baseline scripts must have generated their respective prediction files
- T006: Anomaly injection must have created ground truth in data/processed/ground_truth.csv
"""

import os
import sys
import json
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import pytest
from scipy import stats

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.metrics import (
    precision_recall_f1,
    auc_roc,
    bootstrap_ci,
    bonferroni_correction,
    wilcoxon_signed_rank,
    paired_ttest,
    evaluate_detection
)
from lib.utils import set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test fixtures
@pytest.fixture(scope="module")
def test_data_dir() -> Path:
    """Return the test data directory."""
    data_dir = PROJECT_ROOT / "data"
    if not data_dir.exists():
        pytest.skip("Data directory not found. Run data download/injection first.")
    return data_dir

@pytest.fixture(scope="module")
def ground_truth(test_data_dir: Path) -> pd.DataFrame:
    """Load ground truth anomaly labels."""
    gt_path = test_data_dir / "processed" / "ground_truth.csv"
    if not gt_path.exists():
        pytest.skip(f"Ground truth file not found: {gt_path}. Run anomaly injection first.")
    return pd.read_csv(gt_path)

@pytest.fixture(scope="module")
def bayesian_predictions(test_data_dir: Path) -> pd.DataFrame:
    """Load Bayesian GP predictions."""
    pred_path = test_data_dir / "results" / "bayesian_predictions.csv"
    if not pred_path.exists():
        pytest.skip(f"Bayesian predictions not found: {pred_path}. Run T015 first.")
    return pd.read_csv(pred_path)

@pytest.fixture(scope="module")
def shewhart_predictions(test_data_dir: Path) -> pd.DataFrame:
    """Load Shewhart baseline predictions."""
    pred_path = test_data_dir / "results" / "shewhart_predictions.csv"
    if not pred_path.exists():
        pytest.skip(f"Shewhart predictions not found: {pred_path}. Run T020 first.")
    return pd.read_csv(pred_path)

@pytest.fixture(scope="module")
def cusum_predictions(test_data_dir: Path) -> pd.DataFrame:
    """Load CUSUM baseline predictions."""
    pred_path = test_data_dir / "results" / "cusum_predictions.csv"
    if not pred_path.exists():
        pytest.skip(f"CUSUM predictions not found: {pred_path}. Run T021 first.")
    return pd.read_csv(pred_path)

@pytest.fixture(scope="module")
def vae_predictions(test_data_dir: Path) -> pd.DataFrame:
    """Load VAE baseline predictions."""
    pred_path = test_data_dir / "results" / "vae_predictions.csv"
    if not pred_path.exists():
        pytest.skip(f"VAE predictions not found: {pred_path}. Run T022 first.")
    return pd.read_csv(pred_path)

@pytest.fixture(scope="module")
def aligned_datasets(
    ground_truth: pd.DataFrame,
    bayesian_predictions: pd.DataFrame,
    shewhart_predictions: pd.DataFrame,
    cusum_predictions: pd.DataFrame,
    vae_predictions: pd.DataFrame
) -> Dict[str, pd.DataFrame]:
    """Align all datasets by timestamp for comparison."""
    # Ensure all have timestamp column
    for name, df in [("ground_truth", ground_truth), 
                    ("bayesian", bayesian_predictions),
                    ("shewhart", shewhart_predictions),
                    ("cusum", cusum_predictions),
                    ("vae", vae_predictions)]:
        if "timestamp" not in df.columns:
            if "time" in df.columns:
                df.rename(columns={"time": "timestamp"}, inplace=True)
            elif "index" in df.columns:
                df.rename(columns={"index": "timestamp"}, inplace=True)
    
    # Merge all on timestamp
    merged = ground_truth[["timestamp", "is_anomaly"]].copy()
    merged = merged.merge(
        bayesian_predictions[["timestamp", "anomaly_score"]], 
        on="timestamp", 
        how="inner",
        suffixes=("", "_bayesian")
    ).rename(columns={"anomaly_score": "bayesian_score"})
    
    merged = merged.merge(
        shewhart_predictions[["timestamp", "anomaly_score"]], 
        on="timestamp", 
        how="inner",
        suffixes=("", "_shewhart")
    ).rename(columns={"anomaly_score": "shewhart_score"})
    
    merged = merged.merge(
        cusum_predictions[["timestamp", "anomaly_score"]], 
        on="timestamp", 
        how="inner",
        suffixes=("", "_cusum")
    ).rename(columns={"anomaly_score": "cusum_score"})
    
    merged = merged.merge(
        vae_predictions[["timestamp", "anomaly_score"]], 
        on="timestamp", 
        how="inner",
        suffixes=("", "_vae")
    ).rename(columns={"anomaly_score": "vae_score"})
    
    # Drop rows with any NaN scores
    merged = merged.dropna(subset=["bayesian_score", "shewhart_score", 
                                  "cusum_score", "vae_score"])
    
    return merged

class TestStatisticalAnalysisIntegration:
    """Integration tests for statistical analysis pipeline."""

    def test_metric_calculation(self, aligned_datasets: pd.DataFrame):
        """Test that metrics are correctly calculated for all methods."""
        df = aligned_datasets
        
        methods = ["bayesian", "shewhart", "cusum", "vae"]
        metrics = {}
        
        for method in methods:
            scores = df[f"{method}_score"].values
            ground_truth = df["is_anomaly"].values
            
            # Convert scores to binary predictions at default threshold (0.5)
            predictions = (scores > 0.5).astype(int)
            
            # Calculate metrics
            precision, recall, f1 = precision_recall_f1(
                ground_truth, predictions, zero_division=0
            )
            auc = auc_roc(ground_truth, scores)
            
            metrics[method] = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "auc": auc
            }
            
            # Assertions
            assert 0 <= precision <= 1, f"Precision out of range for {method}"
            assert 0 <= recall <= 1, f"Recall out of range for {method}"
            assert 0 <= f1 <= 1, f"F1 out of range for {method}"
            assert 0 <= auc <= 1, f"AUC out of range for {method}"
            
            logger.info(f"{method}: P={precision:.3f}, R={recall:.3f}, F1={f1:.3f}, AUC={auc:.3f}")

    def test_bootstrap_confidence_intervals(self, aligned_datasets: pd.DataFrame):
        """Test bootstrap confidence interval calculation."""
        df = aligned_datasets
        
        # Use Bayesian method as example
        scores = df["bayesian_score"].values
        ground_truth = df["is_anomaly"].values
        predictions = (scores > 0.5).astype(int)
        
        # Calculate bootstrap CI for F1 score
        ci_lower, ci_upper, ci_mean = bootstrap_ci(
            ground_truth, predictions, metric="f1", n_bootstraps=100, random_state=42
        )
        
        # Assertions
        assert ci_lower <= ci_mean <= ci_upper, "CI bounds incorrect"
        assert 0 <= ci_lower <= 1, "CI lower bound out of range"
        assert 0 <= ci_upper <= 1, "CI upper bound out of range"
        
        logger.info(f"Bootstrap CI for F1: [{ci_lower:.3f}, {ci_upper:.3f}], mean={ci_mean:.3f}")

    def test_wilcoxon_signed_rank_test(self, aligned_datasets: pd.DataFrame):
        """Test Wilcoxon signed-rank test between Bayesian and baselines."""
        df = aligned_datasets
        
        # Calculate F1 scores at optimized threshold for each method
        methods = ["bayesian", "shewhart", "cusum", "vae"]
        f1_scores = {}
        
        for method in methods:
            scores = df[f"{method}_score"].values
            ground_truth = df["is_anomaly"].values
            
            # Find optimal threshold
            best_f1 = 0
            best_threshold = 0.5
            for thresh in np.arange(0.1, 0.9, 0.1):
                preds = (scores > thresh).astype(int)
                _, _, f1 = precision_recall_f1(ground_truth, preds, zero_division=0)
                if f1 > best_f1:
                    best_f1 = f1
                    best_threshold = thresh
            
            f1_scores[method] = best_f1
        
        # Compare Bayesian vs each baseline
        bayesian_f1 = f1_scores["bayesian"]
        
        for baseline in ["shewhart", "cusum", "vae"]:
            baseline_f1 = f1_scores[baseline]
            
            # For Wilcoxon, we need paired samples
            # Create paired F1 scores by bootstrap resampling
            n_bootstraps = 100
            bayesian_boot = []
            baseline_boot = []
            
            n_samples = len(df)
            for _ in range(n_bootstraps):
                indices = np.random.choice(n_samples, n_samples, replace=True)
                sample = df.iloc[indices]
                
                bayesian_scores = sample["bayesian_score"].values
                baseline_scores = sample[f"{baseline}_score"].values
                ground_truth = sample["is_anomaly"].values
                
                # Calculate F1 at threshold 0.5 for consistency
                bayesian_preds = (bayesian_scores > 0.5).astype(int)
                baseline_preds = (baseline_scores > 0.5).astype(int)
                
                _, _, bayesian_f1 = precision_recall_f1(ground_truth, bayesian_preds, zero_division=0)
                _, _, baseline_f1 = precision_recall_f1(ground_truth, baseline_preds, zero_division=0)
                
                bayesian_boot.append(bayesian_f1)
                baseline_boot.append(baseline_f1)
            
            # Perform Wilcoxon signed-rank test
            stat, p_value = wilcoxon_signed_rank(bayesian_boot, baseline_boot)
            
            logger.info(f"Wilcoxon Bayesian vs {baseline}: W={stat:.2f}, p={p_value:.4f}")
            
            # Assertions
            assert not np.isnan(p_value), f"P-value is NaN for {baseline}"
            assert 0 <= p_value <= 1, f"P-value out of range for {baseline}"

    def test_bonferroni_correction(self, aligned_datasets: pd.DataFrame):
        """Test Bonferroni correction for multiple hypothesis testing."""
        df = aligned_datasets
        
        # Calculate raw p-values for comparisons
        raw_p_values = []
        comparisons = []
        
        bayesian_scores = df["bayesian_score"].values
        ground_truth = df["is_anomaly"].values
        
        for baseline in ["shewhart", "cusum", "vae"]:
            baseline_scores = df[f"{baseline}_score"].values
            
            # Create bootstrap samples for F1 scores
            n_bootstraps = 50  # Reduced for test speed
            bayesian_f1s = []
            baseline_f1s = []
            n_samples = len(df)
            
            for _ in range(n_bootstraps):
                indices = np.random.choice(n_samples, n_samples, replace=True)
                sample = df.iloc[indices]
                
                gt = sample["is_anomaly"].values
                bay_scores = sample["bayesian_score"].values
                base_scores = sample[f"{baseline}_score"].values
                
                bay_preds = (bay_scores > 0.5).astype(int)
                base_preds = (base_scores > 0.5).astype(int)
                
                _, _, bay_f1 = precision_recall_f1(gt, bay_preds, zero_division=0)
                _, _, base_f1 = precision_recall_f1(gt, base_preds, zero_division=0)
                
                bayesian_f1s.append(bay_f1)
                baseline_f1s.append(base_f1)
            
            # Paired t-test
            _, p_value = paired_ttest(bayesian_f1s, baseline_f1s)
            raw_p_values.append(p_value)
            comparisons.append(f"Bayesian vs {baseline}")
        
        # Apply Bonferroni correction
        adjusted_p_values = bonferroni_correction(raw_p_values, alpha=0.05)
        
        logger.info(f"Raw p-values: {raw_p_values}")
        logger.info(f"Adjusted p-values (Bonferroni): {adjusted_p_values}")
        
        # Assertions
        assert len(adjusted_p_values) == len(raw_p_values), "Number of adjusted p-values mismatch"
        for adj_p in adjusted_p_values:
            assert 0 <= adj_p <= 1, f"Adjusted p-value out of range: {adj_p}"

    def test_threshold_sensitivity(self, aligned_datasets: pd.DataFrame):
        """Test sensitivity analysis across different thresholds."""
        df = aligned_datasets
        
        thresholds = [0.1, 0.3, 0.5, 0.7, 0.9]
        sensitivity_results = {}
        
        for method in ["bayesian", "shewhart", "cusum", "vae"]:
            scores = df[f"{method}_score"].values
            ground_truth = df["is_anomaly"].values
            
            method_results = []
            for thresh in thresholds:
                predictions = (scores > thresh).astype(int)
                precision, recall, f1 = precision_recall_f1(
                    ground_truth, predictions, zero_division=0
                )
                method_results.append({
                    "threshold": thresh,
                    "precision": precision,
                    "recall": recall,
                    "f1": f1
                })
            
            sensitivity_results[method] = method_results
        
        # Assertions
        for method, results in sensitivity_results.items():
            assert len(results) == len(thresholds), f"Missing results for {method}"
            for result in results:
                assert 0 <= result["precision"] <= 1
                assert 0 <= result["recall"] <= 1
                assert 0 <= result["f1"] <= 1
        
        logger.info("Threshold sensitivity analysis completed successfully")

    def test_evaluation_output_format(self, aligned_datasets: pd.DataFrame):
        """Test that evaluation output matches expected schema."""
        df = aligned_datasets
        
        # Simulate evaluation output structure
        evaluation_output = {
            "methods": {},
            "statistical_tests": {},
            "threshold_analysis": {}
        }
        
        # Calculate metrics for each method
        for method in ["bayesian", "shewhart", "cusum", "vae"]:
            scores = df[f"{method}_score"].values
            ground_truth = df["is_anomaly"].values
            predictions = (scores > 0.5).astype(int)
            
            precision, recall, f1 = precision_recall_f1(
                ground_truth, predictions, zero_division=0
            )
            auc = auc_roc(ground_truth, scores)
            ci_lower, ci_upper, ci_mean = bootstrap_ci(
                ground_truth, predictions, metric="f1", n_bootstraps=50, random_state=42
            )
            
            evaluation_output["methods"][method] = {
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
                "auc": float(auc),
                "bootstrap_ci": {
                    "lower": float(ci_lower),
                    "upper": float(ci_upper),
                    "mean": float(ci_mean)
                }
            }
        
        # Statistical tests
        bayesian_scores = df["bayesian_score"].values
        for baseline in ["shewhart", "cusum", "vae"]:
            baseline_scores = df[f"{baseline}_score"].values
            
            # Paired t-test on F1 scores from bootstrap
            n_bootstraps = 50
            bay_f1s = []
            base_f1s = []
            n_samples = len(df)
            ground_truth = df["is_anomaly"].values
            
            for _ in range(n_bootstraps):
                indices = np.random.choice(n_samples, n_samples, replace=True)
                sample = df.iloc[indices]
                
                gt = sample["is_anomaly"].values
                bay_preds = (sample["bayesian_score"].values > 0.5).astype(int)
                base_preds = (sample[f"{baseline}_score"].values > 0.5).astype(int)
                
                _, _, bay_f1 = precision_recall_f1(gt, bay_preds, zero_division=0)
                _, _, base_f1 = precision_recall_f1(gt, base_preds, zero_division=0)
                
                bay_f1s.append(bay_f1)
                base_f1s.append(base_f1)
            
            stat, p_value = paired_ttest(bay_f1s, base_f1s)
            
            evaluation_output["statistical_tests"][f"bayesian_vs_{baseline}"] = {
                "test": "paired_ttest",
                "statistic": float(stat),
                "p_value": float(p_value)
            }
        
        # Threshold analysis
        for method in ["bayesian", "shewhart", "cusum", "vae"]:
            scores = df[f"{method}_score"].values
            ground_truth = df["is_anomaly"].values
            
            thresholds = [0.3, 0.5, 0.7]
            threshold_results = []
            
            for thresh in thresholds:
                predictions = (scores > thresh).astype(int)
                precision, recall, f1 = precision_recall_f1(
                    ground_truth, predictions, zero_division=0
                )
                threshold_results.append({
                    "threshold": float(thresh),
                    "precision": float(precision),
                    "recall": float(recall),
                    "f1": float(f1)
                })
            
            evaluation_output["threshold_analysis"][method] = threshold_results
        
        # Validate output structure
        assert "methods" in evaluation_output
        assert "statistical_tests" in evaluation_output
        assert "threshold_analysis" in evaluation_output
        
        for method in ["bayesian", "shewhart", "cusum", "vae"]:
            assert method in evaluation_output["methods"]
            assert method in evaluation_output["threshold_analysis"]
        
        logger.info("Evaluation output format validated successfully")

    def test_reproducibility(self, aligned_datasets: pd.DataFrame):
        """Test that results are reproducible with fixed random seed."""
        set_seed(42)
        
        df = aligned_datasets
        scores = df["bayesian_score"].values
        ground_truth = df["is_anomaly"].values
        predictions = (scores > 0.5).astype(int)
        
        # First run
        ci1_lower, ci1_upper, ci1_mean = bootstrap_ci(
            ground_truth, predictions, metric="f1", n_bootstraps=100, random_state=42
        )
        
        # Reset seed
        set_seed(42)
        
        # Second run
        ci2_lower, ci2_upper, ci2_mean = bootstrap_ci(
            ground_truth, predictions, metric="f1", n_bootstraps=100, random_state=42
        )
        
        # Assertions
        assert ci1_lower == ci2_lower, "Bootstrap CI lower bound not reproducible"
        assert ci1_upper == ci2_upper, "Bootstrap CI upper bound not reproducible"
        assert ci1_mean == ci2_mean, "Bootstrap CI mean not reproducible"
        
        logger.info("Reproducibility test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])