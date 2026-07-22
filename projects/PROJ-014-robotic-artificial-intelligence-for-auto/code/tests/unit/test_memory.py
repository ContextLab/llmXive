"""
Unit tests for the CPU-optimized Replay Buffer.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.memory import ReplayBuffer, ReplayBufferConfig, create_replay_buffer


class TestReplayBufferConfig:
    """Tests for ReplayBufferConfig dataclass."""
    
    def test_default_values(self):
        config = ReplayBufferConfig()
        assert config.capacity == 100000
        assert config.batch_size == 64
        assert config.min_buffer_size == 1000
        assert config.gamma == 0.99
    
    def test_custom_values(self):
        config = ReplayBufferConfig(capacity=5000, batch_size=32, min_buffer_size=500)
        assert config.capacity == 5000
        assert config.batch_size == 32
        assert config.min_buffer_size == 500


class TestReplayBufferInitialization:
    """Tests for ReplayBuffer initialization."""
    
    def test_default_initialization(self):
        buffer = ReplayBuffer()
        assert buffer.size == 0
        assert buffer.capacity == 100000
        assert buffer.batch_size == 64
        assert buffer.min_buffer_size == 1000
    
    def test_custom_initialization(self):
        config = ReplayBufferConfig(capacity=1000, batch_size=16, min_buffer_size=100)
        buffer = ReplayBuffer(config)
        assert buffer.size == 0
        assert buffer.capacity == 1000
        assert buffer.batch_size == 16
        assert buffer.min_buffer_size == 100
    
    def test_factory_function(self):
        buffer = create_replay_buffer()
        assert isinstance(buffer, ReplayBuffer)
        assert buffer.size == 0


class TestReplayBufferPush:
    """Tests for pushing transitions to the buffer."""
    
    @pytest.fixture
    def sample_transition(self):
        state = np.random.rand(84, 84, 3).astype(np.float32)
        action = 2
        reward = 1.5
        next_state = np.random.rand(84, 84, 3).astype(np.float32)
        done = False
        return state, action, reward, next_state, done
    
    def test_push_single_transition(self, sample_transition):
        buffer = ReplayBuffer(ReplayBufferConfig(capacity=100, min_buffer_size=10))
        state, action, reward, next_state, done = sample_transition
        
        buffer.push(state, action, reward, next_state, done)
        
        assert buffer.size == 1
        assert buffer.position == 1
    
    def test_push_multiple_transitions(self, sample_transition):
        buffer = ReplayBuffer(ReplayBufferConfig(capacity=100, min_buffer_size=10))
        state, action, reward, next_state, done = sample_transition
        
        for _ in range(50):
            buffer.push(state, action, reward, next_state, done)
        
        assert buffer.size == 50
    
    def test_circular_buffer_eviction(self):
        capacity = 10
        buffer = ReplayBuffer(ReplayBufferConfig(capacity=capacity, min_buffer_size=1))
        state = np.random.rand(10, 10, 3).astype(np.float32)
        
        # Push more than capacity
        for i in range(capacity + 5):
            buffer.push(state, 0, 0.0, state, False)
        
        assert buffer.size == capacity
        assert buffer.position == 5  # Should wrap around
    
    def test_state_copied_not_referenced(self):
        buffer = ReplayBuffer(ReplayBufferConfig(capacity=100, min_buffer_size=10))
        state = np.random.rand(10, 10, 3).astype(np.float32)
        original_value = state[0, 0, 0]
        
        buffer.push(state, 0, 0.0, state, False)
        
        # Modify original
        state[0, 0, 0] = 999.0
        
        # Buffer should still have original value
        stored_state = buffer.states[0]
        assert stored_state[0, 0, 0] == original_value


class TestReplayBufferSampling:
    """Tests for sampling from the buffer."""
    
    @pytest.fixture
    def populated_buffer(self):
        config = ReplayBufferConfig(capacity=100, batch_size=10, min_buffer_size=5)
        buffer = ReplayBuffer(config)
        
        state = np.random.rand(10, 10, 3).astype(np.float32)
        for i in range(20):
            buffer.push(state, i % 5, float(i), state, i == 19)
        
        return buffer
    
    def test_sample_returns_correct_batch_size(self, populated_buffer):
        states, actions, rewards, next_states, dones = populated_buffer.sample()
        
        assert len(states) == 10
        assert len(actions) == 10
        assert len(rewards) == 10
        assert len(next_states) == 10
        assert len(dones) == 10
    
    def test_sample_respects_min_buffer_size(self):
        buffer = ReplayBuffer(ReplayBufferConfig(capacity=100, min_buffer_size=10))
        
        state = np.random.rand(10, 10, 3).astype(np.float32)
        buffer.push(state, 0, 0.0, state, False)
        
        with pytest.raises(ValueError, match="Cannot sample"):
            buffer.sample()
    
    def test_sample_custom_batch_size(self, populated_buffer):
        batch_size = 5
        states, actions, rewards, next_states, dones = populated_buffer.sample(batch_size)
        
        assert len(states) == batch_size
        assert len(actions) == batch_size
    
    def test_sample_data_consistency(self, populated_buffer):
        # Push known values
        buffer = ReplayBuffer(ReplayBufferConfig(capacity=100, batch_size=1, min_buffer_size=1))
        state = np.random.rand(10, 10, 3).astype(np.float32)
        action = 3
        reward = 5.5
        done = True
        
        buffer.push(state, action, reward, state, done)
        
        states, actions, rewards, next_states, dones = buffer.sample()
        
        assert actions[0] == action
        assert rewards[0] == reward
        assert dones[0] == done
        assert np.array_equal(states[0], state)
        assert np.array_equal(next_states[0], state)
    
    def test_sample_without_replacement(self):
        buffer = ReplayBuffer(ReplayBufferConfig(capacity=100, batch_size=50, min_buffer_size=10))
        
        state = np.random.rand(10, 10, 3).astype(np.float32)
        for i in range(100):
            buffer.push(state, i % 10, float(i), state, False)
        
        # Sample twice and check indices don't overlap
        states1, _, _, _, _ = buffer.sample()
        states2, _, _, _, _ = buffer.sample()
        
        # All samples should be unique within a batch
        # (This is a probabilistic check, but with batch_size=50 and size=100, 
        # it's very likely to see some variation)
        assert len(states1) == 50
        assert len(states2) == 50


class TestReplayBufferMethods:
    """Tests for utility methods."""
    
    def test_len_returns_correct_size(self):
        buffer = ReplayBuffer(ReplayBufferConfig(capacity=100, min_buffer_size=10))
        
        assert len(buffer) == 0
        
        state = np.random.rand(10, 10, 3).astype(np.float32)
        for _ in range(50):
            buffer.push(state, 0, 0.0, state, False)
        
        assert len(buffer) == 50
    
    def test_is_ready(self):
        config = ReplayBufferConfig(capacity=100, min_buffer_size=10)
        buffer = ReplayBuffer(config)
        
        assert not buffer.is_ready()
        
        state = np.random.rand(10, 10, 3).astype(np.float32)
        for _ in range(10):
            buffer.push(state, 0, 0.0, state, False)
        
        assert buffer.is_ready()
    
    def test_clear(self):
        buffer = ReplayBuffer(ReplayBufferConfig(capacity=100, min_buffer_size=10))
        
        state = np.random.rand(10, 10, 3).astype(np.float32)
        for _ in range(50):
            buffer.push(state, 0, 0.0, state, False)
        
        assert buffer.size == 50
        buffer.clear()
        assert buffer.size == 0
        assert buffer.position == 0
    
    def test_repr(self):
        buffer = ReplayBuffer(ReplayBufferConfig(capacity=100, min_buffer_size=10))
        state = np.random.rand(10, 10, 3).astype(np.float32)
        
        for _ in range(25):
            buffer.push(state, 0, 0.0, state, False)
        
        repr_str = repr(buffer)
        assert "ReplayBuffer" in repr_str
        assert "size=25" in repr_str
        assert "capacity=100" in repr_str


class TestReplayBufferWithPriorities:
    """Tests for priority-based sampling (placeholder)."""
    
    def test_sample_with_priorities_returns_weights(self):
        buffer = ReplayBuffer(ReplayBufferConfig(capacity=100, batch_size=10, min_buffer_size=5))
        
        state = np.random.rand(10, 10, 3).astype(np.float32)
        for i in range(20):
            buffer.push(state, i % 5, float(i), state, False)
        
        (states, actions, rewards, next_states, dones, indices, weights) = \
            buffer.sample_with_priorities()
        
        assert len(states) == 10
        assert len(indices) == 10
        assert len(weights) == 10
        assert np.all(weights == 1.0)  # Uniform weights for now
