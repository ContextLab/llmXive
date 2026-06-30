"""
Unit tests for the report generator module.
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
    """Test cases for report generation functionality."""

    @pytest.fixture
    def sample_results(self):
        """Provide sample benchmark results for testing."""
        return [
            {
                'task_id': 'T001',
                'condition': 'heterogeneous',
                'accuracy': 0.85,
                'timestamp': datetime.now().isoformat(),
                'statistics': {
                    't_statistic': 2.34,
                    'p_value': 0.021,
                    'bootstrap_ci': {'lower': 0.02, 'upper': 0.15},
                    'wilcoxon_effect_size': 0.45,
                    'wilcoxon_ci': {'lower': 0.01, 'upper': 0.12}
                }
            },
            {
                'task_id': 'T002',
                'condition': 'unified',
                'accuracy': 0.82,
                'timestamp': datetime.now().isoformat(),
                'statistics': {
                    't_statistic': 1.89,
                    'p_value': 0.062,
                    'bootstrap_ci': {'lower': -0.01, 'upper': 0.08},
                    'wilcoxon_effect_size': 0.32,
                    'wilcoxon_ci': {'lower': -0.02, 'upper': 0.09}
                }
            }
        ]

    def test_generate_csv_report_creates_file(self, sample_results):
        """Test that CSV report file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_report.csv')
            result_path = generate_csv_report(sample_results, output_path)

            assert os.path.exists(result_path), "CSV file was not created"
            assert result_path.endswith('.csv'), "Output path should end with .csv"

    def test_generate_csv_report_has_correct_headers(self, sample_results):
        """Test that CSV report contains expected headers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_report.csv')
            generate_csv_report(sample_results, output_path)

            with open(output_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames

                expected_headers = [
                    'task_id', 'condition', 'accuracy', 't_statistic', 'p_value',
                    'bootstrap_ci_lower', 'bootstrap_ci_upper',
                    'wilcoxon_effect_size', 'wilcoxon_ci_lower', 'wilcoxon_ci_upper',
                    'timestamp'
                ]

                for header in expected_headers:
                    assert header in headers, f"Missing header: {header}"

    def test_generate_csv_report_has_correct_data(self, sample_results):
        """Test that CSV report contains correct data values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_report.csv')
            generate_csv_report(sample_results, output_path)

            with open(output_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == len(sample_results), "Row count mismatch"

                # Check first row
                first_row = rows[0]
                assert first_row['task_id'] == 'T001'
                assert first_row['condition'] == 'heterogeneous'
                assert float(first_row['accuracy']) == 0.85
                assert float(first_row['t_statistic']) == 2.34
                assert float(first_row['p_value']) == 0.021

    def test_generate_pdf_report_creates_file(self, sample_results):
        """Test that PDF report file is created (or text fallback)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_report.pdf')
            result_path = generate_pdf_report(sample_results, output_path)

            # Should create either PDF or .txt fallback
            assert os.path.exists(result_path), "PDF or fallback file was not created"

    def test_generate_reports_creates_both_files(self, sample_results):
        """Test that generate_reports creates both CSV and PDF files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reports = generate_reports(sample_results, tmpdir)

            assert 'csv' in reports, "Missing 'csv' key in reports"
            assert 'pdf' in reports, "Missing 'pdf' key in reports"
            assert os.path.exists(reports['csv']), "CSV file not created"

            # PDF might be .txt fallback if reportlab not installed
            pdf_path = reports['pdf']
            assert os.path.exists(pdf_path) or os.path.exists(pdf_path.replace('.pdf', '.txt')), \
                "PDF or fallback file not created"

    def test_generate_csv_report_empty_results(self):
        """Test handling of empty results list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'empty_report.csv')
            result_path = generate_csv_report([], output_path)

            assert os.path.exists(result_path), "CSV file should be created even with empty results"

            with open(output_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 0, "Empty results should produce empty CSV (except headers)"

    def test_generate_csv_report_missing_statistics(self):
        """Test handling of results without statistics."""
        results = [
            {
                'task_id': 'T001',
                'condition': 'test',
                'accuracy': 0.90,
                'timestamp': datetime.now().isoformat()
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'no_stats_report.csv')
            result_path = generate_csv_report(results, output_path)

            assert os.path.exists(result_path), "CSV file should be created even without statistics"

            with open(output_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1

                # Statistics should be empty strings or N/A
                assert rows[0]['t_statistic'] in ['', 'N/A']
                assert rows[0]['p_value'] in ['', 'N/A']

    def test_generate_reports_creates_files_in_directory(self, sample_results):
        """Test that reports are created in the specified directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reports = generate_reports(sample_results, tmpdir)

            # Check that files are in the correct directory
            assert Path(reports['csv']).parent == Path(tmpdir)
            pdf_path = Path(reports['pdf'])
            assert pdf_path.parent == Path(tmpdir) or pdf_path.with_suffix('.txt').parent == Path(tmpdir)
