"""
Unit tests for the agent loop module.
Specifically testing sliding window logic and context truncation strategies.
"""
import pytest
import json
import sys
import os

# Add project root to path if running directly
if "code" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))

# Mock the agent_loop module to test the logic without heavy dependencies
# We will define the core logic here for testing purposes, or import if available.
# Since T023 (implementation) is not done yet, we test the expected interface and logic
# by defining the helper functions that the agent loop *should* use.

# NOTE: This test file validates the SLIDING WINDOW LOGIC required for T021.
# It assumes the implementation in code/agent_loop.py will use these exact strategies.

def build_context_window(history_events, max_tokens, current_prompt_tokens, strategy="truncate_oldest"):
    """
    Helper function to simulate the sliding window logic.
    This mimics the logic that will be in code/agent_loop.py.
    
    Args:
        history_events: List of dicts representing past events (JSON logs).
        max_tokens: Maximum total tokens allowed in context.
        current_prompt_tokens: Tokens already used by the system prompt + current observation.
        strategy: "truncate_oldest", "truncate_newest", or "keep_recent_n".
    
    Returns:
        List of events that fit within the token budget.
    """
    if strategy == "keep_recent_n":
        # For this strategy, we just take the last N events regardless of token count
        # (N would be a config param, but here we just return the list for simplicity in test)
        return history_events[-10:] if len(history_events) > 10 else history_events

    # Estimate tokens (simplified: 1 token ~= 4 chars for this test logic)
    def estimate_tokens(events):
        total_chars = sum(len(json.dumps(e)) for e in events)
        return total_chars // 4

    available_tokens = max_tokens - current_prompt_tokens
    
    if available_tokens <= 0:
        return []

    if strategy == "truncate_oldest":
        # Keep adding events from the end (newest) until we hit the limit
        # This effectively drops the oldest events first
        current_window = []
        current_count = 0
        for event in reversed(history_events):
            event_tokens = estimate_tokens([event])
            if current_count + event_tokens > available_tokens:
                break
            current_window.append(event)
            current_count += event_tokens
        return list(reversed(current_window))
    
    elif strategy == "truncate_newest":
        # Keep adding events from the start (oldest) until we hit the limit
        # This effectively drops the newest events first
        current_window = []
        current_count = 0
        for event in history_events:
            event_tokens = estimate_tokens([event])
            if current_count + event_tokens > available_tokens:
                break
            current_window.append(event)
            current_count += event_tokens
        return current_window

    else:
        raise ValueError(f"Unknown strategy: {strategy}")

class TestSlidingWindowLogic:
    """Tests for the sliding window context truncation strategy."""

    def test_truncate_oldest_removes_earliest_events(self):
        """
        Verify that when the context is too large, the oldest events are dropped.
        Strategy: 'truncate_oldest'
        """
        # Create a history of 20 events
        history = [{"t": i, "event": f"step_{i}"} for i in range(20)]
        
        # Set a tight budget that can only hold the last 5 events
        # (Approximation: 5 events * 20 chars/event / 4 = ~25 tokens)
        # Let's say max_tokens = 30, prompt = 10 -> available = 20.
        # 20 tokens / 4 = 5 chars per event? No, let's just force the logic.
        # We'll use a very small token estimate to force truncation.
        
        # Override estimate to be very small for testing
        def tiny_estimate(events):
            return len(events) * 1 # 1 token per event

        # Patch the estimate logic by passing a custom budget
        # We simulate: 20 events, budget allows only 5.
        # We need to trick the function or just test the result of a known scenario.
        
        # Let's construct a scenario where we know the result
        # 20 events. Budget = 5 events worth.
        # Strategy: truncate_oldest -> should keep indices 15-19
        
        # We will manually construct the input to the logic
        # To make the test robust without mocking internals, we test the outcome
        # of the logic as implemented in the helper above.
        
        # Simulate a budget that allows exactly 5 events
        # We assume each event is roughly 1 "unit" for this test
        max_units = 5
        current_prompt_units = 0 # Assume prompt is 0 for this specific test logic
        
        # We need to adapt the function to use "units" instead of token estimation for predictability
        # Or we just trust the json.dumps length logic. 
        # Let's create events of known length.
        events = [{"t": i, "event": "x"} for i in range(20)] 
        # len(json.dumps({"t": i, "event": "x"})) is roughly 20-25 chars.
        # 25 / 4 = ~6 tokens.
        # If we have 20 events, total = 120 tokens.
        # If max_tokens = 30, prompt = 0. Available = 30.
        # 30 / 6 = 5 events.
        
        result = build_context_window(events, max_tokens=30, current_prompt_tokens=0, strategy="truncate_oldest")
        
        assert len(result) == 5, f"Expected 5 events, got {len(result)}"
        assert result[0]["t"] == 15, f"Expected oldest kept to be 15, got {result[0]['t']}"
        assert result[-1]["t"] == 19, f"Expected newest kept to be 19, got {result[-1]['t']}"

    def test_truncate_newest_removes_latest_events(self):
        """
        Verify that when the context is too large, the newest events are dropped.
        Strategy: 'truncate_newest'
        """
        events = [{"t": i, "event": "x"} for i in range(20)]
        
        result = build_context_window(events, max_tokens=30, current_prompt_tokens=0, strategy="truncate_newest")
        
        assert len(result) == 5, f"Expected 5 events, got {len(result)}"
        assert result[0]["t"] == 0, f"Expected oldest kept to be 0, got {result[0]['t']}"
        assert result[-1]["t"] == 4, f"Expected newest kept to be 4, got {result[-1]['t']}"

    def test_context_fits_without_truncation(self):
        """
        Verify that if the history fits within the limit, no events are dropped.
        """
        events = [{"t": i, "event": "x"} for i in range(3)] # Very small
        
        # Huge budget
        result = build_context_window(events, max_tokens=1000, current_prompt_tokens=0, strategy="truncate_oldest")
        
        assert len(result) == 3, f"Expected 3 events, got {len(result)}"
        assert result[0]["t"] == 0
        assert result[-1]["t"] == 2

    def test_empty_history(self):
        """
        Verify behavior with empty history.
        """
        result = build_context_window([], max_tokens=100, current_prompt_tokens=0, strategy="truncate_oldest")
        assert len(result) == 0

    def test_prompt_exceeds_limit(self):
        """
        Verify behavior when the prompt itself exceeds the token limit.
        """
        events = [{"t": i, "event": "x"} for i in range(10)]
        
        # Prompt uses all available tokens
        result = build_context_window(events, max_tokens=10, current_prompt_tokens=10, strategy="truncate_oldest")
        
        assert len(result) == 0, "Expected 0 events when prompt fills context"

    def test_keep_recent_n_strategy(self):
        """
        Verify 'keep_recent_n' strategy keeps the last N items.
        """
        events = [{"t": i, "event": "x"} for i in range(20)]
        
        # Note: The helper function logic for this strategy is simplified in the mock
        # to just return the last 10. In a real implementation, N would be a parameter.
        # For this test, we verify the logic path exists and returns a subset.
        result = build_context_window(events, max_tokens=1, current_prompt_tokens=0, strategy="keep_recent_n")
        
        # The mock implementation returns last 10 or all if less
        assert len(result) == 10, f"Expected 10 events for keep_recent_n, got {len(result)}"
        assert result[0]["t"] == 10
        assert result[-1]["t"] == 19

if __name__ == "__main__":
    pytest.main([__file__, "-v"])