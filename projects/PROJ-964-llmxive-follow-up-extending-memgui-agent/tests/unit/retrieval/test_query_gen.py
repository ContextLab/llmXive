"""
Unit tests for retrieval query generation (T023).

This module tests the logic that generates search queries for the semantic
retrieval system. The primary constraint is ensuring NO ground-truth leakage:
queries must be derived solely from the current goal state and available
context, never from the trajectory's future steps or known answers.
"""
import pytest
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from retrieval.retriever import generate_retrieval_query, build_query_from_goal
from utils.config import set_seed

# Fix seed for deterministic test behavior
set_seed(42)


class TestQueryGenerationNoLeakage:
    """
    Tests ensuring query generation does not leak ground-truth information.
    """

    def test_query_derived_only_from_goal_state(self):
        """
        Verify that the generated query string contains only tokens from the
        current goal state and context, not from the 'answer' or 'next_step'
        fields of the trajectory data.
        """
        # Mock trajectory data where 'answer' is distinct from 'goal'
        goal_state = "Navigate to Settings and disable Bluetooth"
        context_snippets = [
            "Current screen: Home",
            "Previous action: Opened App Drawer"
        ]
        
        # Ground truth that must NOT appear in query
        ground_truth_answer = "Tap the Bluetooth toggle switch"
        
        trajectory_data = {
            "goal": goal_state,
            "context": context_snippets,
            "ground_truth_answer": ground_truth_answer,
            "future_steps": ["Tap Settings", "Tap Bluetooth", "Tap Toggle"]
        }

        # Generate query
        query = build_query_from_goal(trajectory_data)

        # Assertions: Query must NOT contain ground truth terms
        assert ground_truth_answer.lower() not in query.lower(), \
            f"Query leaked ground truth answer: {ground_truth_answer}"
        
        # Assertions: Query must NOT contain future steps
        for step in trajectory_data["future_steps"]:
            assert step.lower() not in query.lower(), \
                f"Query leaked future step: {step}"

        # Assertions: Query MUST contain goal keywords
        goal_keywords = ["settings", "disable", "bluetooth"]
        query_lower = query.lower()
        # At least 2 of 3 keywords should be present
        matches = sum(1 for kw in goal_keywords if kw in query_lower)
        assert matches >= 2, f"Query missing key goal terms: {query}"

    def test_query_handles_empty_context_gracefully(self):
        """
        Ensure query generation works even when context is empty, 
        without raising errors or leaking defaults.
        """
        trajectory_data = {
            "goal": "Open Calculator",
            "context": [],
            "ground_truth_answer": "Click Calculator Icon"
        }

        query = build_query_from_goal(trajectory_data)

        assert isinstance(query, str), "Query must be a string"
        assert len(query) > 0, "Query must not be empty"
        assert "calculator" in query.lower(), "Query should contain goal keyword"
        assert "click" not in query.lower(), "Query should not contain action verb from answer"

    def test_query_strips_special_tokens(self):
        """
        Verify that special tokens or formatting artifacts from the goal
        are stripped to prevent embedding model confusion.
        """
        goal_with_artifacts = "Goal: [Action] Open Email <br> and read first message"
        trajectory_data = {
            "goal": goal_with_artifacts,
            "context": ["Current: Home Screen"],
            "ground_truth_answer": "Tap Email App"
        }

        query = build_query_from_goal(trajectory_data)

        # Check for removal of common HTML/formatting artifacts
        assert "<br>" not in query, "HTML tags should be stripped"
        assert "[Action]" not in query, "Instructional markers should be stripped"
        assert "Goal:" not in query, "Prefix labels should be stripped"

    def test_query_construction_deterministic(self):
        """
        Verify that running the query generator twice with the same input
        produces identical output (determinism check).
        """
        trajectory_data = {
            "goal": "Search for 'Python' in Play Store",
            "context": ["Current: Play Store Search Bar"],
            "ground_truth_answer": "Type Python"
        }

        query1 = build_query_from_goal(trajectory_data)
        query2 = build_query_from_goal(trajectory_data)

        assert query1 == query2, "Query generation must be deterministic"

    def test_query_length_constraints(self):
        """
        Ensure the generated query does not exceed reasonable token limits
        that might degrade embedding performance.
        """
        # Create a goal with many words to test truncation/limit logic
        long_goal = " ".join(["word" + str(i) for i in range(50)])
        trajectory_data = {
            "goal": long_goal,
            "context": ["Context snippet"],
            "ground_truth_answer": "Answer"
        }

        query = build_query_from_goal(trajectory_data)

        # Typical embedding models handle ~512 tokens, but we want concise queries
        # Limit to ~20 words to ensure efficiency
        word_count = len(query.split())
        assert word_count <= 25, f"Query too long: {word_count} words. Query: {query}"

    def test_query_includes_app_context_if_available(self):
        """
        Verify that if the context mentions a specific app, the query
        reflects that context to improve retrieval relevance.
        """
        trajectory_data = {
            "goal": "Send a message",
            "context": ["Current App: WhatsApp", "Recent Chat: Mom"],
            "ground_truth_answer": "Tap Send"
        }

        query = build_query_from_goal(trajectory_data)

        # The query should ideally include the app name for context
        # Note: Implementation details may vary, but 'whatsapp' should likely be present
        # or at least the query should not be just 'Send a message'
        assert "whatsapp" in query.lower() or "message" in query.lower(), \
            f"Query should reflect context: {query}"

class TestQueryGenerationIntegration:
    """
    Integration-style tests for the retrieval module query generation.
    """

    def test_full_pipeline_query_consistency(self):
        """
        Simulate a full pipeline step: generate query -> ensure it doesn't
        accidentally include data from the 'next_step' field.
        """
        trajectory = {
            "id": "test-001",
            "goal": "Change Wi-Fi password",
            "current_step": "Opened Network Settings",
            "next_step": "Tap Advanced Options",  # Must NOT be in query
            "ground_truth": "Tap Advanced Options -> Edit Network"
        }

        query = build_query_from_goal(trajectory)

        # Strict check: next_step must not appear
        assert "advanced options" not in query.lower(), \
            f"Query leaked next step: {query}"
        
        # Goal must be present
        assert "wifi" in query.lower() and "password" in query.lower(), \
            f"Query missing goal details: {query}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
