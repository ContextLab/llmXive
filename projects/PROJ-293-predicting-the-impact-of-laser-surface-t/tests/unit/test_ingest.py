import pytest
import json
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingest import (
    count_records,
    save_record_counts,
    compare_thresholds,
    save_threshold_check,
    save_pre_check,
    main
)

class TestThresholdExitCodes:
    """
    Test cases for T016b: compare_thresholds function.
    Verifies correct exit codes and output artifacts based on normalized_count.
    """

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_clean_csv(self, temp_dir):
        """Create a mock aggregated_clean.csv with normalization_method column."""
        csv_path = temp_dir / "aggregated_clean.csv"
        data = {
            'pulse_duration': [10] * 50 + [20] * 60,
            'power': [100] * 50 + [200] * 60,
            'scanning_speed': [5] * 50 + [10] * 60,
            'pattern_geometry': ['grid'] * 50 + ['honeycomb'] * 60,
            'hardness': [500] * 50 + [600] * 60,
            'elastic_modulus': [200] * 50 + [210] * 60,
            'wear_rate': [0.1] * 50 + [0.2] * 60,
            'normalization_method': ['raw'] * 50 + ['normalized'] * 60
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return csv_path

    @pytest.fixture
    def mock_record_counts_failed(self, temp_dir):
        """Create mock record_counts.json with normalized_count < 100."""
        json_path = temp_dir / "record_counts.json"
        counts = {
            "normalized_count": 50,
            "raw_count": 20,
            "total_count": 70
        }
        with open(json_path, 'w') as f:
            json.dump(counts, f)
        return json_path

    @pytest.fixture
    def mock_record_counts_pilot(self, temp_dir):
        """Create mock record_counts.json with 100 <= normalized_count < 300."""
        json_path = temp_dir / "record_counts.json"
        counts = {
            "normalized_count": 150,
            "raw_count": 30,
            "total_count": 180
        }
        with open(json_path, 'w') as f:
            json.dump(counts, f)
        return json_path

    @pytest.fixture
    def mock_record_counts_full(self, temp_dir):
        """Create mock record_counts.json with normalized_count >= 300."""
        json_path = temp_dir / "record_counts.json"
        counts = {
            "normalized_count": 350,
            "raw_count": 40,
            "total_count": 390
        }
        with open(json_path, 'w') as f:
            json.dump(counts, f)
        return json_path

    def test_threshold_insufficient_data(self, temp_dir, mock_record_counts_failed):
        """Test exit code 1 when normalized_count < 100."""
        # Patch paths to use temp_dir
        original_counts_path = Path("data/processed/record_counts.json")
        original_threshold_path = Path("data/processed/threshold_check.json")
        original_pre_check_path = Path("reports/pre_check.json")

        # We will test the function directly instead of main() to avoid path issues
        counts = json.load(open(mock_record_counts_failed))
        
        result, exit_code = compare_thresholds(counts)
        
        assert exit_code == 1, "Exit code should be 1 for insufficient data"
        assert result['status'] == 'failed', "Status should be 'failed'"
        assert result['reason'] == 'insufficient_data', "Reason should be 'insufficient_data'"
        assert result['normalized_count'] == 50, "Normalized count should be 50"

    def test_threshold_pilot_study(self, temp_dir, mock_record_counts_pilot):
        """Test exit code 2 when 100 <= normalized_count < 300."""
        counts = json.load(open(mock_record_counts_pilot))
        
        result, exit_code = compare_thresholds(counts)
        
        assert exit_code == 2, "Exit code should be 2 for pilot study"
        assert result['status'] == 'success', "Status should be 'success'"
        assert result['study_scope'] == 'pilot_study', "Study scope should be 'pilot_study'"
        assert result['normalized_count'] == 150, "Normalized count should be 150"

    def test_threshold_full_study(self, temp_dir, mock_record_counts_full):
        """Test exit code 0 when normalized_count >= 300."""
        counts = json.load(open(mock_record_counts_full))
        
        result, exit_code = compare_thresholds(counts)
        
        assert exit_code == 0, "Exit code should be 0 for full study"
        assert result['status'] == 'success', "Status should be 'success'"
        assert result['study_scope'] == 'full_study', "Study scope should be 'full_study'"
        assert result['normalized_count'] == 350, "Normalized count should be 350"

    def test_save_threshold_check(self, temp_dir):
        """Test saving threshold check result to JSON."""
        result = {
            "status": "success",
            "study_scope": "pilot_study",
            "normalized_count": 150
        }
        output_path = temp_dir / "threshold_check.json"
        
        save_threshold_check(result, output_path)
        
        assert output_path.exists(), "Threshold check file should exist"
        
        with open(output_path, 'r') as f:
            saved_result = json.load(f)
        
        assert saved_result == result, "Saved result should match input result"

    def test_save_pre_check(self, temp_dir):
        """Test saving pre-check result to reports/pre_check.json."""
        result = {
            "status": "failed",
            "reason": "insufficient_data",
            "normalized_count": 50
        }
        output_path = temp_dir / "pre_check.json"
        
        save_pre_check(result, output_path)
        
        assert output_path.exists(), "Pre-check file should exist"
        
        with open(output_path, 'r') as f:
            saved_result = json.load(f)
        
        assert saved_result == result, "Saved result should match input result"

    def test_main_failure_path(self, temp_dir, mock_record_counts_failed, mock_clean_csv):
        """Test main() execution path for failure case (exit code 1)."""
        # Temporarily override global paths
        import ingest
        original_counts_path = ingest.RECORD_COUNTS_PATH
        original_pre_check_path = ingest.PRE_CHECK_PATH
        
        ingest.RECORD_COUNTS_PATH = mock_record_counts_failed
        ingest.PRE_CHECK_PATH = temp_dir / "pre_check.json"
        
        try:
            exit_code = main()
            assert exit_code == 1, "Main should return exit code 1 for failure"
            assert (temp_dir / "pre_check.json").exists(), "pre_check.json should be created"
        finally:
            # Restore original paths
            ingest.RECORD_COUNTS_PATH = original_counts_path
            ingest.PRE_CHECK_PATH = original_pre_check_path

    def test_main_pilot_path(self, temp_dir, mock_record_counts_pilot, mock_clean_csv):
        """Test main() execution path for pilot case (exit code 2)."""
        import ingest
        original_counts_path = ingest.RECORD_COUNTS_PATH
        
        ingest.RECORD_COUNTS_PATH = mock_record_counts_pilot
        
        try:
            exit_code = main()
            assert exit_code == 2, "Main should return exit code 2 for pilot"
        finally:
            ingest.RECORD_COUNTS_PATH = original_counts_path

    def test_main_success_path(self, temp_dir, mock_record_counts_full, mock_clean_csv):
        """Test main() execution path for success case (exit code 0)."""
        import ingest
        original_counts_path = ingest.RECORD_COUNTS_PATH
        
        ingest.RECORD_COUNTS_PATH = mock_record_counts_full
        
        try:
            exit_code = main()
            assert exit_code == 0, "Main should return exit code 0 for success"
        finally:
            ingest.RECORD_COUNTS_PATH = original_counts_path