"""
Unit tests for the AugmentedAgent.
Verifies signature matching logic (exact vs regex) and recovery triggering.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust import path for testing within the project structure
import sys
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from agents.augmented import AugmentedAgent
from utils.config import get_path

class TestAugmentedAgent:
    
    def setup_method(self):
        """Create a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_derived = Path(self.temp_dir) / "data" / "derived"
        self.data_derived.mkdir(parents=True)
        
        # Create a mock signatures file
        self.signatures = {
            "exact_error": {
                "pattern": "ERROR: exact_match",
                "recovery_strategy": "replan"
            },
            "wildcard_error": {
                "pattern": "ERROR: timeout_*",
                "recovery_strategy": "retry"
            }
        }
        self.signatures_path = self.data_derived / "failure_signatures.json"
        with open(self.signatures_path, 'w') as f:
            json.dump(self.signatures, f)
        
        # Mock the config to point to our temp directory
        self.patcher = patch('agents.augmented.get_path')
        self.mock_get_path = self.patcher.start()
        
        def mock_get_path(key):
            if key == "failure_signatures":
                return self.signatures_path
            elif key == "data_logs":
                return Path(self.temp_dir) / "data" / "logs"
            elif key == "data_derived":
                return self.data_derived
            elif key == "augmented_log":
                return Path(self.temp_dir) / "data" / "logs" / "augmented_execution.jsonl"
            else:
                # Fallback for other paths needed by config
                return Path(self.temp_dir) / "data" / "logs"
        
        self.mock_get_path.side_effect = mock_get_path

    def teardown_method(self):
        """Clean up temporary directory."""
        self.patcher.stop()
        shutil.rmtree(self.temp_dir)

    def test_exact_match_detection(self):
        """Test that exact match triggers recovery."""
        agent = AugmentedAgent()
        
        # Test data with exact match
        task = {"task_id": "1", "instruction": "Test task"}
        
        # Mock the _simulate_llm_call to return the exact error pattern
        with patch.object(agent, '_simulate_llm_call', return_value="ERROR: exact_match"):
            result = agent.execute_task(task)
        
        assert result["signature_detected"] is True
        assert result["signature_pattern"] == "exact_error"
        assert result["recovery_info"] is not None
        assert result["status"] == "recovered"

    def test_exact_match_failure(self):
        """Test that partial match does NOT trigger recovery for exact patterns."""
        agent = AugmentedAgent()
        
        task = {"task_id": "2", "instruction": "Test task"}
        
        # Return a string that contains the pattern but is not an exact match
        with patch.object(agent, '_simulate_llm_call', return_value="Something ERROR: exact_match happened"):
            result = agent.execute_task(task)
        
        # Should NOT detect signature because exact match is required for non-wildcards
        assert result["signature_detected"] is False
        assert result["signature_pattern"] is None
        assert result["recovery_info"] is None
        assert result["status"] == "completed"

    def test_wildcard_match_detection(self):
        """Test that wildcard patterns trigger recovery with regex matching."""
        agent = AugmentedAgent()
        
        task = {"task_id": "3", "instruction": "Test task"}
        
        # Test various matches for "ERROR: timeout_*"
        test_cases = [
            "ERROR: timeout_123",
            "ERROR: timeout_connection_lost",
            "ERROR: timeout" # Should NOT match as * is not empty in standard regex unless specified, but our conversion '.*' matches empty too. 
            # Wait: "timeout_*" -> "timeout_.*" matches "timeout_" (empty suffix).
            # Let's test a clear match.
        ]
        
        for output in ["ERROR: timeout_123", "ERROR: timeout_connection"]:
            with patch.object(agent, '_simulate_llm_call', return_value=output):
                result = agent.execute_task(task)
            assert result["signature_detected"] is True
            assert result["signature_pattern"] == "wildcard_error"

    def test_no_match(self):
        """Test that unknown errors do not trigger recovery."""
        agent = AugmentedAgent()
        
        task = {"task_id": "4", "instruction": "Test task"}
        
        with patch.object(agent, '_simulate_llm_call', return_value="ERROR: unknown_failure"):
            result = agent.execute_task(task)
        
        assert result["signature_detected"] is False
        assert result["recovery_info"] is None

    def test_recovery_strategy_preserved(self):
        """Test that the correct recovery strategy is used based on signature metadata."""
        agent = AugmentedAgent()
        
        task = {"task_id": "5", "instruction": "Test task"}
        
        with patch.object(agent, '_simulate_llm_call', return_value="ERROR: timeout_123"):
            result = agent.execute_task(task)
        
        assert result["recovery_info"]["recovery_action"] == "retry"
        
        # Test with exact match (replan)
        with patch.object(agent, '_simulate_llm_call', return_value="ERROR: exact_match"):
            result = agent.execute_task(task)
        
        assert result["recovery_info"]["recovery_action"] == "replan"