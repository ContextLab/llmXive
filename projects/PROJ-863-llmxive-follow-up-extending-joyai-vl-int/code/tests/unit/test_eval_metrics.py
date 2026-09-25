import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

from src.scheduler.eval import (
    calculate_auc_roc,
    calculate_cohen_kappa,
    calculate_interruption_reduction_rate,
    calculate_safety_recall,
    calculate_inference_latency,
    align_predictions_with_ground_truth,
    evaluate_scheduler,
    EvaluationMetrics
)

class TestAUCROC:
    def test_perfect_classifier(self):
        y_true = [0, 0, 0, 1, 1, 1]
        y_scores = [0.1, 0.2, 0.3, 0.7, 0.8, 0.9]
        auc = calculate_auc_roc(y_true, y_scores)
        assert auc == 1.0

    def test_random_classifier(self):
        y_true = [0, 0, 0, 1, 1, 1]
        y_scores = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        auc = calculate_auc_roc(y_true, y_scores)
        assert 0.4 <= auc <= 0.6  # Allow small variance

    def test_single_class(self):
        y_true = [1, 1, 1, 1]
        y_scores = [0.1, 0.5, 0.8, 0.9]
        auc = calculate_auc_roc(y_true, y_scores)
        assert auc == 0.5

    def test_mismatched_lengths(self):
        y_true = [0, 1, 1]
        y_scores = [0.1, 0.9]
        with pytest.raises(ValueError):
            calculate_auc_roc(y_true, y_scores)

class TestCohenKappa:
    def test_perfect_agreement(self):
        y_true = [0, 1, 0, 1, 1]
        y_pred = [0, 1, 0, 1, 1]
        kappa = calculate_cohen_kappa(y_true, y_pred)
        assert kappa == 1.0

    def test_no_agreement(self):
        y_true = [0, 0, 0, 1, 1]
        y_pred = [1, 1, 1, 0, 0]
        kappa = calculate_cohen_kappa(y_true, y_pred)
        assert kappa < 0

    def test_empty_lists(self):
        kappa = calculate_cohen_kappa([], [])
        assert kappa == 0.0

    def test_mismatched_lengths(self):
        y_true = [0, 1, 1]
        y_pred = [0, 1]
        with pytest.raises(ValueError):
            calculate_cohen_kappa(y_true, y_pred)

class TestInterruptionReductionRate:
    def test_reduction(self):
        # Baseline: 100 interruptions, Scheduler: 60 interruptions
        irr = calculate_interruption_reduction_rate(100, 60, 1000)
        assert irr == 0.4

    def test_increase(self):
        # Baseline: 100 interruptions, Scheduler: 120 interruptions
        irr = calculate_interruption_reduction_rate(100, 120, 1000)
        assert irr == -0.2

    def test_no_baseline_interruptions(self):
        irr = calculate_interruption_reduction_rate(0, 10, 1000)
        assert irr == 0.0

    def test_zero_interruptions(self):
        irr = calculate_interruption_reduction_rate(100, 0, 1000)
        assert irr == 1.0

class TestSafetyRecall:
    def test_perfect_recall(self):
        y_true = [1, 1, 1, 1]
        y_pred = [1, 1, 1, 1]
        recall = calculate_safety_recall(y_true, y_pred)
        assert recall == 1.0

    def test_zero_recall(self):
        y_true = [1, 1, 1, 1]
        y_pred = [0, 0, 0, 0]
        recall = calculate_safety_recall(y_true, y_pred)
        assert recall == 0.0

    def test_partial_recall(self):
        y_true = [1, 1, 1, 1]
        y_pred = [1, 0, 1, 0]
        recall = calculate_safety_recall(y_true, y_pred)
        assert recall == 0.5

    def test_no_positive_samples(self):
        y_true = [0, 0, 0, 0]
        y_pred = [1, 1, 0, 0]
        recall = calculate_safety_recall(y_true, y_pred)
        assert recall == 0.0

class TestInferenceLatency:
    def test_mean_calculation(self):
        latencies = [10.0, 20.0, 30.0]
        mean = calculate_inference_latency(latencies)
        assert mean == 20.0

    def test_empty_list(self):
        mean = calculate_inference_latency([])
        assert mean == 0.0

    def test_single_value(self):
        mean = calculate_inference_latency([15.5])
        assert mean == 15.5

class TestAlignment:
    def test_basic_alignment(self):
        predictions = [
            {'frame_id': 1, 'prediction': 1, 'probability': 0.9},
            {'frame_id': 2, 'prediction': 0, 'probability': 0.2},
            {'frame_id': 3, 'prediction': 1, 'probability': 0.8}
        ]
        ground_truth = [
            {'frame_id': 1, 'label': 1},
            {'frame_id': 2, 'label': 0},
            {'frame_id': 3, 'label': 1}
        ]
        
        y_true, y_pred, baseline, scores = align_predictions_with_ground_truth(
            predictions, ground_truth
        )
        
        assert y_true == [1, 0, 1]
        assert y_pred == [1, 0, 1]
        assert scores == [0.9, 0.2, 0.8]

    def test_missing_keys(self):
        predictions = [
            {'frame_id': 1, 'prediction': 1},
            {'frame_id': 2, 'prediction': 0}
        ]
        ground_truth = [
            {'frame_id': 2, 'label': 0},
            {'frame_id': 3, 'label': 1}
        ]
        
        y_true, y_pred, baseline, scores = align_predictions_with_ground_truth(
            predictions, ground_truth
        )
        
        # Only frame_id 2 is common
        assert len(y_true) == 1
        assert y_true[0] == 0
        assert y_pred[0] == 0

    def test_no_common_keys(self):
        predictions = [{'frame_id': 1, 'prediction': 1}]
        ground_truth = [{'frame_id': 2, 'label': 1}]
        
        with pytest.raises(ValueError):
            align_predictions_with_ground_truth(predictions, ground_truth)

class TestEvaluateScheduler:
    @pytest.fixture
    def temp_eval_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create data directory structure
            data_dir = tmpdir / 'data'
            data_dir.mkdir()
            
            scheduler_dir = data_dir / 'scheduler'
            scheduler_dir.mkdir()
            
            raw_dir = data_dir / 'raw'
            raw_dir.mkdir()
            
            baseline_dir = data_dir / 'baseline'
            baseline_dir.mkdir()
            
            evaluation_dir = data_dir / 'evaluation'
            evaluation_dir.mkdir()
            
            yield tmpdir

    def test_full_evaluation(self, temp_eval_dirs):
        tmpdir = temp_eval_dirs
        
        # Create ground truth file
        gt_path = tmpdir / 'data' / 'raw' / 'manifest.jsonl'
        with open(gt_path, 'w') as f:
            f.write(json.dumps({'frame_id': 1, 'label': 1}) + '\n')
            f.write(json.dumps({'frame_id': 2, 'label': 0}) + '\n')
            f.write(json.dumps({'frame_id': 3, 'label': 1}) + '\n')
            f.write(json.dumps({'frame_id': 4, 'label': 1}) + '\n')
            f.write(json.dumps({'frame_id': 5, 'label': 0}) + '\n')
        
        # Create predictions file
        pred_path = tmpdir / 'data' / 'scheduler' / 'predictions.jsonl'
        with open(pred_path, 'w') as f:
            f.write(json.dumps({'frame_id': 1, 'prediction': 1, 'probability': 0.9, 'inference_latency_ms': 15.0}) + '\n')
            f.write(json.dumps({'frame_id': 2, 'prediction': 0, 'probability': 0.1, 'inference_latency_ms': 12.0}) + '\n')
            f.write(json.dumps({'frame_id': 3, 'prediction': 1, 'probability': 0.85, 'inference_latency_ms': 14.0}) + '\n')
            f.write(json.dumps({'frame_id': 4, 'prediction': 0, 'probability': 0.4, 'inference_latency_ms': 13.0}) + '\n')
            f.write(json.dumps({'frame_id': 5, 'prediction': 0, 'probability': 0.2, 'inference_latency_ms': 11.0}) + '\n')
        
        # Create baseline predictions
        baseline_path = tmpdir / 'data' / 'baseline' / 'noisy_predictions.jsonl'
        with open(baseline_path, 'w') as f:
            f.write(json.dumps({'frame_id': 1, 'prediction': 1}) + '\n')
            f.write(json.dumps({'frame_id': 2, 'prediction': 1}) + '\n')
            f.write(json.dumps({'frame_id': 3, 'prediction': 1}) + '\n')
            f.write(json.dumps({'frame_id': 4, 'prediction': 1}) + '\n')
            f.write(json.dumps({'frame_id': 5, 'prediction': 0}) + '\n')
        
        # Run evaluation
        metrics = evaluate_scheduler(
            predictions_path=pred_path,
            ground_truth_path=gt_path,
            baseline_predictions_path=baseline_path
        )
        
        # Verify metrics are calculated
        assert metrics.total_samples == 5
        assert metrics.auc_roc >= 0.0
        assert metrics.auc_roc <= 1.0
        assert metrics.cohen_kappa >= -1.0
        assert metrics.cohen_kappa <= 1.0
        assert metrics.safety_recall >= 0.0
        assert metrics.safety_recall <= 1.0
        assert metrics.mean_inference_latency_ms > 0

    def test_missing_predictions_file(self, temp_eval_dirs):
        tmpdir = temp_eval_dirs
        pred_path = tmpdir / 'data' / 'scheduler' / 'nonexistent.jsonl'
        gt_path = tmpdir / 'data' / 'raw' / 'manifest.jsonl'
        
        # Create ground truth
        gt_path.parent.mkdir(parents=True, exist_ok=True)
        with open(gt_path, 'w') as f:
            f.write(json.dumps({'frame_id': 1, 'label': 1}) + '\n')
        
        with pytest.raises(FileNotFoundError):
            evaluate_scheduler(
                predictions_path=pred_path,
                ground_truth_path=gt_path
            )

    def test_separate_metrics_calculation(self, temp_eval_dirs):
        """Test that Interruption Reduction Rate and Safety Recall are calculated separately."""
        tmpdir = temp_eval_dirs
        
        # Create ground truth
        gt_path = tmpdir / 'data' / 'raw' / 'manifest.jsonl'
        with open(gt_path, 'w') as f:
            for i in range(1, 11):
                label = 1 if i <= 5 else 0
                f.write(json.dumps({'frame_id': i, 'label': label}) + '\n')
        
        # Create predictions
        pred_path = tmpdir / 'data' / 'scheduler' / 'predictions.jsonl'
        with open(pred_path, 'w') as f:
            for i in range(1, 11):
                pred = 1 if i <= 3 else 0
                prob = 0.9 if pred == 1 else 0.2
                f.write(json.dumps({
                    'frame_id': i,
                    'prediction': pred,
                    'probability': prob,
                    'inference_latency_ms': 10.0
                }) + '\n')
        
        # Create baseline (more aggressive)
        baseline_path = tmpdir / 'data' / 'baseline' / 'noisy_predictions.jsonl'
        with open(baseline_path, 'w') as f:
            for i in range(1, 11):
                pred = 1 if i <= 7 else 0
                f.write(json.dumps({'frame_id': i, 'prediction': pred}) + '\n')
        
        metrics = evaluate_scheduler(
            predictions_path=pred_path,
            ground_truth_path=gt_path,
            baseline_predictions_path=baseline_path
        )
        
        # Verify both metrics are present and non-trivial
        assert hasattr(metrics, 'interruption_reduction_rate')
        assert hasattr(metrics, 'safety_recall')
        assert metrics.interruption_reduction_rate >= -1.0
        assert metrics.interruption_reduction_rate <= 1.0
        assert metrics.safety_recall >= 0.0
        assert metrics.safety_recall <= 1.0