import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code directory to path if running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.memory_analysis import (
    parse_memory_log,
    compute_memory_statistics,
    generate_markdown_report,
    save_json_profile,
    GITHUB_ACTIONS_MEMORY_LIMIT_GB
)

class TestMemoryAnalysis:

    def test_parse_memory_log_empty_file(self, tmp_path):
        log_file = tmp_path / "memory_profile_raw.jsonl"
        log_file.write_text("")
        result = parse_memory_log(log_file)
        assert result == []

    def test_parse_memory_log_valid_entries(self, tmp_path):
        log_file = tmp_path / "memory_profile_raw.jsonl"
        entries = [
            {"image_index": 0, "peak_memory_gb": 2.5, "status": "PASS"},
            {"image_index": 1, "peak_memory_gb": 3.1, "status": "PASS"},
            {"image_index": 2, "message": "MemoryError", "status": "MemoryError"}
        ]
        log_file.write_text("\n".join(json.dumps(e) for e in entries))
        
        result = parse_memory_log(log_file)
        assert len(result) == 3
        assert result[0]["image_index"] == 0
        assert result[2]["status"] == "MemoryError"

    def test_parse_memory_log_malformed_json(self, tmp_path):
        log_file = tmp_path / "memory_profile_raw.jsonl"
        log_file.write_text('{"valid": 1}\ninvalid json\n{"valid": 2}')
        
        with patch('src.memory_analysis.logger') as mock_logger:
            result = parse_memory_log(log_file)
            assert len(result) == 2
            mock_logger.warning.assert_called_once()

    def test_compute_memory_statistics_no_entries(self):
        stats = compute_memory_statistics([])
        assert stats["peak_memory_gb"] == 0.0
        assert stats["status"] == "FAIL"
        assert stats["had_oom_error"] is False

    def test_compute_memory_statistics_with_oom(self):
        entries = [
            {"image_index": 0, "peak_memory_gb": 2.0, "status": "PASS"},
            {"status": "MemoryError", "message": "OOM"}
        ]
        stats = compute_memory_statistics(entries)
        assert stats["peak_memory_gb"] == 2.0
        assert stats["had_oom_error"] is True
        assert stats["status"] == "FAIL"

    def test_compute_memory_statistics_within_limit(self):
        entries = [
            {"peak_memory_gb": 4.0},
            {"peak_memory_gb": 5.5},
            {"peak_memory_gb": 6.0}
        ]
        stats = compute_memory_statistics(entries)
        assert stats["peak_memory_gb"] == 6.0
        assert stats["within_limit"] is True
        assert stats["status"] == "PASS"

    def test_compute_memory_statistics_exceeds_limit(self):
        entries = [
            {"peak_memory_gb": 4.0},
            {"peak_memory_gb": 7.5} # Exceeds 7.0
        ]
        stats = compute_memory_statistics(entries)
        assert stats["peak_memory_gb"] == 7.5
        assert stats["within_limit"] is False
        assert stats["status"] == "FAIL"

    def test_generate_markdown_report(self):
        stats = {
            "peak_memory_gb": 5.0,
            "average_memory_gb": 4.0,
            "min_memory_gb": 3.0,
            "entry_count": 10,
            "had_oom_error": False,
            "within_limit": True,
            "status": "PASS",
            "limit_gb": GITHUB_ACTIONS_MEMORY_LIMIT_GB
        }
        
        report = generate_markdown_report(stats, Path("dummy.log"))
        
        assert "# Memory Analysis Report" in report
        assert "Status: PASS" in report
        assert "5.0" in report
        assert "GitHub Actions Memory Limit" in report

    def test_save_json_profile(self, tmp_path):
        stats = {"peak_memory_gb": 5.0, "status": "PASS"}
        output_file = tmp_path / "profile.json"
        
        save_json_profile(stats, output_file)
        
        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert data["peak_memory_gb"] == 5.0
        assert data["status"] == "PASS"

    @patch('src.memory_analysis.parse_memory_log')
    @patch('src.memory_analysis.compute_memory_statistics')
    @patch('src.memory_analysis.save_json_profile')
    @patch('src.memory_analysis.generate_markdown_report')
    def test_run_memory_analysis_integration(
        self, mock_gen_report, mock_save_json, mock_compute, mock_parse, tmp_path
    ):
        # Setup mocks
        mock_parse.return_value = [{"peak_memory_gb": 5.0}]
        mock_compute.return_value = {
            "peak_memory_gb": 5.0, "status": "PASS", 
            "average_memory_gb": 0.0, "min_memory_gb": 0.0,
            "entry_count": 1, "had_oom_error": False,
            "within_limit": True, "limit_gb": 7.0
        }
        mock_gen_report.return_value = "# Report"
        
        # Temporarily override paths for test
        import src.memory_analysis as ma
        original_raw = ma.RAW_LOG_PATH
        original_json = ma.PROFILE_JSON_PATH
        original_md = ma.REPORT_MD_PATH
        original_dir = ma.RESULTS_DIR

        # Create temp dirs
        (tmp_path / "data" / "results").mkdir(parents=True)
        (tmp_path / "docs").mkdir(parents=True)
        
        ma.RESULTS_DIR = tmp_path / "data" / "results"
        ma.RAW_LOG_PATH = ma.RESULTS_DIR / "memory_profile_raw.jsonl"
        ma.PROFILE_JSON_PATH = ma.RESULTS_DIR / "memory_profile.json"
        ma.REPORT_MD_PATH = tmp_path / "docs" / "memory_report.md"

        try:
            result = ma.run_memory_analysis()
            assert result["status"] == "PASS"
            mock_save_json.assert_called_once()
            mock_gen_report.assert_called_once()
        finally:
            # Restore
            ma.RESULTS_DIR = original_dir
            ma.RAW_LOG_PATH = original_raw
            ma.PROFILE_JSON_PATH = original_json
            ma.REPORT_MD_PATH = original_md