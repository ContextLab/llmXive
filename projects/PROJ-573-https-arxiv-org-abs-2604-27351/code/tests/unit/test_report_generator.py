"""
Unit tests for the report generator module.

Tests verify:
- CSV generation with correct headers and data formatting
- PDF generation creates a valid file
- Statistical values are correctly formatted
"""

import os
import csv
import tempfile
from pathlib import Path
import pytest
from datetime import datetime

from src.evaluation.report_generator import (
    generate_csv_report,
    generate_pdf_report,
    generate_reports
)


class TestReportGenerator:
    """Test suite for Report Generator functionality."""

    @pytest.fixture
    def sample_results(self):
        """Provide sample statistical results for testing."""
        return [
            {
                "task_id": "T001",
                "condition_a": "Heterogeneous",
                "condition_b": "Unified",
                "t_statistic": 2.4567,
                "p_value_ttest": 0.0182,
                "wilcoxon_r": 0.4231,
                "wilcoxon_p": 0.0124,
                "bootstrap_mean_diff": 0.0352,
                "bootstrap_ci_lower": 0.0121,
                "bootstrap_ci_upper": 0.0583,
                "timestamp": datetime.now().isoformat()
            },
            {
                "task_id": "T002",
                "condition_a": "Heterogeneous",
                "condition_b": "Unified",
                "t_statistic": 1.1234,
                "p_value_ttest": 0.2651,
                "wilcoxon_r": 0.1523,
                "wilcoxon_p": 0.3102,
                "bootstrap_mean_diff": 0.0081,
                "bootstrap_ci_lower": -0.0152,
                "bootstrap_ci_upper": 0.0314,
                "timestamp": datetime.now().isoformat()
            }
        ]

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_csv_report_generation(self, sample_results, temp_dir):
        """Test that CSV report is generated with correct structure."""
        output_path = temp_dir / "test_results.csv"
        
        result_path = generate_csv_report(sample_results, str(output_path))
        
        # Verify file exists
        assert os.path.exists(result_path)
        
        # Verify content
        with open(result_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check row count
            assert len(rows) == 2
            
            # Check headers
            expected_headers = [
                'task_id', 'condition_a', 'condition_b', 't_statistic',
                'p_value_ttest', 'wilcoxon_r', 'wilcoxon_p',
                'bootstrap_mean_diff', 'bootstrap_ci_lower', 'bootstrap_ci_upper',
                'timestamp'
            ]
            assert reader.fieldnames == expected_headers
            
            # Check data values
            assert rows[0]['task_id'] == 'T001'
            assert float(rows[0]['t_statistic']) == 2.4567
            assert float(rows[0]['wilcoxon_r']) == 0.4231
            assert rows[0]['condition_a'] == 'Heterogeneous'

    def test_pdf_report_generation(self, sample_results, temp_dir):
        """Test that PDF report is generated and is non-empty."""
        output_path = temp_dir / "test_results.pdf"
        
        result_path = generate_pdf_report(sample_results, str(output_path))
        
        # Verify file exists
        assert os.path.exists(result_path)
        
        # Verify file is not empty
        assert os.path.getsize(result_path) > 0
        
        # Verify it starts with PDF header
        with open(result_path, 'rb') as f:
            header = f.read(4)
            assert header == b'%PDF'

    def test_generate_reports_both_outputs(self, sample_results, temp_dir):
        """Test that generate_reports creates both CSV and PDF."""
        csv_path = temp_dir / "results.csv"
        pdf_path = temp_dir / "results.pdf"
        
        csv_result, pdf_result = generate_reports(
            sample_results,
            str(csv_path),
            str(pdf_path)
        )
        
        assert os.path.exists(csv_result)
        assert os.path.exists(pdf_result)
        assert os.path.getsize(csv_result) > 0
        assert os.path.getsize(pdf_result) > 0

    def test_empty_results_list(self, temp_dir):
        """Test handling of empty results list."""
        csv_path = temp_dir / "empty.csv"
        pdf_path = temp_dir / "empty.pdf"
        
        # CSV should still generate with headers
        csv_result = generate_csv_report([], str(csv_path))
        assert os.path.exists(csv_result)
        
        with open(csv_result, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            # Should have headers even if no data
            assert len(headers) > 0

    def test_missing_optional_fields(self, temp_dir):
        """Test handling of results with missing optional fields."""
        incomplete_results = [
            {
                "task_id": "T001",
                "condition_a": "A",
                "condition_b": "B",
                # Missing statistical fields
            }
        ]
        
        output_path = temp_dir / "incomplete.csv"
        result_path = generate_csv_report(incomplete_results, str(output_path))
        
        assert os.path.exists(result_path)
        
        with open(result_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['t_statistic'] == 'N/A'
            assert rows[0]['wilcoxon_r'] == 'N/A'