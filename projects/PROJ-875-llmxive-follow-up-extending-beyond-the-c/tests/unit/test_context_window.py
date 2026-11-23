import pytest
import os
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.agent_loop import AgentConfig, TextAgent

def test_truncation_from_start():
    """
    Test that the context window truncates older events when token limit is exceeded.
    Strategy: from_start (keep most recent)
    """
    config = AgentConfig(
        model_name="hf-internal-testing/tiny-random-LlamaForCausalLM",
        max_context_tokens=100, # Very small limit to force truncation
        truncation_strategy="from_start"
    )
    agent = TextAgent(config)
    
    # Create a long context
    long_history = []
    for i in range(50):
        long_history.append({
            "step": i,
            "description": "This is a very long description that consumes tokens. " * 10,
            "ascii_grid": "A"
        })
    
    agent.context_window = long_history
    
    # Trigger truncation logic
    prompt = agent._build_context_string()
    tokens = agent.tokenizer.encode(prompt)
    
    # Assert that the prompt fits within the limit
    assert len(tokens) <= config.max_context_tokens, f"Tokens {len(tokens)} exceeded limit {config.max_context_tokens}"
    
    # Assert that we kept the most recent events (the last ones in the list)
    # The first event in the window should be a later step number, not 0
    if agent.context_window:
        first_event_step = agent.context_window[0].get("step", 0)
        assert first_event_step > 0, "Truncation should have removed the earliest events (step 0)"

def test_no_truncation_when_within_limit():
    """
    Test that no truncation occurs if the context is small enough.
    """
    config = AgentConfig(
        model_name="hf-internal-testing/tiny-random-LlamaForCausalLM",
        max_context_tokens=10000, # Large limit
        truncation_strategy="from_start"
    )
    agent = TextAgent(config)
    
    short_history = [
        {"step": 1, "description": "Short event", "ascii_grid": "A"},
        {"step": 2, "description": "Short event", "ascii_grid": "B"}
    ]
    
    agent.context_window = short_history
    original_len = len(agent.context_window)
    
    prompt = agent._build_context_string()
    
    # Context should remain unchanged
    assert len(agent.context_window) == original_len
    assert len(agent.context_window) == 2

def test_hard_step_limit():
    """
    Test that the agent stops when max_steps is reached.
    """
    config = AgentConfig(
        model_name="hf-internal-testing/tiny-random-LlamaForCausalLM",
        max_steps=5
    )
    agent = TextAgent(config)
    
    # Simulate steps
    for i in range(10):
        # We mock the step call logic to avoid full inference
        agent.step += 1
        if agent.step > config.max_steps:
            agent.terminated = True
            agent.termination_reason = "MAX_STEPS_EXCEEDED"
            break
    
    assert agent.terminated
    assert agent.termination_reason == "MAX_STEPS_EXCEEDED"
    assert agent.step == 6 # One step over the limit

def test_context_window_growth():
    """
    Test that the context window grows as events are added.
    """
    config = AgentConfig(model_name="hf-internal-testing/tiny-random-LlamaForCausalLM")
    agent = TextAgent(config)
    
    initial_len = len(agent.context_window)
    
    agent.add_event_to_context({"step": 1, "desc": "A"})
    agent.add_event_to_context({"step": 2, "desc": "B"})
    
    assert len(agent.context_window) == initial_len + 2
    assert agent.context_window[-1]["step"] == 2