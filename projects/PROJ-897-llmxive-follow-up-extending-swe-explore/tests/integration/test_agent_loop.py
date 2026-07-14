"""
Integration test for agent loop termination conditions.

Tests:
1. Maximum turn limit enforcement (FR-003: 3 turns)
2. Loop detection (repeated query detection)

This test simulates the iterative agent loop behavior without requiring
a live LLM. It uses mock responses to verify that the termination
logic works correctly.
"""
import json
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock, patch

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.agent.iterative import run_iterative_agent
from code.agent.static_analysis import run_static_analysis
from code.config import get_config_summary


class MockStaticAnalyzer:
    """Mock static analyzer that returns deterministic signals."""
    
    def __init__(self, signals: List[Dict[str, Any]]):
        self.signals = signals
        self.call_count = 0
    
    def analyze(self, code: str, issue_desc: str) -> List[Dict[str, Any]]:
        """Return pre-defined signals based on call count."""
        self.call_count += 1
        if self.call_count <= len(self.signals):
            return self.signals[self.call_count - 1]
        return []  # No errors after defined signals


class MockQueryReformulator:
    """Mock query reformulator that tracks query history."""
    
    def __init__(self, responses: List[str]):
        self.responses = responses
        self.query_history: List[str] = []
        self.call_count = 0
    
    def reformulate(self, original_query: str, error_signals: List[Dict], context: str) -> str:
        """Return pre-defined reformulated queries."""
        self.call_count += 1
        self.query_history.append(original_query)
        
        if self.call_count <= len(self.responses):
            return self.responses[self.call_count - 1]
        # Fallback: repeat last response
        return self.responses[-1] if self.responses else original_query


def test_max_turn_limit_enforcement():
    """Test that the agent stops after MAX_TURNS (3) even without resolution."""
    
    # Prepare a mock issue
    issue = {
        "issue_id": "test_max_turns_001",
        "code": "def foo():\n    x = undefined_var\n    return x",
        "description": "Fix undefined variable",
        "ground_truth_lines": [2]
    }
    
    # Mock signals that always produce errors (no resolution)
    mock_signals = [
        [{"type": "undefined_variable", "message": "Name 'undefined_var' is not defined"}],
        [{"type": "undefined_variable", "message": "Name 'undefined_var' is not defined"}],
        [{"type": "undefined_variable", "message": "Name 'undefined_var' is not defined"}],
        [{"type": "undefined_variable", "message": "Name 'undefined_var' is not defined"}],
    ]
    
    # Mock queries that keep changing (no loop)
    mock_queries = [
        "Fix undefined variable in line 2",
        "Import the missing module for undefined_var",
        "Define undefined_var before usage",
        "Attempt 4: Define undefined_var",
        "Attempt 5: Define undefined_var",
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "agent_log.json"
        
        # Run the agent with mocked dependencies
        with patch('code.agent.iterative.run_static_analysis', MockStaticAnalyzer(mock_signals).analyze), \
             patch('code.agent.iterative.reformulate_query', MockQueryReformulator(mock_queries).reformulate):
            
            # We need to patch the actual functions, not just create objects
            analyzer = MockStaticAnalyzer(mock_signals)
            reformulator = MockQueryReformulator(mock_queries)
            
            result = run_iterative_agent(
                issue=issue,
                static_analyzer=analyzer,
                reformulator=reformulator,
                max_turns=3,
                output_path=str(output_path)
            )
            
            # Verify termination by max turns
            assert result["turns_executed"] == 3, f"Expected 3 turns, got {result['turns_executed']}"
            assert result["termination_reason"] == "max_turns_reached", \
                f"Expected 'max_turns_reached', got {result['termination_reason']}"
            assert len(result["query_history"]) == 3, \
                f"Expected 3 queries in history, got {len(result['query_history'])}"
            
            # Verify log file was created and is valid JSON
            assert output_path.exists(), "Agent log file was not created"
            with open(output_path, 'r') as f:
                log_data = json.load(f)
            
            assert log_data["issue_id"] == issue["issue_id"]
            assert log_data["turns_executed"] == 3


def test_loop_detection_termination():
    """Test that the agent stops when it detects repeated queries."""
    
    # Prepare a mock issue
    issue = {
        "issue_id": "test_loop_detection_001",
        "code": "def bar():\n    y = undefined_y\n    return y",
        "description": "Fix undefined variable",
        "ground_truth_lines": [2]
    }
    
    # Mock signals
    mock_signals = [
        [{"type": "undefined_variable", "message": "Name 'undefined_y' is not defined"}],
        [{"type": "undefined_variable", "message": "Name 'undefined_y' is not defined"}],
        [{"type": "undefined_variable", "message": "Name 'undefined_y' is not defined"}],
    ]
    
    # Mock queries where the 3rd query repeats the 1st (loop detected)
    mock_queries = [
        "Fix undefined variable in line 2",
        "Try importing the missing module",
        "Fix undefined variable in line 2",  # Repeat of query 1
        "Attempt 4: Try something else",
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "agent_log_loop.json"
        
        analyzer = MockStaticAnalyzer(mock_signals)
        reformulator = MockQueryReformulator(mock_queries)
        
        result = run_iterative_agent(
            issue=issue,
            static_analyzer=analyzer,
            reformulator=reformulator,
            max_turns=3,
            output_path=str(output_path)
        )
        
        # Verify termination by loop detection
        assert result["turns_executed"] == 3, f"Expected 3 turns, got {result['turns_executed']}"
        assert result["termination_reason"] == "loop_detected", \
            f"Expected 'loop_detected', got {result['termination_reason']}"
        assert len(result["query_history"]) == 3, \
            f"Expected 3 queries in history, got {len(result['query_history'])}"
        
        # Verify the log contains loop detection info
        assert "loop_detection" in result, "Loop detection info missing from result"
        assert result["loop_detection"]["detected"] is True


def test_early_termination_on_success():
    """Test that the agent stops early when a solution is found."""
    
    # Prepare a mock issue
    issue = {
        "issue_id": "test_success_001",
        "code": "def baz():\n    z = undefined_z\n    return z",
        "description": "Fix undefined variable",
        "ground_truth_lines": [2]
    }
    
    # Mock signals: error on first turn, no errors on second
    mock_signals = [
        [{"type": "undefined_variable", "message": "Name 'undefined_z' is not defined"}],
        [],  # No errors after fix
        [{"type": "undefined_variable", "message": "Name 'undefined_z' is not defined"}],
    ]
    
    mock_queries = [
        "Fix undefined variable in line 2",
        "Verify the fix works",
        "Attempt 3: Should not reach here",
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "agent_log_success.json"
        
        analyzer = MockStaticAnalyzer(mock_signals)
        reformulator = MockQueryReformulator(mock_queries)
        
        result = run_iterative_agent(
            issue=issue,
            static_analyzer=analyzer,
            reformulator=reformulator,
            max_turns=3,
            output_path=str(output_path)
        )
        
        # Verify early termination
        assert result["turns_executed"] == 2, f"Expected 2 turns, got {result['turns_executed']}"
        assert result["termination_reason"] == "success", \
            f"Expected 'success', got {result['termination_reason']}"
        assert len(result["query_history"]) == 2, \
            f"Expected 2 queries in history, got {len(result['query_history'])}"


if __name__ == "__main__":
    # Run tests manually if executed as script
    print("Running max turn limit test...")
    test_max_turn_limit_enforcement()
    print("✓ Max turn limit test passed")
    
    print("Running loop detection test...")
    test_loop_detection_termination()
    print("✓ Loop detection test passed")
    
    print("Running early termination test...")
    test_early_termination_on_success()
    print("✓ Early termination test passed")
    
    print("\nAll integration tests passed!")