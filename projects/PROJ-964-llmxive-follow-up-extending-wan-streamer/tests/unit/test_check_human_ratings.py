import os
import sys
import json
import pytest
import tempfile
import shutil
from pathlib import Path
import yaml

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.check_human_ratings import (
    check_human_ratings_exist,
    load_human_ratings,
    prepare_assumption_validated_flag,
    update_state_with_human_ratings_check
)

class TestCheckHumanRatings:
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory structure."""
        temp_dir = tempfile.mkdtemp()
        base_path = Path(temp_dir)
        
        # Create necessary directories
        (base_path / "data" / "raw").mkdir(parents=True)
        (base_path / "data" / "metrics").mkdir(parents=True)
        
        yield base_path
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_check_human_ratings_exist_missing(self, temp_project_dir):
        """Test that check_human_ratings_exist returns False when file is missing."""
        result = check_human_ratings_exist(temp_project_dir)
        assert result is False

    def test_check_human_ratings_exist_present(self, temp_project_dir):
        """Test that check_human_ratings_exist returns True when file exists."""
        # Create a dummy human ratings file
        human_ratings_path = temp_project_dir / "data" / "raw" / "human_ratings.json"
        human_ratings_path.write_text(json.dumps({"test": "data"}))
        
        result = check_human_ratings_exist(temp_project_dir)
        assert result is True

    def test_load_human_ratings_missing_raises(self, temp_project_dir):
        """Test that load_human_ratings raises FileNotFoundError when file is missing."""
        with pytest.raises(FileNotFoundError):
            load_human_ratings(temp_project_dir)

    def test_load_human_ratings_present(self, temp_project_dir):
        """Test that load_human_ratings returns data when file exists."""
        # Create a dummy human ratings file
        human_ratings_path = temp_project_dir / "data" / "raw" / "human_ratings.json"
        test_data = {"rating_id": 1, "score": 4.5}
        human_ratings_path.write_text(json.dumps(test_data))
        
        result = load_human_ratings(temp_project_dir)
        assert result == test_data

    def test_prepare_assumption_validated_flag(self):
        """Test that prepare_assumption_validated_flag returns correct structure."""
        result = prepare_assumption_validated_flag("present", "File exists")
        
        assert "status" in result
        assert "reason" in result
        assert result["status"] == "present"
        assert result["reason"] == "File exists"

    def test_update_state_with_human_ratings_check(self, temp_project_dir):
        """Test that update_state_with_human_ratings_check updates state.yaml correctly."""
        state_file = temp_project_dir / "state.yaml"
        
        # Create initial state file
        initial_state = {"existing_key": "existing_value"}
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f)
        
        # Update state
        update_state_with_human_ratings_check(state_file, "missing", "File not found")
        
        # Verify update
        with open(state_file, 'r') as f:
            updated_state = yaml.safe_load(f)
        
        assert "human_ratings_check" in updated_state
        assert updated_state["human_ratings_check"]["status"] == "missing"
        assert updated_state["human_ratings_check"]["reason"] == "File not found"
        assert "existing_key" in updated_state  # Preserve existing data

    def test_prepare_assumption_validated_flag_missing(self):
        """Test prepare_assumption_validated_flag with missing status."""
        result = prepare_assumption_validated_flag("missing", "File not found")
        
        assert result["status"] == "missing"
        assert result["reason"] == "File not found"