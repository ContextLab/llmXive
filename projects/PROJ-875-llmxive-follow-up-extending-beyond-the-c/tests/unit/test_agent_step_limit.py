import pytest
import time
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path if running from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.agent_loop import AgentConfig, AgentState, TextAgent
from code.logger import configure_global_logging

class TestHardStepLimit:
    """
    Tests for T026: Hard step limit to prevent hangs on stuck agents.
    """

    def setup_method(self):
        configure_global_logging()
        self.config = AgentConfig(
            model_name="test-model",
            max_steps=10,
            temperature=0.0
        )

    def test_agent_terminates_at_max_steps(self):
        """
        Verify that the agent stops exactly when current_step reaches max_steps.
        """
        agent = TextAgent(self.config)
        initial_state = AgentState()
        
        result = agent.run(initial_state)

        assert result.is_terminated is True
        assert result.termination_reason == "MAX_STEPS_REACHED"
        assert result.current_step == self.config.max_steps
        assert result.end_time is not None

    def test_agent_does_not_exceed_max_steps(self):
        """
        Verify that the agent never executes a step beyond max_steps.
        """
        # Run with a very small limit
        config = AgentConfig(model_name="test", max_steps=3)
        agent = TextAgent(config)
        
        result = agent.run()

        assert result.current_step == 3
        assert result.termination_reason == "MAX_STEPS_REACHED"

    def test_agent_state_preserved_until_limit(self):
        """
        Verify that event log and mental map are populated correctly before termination.
        """
        config = AgentConfig(model_name="test", max_steps=5)
        agent = TextAgent(config)
        
        result = agent.run()

        # Should have 5 entries in the event log
        assert len(result.event_log) == 5
        assert result.mental_map is not None
        assert result.mental_map.get("step") == 5

    def test_termination_reason_specific(self):
        """
        Verify the specific termination reason string for step limit.
        """
        config = AgentConfig(model_name="test", max_steps=1)
        agent = TextAgent(config)
        
        result = agent.run()

        assert result.termination_reason == "MAX_STEPS_REACHED"
        assert "MAX_STEPS" in result.termination_reason

    def test_zero_step_limit(self):
        """
        Edge case: max_steps=0 should terminate immediately.
        """
        config = AgentConfig(model_name="test", max_steps=0)
        agent = TextAgent(config)
        
        result = agent.run()

        assert result.current_step == 0
        assert result.is_terminated is True
        assert result.termination_reason == "MAX_STEPS_REACHED"
        # Should not have executed any steps
        assert len(result.event_log) == 0