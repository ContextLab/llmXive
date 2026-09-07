"""
Unit tests for the split_dataset module.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.analysis.split_dataset import (
    load_llm_detections,
    split_by_llm_flag,
    save_split_datasets,
    run_split_analysis,
    main
)


class TestSplitDataset:
    """Test cases for split_dataset functions."""

    @pytest.fixture
    def sample_detections(self):
        """Provide sample detection data for testing."""
        return [
            {
                "pr_id": "PR-001",
                "file_path": "src/main.py",
                "llm_code_flag": False,
                "confidence": "high"
            },
            {
                "pr_id": "PR-002",
                "file_path": "src/utils.py",
                "llm_code_flag": True,
                "confidence": "medium"
            },
            {
                "pr_id": "PR-003",
                "file_path": "src/test.py",
                "llm_code_flag": False,
                "confidence": "high"
            },
            {
                "pr_id": "PR-004",
                "file_path": "src/core.py",
                "llm_code_flag": True,
                "confidence": "low"
            }
        ]

    @pytest.fixture
    def temp_input_file(self, sample_detections):
        """Create a temporary input JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_detections, f)
            input_path = Path(f.name)
        yield input_path
        input_path.unlink()

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_load_llm_detections_valid(self, temp_input_file, sample_detections):
        """Test loading a valid JSON file."""
        result = load_llm_detections(temp_input_file)
        assert result == sample_detections
        assert len(result) == 4

    def test_load_llm_detections_file_not_found(self):
        """Test loading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_llm_detections(Path("/nonexistent/path/file.json"))

    def test_load_llm_detections_invalid_json(self):
        """Test loading invalid JSON raises JSONDecodeError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            invalid_path = Path(f.name)
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_llm_detections(invalid_path)
        finally:
            invalid_path.unlink()

    def test_split_by_llm_flag(self, sample_detections):
        """Test splitting detections by llm_code_flag."""
        human, llm = split_by_llm_flag(sample_detections)
        
        assert len(human) == 2
        assert len(llm) == 2
        
        # Verify human-written PRs
        human_ids = [r["pr_id"] for r in human]
        assert "PR-001" in human_ids
        assert "PR-003" in human_ids
        
        # Verify LLM-generated PRs
        llm_ids = [r["pr_id"] for r in llm]
        assert "PR-002" in llm_ids
        assert "PR-004" in llm_ids

    def test_split_by_llm_flag_missing_field(self, sample_detections):
        """Test that missing llm_code_flag raises KeyError."""
        invalid_data = sample_detections.copy()
        invalid_data[0].pop("llm_code_flag")
        
        with pytest.raises(KeyError):
            split_by_llm_flag(invalid_data)

    def test_save_split_datasets(self, sample_detections, temp_output_dir):
        """Test saving split datasets to files."""
        human, llm = split_by_llm_flag(sample_detections)
        
        human_path, llm_path = save_split_datasets(human, llm, temp_output_dir)
        
        assert human_path.exists()
        assert llm_path.exists()
        
        # Verify contents
        with open(human_path, 'r') as f:
            saved_human = json.load(f)
        assert len(saved_human) == 2
        
        with open(llm_path, 'r') as f:
            saved_llm = json.load(f)
        assert len(saved_llm) == 2

    def test_run_split_analysis(self, temp_input_file, temp_output_dir):
        """Test the full analysis pipeline."""
        result = run_split_analysis(temp_input_file, temp_output_dir)
        
        assert result["total"] == 4
        assert result["human_written_count"] == 2
        assert result["llm_generated_count"] == 2
        assert Path(result["human_written_path"]).exists()
        assert Path(result["llm_generated_path"]).exists()

    @patch('code.src.analysis.split_dataset.get_paths')
    @patch('code.src.analysis.split_dataset.run_split_analysis')
    @patch('code.src.analysis.split_dataset.get_logger')
    def test_main_success(self, mock_logger, mock_run, mock_get_paths, temp_input_file, temp_output_dir):
        """Test main function successful execution."""
        mock_logger.return_value.info = MagicMock()
        mock_logger.return_value.error = MagicMock()
        
        mock_get_paths.return_value = {
            "derived": temp_output_dir
        }
        
        mock_run.return_value = {
            "total": 10,
            "human_written_count": 5,
            "llm_generated_count": 5,
            "human_written_path": str(temp_output_dir / "human.json"),
            "llm_generated_path": str(temp_output_dir / "llm.json")
        }
        
        # Mock the input file existence
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', MagicMock()):
                result = main()
                
        assert result == 0

    @patch('code.src.analysis.split_dataset.get_paths')
    @patch('code.src.analysis.split_dataset.get_logger')
    def test_main_file_not_found(self, mock_logger, mock_get_paths):
        """Test main function when input file is missing."""
        mock_logger.return_value.info = MagicMock()
        mock_logger.return_value.error = MagicMock()
        
        mock_get_paths.return_value = {
            "derived": Path("/tmp")
        }
        
        # Mock Path.exists to return False
        with patch('pathlib.Path.exists', return_value=False):
            result = main()
            
        assert result == 1
        mock_logger.return_value.error.assert_called()

    @patch('code.src.analysis.split_dataset.get_paths')
    @patch('code.src.analysis.split_dataset.get_logger')
    def test_main_json_error(self, mock_logger, mock_get_paths):
        """Test main function when JSON is invalid."""
        mock_logger.return_value.info = MagicMock()
        mock_logger.return_value.error = MagicMock()
        
        mock_get_paths.return_value = {
            "derived": Path("/tmp")
        }
        
        # Mock Path.exists to return True but raise JSONDecodeError on open
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', side_effect=json.JSONDecodeError("Expecting value", "", 0)):
                result = main()
                
        assert result == 1
        mock_logger.return_value.error.assert_called()

    def test_split_empty_list(self):
        """Test splitting an empty list."""
        human, llm = split_by_llm_flag([])
        
        assert len(human) == 0
        assert len(llm) == 0

    def test_split_all_human(self):
        """Test splitting when all records are human-written."""
        data = [
            {"pr_id": "1", "llm_code_flag": False},
            {"pr_id": "2", "llm_code_flag": False}
        ]
        human, llm = split_by_llm_flag(data)
        
        assert len(human) == 2
        assert len(llm) == 0

    def test_split_all_llm(self):
        """Test splitting when all records are LLM-generated."""
        data = [
            {"pr_id": "1", "llm_code_flag": True},
            {"pr_id": "2", "llm_code_flag": True}
        ]
        human, llm = split_by_llm_flag(data)
        
        assert len(human) == 0
        assert len(llm) == 2