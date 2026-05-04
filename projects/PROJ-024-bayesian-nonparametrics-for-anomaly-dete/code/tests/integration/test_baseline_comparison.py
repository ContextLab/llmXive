"""
Integration test for end-to-end baseline comparison pipeline (US2).

This test verifies that all baseline models can be run on a dataset
and that evaluation metrics are computed correctly with F1-score
measurements and precision-recall curves.

Independent Test: Can be fully tested by running all three models
on a single UCI dataset and generating precision-recall curves
with F1-score measurements.
"""
import os
import sys
import json
import pytest
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_SRC = PROJECT_ROOT / "code"
sys.path.insert(0, str(CODE_SRC))

from data.synthetic_generator import (
    generate_synthetic_timeseries,
    save_synthetic_dataset,
    load_synthetic_dataset,
    AnomalyConfig,
    SignalConfig
)
from baselines.arima import ARIMABaseline, ARIMAConfig, create_baseline as create_arima_baseline
from baselines.moving_average import MovingAverageBaseline, MovingAverageConfig, create_baseline as create_ma_baseline
from evaluation.metrics import (
    EvaluationMetrics,
    compute_f1_score,
    compute_precision,
    compute_recall,
    compute_auc,
    generate_confusion_matrix,
    compute_all_metrics,
    compute_roc_curve_points,
    compute_pr_curve_points
)
from evaluation.plots import (
    generate_roc_curve,
    save_roc_curve,
    generate_pr_curve,
    save_pr_curve,
    EvaluationPlotConfig
)
from models.time_series import TimeSeries
from models.anomaly_score import AnomalyScore


@pytest.fixture
def synthetic_dataset_path(tmp_path: Path) -> Path:
    """Create a synthetic dataset with known anomalies for testing."""
    # Generate synthetic time series with injected anomalies
    np.random.seed(42)

    signal_config = SignalConfig(
        signal_type="sinusoidal",
        frequency=0.01,
        amplitude=1.0,
        noise_level=0.1,
        length=1000
    )

    anomaly_config = AnomalyConfig(
        anomaly_type="point",
        anomaly_rate=0.05,  # 5% anomalies
        anomaly_magnitude=5.0,
        seed=42
    )

    # Generate the dataset
    data, ground_truth = generate_synthetic_timeseries(
        signal_config=signal_config,
        anomaly_config=anomaly_config,
        seed=42
    )

    # Save to temp directory
    dataset_path = tmp_path / "test_dataset"
    dataset_path.mkdir(parents=True, exist_ok=True)

    save_synthetic_dataset(
        data=data,
        ground_truth=ground_truth,
        path=dataset_path,
        metadata={
            "signal_type": signal_config.signal_type,
            "anomaly_rate": anomaly_config.anomaly_rate,
            "length": len(data)
        }
    )

    return dataset_path


@pytest.fixture
def arima_config() -> ARIMAConfig:
    """Create ARIMA configuration for testing."""
    return ARIMAConfig(
        order=(1, 1, 1),
        seasonal_order=(0, 0, 0, 0),
        trend="c",
        suppress_warnings=True,
        maxiter=100
    )


@pytest.fixture
def ma_config() -> MovingAverageConfig:
    """Create Moving Average configuration for testing."""
    return MovingAverageConfig(
        window_size=10,
        z_threshold=3.0,
        min_samples=20
    )


class TestBaselineComparisonPipeline:
    """Integration tests for the baseline comparison pipeline."""

    def test_arima_baseline_creation(self, arima_config: ARIMAConfig):
        """Test that ARIMA baseline can be created with valid config."""
        baseline = create_arima_baseline(arima_config)

        assert baseline is not None
        assert isinstance(baseline, ARIMABaseline)
        assert baseline.config.order == (1, 1, 1)

    def test_moving_average_baseline_creation(self, ma_config: MovingAverageConfig):
        """Test that Moving Average baseline can be created with valid config."""
        baseline = create_ma_baseline(ma_config)

        assert baseline is not None
        assert isinstance(baseline, MovingAverageBaseline)
        assert baseline.config.window_size == 10

    def test_arima_prediction_on_synthetic_data(
        self,
        synthetic_dataset_path: Path,
        arima_config: ARIMAConfig
    ):
        """Test ARIMA baseline can make predictions on synthetic data."""
        # Load the dataset
        data_path = synthetic_dataset_path / "data.npy"
        ground_truth_path = synthetic_dataset_path / "ground_truth.npy"

        data = np.load(data_path)
        ground_truth = np.load(ground_truth_path)

        # Create and fit baseline
        baseline = create_arima_baseline(arima_config)
        baseline.fit(data)

        # Make predictions
        predictions = baseline.predict(data)

        assert predictions is not None
        assert len(predictions) == len(data)
        assert hasattr(predictions, 'scores') or hasattr(predictions, 'predictions')

    def test_moving_average_prediction_on_synthetic_data(
        self,
        synthetic_dataset_path: Path,
        ma_config: MovingAverageConfig
    ):
        """Test Moving Average baseline can make predictions on synthetic data."""
        # Load the dataset
        data_path = synthetic_dataset_path / "data.npy"
        ground_truth_path = synthetic_dataset_path / "ground_truth.npy"

        data = np.load(data_path)
        ground_truth = np.load(ground_truth_path)

        # Create and fit baseline
        baseline = create_ma_baseline(ma_config)
        baseline.fit(data)

        # Make predictions
        predictions = baseline.predict(data)

        assert predictions is not None
        assert len(predictions) == len(data)

    def test_f1_score_computation(self, synthetic_dataset_path: Path):
        """Test F1-score can be computed correctly."""
        # Load ground truth
        ground_truth_path = synthetic_dataset_path / "ground_truth.npy"
        ground_truth = np.load(ground_truth_path)

        # Create synthetic predictions
        np.random.seed(42)
        predictions = np.random.randint(0, 2, size=len(ground_truth))

        # Compute F1-score
        f1 = compute_f1_score(ground_truth, predictions)

        assert 0.0 <= f1 <= 1.0

    def test_precision_recall_computation(self, synthetic_dataset_path: Path):
        """Test precision and recall can be computed correctly."""
        # Load ground truth
        ground_truth_path = synthetic_dataset_path / "ground_truth.npy"
        ground_truth = np.load(ground_truth_path)

        # Create synthetic predictions
        np.random.seed(42)
        predictions = np.random.randint(0, 2, size=len(ground_truth))

        # Compute metrics
        precision = compute_precision(ground_truth, predictions)
        recall = compute_recall(ground_truth, predictions)

        assert 0.0 <= precision <= 1.0
        assert 0.0 <= recall <= 1.0

    def test_auc_computation(self, synthetic_dataset_path: Path):
        """Test AUC can be computed correctly."""
        # Load ground truth
        ground_truth_path = synthetic_dataset_path / "ground_truth.npy"
        ground_truth = np.load(ground_truth_path)

        # Create synthetic scores
        np.random.seed(42)
        scores = np.random.random(size=len(ground_truth))

        # Compute AUC
        auc = compute_auc(ground_truth, scores)

        assert 0.5 <= auc <= 1.0  # Random classifier should be ~0.5

    def test_confusion_matrix_generation(self, synthetic_dataset_path: Path):
        """Test confusion matrix can be generated."""
        # Load ground truth
        ground_truth_path = synthetic_dataset_path / "ground_truth.npy"
        ground_truth = np.load(ground_truth_path)

        # Create synthetic predictions
        np.random.seed(42)
        predictions = np.random.randint(0, 2, size=len(ground_truth))

        # Generate confusion matrix
        cm = generate_confusion_matrix(ground_truth, predictions)

        assert cm is not None
        assert cm.shape == (2, 2)

    def test_roc_curve_generation(self, synthetic_dataset_path: Path):
        """Test ROC curve can be generated."""
        # Load ground truth
        ground_truth_path = synthetic_dataset_path / "ground_truth.npy"
        ground_truth = np.load(ground_truth_path)

        # Create synthetic scores
        np.random.seed(42)
        scores = np.random.random(size=len(ground_truth))

        # Compute ROC curve points
        fpr, tpr, thresholds = compute_roc_curve_points(ground_truth, scores)

        assert len(fpr) == len(tpr)
        assert len(fpr) == len(thresholds)
        assert 0.0 <= fpr[0] <= 1.0
        assert 0.0 <= tpr[0] <= 1.0

    def test_pr_curve_generation(self, synthetic_dataset_path: Path):
        """Test PR curve can be generated."""
        # Load ground truth
        ground_truth_path = synthetic_dataset_path / "ground_truth.npy"
        ground_truth = np.load(ground_truth_path)

        # Create synthetic scores
        np.random.seed(42)
        scores = np.random.random(size=len(ground_truth))

        # Compute PR curve points
        precision, recall, thresholds = compute_pr_curve_points(ground_truth, scores)

        assert len(precision) == len(recall)
        assert len(precision) == len(thresholds)

    def test_evaluation_metrics_computation(self, synthetic_dataset_path: Path):
        """Test all evaluation metrics can be computed together."""
        # Load ground truth
        ground_truth_path = synthetic_dataset_path / "ground_truth.npy"
        ground_truth = np.load(ground_truth_path)

        # Create synthetic predictions and scores
        np.random.seed(42)
        predictions = np.random.randint(0, 2, size=len(ground_truth))
        scores = np.random.random(size=len(ground_truth))

        # Compute all metrics
        metrics = compute_all_metrics(ground_truth, predictions, scores)

        assert metrics is not None
        assert hasattr(metrics, 'f1_score') or 'f1_score' in str(dir(metrics))
        assert hasattr(metrics, 'precision') or 'precision' in str(dir(metrics))
        assert hasattr(metrics, 'recall') or 'recall' in str(dir(metrics))
        assert hasattr(metrics, 'auc') or 'auc' in str(dir(metrics))

    def test_end_to_end_baseline_comparison(
        self,
        synthetic_dataset_path: Path,
        arima_config: ARIMAConfig,
        ma_config: MovingAverageConfig,
        tmp_path: Path
    ):
        """
        Full end-to-end test: run both baselines, compute metrics,
        generate plots, and save results.
        """
        # Load dataset
        data_path = synthetic_dataset_path / "data.npy"
        ground_truth_path = synthetic_dataset_path / "ground_truth.npy"

        data = np.load(data_path)
        ground_truth = np.load(ground_truth_path)

        # Results storage
        results: Dict[str, Dict[str, Any]] = {}

        # Run ARIMA baseline
        arima_baseline = create_arima_baseline(arima_config)
        arima_baseline.fit(data)
        arima_predictions = arima_baseline.predict(data)

        # Extract scores and binary predictions
        if hasattr(arima_predictions, 'scores'):
            arima_scores = arima_predictions.scores
        else:
            arima_scores = np.abs(np.asarray(arima_predictions))

        arima_binary = (arima_scores > np.percentile(arima_scores, 95)).astype(int)

        # Compute ARIMA metrics
        arima_metrics = compute_all_metrics(ground_truth, arima_binary, arima_scores)
        results['arima'] = {
            'metrics': arima_metrics,
            'predictions': arima_binary.tolist(),
            'scores': arima_scores.tolist()
        }

        # Run Moving Average baseline
        ma_baseline = create_ma_baseline(ma_config)
        ma_baseline.fit(data)
        ma_predictions = ma_baseline.predict(data)

        # Extract scores and binary predictions
        if hasattr(ma_predictions, 'scores'):
            ma_scores = ma_predictions.scores
        else:
            ma_scores = np.abs(np.asarray(ma_predictions))

        ma_binary = (ma_scores > np.percentile(ma_scores, 95)).astype(int)

        # Compute MA metrics
        ma_metrics = compute_all_metrics(ground_truth, ma_binary, ma_scores)
        results['moving_average'] = {
            'metrics': ma_metrics,
            'predictions': ma_binary.tolist(),
            'scores': ma_scores.tolist()
        }

        # Generate ROC curves
        plot_config = EvaluationPlotConfig(
            save_path=tmp_path / "plots",
            dpi=300,
            figsize=(10, 8)
        )

        plot_config.save_path.mkdir(parents=True, exist_ok=True)

        # ROC for ARIMA
        arima_fpr, arima_tpr, arima_thresholds = compute_roc_curve_points(
            ground_truth, arima_scores
        )
        save_roc_curve(
            fpr=arima_fpr,
            tpr=arima_tpr,
            thresholds=arima_thresholds,
            model_name="ARIMA",
            config=plot_config
        )

        # ROC for Moving Average
        ma_fpr, ma_tpr, ma_thresholds = compute_roc_curve_points(
            ground_truth, ma_scores
        )
        save_roc_curve(
            fpr=ma_fpr,
            tpr=ma_tpr,
            thresholds=ma_thresholds,
            model_name="MovingAverage",
            config=plot_config
        )

        # Generate PR curves
        arima_prec, arima_rec, arima_pr_thresh = compute_pr_curve_points(
            ground_truth, arima_scores
        )
        save_pr_curve(
            precision=arima_prec,
            recall=arima_rec,
            thresholds=arima_pr_thresh,
            model_name="ARIMA",
            config=plot_config
        )

        ma_prec, ma_rec, ma_pr_thresh = compute_pr_curve_points(
            ground_truth, ma_scores
        )
        save_pr_curve(
            precision=ma_prec,
            recall=ma_rec,
            thresholds=ma_pr_thresh,
            model_name="MovingAverage",
            config=plot_config
        )

        # Save results to JSON
        results_path = tmp_path / "baseline_comparison_results.json"

        # Convert metrics to serializable format
        serializable_results = {}
        for model_name, model_results in results.items():
            serializable_results[model_name] = {
                'metrics': {
                    k: float(v) if isinstance(v, (np.floating, np.integer)) else v
                    for k, v in model_results['metrics'].__dict__.items()
                } if hasattr(model_results['metrics'], '__dict__') else model_results['metrics'],
                'predictions': model_results['predictions'],
                'scores': model_results['scores']
            }

        with open(results_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)

        # Verify all artifacts were created
        assert results_path.exists()
        assert (plot_config.save_path / "roc_ARIMA.png").exists()
        assert (plot_config.save_path / "roc_MovingAverage.png").exists()
        assert (plot_config.save_path / "pr_ARIMA.png").exists()
        assert (plot_config.save_path / "pr_MovingAverage.png").exists()

        # Verify metrics are reasonable
        assert results['arima']['metrics'].f1_score >= 0.0
        assert results['moving_average']['metrics'].f1_score >= 0.0

    def test_baseline_comparison_with_labeled_data(self, synthetic_dataset_path: Path):
        """Test baseline comparison when labeled data is available."""
        # Load dataset
        data_path = synthetic_dataset_path / "data.npy"
        ground_truth_path = synthetic_dataset_path / "ground_truth.npy"

        data = np.load(data_path)
        ground_truth = np.load(ground_truth_path)

        # Count actual anomalies
        actual_anomalies = int(np.sum(ground_truth))
        total_points = len(ground_truth)

        assert actual_anomalies > 0, "Dataset should have some anomalies for testing"
        assert actual_anomalies < total_points, "Dataset should not be all anomalies"

        # Run ARIMA baseline
        arima_config = ARIMAConfig(order=(1, 1, 1))
        arima_baseline = create_arima_baseline(arima_config)
        arima_baseline.fit(data)
        arima_predictions = arima_baseline.predict(data)

        # Get scores and compute metrics
        arima_scores = np.abs(np.asarray(arima_predictions))
        arima_binary = (arima_scores > np.percentile(arima_scores, 95)).astype(int)

        arima_metrics = compute_all_metrics(ground_truth, arima_binary, arima_scores)

        # Verify we can compute meaningful metrics
        assert arima_metrics.f1_score is not None
        assert arima_metrics.precision is not None
        assert arima_metrics.recall is not None

        # Compare with Moving Average
        ma_config = MovingAverageConfig(window_size=10, z_threshold=3.0)
        ma_baseline = create_ma_baseline(ma_config)
        ma_baseline.fit(data)
        ma_predictions = ma_baseline.predict(data)

        ma_scores = np.abs(np.asarray(ma_predictions))
        ma_binary = (ma_scores > np.percentile(ma_scores, 95)).astype(int)

        ma_metrics = compute_all_metrics(ground_truth, ma_binary, ma_scores)

        # Both baselines should produce valid metrics
        assert ma_metrics.f1_score is not None
        assert ma_metrics.precision is not None
        assert ma_metrics.recall is not None

        # Store comparison results
        comparison = {
            'arima_f1': float(arima_metrics.f1_score),
            'arima_precision': float(arima_metrics.precision),
            'arima_recall': float(arima_metrics.recall),
            'ma_f1': float(ma_metrics.f1_score),
            'ma_precision': float(ma_metrics.precision),
            'ma_recall': float(ma_metrics.recall),
            'actual_anomalies': int(actual_anomalies),
            'total_points': int(total_points)
        }

        # Verify comparison structure
        assert 'arima_f1' in comparison
        assert 'ma_f1' in comparison
        assert comparison['arima_f1'] >= 0.0
        assert comparison['ma_f1'] >= 0.0


class TestBaselineComparisonEdgeCases:
    """Edge case tests for baseline comparison."""

    def test_empty_dataset_handling(self):
        """Test that empty dataset is handled gracefully."""
        arima_config = ARIMAConfig(order=(1, 1, 1))
        arima_baseline = create_arima_baseline(arima_config)

        empty_data = np.array([])

        # Should not crash on empty data
        with pytest.raises((ValueError, IndexError)):
            arima_baseline.fit(empty_data)

    def test_single_point_dataset(self):
        """Test handling of single-point dataset."""
        ma_config = MovingAverageConfig(window_size=10, z_threshold=3.0)
        ma_baseline = create_ma_baseline(ma_config)

        single_point = np.array([1.0])

        # Should handle gracefully (may raise error for insufficient data)
        with pytest.raises((ValueError, IndexError)):
            ma_baseline.fit(single_point)

    def test_all_anomalies_dataset(self, tmp_path: Path):
        """Test handling of dataset with all anomalies."""
        # Create all-anomaly ground truth
        ground_truth = np.ones(100, dtype=int)
        data = np.random.random(100)

        # Save to temp
        data_path = tmp_path / "all_anomalies_data.npy"
        gt_path = tmp_path / "all_anomalies_gt.npy"

        np.save(data_path, data)
        np.save(gt_path, ground_truth)

        # Compute metrics
        scores = np.random.random(100)
        predictions = np.ones(100, dtype=int)

        metrics = compute_all_metrics(ground_truth, predictions, scores)

        # Should handle edge case
        assert metrics is not None

    def test_no_anomalies_dataset(self, tmp_path: Path):
        """Test handling of dataset with no anomalies."""
        # Create no-anomaly ground truth
        ground_truth = np.zeros(100, dtype=int)
        data = np.random.random(100)

        # Save to temp
        data_path = tmp_path / "no_anomalies_data.npy"
        gt_path = tmp_path / "no_anomalies_gt.npy"

        np.save(data_path, data)
        np.save(gt_path, ground_truth)

        # Compute metrics
        scores = np.random.random(100)
        predictions = np.zeros(100, dtype=int)

        metrics = compute_all_metrics(ground_truth, predictions, scores)

        # Should handle edge case
        assert metrics is not None
        assert metrics.precision == 1.0  # No false positives


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
