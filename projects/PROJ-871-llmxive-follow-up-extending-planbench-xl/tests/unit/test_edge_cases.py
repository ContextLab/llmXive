import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import modules to test edge case handling
from dataset.loader import download_planbench_xl, load_injected_data
from dataset.injector import load_raw_planbench_xl, inject_failures
from utils.config import get_path, get_project_root
from analysis.log_parser import load_execution_log, count_outcomes

PROJECT_ROOT = get_project_root()
TEST_DATA_DIR = PROJECT_ROOT / "data" / "derived"


class TestCorruptedDataHandling:
    """Tests for handling corrupted or malformed data files."""

    @pytest.fixture
    def corrupted_json_file(self, tmp_path):
        """Create a temporary corrupted JSON file."""
        file_path = tmp_path / "corrupted.jsonl"
        file_path.write_text('{"task_id": 1, "injected_error": true\n{"task_id": 2}')
        return file_path

    @pytest.fixture
    def empty_json_file(self, tmp_path):
        """Create a temporary empty JSON file."""
        file_path = tmp_path / "empty.jsonl"
        file_path.write_text('')
        return file_path

    @pytest.fixture
    def malformed_json_file(self, tmp_path):
        """Create a temporary file with non-JSON content."""
        file_path = tmp_path / "malformed.jsonl"
        file_path.write_text('This is not JSON at all!')
        return file_path

    def test_load_injected_data_with_corrupted_json(self, corrupted_json_file):
        """Test that load_injected_data handles corrupted JSON gracefully."""
        with pytest.raises((json.JSONDecodeError, ValueError)):
            load_injected_data(str(corrupted_json_file))

    def test_load_injected_data_with_empty_file(self, empty_json_file):
        """Test that load_injected_data handles empty files."""
        data = load_injected_data(str(empty_json_file))
        assert data == [], "Empty file should return empty list"

    def test_load_injected_data_with_malformed_content(self, malformed_json_file):
        """Test that load_injected_data handles non-JSON content."""
        with pytest.raises((json.JSONDecodeError, ValueError)):
            load_injected_data(str(malformed_json_file))

    def test_count_outcomes_with_missing_fields(self, tmp_path):
        """Test count_outcomes with logs missing required fields."""
        log_file = tmp_path / "missing_fields.jsonl"
        log_file.write_text('{"task_id": 1}\n{"task_id": 2, "status": "success"}')
        
        # Should handle missing 'status' field gracefully
        counts = count_outcomes(str(log_file))
        assert isinstance(counts, dict)
        assert "success" in counts or "failure" in counts

    def test_count_outcomes_with_invalid_status_value(self, tmp_path):
        """Test count_outcomes with invalid status values."""
        log_file = tmp_path / "invalid_status.jsonl"
        log_file.write_text('{"task_id": 1, "status": "unknown"}\n{"task_id": 2, "status": "success"}')
        
        counts = count_outcomes(str(log_file))
        assert isinstance(counts, dict)
        # Should count valid statuses and ignore or handle invalid ones
        assert "success" in counts


class TestAPITimeoutHandling:
    """Tests for handling API timeouts and network failures."""

    @patch('dataset.loader.requests.get')
    def test_download_planbench_xl_with_timeout(self, mock_get, tmp_path):
        """Test download_planbench_xl handles request timeouts."""
        mock_get.side_effect = Exception("Connection timed out")
        
        # Should raise an exception or handle gracefully
        with pytest.raises(Exception):
            download_planbench_xl(str(tmp_path))

    @patch('dataset.loader.requests.get')
    def test_download_planbench_xl_with_http_error(self, mock_get, tmp_path):
        """Test download_planbench_xl handles HTTP errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404 Client Error")
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception):
            download_planbench_xl(str(tmp_path))

    @patch('dataset.loader.requests.get')
    def test_download_planbench_xl_with_connection_error(self, mock_get, tmp_path):
        """Test download_planbench_xl handles connection errors."""
        mock_get.side_effect = ConnectionError("Network unreachable")
        
        with pytest.raises(ConnectionError):
            download_planbench_xl(str(tmp_path))

    def test_get_path_with_nonexistent_config(self):
        """Test get_path handles missing configuration keys."""
        # Should raise KeyError for non-existent keys
        with pytest.raises(KeyError):
            get_path("non_existent_key")

    def test_load_raw_planbench_xl_with_missing_file(self):
        """Test load_raw_planbench_xl handles missing source file."""
        non_existent_path = PROJECT_ROOT / "data" / "raw" / "non_existent.parquet"
        
        with pytest.raises(FileNotFoundError):
            load_raw_planbench_xl(str(non_existent_path))


class TestMemoryAndResourceEdgeCases:
    """Tests for memory and resource edge cases."""

    def test_inject_failures_with_empty_dataset(self, tmp_path):
        """Test inject_failures handles empty input dataset."""
        empty_data = []
        output_path = tmp_path / "output.jsonl"
        
        result = inject_failures(empty_data, str(output_path), seed=42)
        assert result == []

    def test_inject_failures_with_all_failures(self, tmp_path):
        """Test inject_failures when all tasks already have failures."""
        # Simulate dataset where all tasks already have errors
        all_failed_data = [
            {"task_id": 1, "status": "failure", "injected_error": True},
            {"task_id": 2, "status": "failure", "injected_error": True}
        ]
        output_path = tmp_path / "output.jsonl"
        
        result = inject_failures(all_failed_data, str(output_path), seed=42)
        # Should handle gracefully, possibly returning unchanged data
        assert isinstance(result, list)

    def test_load_execution_log_with_large_file(self, tmp_path):
        """Test load_execution_log handles reasonably large files."""
        # Create a moderately large log file
        log_file = tmp_path / "large_log.jsonl"
        with open(log_file, 'w') as f:
            for i in range(1000):
                f.write(json.dumps({"task_id": i, "status": "success"}) + '\n')
        
        data = load_execution_log(str(log_file))
        assert len(data) == 1000
        assert all("task_id" in item for item in data)


class TestConfigAndPathEdgeCases:
    """Tests for configuration and path edge cases."""

    def test_get_project_root_returns_valid_path(self):
        """Test get_project_root returns a valid Path object."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_ensure_dirs_exist_creates_missing_dirs(self, tmp_path):
        """Test ensure_dirs_exist creates missing directories."""
        import sys
        # Temporarily override get_project_root to use tmp_path
        with patch('utils.config.get_project_root', return_value=tmp_path):
            from utils.config import ensure_dirs_exist
            ensure_dirs_exist()
            
            # Verify standard directories were created
            assert (tmp_path / "data").exists()
            assert (tmp_path / "code").exists()

    def test_get_hyperparameter_with_missing_key(self):
        """Test get_hyperparameter handles missing hyperparameter keys."""
        with pytest.raises(KeyError):
            get_hyperparameter("non_existent_param")

    def test_get_hyperparameter_with_default(self):
        """Test get_hyperparameter uses default when key missing."""
        # This tests the fallback behavior if implemented
        # If not implemented, this will raise KeyError which is also valid
        try:
            result = get_hyperparameter("non_existent_param", default="fallback")
            assert result == "fallback"
        except KeyError:
            # Expected if default parameter not implemented
            pass

class TestAgentExecutionEdgeCases:
    """Tests for agent execution edge cases."""

    def test_parse_baseline_log_with_empty_log(self, tmp_path):
        """Test parse_baseline_log handles empty log files."""
        log_file = tmp_path / "empty_baseline.jsonl"
        log_file.write_text('')
        
        result = parse_baseline_log(str(log_file))
        assert result == []

    def test_parse_augmented_log_with_malformed_entries(self, tmp_path):
        """Test parse_augmented_log handles malformed log entries."""
        log_file = tmp_path / "malformed_augmented.jsonl"
        log_file.write_text('{"task_id": 1, "status": "success"}\ninvalid json\n{"task_id": 2, "status": "failure"}')
        
        # Should handle gracefully, possibly skipping invalid lines
        result = parse_augmented_log(str(log_file))
        assert isinstance(result, list)
        # Should have at least the valid entries
        assert len(result) >= 1

    def test_get_aggregated_counts_with_mixed_logs(self, tmp_path):
        """Test get_aggregated_counts with mixed success/failure logs."""
        baseline_log = tmp_path / "baseline.jsonl"
        augmented_log = tmp_path / "augmented.jsonl"
        
        baseline_log.write_text('{"task_id": 1, "status": "success"}\n{"task_id": 2, "status": "failure"}')
        augmented_log.write_text('{"task_id": 1, "status": "success"}\n{"task_id": 2, "status": "success"}')
        
        counts = get_aggregated_counts(str(baseline_log), str(augmented_log))
        assert isinstance(counts, dict)
        assert "baseline" in counts
        assert "augmented" in counts