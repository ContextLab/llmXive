"""
Unit tests for T029 evaluation module.

Tests the evaluation logic for inconsistency detection on synthetic datasets.
"""
import json
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from code.src.audit.evaluation import (
    load_synthetic_summaries,
    load_ground_truth,
    load_audit_records,
    evaluate_detection,
    validate_summary,
    write_evaluation_results,
    PRECISION_THRESHOLD,
    RECALL_THRESHOLD
)


class TestLoadSyntheticSummaries:
    def test_load_csv_success(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("url,is_inconsistent\nhttp://example.com,true\nhttp://test.com,false\n")
        
        result = load_synthetic_summaries(csv_file)
        
        assert len(result) == 2
        assert result[0]["url"] == "http://example.com"
        assert result[0]["is_inconsistent"] == "true"
    
    def test_file_not_found(self, tmp_path):
        non_existent = tmp_path / "non_existent.csv"
        
        with pytest.raises(FileNotFoundError):
            load_synthetic_summaries(non_existent)


class TestLoadGroundTruth:
    def test_load_json_success(self, tmp_path):
        json_file = tmp_path / "ground_truth.json"
        data = {"summaries": [{"url": "http://a.com", "is_inconsistent": True}]}
        json_file.write_text(json.dumps(data))
        
        result = load_ground_truth(json_file)
        
        assert len(result["summaries"]) == 1
    
    def test_file_not_found(self, tmp_path):
        non_existent = tmp_path / "non_existent.json"
        
        with pytest.raises(FileNotFoundError):
            load_ground_truth(non_existent)


class TestLoadAuditRecords:
    def test_load_list_format(self, tmp_path):
        json_file = tmp_path / "audit.json"
        records = [{"url": "http://a.com", "is_inconsistent": True}]
        json_file.write_text(json.dumps(records))
        
        result = load_audit_records(json_file)
        
        assert len(result) == 1
    
    def test_load_dict_format(self, tmp_path):
        json_file = tmp_path / "audit.json"
        data = {"records": [{"url": "http://a.com", "is_inconsistent": True}]}
        json_file.write_text(json.dumps(data))
        
        result = load_audit_records(json_file)
        
        assert len(result) == 1
    
    def test_file_not_found(self, tmp_path):
        non_existent = tmp_path / "non_existent.json"
        
        with pytest.raises(FileNotFoundError):
            load_audit_records(non_existent)


class TestEvaluateDetection:
    def test_perfect_detection(self):
        ground_truth = {
            "summaries": [
                {"url": "http://a.com", "is_inconsistent": True},
                {"url": "http://b.com", "is_inconsistent": False}
            ]
        }
        audit_records = [
            {"url": "http://a.com", "is_inconsistent": True},
            {"url": "http://b.com", "is_inconsistent": False}
        ]
        
        tp, fp, fn, tn = evaluate_detection(ground_truth, audit_records)
        
        assert tp == 1
        assert fp == 0
        assert fn == 0
        assert tn == 1
    
    def test_mixed_detection(self):
        ground_truth = {
            "summaries": [
                {"url": "http://a.com", "is_inconsistent": True},
                {"url": "http://b.com", "is_inconsistent": True},
                {"url": "http://c.com", "is_inconsistent": False}
            ]
        }
        audit_records = [
            {"url": "http://a.com", "is_inconsistent": True},  # TP
            {"url": "http://b.com", "is_inconsistent": False}, # FN
            {"url": "http://c.com", "is_inconsistent": True}   # FP
        ]
        
        tp, fp, fn, tn = evaluate_detection(ground_truth, audit_records)
        
        assert tp == 1
        assert fp == 1
        assert fn == 1
        assert tn == 0
    
    def test_no_common_keys(self):
        ground_truth = {
            "summaries": [{"url": "http://a.com", "is_inconsistent": True}]
        }
        audit_records = [
            {"url": "http://b.com", "is_inconsistent": True}
        ]
        
        tp, fp, fn, tn = evaluate_detection(ground_truth, audit_records)
        
        assert tp == 0
        assert fp == 0
        assert fn == 0
        assert tn == 0


class TestValidateSummary:
    def test_perfect_scores(self):
        precision, recall, f1, met = validate_summary(10, 0, 0, 90)
        
        assert precision == 1.0
        assert recall == 1.0
        assert f1 == 1.0
        assert met is True
    
    def test_below_precision_threshold(self):
        # Precision = 10/(10+10) = 0.5, Recall = 10/(10+0) = 1.0
        precision, recall, f1, met = validate_summary(10, 10, 0, 80)
        
        assert precision == 0.5
        assert recall == 1.0
        assert f1 == 0.6666666666666666
        assert met is False
    
    def test_below_recall_threshold(self):
        # Precision = 10/(10+0) = 1.0, Recall = 10/(10+10) = 0.5
        precision, recall, f1, met = validate_summary(10, 0, 10, 80)
        
        assert precision == 1.0
        assert recall == 0.5
        assert f1 == 0.6666666666666666
        assert met is False
    
    def test_division_by_zero(self):
        precision, recall, f1, met = validate_summary(0, 0, 0, 0)
        
        assert precision == 0.0
        assert recall == 0.0
        assert f1 == 0.0
        assert met is False


class TestWriteEvaluationResults:
    def test_write_success(self, tmp_path):
        output_file = tmp_path / "results.json"
        metrics = {
            "precision": 0.95,
            "recall": 0.85,
            "f1_score": 0.90
        }
        
        write_evaluation_results(output_file, metrics, True)
        
        assert output_file.exists()
        
        with open(output_file) as f:
            data = json.load(f)
        
        assert "timestamp" in data
        assert data["metrics"]["precision"] == 0.95
        assert data["thresholds_met"] is True