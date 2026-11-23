import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
from src.ingestion.merge_spectra import validate_class_balance, CLASS_LABELS, MIN_SAMPLE_THRESHOLD

class TestClassBalanceValidation:
    """Tests for class balance validation logic in merge_spectra.py"""

    def test_balanced_classes(self, tmp_path):
        """Test with a perfectly balanced dataset"""
        # Create balanced data
        n_samples_per_class = 100
        labels = []
        for cls in CLASS_LABELS:
            labels.extend([cls] * n_samples_per_class)
        
        df = pd.DataFrame({
            'sample_id': [f'sample_{i}' for i in range(len(labels))],
            'fingerprint': [np.random.rand(512) for _ in range(len(labels))],
            'label': labels
        })
        
        output_path = tmp_path / "class_balance_report.json"
        report = validate_class_balance(df, str(output_path))
        
        assert report['total_samples'] == 300
        assert report['class_counts']['SN1'] == 100
        assert report['class_counts']['SN2'] == 100
        assert report['class_counts']['E1'] == 100
        assert report['max_min_ratio'] == 1.0
        assert report['under_sampled_classes'] == []
        assert report['is_balanced'] == True
        assert os.path.exists(output_path)

    def test_imbalanced_classes(self, tmp_path):
        """Test with an imbalanced dataset"""
        labels = ['SN1'] * 200 + ['SN2'] * 50 + ['E1'] * 10
        df = pd.DataFrame({
            'sample_id': [f'sample_{i}' for i in range(len(labels))],
            'fingerprint': [np.random.rand(512) for _ in range(len(labels))],
            'label': labels
        })
        
        output_path = tmp_path / "class_balance_report.json"
        report = validate_class_balance(df, str(output_path))
        
        assert report['total_samples'] == 260
        assert report['class_counts']['SN1'] == 200
        assert report['class_counts']['SN2'] == 50
        assert report['class_counts']['E1'] == 10
        assert report['max_min_ratio'] == 20.0  # 200/10
        assert 'E1' in report['under_sampled_classes']
        assert report['is_balanced'] == False

    def test_missing_class(self, tmp_path):
        """Test when one class is completely missing"""
        labels = ['SN1'] * 100 + ['SN2'] * 100
        df = pd.DataFrame({
            'sample_id': [f'sample_{i}' for i in range(len(labels))],
            'fingerprint': [np.random.rand(512) for _ in range(len(labels))],
            'label': labels
        })
        
        output_path = tmp_path / "class_balance_report.json"
        report = validate_class_balance(df, str(output_path))
        
        assert report['total_samples'] == 200
        assert report['class_counts']['SN1'] == 100
        assert report['class_counts']['SN2'] == 100
        assert report['class_counts']['E1'] == 0
        assert report['max_min_ratio'] == float('inf')
        assert 'E1' in report['under_sampled_classes']
        assert report['is_balanced'] == False

    def test_under_sampled_threshold(self, tmp_path):
        """Test that classes with <50 samples are flagged"""
        labels = ['SN1'] * 60 + ['SN2'] * 40 + ['E1'] * 30
        df = pd.DataFrame({
            'sample_id': [f'sample_{i}' for i in range(len(labels))],
            'fingerprint': [np.random.rand(512) for _ in range(len(labels))],
            'label': labels
        })
        
        output_path = tmp_path / "class_balance_report.json"
        report = validate_class_balance(df, str(output_path))
        
        assert report['class_counts']['SN2'] == 40
        assert report['class_counts']['E1'] == 30
        assert 'SN2' in report['under_sampled_classes']
        assert 'E1' in report['under_sampled_classes']
        assert 'SN1' not in report['under_sampled_classes']

    def test_missing_label_column(self, tmp_path):
        """Test error handling when label column is missing"""
        df = pd.DataFrame({
            'sample_id': [f'sample_{i}' for i in range(10)],
            'fingerprint': [np.random.rand(512) for _ in range(10)]
        })
        
        output_path = tmp_path / "class_balance_report.json"
        report = validate_class_balance(df, str(output_path))
        
        assert 'error' in report
        assert report['error'] == 'missing_label_column'
        assert not os.path.exists(output_path)

    def test_report_file_created(self, tmp_path):
        """Test that the report file is actually created on disk"""
        labels = ['SN1'] * 50 + ['SN2'] * 50 + ['E1'] * 50
        df = pd.DataFrame({
            'sample_id': [f'sample_{i}' for i in range(len(labels))],
            'fingerprint': [np.random.rand(512) for _ in range(len(labels))],
            'label': labels
        })
        
        output_path = tmp_path / "class_balance_report.json"
        validate_class_balance(df, str(output_path))
        
        assert os.path.exists(output_path)
        
        # Verify file content
        import json
        with open(output_path, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report['total_samples'] == 150
        assert saved_report['class_counts']['SN1'] == 50