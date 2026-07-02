"""Basic sanity checks for the BaseAgent implementation."""
import pytest
from agent.base_agent import BaseAgent, AgentConfig

def test_agent_initialization():
    cfg = AgentConfig(name="test", model_name="opt-125m")
    agent = BaseAgent(cfg)
    assert agent.config.name == "test"
    assert agent.config.model_name == "opt-125m"

def test_agent_generation_is_deterministic():
    cfg = AgentConfig(name="gen", model_name="opt-125m")
    agent = BaseAgent(cfg)
    out1 = agent.generate("Hello")
    out2 = agent.generate("Hello")
    assert out1 == out2  # deterministic with fixed seed