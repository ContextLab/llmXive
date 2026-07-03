"""
Tests for the BaseAgent implementation.
"""

import pytest
import torch
from agent.base_agent import BaseAgent, AgentConfig

def test_agent_initialization():
    """Test that an agent can be initialized."""
    config = AgentConfig(name="TestAgent", temperature=0.7)
    agent = BaseAgent(config)
    
    assert agent.agent_id >= 0
    assert agent.config.name == "TestAgent"
    assert agent.config.temperature == 0.7
    assert len(agent.history) == 0

def test_generate_observation_with_game_id():
    """Test observation generation with a game_id."""
    config = AgentConfig(max_new_tokens=10)
    agent = BaseAgent(config)
    
    observation = agent.generate_observation(game_id=42)
    
    assert isinstance(observation, str)
    assert len(observation) > 0
    assert len(agent.history) == 1
    assert observation in agent.history

def test_generate_observation_without_game_id():
    """Test observation generation without a game_id."""
    config = AgentConfig(max_new_tokens=10)
    agent = BaseAgent(config)
    
    observation = agent.generate_observation()
    
    assert isinstance(observation, str)
    assert len(observation) > 0
    assert len(agent.history) == 1

def test_process_memory_action():
    """Test processing a memory action."""
    agent = BaseAgent()
    
    agent.process_memory_action("STORE: memory_content")
    
    assert len(agent.history) == 1
    assert "action:STORE: memory_content" in agent.history[0]

def test_reset():
    """Test resetting the agent's history."""
    agent = BaseAgent()
    agent.generate_observation(game_id=1)
    agent.process_memory_action("STORE: test")
    
    assert len(agent.history) == 2
    
    agent.reset()
    
    assert len(agent.history) == 0

def test_multiple_agents_unique_ids():
    """Test that multiple agents have unique IDs."""
    agent1 = BaseAgent()
    agent2 = BaseAgent()
    agent3 = BaseAgent()
    
    ids = [agent1.agent_id, agent2.agent_id, agent3.agent_id]
    assert len(set(ids)) == 3, "Agent IDs should be unique"

@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_cuda_device():
    """Test agent initialization with CUDA device."""
    config = AgentConfig(device="cuda")
    agent = BaseAgent(config)
    assert agent.config.device == "cuda"

def test_cpu_device():
    """Test agent initialization with CPU device."""
    config = AgentConfig(device="cpu")
    agent = BaseAgent(config)
    assert agent.config.device == "cpu"
