"""
Unit tests for the EvoMem-All agent implementation.
"""
import pytest
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.evomem_all import EvoMemAll


class TestEvoMemAllInitialization:
    """Test cases for EvoMemAll initialization."""

    def test_default_window_size(self):
        """Test that default memory window size is 50."""
        config = {}
        agent = EvoMemAll(config, seed=42)
        assert agent.memory_window_size == 50

    def test_custom_window_size(self):
        """Test that custom memory window size is respected."""
        config = {'memory_window_size': 100}
        agent = EvoMemAll(config, seed=42)
        assert agent.memory_window_size == 100

    def test_seed_configuration(self):
        """Test that seed is properly set."""
        config = {}
        agent = EvoMemAll(config, seed=123)
        assert agent.seed == 123

    def test_variant_name(self):
        """Test that variant name is correctly reported."""
        agent = EvoMemAll({})
        assert agent.get_variant_name() == "EvoMem-All"


class TestEvoMemAllRetrieval:
    """Test cases for context retrieval logic."""

    def test_retrieve_last_n_patches(self):
        """Test that the last N patches are retrieved correctly."""
        config = {'memory_window_size': 3}
        agent = EvoMemAll(config, seed=42)

        # Create a mock memory history with 10 patches
        memory_history = [{'id': i, 'content': f'patch_{i}'} for i in range(10)]

        context, count = agent.retrieve_context(memory_history, {})

        assert count == 3
        assert len(context) == 3
        # Should be the last 3 patches (indices 7, 8, 9)
        assert context[0]['id'] == 7
        assert context[1]['id'] == 8
        assert context[2]['id'] == 9

    def test_retrieve_when_history_smaller_than_window(self):
        """Test retrieval when history is smaller than window size."""
        config = {'memory_window_size': 10}
        agent = EvoMemAll(config, seed=42)

        # Create a mock memory history with only 3 patches
        memory_history = [{'id': i, 'content': f'patch_{i}'} for i in range(3)]

        context, count = agent.retrieve_context(memory_history, {})

        assert count == 3
        assert len(context) == 3
        assert context[0]['id'] == 0
        assert context[2]['id'] == 2

    def test_retrieve_empty_history(self):
        """Test retrieval when memory history is empty."""
        config = {'memory_window_size': 5}
        agent = EvoMemAll(config, seed=42)

        context, count = agent.retrieve_context([], {})

        assert count == 0
        assert len(context) == 0
        assert context == []

    def test_retrieve_single_patch(self):
        """Test retrieval with a single patch in history."""
        config = {'memory_window_size': 5}
        agent = EvoMemAll(config, seed=42)

        memory_history = [{'id': 0, 'content': 'single_patch'}]

        context, count = agent.retrieve_context(memory_history, {})

        assert count == 1
        assert len(context) == 1
        assert context[0]['id'] == 0

    def test_window_size_equals_history_length(self):
        """Test when window size exactly matches history length."""
        config = {'memory_window_size': 5}
        agent = EvoMemAll(config, seed=42)

        memory_history = [{'id': i, 'content': f'patch_{i}'} for i in range(5)]

        context, count = agent.retrieve_context(memory_history, {})

        assert count == 5
        assert len(context) == 5
        # Should retrieve all patches
        assert context[0]['id'] == 0
        assert context[4]['id'] == 4


class TestEvoMemAllExecution:
    """Test cases for task execution."""

    def test_execute_returns_correct_structure(self):
        """Test that execute_task returns a dictionary with expected keys."""
        config = {'memory_window_size': 5}
        agent = EvoMemAll(config, seed=42)

        memory_history = [{'id': i, 'content': f'patch_{i}'} for i in range(10)]

        result = agent.execute_task(
            task_id='test_task_001',
            task_description='Test task description',
            memory_history=memory_history
        )

        expected_keys = [
            'task_id', 'agent_variant', 'context_tokens', 'context_patches',
            'success_status', 'inference_time', 'retrieved_patches'
        ]

        for key in expected_keys:
            assert key in result

        assert result['task_id'] == 'test_task_001'
        assert result['agent_variant'] == 'EvoMem-All'
        assert result['success_status'] is True

    def test_execute_context_count_matches_retrieval(self):
        """Test that context_patches count matches actual retrieved patches."""
        config = {'memory_window_size': 3}
        agent = EvoMemAll(config, seed=42)

        memory_history = [{'id': i, 'content': f'patch_{i}'} for i in range(10)]

        result = agent.execute_task(
            task_id='test_task_002',
            task_description='Test task',
            memory_history=memory_history
        )

        assert result['context_patches'] == 3
        assert len(result['retrieved_patches']) == 3

    def test_execute_with_empty_history(self):
        """Test execution with empty memory history."""
        config = {'memory_window_size': 5}
        agent = EvoMemAll(config, seed=42)

        result = agent.execute_task(
            task_id='test_task_003',
            task_description='Test task',
            memory_history=[]
        )

        assert result['context_patches'] == 0
        assert result['retrieved_patches'] == []
        assert result['context_tokens'] == 0


class TestEvoMemAllTokenCounting:
    """Test cases for token counting estimation."""

    def test_token_count_positive(self):
        """Test that token counting returns positive values."""
        agent = EvoMemAll({})

        text = "This is a test string."
        tokens = agent._count_tokens(text)

        assert tokens > 0

    def test_token_count_empty_string(self):
        """Test token counting with empty string."""
        agent = EvoMemAll({})

        tokens = agent._count_tokens("")

        assert tokens == 1  # Should return at least 1

    def test_token_count_proportional(self):
        """Test that longer strings get more tokens."""
        agent = EvoMemAll({})

        short_text = "short"
        long_text = "This is a much longer string that should result in more tokens."

        short_tokens = agent._count_tokens(short_text)
        long_tokens = agent._count_tokens(long_text)

        assert long_tokens > short_tokens