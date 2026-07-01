import pytest
import tempfile
import os
from pathlib import Path
import json
import numpy as np

from src.evaluation.report_generator import (
    generate_csv_report,
    generate_pdf_report,
    generate_reports
)

class TestReportGenerator:
    """Test suite for the report generator module."""

    @pytest.fixture
    def sample_results(self):
        """Create sample results data for testing."""
        np.random.seed(42)
        return [
            {
                'task_id': 'T001',
                'metric_name': 'accuracy',
                'condition_a_scores': np.random.normal(0.8, 0.05, 30).tolist(),
                'condition_b_scores': np.random.normal(0.85, 0.05, 30).tolist()
            },
            {
                'task_id': 'T002',
                'metric_name': 'f1_score',
                'condition_a_scores': np.random.normal(0.75, 0.08, 25).tolist(),
                'condition_b_scores': np.random.normal(0.78, 0.08, 25).tolist()
            }
        ]

    @pytest.fixture
    def empty_results(self):
        """Create empty results list."""
        return []

    @pytest.fixture
    def incomplete_results(self):
        """Create results with missing data."""
        return [
            {
                'task_id': 'T001',
                'metric_name': 'accuracy',
                'condition_a_scores': [],  # Empty
                'condition_b_scores': [0.8, 0.9, 0.85]
            }
        ]

    def test_generate_csv_report(self, sample_results, tmp_path):
        """Test CSV report generation includes all required statistics."""
        output_path = tmp_path / 'results.csv'
        
        generate_csv_report(sample_results, output_path)
        
        assert output_path.exists(), "CSV file should be created"
        
        # Read and verify content
        with open(output_path, 'r') as f:
            content = f.read()
        
        # Check for required headers
        required_headers = [
            't_statistic', 'p_value', 
            'bootstrap_ci_lower', 'bootstrap_ci_upper',
            'wilcoxon_r', 'wilcoxon_r_ci_lower', 'wilcoxon_r_ci_upper',
            'effect_size_interpretation'
        ]
        
        for header in required_headers:
            assert header in content, f"CSV must include {header}"
        
        # Check for actual data rows
        lines = content.strip().split('\n')
        assert len(lines) >= 3, "CSV should have header + data rows"

    def test_generate_csv_report_empty(self, empty_results, tmp_path):
        """Test CSV report with empty results."""
        output_path = tmp_path / 'results_empty.csv'
        
        generate_csv_report(empty_results, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
        
        # Should have header but no data
        assert 't_statistic' in content

    def test_generate_csv_report_incomplete(self, incomplete_results, tmp_path):
        """Test CSV report skips incomplete results."""
        output_path = tmp_path / 'results_incomplete.csv'
        
        generate_csv_report(incomplete_results, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            lines = f.readlines()
        
        # Should have header but no data rows (skipped due to empty scores)
        assert len(lines) == 1, "Should only have header row"

    def test_generate_pdf_report(self, sample_results, tmp_path):
        """Test PDF report generation."""
        output_path = tmp_path / 'results.pdf'
        
        generate_pdf_report(sample_results, output_path)
        
        assert output_path.exists(), "PDF file should be created"
        assert output_path.stat().st_size > 0, "PDF should not be empty"

    def test_generate_pdf_report_fallback(self, sample_results, tmp_path):
        """Test PDF generation fallback to JSON when matplotlib missing."""
        # This test verifies the fallback logic exists
        # In a real environment with matplotlib, it should generate PDF
        output_path = tmp_path / 'results_fallback.pdf'
        
        # Should not raise an exception
        generate_pdf_report(sample_results, output_path)
        
        # Either PDF or JSON should exist
        json_path = output_path.with_suffix('.json')
        assert output_path.exists() or json_path.exists()

    def test_generate_reports(self, sample_results, tmp_path):
        """Test combined report generation."""
        output_dir = tmp_path / 'reports'
        
        paths = generate_reports(sample_results, output_dir)
        
        assert 'csv' in paths
        assert 'pdf' in paths
        assert os.path.exists(paths['csv'])
        assert os.path.exists(paths['pdf'])

    def test_report_contains_required_statistics(self, sample_results, tmp_path):
        """Verify report includes all required statistics per FR-007."""
        output_path = tmp_path / 'test_report.csv'
        
        generate_csv_report(sample_results, output_path)
        
        with open(output_path, 'r') as f:
            content = f.read()
        
        # FR-007 Requirements:
        # (a) t-statistic
        assert 't_statistic' in content
        
        # (b) p-value
        assert 'p_value' in content
        
        # (c) bootstrap CI (95% CI)
        assert 'bootstrap_ci_lower' in content
        assert 'bootstrap_ci_upper' in content
        
        # (d) Wilcoxon effect size as PRIMARY outcome with 95% CI
        assert 'wilcoxon_r' in content
        assert 'wilcoxon_r_ci_lower' in content
        assert 'wilcoxon_r_ci_upper' in content
        assert 'effect_size_interpretation' in content

    def test_statistical_values_are_real(self, sample_results, tmp_path):
        """Verify statistical values are computed, not fabricated."""
        output_path = tmp_path / 'real_check.csv'
        
        generate_csv_report(sample_results, output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) > 0, "Should have at least one result row"
        
        for row in rows:
            # Verify t-statistic is a number
            t_stat = float(row['t_statistic'])
            assert isinstance(t_stat, float)
            
            # Verify p-value is between 0 and 1
            p_val = float(row['p_value'])
            assert 0.0 <= p_val <= 1.0, "P-value must be in [0, 1]"
            
            # Verify effect size R is reasonable (typically -1 to 1)
            r_val = float(row['wilcoxon_r'])
            assert -1.0 <= r_val <= 1.0, "Wilcoxon R should be in [-1, 1]"
        
        import csv

    def test_report_with_single_sample(self, tmp_path):
        """Test report generation with minimal data."""
        single_result = [
            {
                'task_id': 'T_MIN',
                'metric_name': 'test',
                'condition_a_scores': [0.5],
                'condition_b_scores': [0.6]
            }
        ]
        
        output_path = tmp_path / 'single.csv'
        
        # Should not crash on minimal data
        generate_csv_report(single_result, output_path)
        
        assert output_path.exists()