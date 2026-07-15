"""
Unit tests for the BaseAgent abstract base class and its concrete implementations.
"""
import pytest
from pathlib import Path
import sys
import os

# Ensure the src directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.base_agent import BaseAgent
from typing import List, Dict, Any


class MockAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing purposes."""

    def __init__(self, name: str = "MockAgent", return_patches: List[Dict] = None):
        super().__init__(name)
        self.return_patches = return_patches or []

    def retrieve_memory_patches(
        self,
        all_patches: List[Dict[str, Any]],
        task_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Mock retrieval that returns pre-defined patches."""
        return self.return_patches


class TestBaseAgentInitialization:
    def test_agent_creation(self):
        """Test that an agent can be instantiated with default values."""
        agent = MockAgent(name="TestAgent")
        assert agent.name == "TestAgent"
        assert agent.max_context_tokens == 4096
        assert agent.retrieval_strategy == "default"

    def test_agent_custom_config(self):
        """Test agent creation with custom configuration."""
        config = {"max_tokens": 2048, "custom_param": "value"}
        agent = MockAgent(name="CustomAgent", max_context_tokens=2048, config=config)
        assert agent.name == "CustomAgent"
        assert agent.max_context_tokens == 2048
        assert agent.config == config


class TestBaseAgentRetrieval:
    def test_retrieve_memory_patches_called(self):
        """Test that retrieve_memory_patches is called during execution."""
        mock_patches = [{"content": "test", "metadata": {"timestamp": "1"}}]
        agent = MockAgent(name="TestAgent", return_patches=mock_patches)
        
        result = agent.execute_task(
            task_description="Test task",
            all_patches=[{"content": "ignored"}],
            task_id="123"
        )
        
        assert result["success"] is True
        assert result["patches_used"] == 1
        assert result["task_id"] == "123"


class TestBaseAgentContextBuilding:
    def test_build_context_includes_task(self):
        """Test that the built context includes the task description."""
        agent = MockAgent(name="TestAgent")
        patches = [{"content": "patch1", "metadata": {"timestamp": "t1"}}]
        
        context_str, token_count = agent.build_context(patches, "Do the thing")
        
        assert "Task: Do the thing" in context_str
        assert "patch1" in context_str
        assert token_count > 0

    def test_build_context_empty_patches(self):
        """Test context building with no patches."""
        agent = MockAgent(name="TestAgent")
        
        context_str, token_count = agent.build_context([], "Do the thing")
        
        assert "Task: Do the thing" in context_str
        assert "Memory History" in context_str
        assert token_count > 0


class TestBaseAgentExecution:
    def test_execute_task_success(self):
        """Test successful task execution."""
        agent = MockAgent(name="TestAgent", return_patches=[])
        result = agent.execute_task("Run", [], "task-001")
        
        assert result["success"] is True
        assert "Executed task" in result["output"]
        assert result["context_tokens"] > 0
        assert result["inference_time"] >= 0

    def test_execute_task_logs_error(self):
        """Test that execution failure returns a structured error response."""
        # This test assumes the agent doesn't throw unhandled exceptions
        # The execute_task method catches exceptions and returns success=False
        agent = MockAgent(name="TestAgent", return_patches=[])
        # Force a scenario that might fail if logic was flawed, but here it should succeed
        # We test the error handling path by mocking a failure in a derived class if needed,
        # but for BaseAgent, the try/except block handles it.
        
        # Let's verify the error path by creating a mock that raises an error in retrieval
        class FailingAgent(MockAgent):
            def retrieve_memory_patches(self, all_patches, task_context):
                raise ValueError("Simulated retrieval failure")

        failing_agent = FailingAgent(name="FailingAgent")
        result = failing_agent.execute_task("Run", [], "task-002")
        
        assert result["success"] is False
        assert "Simulated retrieval failure" in result["output"]
        assert result["context_tokens"] == 0


class TestTokenCounting:
    def test_token_counting(self):
        """Test the internal token counting heuristic."""
        agent = MockAgent(name="TestAgent")
        text = "This is a test string with some words."
        count = agent._tokenize_and_count(text)
        
        # Simple whitespace split: "This", "is", "a", "test", "string", "with", "some", "words."
        assert count == 8

    def test_empty_text_count(self):
        """Test token counting for empty string."""
        agent = MockAgent(name="TestAgent")
        count = agent._tokenize_and_count("")
        assert count == 0