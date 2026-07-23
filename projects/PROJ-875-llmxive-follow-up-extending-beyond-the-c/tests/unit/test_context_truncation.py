"""
Unit tests for context window truncation logic in code/agent_loop.py (T025).

Tests verify that the TextAgent correctly implements a sliding window
that keeps only the last N events and drops older ones.
"""
import pytest
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agent_loop import TextAgent, AgentConfig


class TestContextTruncation:
    """Test suite for context window truncation functionality."""

    @pytest.fixture
    def agent_config(self):
        """Create agent config with specific window size."""
        return AgentConfig(
            max_context_events=50,
            max_steps=1000,
            temperature=0.0
        )

    @pytest.fixture
    def agent(self, agent_config):
        """Create a TextAgent instance."""
        return TextAgent(agent_config)

    def test_context_window_size_limit(self, agent):
        """Verify that context window does not exceed configured size."""
        # Generate more events than window size
        num_events = 200
        window_size = 50

        for i in range(num_events):
            event = {
                "step": i,
                "action": f"move_{i}",
                "observation": f"Obs {i}"
            }
            agent.step(event)

        context = agent.get_context_window()
        assert len(context) == window_size, \
            f"Context window size {len(context)} exceeds limit {window_size}"

    def test_oldest_events_dropped(self, agent):
        """Verify that oldest events are dropped when window is full."""
        num_events = 100
        window_size = 50

        # Generate events
        for i in range(num_events):
            event = {
                "step": i,
                "action": f"move_{i}",
                "observation": f"Obs {i}"
            }
            agent.step(event)

        context = agent.get_context_window()
        
        # The oldest event in context should be step 50 (0-indexed: 50-99)
        oldest_step = context[0]["step"]
        expected_oldest = num_events - window_size  # 100 - 50 = 50
        
        assert oldest_step == expected_oldest, \
            f"Oldest event in context is step {oldest_step}, expected {expected_oldest}"

    def test_newest_events_retained(self, agent):
        """Verify that newest events are retained in context."""
        num_events = 100
        window_size = 50

        for i in range(num_events):
            event = {
                "step": i,
                "action": f"move_{i}",
                "observation": f"Obs {i}"
            }
            agent.step(event)

        context = agent.get_context_window()
        
        # The newest event should be the last one generated
        newest_step = context[-1]["step"]
        expected_newest = num_events - 1  # 99
        
        assert newest_step == expected_newest, \
            f"Newest event in context is step {newest_step}, expected {expected_newest}"

    def test_sliding_window_behavior(self, agent):
        """Verify sliding window behavior: as new events come, old ones leave."""
        window_size = 10
        
        # First batch: events 0-9
        for i in range(10):
            agent.step({"step": i, "action": f"move_{i}", "observation": f"Obs {i}"})
        
        context = agent.get_context_window()
        assert len(context) == 10
        assert context[0]["step"] == 0
        assert context[-1]["step"] == 9

        # Second batch: events 10-19
        for i in range(10, 20):
            agent.step({"step": i, "action": f"move_{i}", "observation": f"Obs {i}"})
        
        context = agent.get_context_window()
        assert len(context) == 10
        # Should now contain events 10-19
        assert context[0]["step"] == 10
        assert context[-1]["step"] == 19

    def test_context_under_limit(self, agent):
        """Verify behavior when total events < window size."""
        num_events = 30
        window_size = 50

        for i in range(num_events):
            agent.step({"step": i, "action": f"move_{i}", "observation": f"Obs {i}"})

        context = agent.get_context_window()
        assert len(context) == num_events, \
            f"Context size {len(context)} should equal total events {num_events}"
        assert context[0]["step"] == 0
        assert context[-1]["step"] == num_events - 1

    def test_empty_context_initially(self, agent):
        """Verify context is empty before any events."""
        context = agent.get_context_window()
        assert len(context) == 0, "Context should be empty initially"

    def test_context_preserves_event_order(self, agent):
        """Verify that events in context maintain chronological order."""
        num_events = 100
        
        for i in range(num_events):
            agent.step({"step": i, "action": f"move_{i}", "observation": f"Obs {i}"})

        context = agent.get_context_window()
        
        # Verify chronological order
        for i in range(len(context) - 1):
            assert context[i]["step"] < context[i + 1]["step"], \
                "Events in context are not in chronological order"

    def test_large_window_size(self, agent_config):
        """Test with a larger window size."""
        agent_config.max_context_events = 200
        agent = TextAgent(agent_config)
        
        num_events = 300
        for i in range(num_events):
            agent.step({"step": i, "action": f"move_{i}", "observation": f"Obs {i}"})

        context = agent.get_context_window()
        assert len(context) == 200
        assert context[0]["step"] == 100  # 300 - 200 = 100
        assert context[-1]["step"] == 299

    def test_single_event_window(self, agent_config):
        """Test with window size of 1."""
        agent_config.max_context_events = 1
        agent = TextAgent(agent_config)
        
        for i in range(5):
            agent.step({"step": i, "action": f"move_{i}", "observation": f"Obs {i}"})

        context = agent.get_context_window()
        assert len(context) == 1
        assert context[0]["step"] == 4  # Only the last event