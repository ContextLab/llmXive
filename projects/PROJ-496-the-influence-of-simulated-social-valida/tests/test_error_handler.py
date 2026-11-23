"""
Tests for the error handling module (T017).
"""
import pytest
import csv
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path if running from tests/
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from error_handler import handle_missing_anxiety_measures, categorize_dataset
from generate_negative_finding_report import main as generate_none_report
from generate_negative_finding_report_separate import main as generate_separate_report


class TestErrorHandler:
    
    @pytest.fixture
    def temp_search_results(self, tmp_path):
        """Creates a temporary CSV file with mock search results."""
        csv_path = tmp_path / "search_results.csv"
        data = [
            {"dataset_id": "ds001", "title": "Social Feedback Sim", "feedback_type": "Simulated", "anxiety_measure": "LSAS", "status": "Eligible", "url": "http://example.com/ds001"},
            {"dataset_id": "ds002", "title": "Social Feedback Real", "feedback_type": "Real", "anxiety_measure": "SPIN", "status": "Eligible", "url": "http://example.com/ds002"},
            {"dataset_id": "ds003", "title": "Sim Only No Anxiety", "feedback_type": "Simulated", "anxiety_measure": "None", "status": "Sim-Only", "url": "http://example.com/ds003"},
            {"dataset_id": "ds004", "title": "Real Only No Anxiety", "feedback_type": "Real", "anxiety_measure": "", "status": "Real-Only", "url": "http://example.com/ds004"},
            {"dataset_id": "ds005", "title": "No Feedback No Anxiety", "feedback_type": "None", "anxiety_measure": "None", "status": "None", "url": "http://example.com/ds005"},
        ]
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["dataset_id", "title", "feedback_type", "anxiety_measure", "status", "url"])
            writer.writeheader()
            writer.writerows(data)
        return csv_path

    @pytest.fixture
    def temp_search_results_no_eligible(self, tmp_path):
        """Creates a temporary CSV file with NO eligible datasets."""
        csv_path = tmp_path / "search_results_no_eligible.csv"
        data = [
            {"dataset_id": "ds003", "title": "Sim Only No Anxiety", "feedback_type": "Simulated", "anxiety_measure": "None", "status": "Sim-Only", "url": "http://example.com/ds003"},
            {"dataset_id": "ds004", "title": "Real Only No Anxiety", "feedback_type": "Real", "anxiety_measure": "", "status": "Real-Only", "url": "http://example.com/ds004"},
        ]
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["dataset_id", "title", "feedback_type", "anxiety_measure", "status", "url"])
            writer.writeheader()
            writer.writerows(data)
        return csv_path

    @pytest.fixture
    def temp_search_results_empty(self, tmp_path):
        """Creates a temporary CSV file with only headers."""
        csv_path = tmp_path / "search_results_empty.csv"
        data = []
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["dataset_id", "title", "feedback_type", "anxiety_measure", "status", "url"])
            writer.writeheader()
            writer.writerows(data)
        return csv_path

    def test_handles_missing_anxiety_and_triggers_separate_report(self, temp_search_results_no_eligible, tmp_path):
        """
        Test that when no eligible datasets are found (only Sim-Only/Real-Only),
        the function logs missing IDs and triggers the separate report generator.
        """
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Mock the report generators to avoid file I/O and PDF generation issues in unit test
        with patch('error_handler.generate_separate_report') as mock_sep, \
             patch('error_handler.generate_none_report') as mock_none:
            
            result = handle_missing_anxiety_measures(temp_search_results_no_eligible, output_dir)

            assert result == 0, "Function should return 0 on success"
            mock_sep.assert_called_once()
            mock_none.assert_not_called()
            
            # Check that the mock was called with expected lists
            call_args = mock_sep.call_args
            assert 'sim_only' in call_args.kwargs
            assert 'real_only' in call_args.kwargs
            assert len(call_args.kwargs['sim_only']) == 1
            assert len(call_args.kwargs['real_only']) == 1

    def test_handles_empty_search_results(self, temp_search_results_empty, tmp_path):
        """
        Test that when search results are empty, it triggers the 'None' report.
        """
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with patch('error_handler.generate_none_report') as mock_none:
            result = handle_missing_anxiety_measures(temp_search_results_empty, output_dir)
            
            assert result == 0
            mock_none.assert_called_once()

    def test_logs_missing_anxiety_ids(self, temp_search_results_no_eligible, tmp_path, caplog):
        """
        Test that specific dataset IDs missing anxiety measures are logged.
        """
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # We need to ensure the logger is configured to capture logs
        import logging
        caplog.set_level(logging.WARNING)

        with patch('error_handler.generate_separate_report'):
            handle_missing_anxiety_measures(temp_search_results_no_eligible, output_dir)

        # Check log messages
        assert "ds003" in caplog.text
        assert "ds004" in caplog.text
        assert "missing anxiety measures" in caplog.text

    def test_returns_1_on_file_not_found(self, tmp_path):
        """
        Test that the function returns 1 if the input file does not exist.
        """
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        fake_path = tmp_path / "nonexistent.csv"

        result = handle_missing_anxiety_measures(fake_path, output_dir)
        assert result == 1

    def test_continues_if_eligible_found(self, temp_search_results, tmp_path):
        """
        Test that if Eligible datasets are found, the function returns 0 without triggering abort.
        """
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with patch('error_handler.generate_separate_report') as mock_sep, \
             patch('error_handler.generate_none_report') as mock_none:
            
            result = handle_missing_anxiety_measures(temp_search_results, output_dir)
            
            assert result == 0
            mock_sep.assert_not_called()
            mock_none.assert_not_called()
