"""
Unit tests for DQN Agent implementation.
Tests T029: Pruned MobileNetV2 backbone DQN agent.
"""

import pytest
import numpy as np
import torch
from pathlib import Path
import tempfile
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from agents.dqn_agent import (
    DQNConfig, 
    PrunedMobileNetBackbone, 
    DQN, 
    DQNAgent, 
    create_dqn_agent
)

@pytest.fixture
def sample_config():
    """Create a minimal config for testing."""
    return DQNConfig(
        input_shape=(84, 84, 3),
        hidden_dim=64,  # Small for testing
        num_filters=16,
        prune_factor=0.3,
        learning_rate=1e-3,
        device="cpu"
    )

@pytest.fixture
def sample_state():
    """Create a sample state tensor."""
    return np.random.rand(84, 84, 3).astype(np.float32)

class TestDQNConfig:
    """Tests for DQNConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = DQNConfig()
        assert config.input_shape == (84, 84, 3)
        assert config.hidden_dim == 512
        assert config.prune_factor == 0.5
        assert config.device == "cpu"
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = DQNConfig(
            input_shape=(64, 64, 1),
            hidden_dim=128,
            prune_factor=0.7
        )
        assert config.input_shape == (64, 64, 1)
        assert config.hidden_dim == 128
        assert config.prune_factor == 0.7

class TestPrunedMobileNetBackbone:
    """Tests for the pruned MobileNet backbone."""
    
    def test_backbone_initialization(self, sample_config):
        """Test backbone initializes without error."""
        backbone = PrunedMobileNetBackbone(
            input_channels=sample_config.input_shape[-1],
            output_dim=sample_config.hidden_dim,
            prune_factor=sample_config.prune_factor
        )
        assert backbone is not None
    
    def test_backbone_forward_pass(self, sample_config):
        """Test forward pass produces correct output shape."""
        backbone = PrunedMobileNetBackbone(
            input_channels=sample_config.input_shape[-1],
            output_dim=sample_config.hidden_dim,
            prune_factor=sample_config.prune_factor
        )
        
        # Create sample input
        x = torch.randn(1, *sample_config.input_shape)
        output = backbone(x)
        
        # Output should be [batch_size, hidden_dim]
        assert output.shape == (1, sample_config.hidden_dim)
    
    def test_pruning_reduces_parameters(self):
        """Test that pruning reduces parameter count."""
        unpruned = PrunedMobileNetBackbone(
            input_channels=3,
            output_dim=64,
            prune_factor=0.0
        )
        
        pruned = PrunedMobileNetBackbone(
            input_channels=3,
            output_dim=64,
            prune_factor=0.5
        )
        
        unpruned_params = sum(p.numel() for p in unpruned.parameters())
        pruned_params = sum(p.numel() for p in pruned.parameters())
        
        assert pruned_params < unpruned_params

class TestDQN:
    """Tests for the DQN model."""
    
    def test_dqn_initialization(self, sample_config):
        """Test DQN model initializes correctly."""
        model = DQN(sample_config)
        assert model is not None
    
    def test_dqn_forward_pass(self, sample_config):
        """Test forward pass produces correct output shape."""
        model = DQN(sample_config)
        
        x = torch.randn(1, *sample_config.input_shape)
        output = model(x)
        
        # Output should be [batch_size, 1] for Q-value
        assert output.shape == (1, 1)
    
    def test_dqn_parameter_count(self, sample_config):
        """Test that model has reasonable parameter count (<1M)."""
        model = DQN(sample_config)
        total_params = sum(p.numel() for p in model.parameters())
        
        # Should be well under 1M for CPU efficiency
        assert total_params < 1_000_000

class TestDQNAgent:
    """Tests for the DQN Agent."""
    
    def test_agent_initialization(self, sample_config):
        """Test agent initializes correctly."""
        agent = DQNAgent(sample_config)
        assert agent is not None
        assert agent.epsilon == sample_config.epsilon_start
    
    def test_select_action_exploration(self, sample_config, sample_state):
        """Test action selection with high epsilon."""
        agent = DQNAgent(sample_config)
        agent.epsilon = 1.0  # Full exploration
        
        action_space = 4
        action = agent.select_action(sample_state, action_space)
        
        # Should be random when epsilon is 1.0
        assert 0 <= action < action_space
    
    def test_select_action_exploitation(self, sample_config, sample_state):
        """Test action selection with low epsilon."""
        agent = DQNAgent(sample_config)
        agent.epsilon = 0.0  # Full exploitation
        
        action_space = 4
        # Run multiple times to ensure deterministic behavior
        actions = [agent.select_action(sample_state, action_space) for _ in range(10)]
        
        # All actions should be the same when epsilon is 0.0
        assert len(set(actions)) == 1
        assert 0 <= actions[0] < action_space
    
    def test_epsilon_decay(self, sample_config):
        """Test epsilon decay over time."""
        agent = DQNAgent(sample_config)
        initial_epsilon = agent.epsilon
        
        # Decay epsilon
        agent.epsilon = max(agent.epsilon_final, agent.epsilon * agent.epsilon_decay)
        
        assert agent.epsilon < initial_epsilon
        assert agent.epsilon >= agent.epsilon_final
    
    def test_save_and_load_checkpoint(self, sample_config, sample_state):
        """Test checkpoint save and load functionality."""
        agent = DQNAgent(sample_config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "test_checkpoint.pt"
            
            # Save checkpoint
            agent.save_checkpoint(checkpoint_path, episode=10)
            assert checkpoint_path.exists()
            
            # Create new agent and load
            new_agent = DQNAgent(sample_config)
            new_agent.load_checkpoint(checkpoint_path)
            
            # Verify loaded state
            assert new_agent.step_count == agent.step_count
            assert new_agent.epsilon == agent.epsilon
    
    def test_model_size(self, sample_config):
        """Test model size is reasonable."""
        agent = DQNAgent(sample_config)
        size_mb = agent.get_model_size_mb()
        
        # Should be small enough for CPU training
        assert size_mb < 50.0  # Less than 50MB

class TestCreateDQNAgent:
    """Tests for the factory function."""
    
    def test_create_agent(self, sample_config):
        """Test factory function creates agent correctly."""
        agent = create_dqn_agent(sample_config)
        assert isinstance(agent, DQNAgent)
    
    def test_create_agent_default_config(self):
        """Test factory function works with default config."""
        agent = create_dqn_agent()
        assert isinstance(agent, DQNAgent)