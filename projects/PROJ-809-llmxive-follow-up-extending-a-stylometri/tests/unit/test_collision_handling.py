import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from data_ingestion import generate_collision_report, update_state_with_collision_status
from utils import load_json
from update_state import load_state, save_state

# Mock state file path for testing
MOCK_STATE_PATH = Path(__file__).resolve().parent.parent.parent / "state" / "test_state.yaml"

@pytest.fixture
def mock_state_dir(tmp_path):
    """Create a temporary state directory."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    # Create a minimal initial state file
    initial_state = {
        "project": "PROJ-809-llmxive-followup",
        "analysis": {}
    }
    import yaml
    with open(state_dir / "PROJ-809-llmxive-followup.yaml", 'w') as f:
        yaml.dump(initial_state, f)
    return state_dir

def test_generate_collision_report_empty():
    """Test report generation with no collisions."""
    report = generate_collision_report([], total_authors=20)
    assert report["status"] == "clean"
    assert report["count_exceeding_threshold"] == 0
    assert report["names_exceeding_threshold"] == []

def test_generate_collision_report_with_collisions():
    """Test report generation with collisions."""
    names = ["Author A", "Author B"]
    report = generate_collision_report(names, total_authors=22)
    assert report["status"] == "warning"
    assert report["count_exceeding_threshold"] == 2
    assert "Author A" in report["names_exceeding_threshold"]

def test_update_state_with_collision_status_clean(mock_state_dir):
    """Test state update when no collisions exist."""
    # Mock the state loading to use our temp file
    with patch('data_ingestion.STATE_FILE_PATH', mock_state_dir / "PROJ-809-llmxive-followup.yaml"):
        report = generate_collision_report([], total_authors=20)
        update_state_with_collision_status(report)
        
        state = load_state(mock_state_dir / "PROJ-809-llmxive-followup.yaml")
        assert state["analysis"]["manual_review"] is False
        assert state["analysis"]["status"] == "clean"

def test_update_state_with_collision_status_warning(mock_state_dir):
    """Test state update when collisions exist but not critical."""
    with patch('data_ingestion.STATE_FILE_PATH', mock_state_dir / "PROJ-809-llmxive-followup.yaml"):
        report = generate_collision_report(["Author X"], total_authors=21)
        update_state_with_collision_status(report)
        
        state = load_state(mock_state_dir / "PROJ-809-llmxive-followup.yaml")
        assert state["analysis"]["manual_review"] is True
        assert state["analysis"]["status"] == "warning"
        assert state["analysis"]["collision_count"] == 1

def test_update_state_with_collision_status_fatal(mock_state_dir):
    """Test that a fatal error is raised when critical threshold is exceeded."""
    # Set critical threshold to a low number for testing
    with patch('data_ingestion.CRITICAL_COLLISION_THRESHOLD', 2):
        with patch('data_ingestion.STATE_FILE_PATH', mock_state_dir / "PROJ-809-llmxive-followup.yaml"):
            # Create a report with 2 collisions (>= critical threshold)
            report = generate_collision_report(["Author A", "Author B"], total_authors=22)
            report["count_exceeding_threshold"] = 2 # Force it to be 2
            
            with pytest.raises(RuntimeError) as excinfo:
                update_state_with_collision_status(report)
            
            assert "CRITICAL FAILURE" in str(excinfo.value)
            assert "2 authors exceed" in str(excinfo.value)
