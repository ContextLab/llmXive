import pytest
from agent.base_agent import BaseAgent, AgentConfig

def test_agent_initialization():
    cfg = AgentConfig(model_name="distilbert-base-uncased", max_length=128)
    agent = BaseAgent(cfg)
    assert agent.config == cfg

def test_agent_generation_is_deterministic():
    cfg = AgentConfig(model_name="distilbert-base-uncased", max_length=128)
    agent = BaseAgent(cfg)
    # Deterministic generation with fixed seed
    output1 = agent.generate("test prompt")
    output2 = agent.generate("test prompt")
    assert output1 == output2
