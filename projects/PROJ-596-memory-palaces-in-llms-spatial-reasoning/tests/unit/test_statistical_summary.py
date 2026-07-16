"""
Unit tests for the Statistical Summary Generator (T022).

These tests verify that the summary generation logic correctly processes
mock data and produces the expected structure without actually running
the heavy statistical computations or requiring real data files.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from evaluation.statistical_summary import (
    load_seed_accuracies,
    generate_statistical_summary,
    main,
    RESULTS_DIR,
    SUMMARY_FILE,
    DATASETS
)


class TestLoadSeedAccuracies:
    def test_missing_file_raises_error(self, tmp_path):
        """Test that FileNotFoundError is raised if recall_accuracy.json is missing."""
        # Create a temp directory that doesn't have the file
        with patch.object(RESULTS_DIR, '__truediv__', return_value=tmp_path):
            with pytest.raises(FileNotFoundError):
                load_seed_accuracies()

    def test_loads_correct_structure(self, tmp_path):
        """Test that the function loads and structures data correctly."""
        mock_data = {
            "babi": {"spatial": [0.8, 0.9], "baseline": [0.6, 0.7]},
            "lambada": {"spatial": [0.5], "baseline": [0.4]}
        }
        
        file_path = tmp_path / "recall_accuracy.json"
        with open(file_path, 'w') as f:
            json.dump(mock_data, f)

        # Mock the RESULTS_DIR to point to tmp_path
        # Since RESULTS_DIR is a Path object, we can't easily patch the global constant
        # in the module being tested without importing it differently.
        # Instead, we will patch the open call or the path resolution.
        
        # Simpler approach: create the file in the actual expected location if possible,
        # or mock the file existence check.
        # Given the constraints of unit tests, we will mock the file reading.
        
        with patch("evaluation.statistical_summary.RESULTS_DIR", tmp_path):
            # Re-import or reload to pick up the patch? 
            # Better to patch the internal logic.
            pass

        # Direct test with file creation
        with open(file_path, 'w') as f:
            json.dump(mock_data, f)
        
        # We need to trick the function into looking at tmp_path
        # Since RESULTS_DIR is defined at module level, we patch the module's attribute
        with patch("evaluation.statistical_summary.RESULTS_DIR", tmp_path):
            result = load_seed_accuracies()
            
        assert result == mock_data


class TestGenerateStatisticalSummary:
    @patch("evaluation.statistical_summary.load_seed_accuracies")
    @patch("evaluation.statistical_summary.run_analysis_for_dataset")
    def test_generates_summary_structure(self, mock_run_analysis, mock_load):
        """Test that the summary has the correct top-level keys."""
        mock_data = {
            "babi": {"spatial": [0.8], "baseline": [0.6]},
            "lambada": {"spatial": [0.5], "baseline": [0.4]}
        }
        mock_load.return_value = mock_data
        
        mock_analysis_result = {
            "p_value": 0.01,
            "corrected_p_value": 0.03,
            "effect_size": 0.5,
            "ci_lower": 0.1,
            "ci_upper": 0.9,
            "normality_check": "passed"
        }
        mock_run_analysis.return_value = mock_analysis_result
        
        summary = generate_statistical_summary()
        
        assert "datasets" in summary
        assert "summary_statistics" in summary
        assert "generated_at" not in summary # generated_at is added in main()
        
        assert "babi" in summary["datasets"]
        assert summary["datasets"]["babi"] == mock_analysis_result

    @patch("evaluation.statistical_summary.load_seed_accuracies")
    def test_handles_missing_dataset(self, mock_load):
        """Test that missing datasets are skipped gracefully."""
        mock_data = {
            "babi": {"spatial": [0.8], "baseline": [0.6]},
            # lambada is missing
        }
        mock_load.return_value = mock_data
        
        with patch("evaluation.statistical_summary.run_analysis_for_dataset") as mock_run:
            summary = generate_statistical_summary()
            
        assert "babi" in summary["datasets"]
        assert "lambada" not in summary["datasets"]
        assert summary["summary_statistics"]["total_datasets_analyzed"] == 1


class TestMain:
    @patch("evaluation.statistical_summary.generate_statistical_summary")
    @patch("evaluation.statistical_summary.open")
    @patch("evaluation.statistical_summary.datetime")
    def test_main_writes_file(self, mock_dt, mock_open, mock_gen_summary, tmp_path):
        """Test that main() writes the JSON file correctly."""
        mock_summary = {"datasets": {"babi": {}}, "summary_statistics": {}}
        mock_gen_summary.return_value = mock_summary
        
        mock_dt.utcnow.return_value = MagicMock(isoformat=MagicMock(return_value="2023-01-01T00:00:00Z"))
        
        # Mock the file handle
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Patch RESULTS_DIR to tmp_path
        with patch("evaluation.statistical_summary.RESULTS_DIR", tmp_path):
            # Patch the path to SUMMARY_FILE to be inside tmp_path
            with patch("evaluation.statistical_summary.SUMMARY_FILE", tmp_path / "statistical_summary.json"):
                exit_code = main()
        
        assert exit_code == 0
        mock_open.assert_called_once()
        mock_file.write.assert_called_once()
        # Verify JSON content was written
        written_content = mock_file.write.call_args[0][0]
        assert "datasets" in written_content
        assert "2023-01-01" in written_content

    @patch("evaluation.statistical_summary.generate_statistical_summary")
    def test_main_handles_errors(self, mock_gen_summary):
        """Test that main() returns 1 on error."""
        mock_gen_summary.side_effect = Exception("Test error")
        
        exit_code = main()
        assert exit_code == 1