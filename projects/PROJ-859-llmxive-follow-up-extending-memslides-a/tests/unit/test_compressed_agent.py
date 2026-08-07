"""
Unit tests for the CompressedAgent.
"""
import json
import pytest
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_config
from agents.compressed import CompressedAgent

@pytest.fixture
def mock_rules_file(tmp_path):
    """Create a temporary rules file for testing."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    
    rules_data = {
        "rules": [
            {
                "rule_id": "test_rule_1",
                "trace_id": "test_session_1",
                "reconstructed_state": {
                    "slide_count": 10,
                    "has_text": True,
                    "is_saved": True
                }
            },
            {
                "rule_id": "test_rule_2",
                "session_id": "test_session_2",
                "reconstructed_state": {
                    "slide_count": 5,
                    "has_image": True
                }
            }
        ]
    }
    
    rules_file = rules_dir / "global_rules.json"
    with open(rules_file, "w") as f:
        json.dump(rules_data, f)
    
    return rules_dir

def test_load_rules_success(mock_rules_file):
    """Test that CompressedAgent successfully loads rules from a valid file."""
    # Temporarily override config path
    original_config = get_config()
    
    class MockConfig:
        data_processed_path = mock_rules_file.parent
    
    try:
        agent = CompressedAgent(MockConfig())
        assert len(agent._rules) == 2
        assert agent._rules[0]["rule_id"] == "test_rule_1"
    finally:
        pass

def test_load_rules_missing_file(tmp_path):
    """Test that CompressedAgent raises error when rules file is missing."""
    non_existent_path = tmp_path / "non_existent_rules"
    
    class MockConfig:
        data_processed_path = non_existent_path
    
    with pytest.raises(FileNotFoundError):
        CompressedAgent(MockConfig())

def test_apply_rules_matched_trace(mock_rules_file):
    """Test rule application when a matching trace_id is found."""
    class MockConfig:
        data_processed_path = mock_rules_file.parent
    
    agent = CompressedAgent(MockConfig())
    
    trace = {
        "session_id": "test_session_1",
        "final_state": {"slide_count": 99}
    }
    
    result = agent._apply_rules(trace)
    
    assert result["slide_count"] == 10
    assert result["rule_applied"] == "test_rule_1"
    assert result["reconstructed"] is True

def test_apply_rules_matched_session_id(mock_rules_file):
    """Test rule application when a matching session_id is found."""
    class MockConfig:
        data_processed_path = mock_rules_file.parent
    
    agent = CompressedAgent(MockConfig())
    
    trace = {
        "session_id": "test_session_2",
        "final_state": {"slide_count": 99}
    }
    
    result = agent._apply_rules(trace)
    
    assert result["slide_count"] == 5
    assert result["rule_applied"] == "test_rule_2"

def test_apply_rules_no_match_heuristic(mock_rules_file):
    """Test fallback heuristic when no rule matches."""
    class MockConfig:
        data_processed_path = mock_rules_file.parent
    
    agent = CompressedAgent(MockConfig())
    
    trace = {
        "session_id": "unknown_session",
        "final_state": {"slide_count": 5}
    }
    
    result = agent._apply_rules(trace)
    
    assert result["slide_count"] == 4  # Heuristic: base_count - 1
    assert result["rule_applied"] == "heuristic_fallback"
    assert result["reconstructed"] is True

def test_apply_rules_no_final_state(mock_rules_file):
    """Test default state when no final_state is present."""
    class MockConfig:
        data_processed_path = mock_rules_file.parent
    
    agent = CompressedAgent(MockConfig())
    
    trace = {
        "session_id": "unknown_session",
        "final_state": None
    }
    
    result = agent._apply_rules(trace)
    
    assert result["slide_count"] == 0
    assert result["rule_applied"] == "none"
    assert result["reconstructed"] is True

def test_process_trace_returns_latency(mock_rules_file):
    """Test that process_trace returns a valid latency value."""
    class MockConfig:
        data_processed_path = mock_rules_file.parent
    
    agent = CompressedAgent(MockConfig())
    
    trace = {
        "session_id": "test_session_1",
        "final_state": {"slide_count": 10}
    }
    
    result, latency = agent.process_trace(trace)
    
    assert isinstance(latency, float)
    assert latency >= 0
    assert "slide_count" in result