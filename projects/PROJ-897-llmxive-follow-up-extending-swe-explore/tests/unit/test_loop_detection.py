"""
Unit tests for deterministic loop detection in the iterative agent.

Tests T047: Verify that query loops are detected correctly and early exit is triggered.
"""
import pytest
from agent.iterative import detect_query_loop, compute_query_hash


class TestQueryHash:
    """Tests for the compute_query_hash function."""
    
    def test_hash_consistency(self):
        """Verify that the same query always produces the same hash."""
        query = "Find all occurrences of function foo"
        hash1 = compute_query_hash(query)
        hash2 = compute_query_hash(query)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest length
    
    def test_hash_uniqueness(self):
        """Verify that different queries produce different hashes."""
        query1 = "Find all occurrences of function foo"
        query2 = "Find all occurrences of function bar"
        assert compute_query_hash(query1) != compute_query_hash(query2)
    
    def test_hash_whitespace_sensitivity(self):
        """Verify that whitespace differences affect the hash."""
        query1 = "find foo"
        query2 = "find  foo"  # Double space
        assert compute_query_hash(query1) != compute_query_hash(query2)


class TestDetectQueryLoop:
    """Tests for the detect_query_loop function."""
    
    def test_empty_history(self):
        """No loop should be detected with an empty history."""
        is_loop, matched = detect_query_loop("current query", [])
        assert is_loop is False
        assert matched is None
    
    def test_exact_match_detection(self):
        """Exact duplicate queries should be detected as a loop."""
        history = ["query 1", "query 2", "query 3"]
        is_loop, matched = detect_query_loop("query 2", history)
        assert is_loop is True
        assert matched == "query 2"
    
    def test_no_loop_when_unique(self):
        """No loop should be detected for a unique query."""
        history = ["query 1", "query 2", "query 3"]
        is_loop, matched = detect_query_loop("new query", history)
        assert is_loop is False
        assert matched is None
    
    def test_lookback_window(self):
        """Only queries within the lookback window should be checked."""
        history = ["old query", "query 1", "query 2", "query 3"]
        # With lookback_window=3, "old query" should not be checked
        is_loop, matched = detect_query_loop("old query", history, lookback_window=3)
        assert is_loop is False
        assert matched is None
        
        # But "query 2" should be detected
        is_loop, matched = detect_query_loop("query 2", history, lookback_window=3)
        assert is_loop is True
        assert matched == "query 2"
    
    def test_single_item_history(self):
        """Loop detection should work with a single-item history."""
        history = ["query 1"]
        is_loop, matched = detect_query_loop("query 1", history)
        assert is_loop is True
        assert matched == "query 1"
        
        is_loop, matched = detect_query_loop("query 2", history)
        assert is_loop is False
        assert matched is None
    
    def test_case_sensitivity(self):
        """Hash comparison is case-sensitive (exact match required)."""
        history = ["Query 1"]
        is_loop, matched = detect_query_loop("query 1", history)
        assert is_loop is False  # Different case means different hash
        assert matched is None
    
    def test_multiple_duplicates(self):
        """Should detect the most recent duplicate in history."""
        history = ["query 1", "query 2", "query 1", "query 3"]
        is_loop, matched = detect_query_loop("query 1", history)
        assert is_loop is True
        # Should match the most recent occurrence
        assert matched == "query 1"


class TestIntegrationScenarios:
    """Integration-style tests for loop detection scenarios."""
    
    def test_agent_loop_scenario_1(self):
        """Simulate a 3-turn agent loop that detects repetition."""
        history = []
        
        # Turn 1: New query
        is_loop, _ = detect_query_loop("Fix import error", history)
        assert is_loop is False
        history.append("Fix import error")
        
        # Turn 2: Reformulated query
        is_loop, _ = detect_query_loop("Fix missing import statement", history)
        assert is_loop is False
        history.append("Fix missing import statement")
        
        # Turn 3: Same as Turn 1 (loop detected)
        is_loop, matched = detect_query_loop("Fix import error", history)
        assert is_loop is True
        assert matched == "Fix import error"
    
    def test_agent_loop_scenario_2(self):
        """Simulate a scenario with no loops."""
        history = []
        
        queries = [
            "Locate function foo",
            "Find definition of foo in module bar",
            "Show implementation of foo in bar.py"
        ]
        
        for query in queries:
            is_loop, matched = detect_query_loop(query, history)
            assert is_loop is False, f"Unexpected loop detected for query: {query}"
            history.append(query)
    
    def test_rapid_repetition_detection(self):
        """Detect immediate repetition (query repeated in next turn)."""
        history = ["query A"]
        is_loop, matched = detect_query_loop("query A", history)
        assert is_loop is True
        assert matched == "query A"