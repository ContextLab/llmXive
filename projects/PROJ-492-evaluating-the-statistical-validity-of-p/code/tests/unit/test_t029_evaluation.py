"""
Unit tests for T029 evaluation module.

Tests the evaluation logic without requiring full pipeline execution.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from code.src.audit.evaluation import (
    load_synthetic_summaries,
    load_ground_truth,
    load_audit_records,
    evaluate_detection,
    validate_summary,
    write_evaluation_results
)


class TestEvaluateDetection:
    """Tests for the evaluate_detection function."""

    def test_perfect_detection(self):
        """Test case where detection is perfect."""
        ground_truth = {
            'id1': True,   # inconsistent
            'id2': True,   # inconsistent
            'id3': False,  # consistent
            'id4': False   # consistent
        }
        
        audit_records = {
            'id1': {'summary_id': 'id1', 'is_inconsistent': True},
            'id2': {'summary_id': 'id2', 'is_inconsistent': True},
            'id3': {'summary_id': 'id3', 'is_inconsistent': False},
            'id4': {'summary_id': 'id4', 'is_inconsistent': False}
        }
        
        precision, recall, f1, counts = evaluate_detection(audit_records, ground_truth)
        
        assert precision == 1.0
        assert recall == 1.0
        assert f1 == 1.0
        assert counts == {'tp': 2, 'fp': 0, 'tn': 2, 'fn': 0}

    def test_no_false_positives(self):
        """Test case with no false positives but some false negatives."""
        ground_truth = {
            'id1': True,   # inconsistent - missed
            'id2': True,   # inconsistent - caught
            'id3': False,  # consistent
        }
        
        audit_records = {
            'id2': {'summary_id': 'id2', 'is_inconsistent': True},
            'id3': {'summary_id': 'id3', 'is_inconsistent': False}
        }
        
        precision, recall, f1, counts = evaluate_detection(audit_records, ground_truth)
        
        # TP=1, FP=0, FN=1, TN=1
        assert precision == 1.0  # 1/(1+0)
        assert recall == 0.5     # 1/(1+1)
        assert f1 == pytest.approx(2/3, rel=1e-3)
        assert counts == {'tp': 1, 'fp': 0, 'tn': 1, 'fn': 1}

    def test_no_true_positives(self):
        """Test case where nothing is detected."""
        ground_truth = {
            'id1': True,
            'id2': False
        }
        
        audit_records = {
            'id1': {'summary_id': 'id1', 'is_inconsistent': False},
            'id2': {'summary_id': 'id2', 'is_inconsistent': False}
        }
        
        precision, recall, f1, counts = evaluate_detection(audit_records, ground_truth)
        
        assert precision == 0.0
        assert recall == 0.0
        assert f1 == 0.0
        assert counts == {'tp': 0, 'fp': 0, 'tn': 1, 'fn': 1}

    def test_missing_audit_record_treated_as_consistent(self):
        """Test that missing audit records are treated as not flagged."""
        ground_truth = {
            'id1': True,   # inconsistent but missing from audit
            'id2': False
        }
        
        audit_records = {
            'id2': {'summary_id': 'id2', 'is_inconsistent': False}
        }
        
        precision, recall, f1, counts = evaluate_detection(audit_records, ground_truth)
        
        # id1 is missing -> treated as not flagged -> FN
        assert counts['fn'] == 1
        assert recall == 0.0


class TestValidateSummary:
    """Tests for the validate_summary function."""

    def test_passes_thresholds(self):
        """Test that metrics above thresholds pass."""
        passed, message = validate_summary(0.95, 0.85, 0.90)
        assert passed is True
        assert 'meet criteria' in message.lower()

    def test_fails_precision_threshold(self):
        """Test that low precision fails."""
        passed, message = validate_summary(0.85, 0.90, 0.87)
        assert passed is False
        assert 'precision' in message.lower()

    def test_fails_recall_threshold(self):
        """Test that low recall fails."""
        passed, message = validate_summary(0.95, 0.75, 0.84)
        assert passed is False
        assert 'recall' in message.lower()

    def test_fails_both_thresholds(self):
        """Test that both low metrics are reported."""
        passed, message = validate_summary(0.80, 0.70, 0.75)
        assert passed is False
        assert 'precision' in message.lower()
        assert 'recall' in message.lower()


class TestLoadFunctions:
    """Tests for data loading functions."""

    def test_load_ground_truth_with_both_keys(self, tmp_path):
        """Test loading ground truth with both inconsistent and consistent IDs."""
        gt_data = {
            'inconsistent_ids': ['id1', 'id2'],
            'consistent_ids': ['id3', 'id4']
        }
        gt_file = tmp_path / 'ground_truth.json'
        gt_file.write_text(json.dumps(gt_data))
        
        gt = load_ground_truth(gt_file)
        
        assert gt['id1'] is True
        assert gt['id2'] is True
        assert gt['id3'] is False
        assert gt['id4'] is False

    def test_load_ground_truth_missing_keys(self, tmp_path):
        """Test that missing keys raise ValueError."""
        gt_data = {'only_one_key': ['id1']}
        gt_file = tmp_path / 'ground_truth.json'
        gt_file.write_text(json.dumps(gt_data))
        
        with pytest.raises(ValueError):
            load_ground_truth(gt_file)

    def test_load_audit_records_as_list(self, tmp_path):
        """Test loading audit records from a list format."""
        records = [
            {'summary_id': 'id1', 'is_inconsistent': True},
            {'summary_id': 'id2', 'is_inconsistent': False}
        ]
        report_file = tmp_path / 'report.json'
        report_file.write_text(json.dumps(records))
        
        result = load_audit_records(report_file)
        
        assert 'id1' in result
        assert result['id1']['is_inconsistent'] is True
        assert result['id2']['is_inconsistent'] is False

    def test_load_audit_records_as_dict(self, tmp_path):
        """Test loading audit records from dict with 'records' key."""
        data = {
            'records': [
                {'summary_id': 'id1', 'is_inconsistent': True}
            ]
        }
        report_file = tmp_path / 'report.json'
        report_file.write_text(json.dumps(data))
        
        result = load_audit_records(report_file)
        
        assert 'id1' in result
        assert result['id1']['is_inconsistent'] is True