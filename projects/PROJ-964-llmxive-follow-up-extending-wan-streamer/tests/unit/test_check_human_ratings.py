import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.check_human_ratings import (
    check_human_ratings_exist,
    load_human_ratings,
    prepare_assumption_validated_flag,
    update_state_with_human_ratings_check
)
from utils.update_state_yaml import load_state_yaml, save_state_yaml


class TestCheckHumanRatings:
    """Unit tests for T046: Check Human Rating Data."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create necessary directory structure
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        Path("state").mkdir(parents=True, exist_ok=True)
        
        yield
        
        # Cleanup
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_check_human_ratings_exist_missing(self):
        """Test that check returns False when file is missing."""
        exists = check_human_ratings_exist()
        assert exists is False

    def test_check_human_ratings_exist_present(self):
        """Test that check returns True when file exists."""
        # Create a dummy file
        dummy_path = Path("data/raw/human_ratings.json")
        dummy_path.write_text(json.dumps({"dummy": "data"}))
        
        exists = check_human_ratings_exist()
        assert exists is True

    def test_load_human_ratings_missing_file(self):
        """Test that load raises FileNotFoundError when file is missing."""
        with pytest.raises(FileNotFoundError):
            load_human_ratings()

    def test_load_human_ratings_present(self):
        """Test that load returns correct data when file exists."""
        # Create a dummy file
        test_data = {"ratings": [1, 2, 3], "metadata": "test"}
        dummy_path = Path("data/raw/human_ratings.json")
        dummy_path.write_text(json.dumps(test_data))
        
        loaded = load_human_ratings()
        assert loaded == test_data
        assert loaded["ratings"] == [1, 2, 3]

    def test_prepare_assumption_validated_flag(self):
        """Test that the assumption flag is prepared correctly."""
        flag = prepare_assumption_validated_flag()
        
        assert "task_id" in flag
        assert flag["task_id"] == "T046"
        assert "assumption_validated" in flag["reason"] or "missing" in flag["reason"].lower()
        assert flag["status"] == "assumption_validated"
        assert "data/raw/human_ratings.json" in flag["checked_path"]

    def test_update_state_with_human_ratings_found(self):
        """Test state update when human ratings are found."""
        state = {"existing_key": "value"}
        ratings = {"user1": 5.0, "user2": 4.5}
        
        updated = update_state_with_human_ratings_check(state, ratings)
        
        assert "human_ratings_check" in updated
        check_section = updated["human_ratings_check"]
        assert check_section["status"] == "found"
        assert check_section["available_for_t044"] is True
        assert "sample_size" in check_section

    def test_update_state_with_human_ratings_missing(self):
        """Test state update when human ratings are missing."""
        state = {"existing_key": "value"}
        
        updated = update_state_with_human_ratings_check(state, None)
        
        assert "human_ratings_check" in updated
        check_section = updated["human_ratings_check"]
        assert check_section["status"] == "missing"
        assert check_section["assumption_validated"] is True
        assert check_section["available_for_t044"] is False
        assert "Assumption Validated" in check_section["message"]

    def test_load_invalid_json(self):
        """Test that load raises JSONDecodeError for invalid JSON."""
        invalid_path = Path("data/raw/human_ratings.json")
        invalid_path.write_text("not valid json {{{")
        
        with pytest.raises(json.JSONDecodeError):
            load_human_ratings()