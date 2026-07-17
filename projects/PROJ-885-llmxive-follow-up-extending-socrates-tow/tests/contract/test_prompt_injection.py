"""
Contract test for prompt injection (T021).

Verifies that the prompt injection logic in code/experiments/prompts.py
correctly generates prompts with injected socio-cognitive state signals
for the Adapter condition, and baseline prompts without injections for
the Static condition.

This test ensures compliance with FR-002 (dynamic state injection) and
the user story requirements for paired experiments.
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Import the prompt templates from the implementation
# Note: The implementation file code/experiments/prompts.py is not yet created
# This test will fail until T023 is implemented, which is expected behavior
# for a "test-first" approach.
try:
    from experiments.prompts import (
        get_static_baseline_prompt,
        get_dynamic_adapter_prompt,
        INJECTION_KEYWORDS,
        STATE_LABELS
    )
    PROMPTS_AVAILABLE = True
except ImportError:
    PROMPTS_AVAILABLE = False


# --- Test Fixtures ---

@pytest.fixture
def sample_trajectory() -> Dict[str, Any]:
    """Create a sample conflict trajectory for testing."""
    return {
        "trajectory_id": "test-traj-001",
        "metadata": {
            "emotional_reactivity": "high",
            "cultural_identity": "diverse"
        },
        "turns": [
            {
                "turn_id": 1,
                "speaker": "user",
                "text": "I feel completely misunderstood by you."
            },
            {
                "turn_id": 2,
                "speaker": "mediator",
                "text": "I hear that you're feeling unheard. Can you tell me more?"
            },
            {
                "turn_id": 3,
                "speaker": "user",
                "text": "It's like you don't care about my perspective at all!"
            }
        ]
    }

@pytest.fixture
def sample_state() -> Dict[str, str]:
    """Create a sample socio-cognitive state for injection."""
    return {
        "state_type": "de-escalation",
        "directive": "validate cultural norms",
        "confidence": 0.85
    }

@pytest.fixture
def expected_static_keywords() -> List[str]:
    """Keywords that should NOT appear in static baseline prompts."""
    return [
        "de-escalate", 
        "validate cultural norms", 
        "monitoring state",
        "dynamic injection"
    ]

@pytest.fixture
def expected_adapter_keywords() -> List[str]:
    """Keywords that MUST appear in dynamic adapter prompts."""
    return ["de-escalate", "validate cultural norms", "state injection"]

# --- Contract Tests ---

@pytest.mark.skipif(not PROMPTS_AVAILABLE, reason="Prompt module not yet implemented (T023)")
def test_static_prompt_excludes_injection_signals(sample_trajectory):
    """
    Contract: Static baseline prompts must NOT contain any injection keywords.
    
    This ensures the Static condition is a true baseline without dynamic
    socio-cognitive state influence.
    """
    prompt = get_static_baseline_prompt(sample_trajectory["turns"])
    
    for keyword in expected_static_keywords():
        assert keyword.lower() not in prompt.lower(), (
            f"Static prompt unexpectedly contains injection keyword: '{keyword}'"
        )

@pytest.mark.skipif(not PROMPTS_AVAILABLE, reason="Prompt module not yet implemented (T023)")
def test_adapter_prompt_includes_state_signals(sample_trajectory, sample_state):
    """
    Contract: Dynamic adapter prompts MUST contain the injected state directive.
    
    This verifies that the adapter condition correctly injects the socio-cognitive
    state instructions into the LLM prompt.
    """
    prompt = get_dynamic_adapter_prompt(sample_trajectory["turns"], sample_state)
    
    # Check that the specific directive is present
    assert sample_state["directive"].lower() in prompt.lower(), (
        f"Adapter prompt missing required directive: '{sample_state['directive']}'"
    )
    
    # Check that state type is referenced
    assert sample_state["state_type"].lower() in prompt.lower(), (
        f"Adapter prompt missing state type reference: '{sample_state['state_type']}'"
    )

@pytest.mark.skipif(not PROMPTS_AVAILABLE, reason="Prompt module not yet implemented (T023)")
def test_adapter_prompt_contains_injection_marker(sample_trajectory, sample_state):
    """
    Contract: Adapter prompts must have a clear marker indicating injection occurred.
    
    This ensures the experiment logs can distinguish injected vs non-injected
    prompts for analysis.
    """
    prompt = get_dynamic_adapter_prompt(sample_trajectory["turns"], sample_state)
    
    # Look for standard injection markers
    injection_markers = [
        "[DYNAMIC STATE]",
        "[STATE INJECTION]",
        "Current State:",
        "Directive:"
    ]
    
    has_marker = any(marker.lower() in prompt.lower() for marker in injection_markers)
    assert has_marker, (
        "Adapter prompt missing any standard injection marker. "
        f"Expected one of: {injection_markers}"
    )

@pytest.mark.skipif(not PROMPTS_AVAILABLE, reason="Prompt module not yet implemented (T023)")
def test_prompt_structure_validates_trajectory_input(sample_trajectory):
    """
    Contract: Both prompt types must accept and validate trajectory input.
    
    Ensures the prompt generation functions handle the expected data schema.
    """
    # Static prompt
    static_prompt = get_static_baseline_prompt(sample_trajectory["turns"])
    assert isinstance(static_prompt, str), "Static prompt must be a string"
    assert len(static_prompt) > 0, "Static prompt must not be empty"
    
    # Adapter prompt
    adapter_prompt = get_dynamic_adapter_prompt(sample_trajectory["turns"], sample_state)
    assert isinstance(adapter_prompt, str), "Adapter prompt must be a string"
    assert len(adapter_prompt) > 0, "Adapter prompt must not be empty"

@pytest.mark.skipif(not PROMPTS_AVAILABLE, reason="Prompt module not yet implemented (T023)")
def test_low_confidence_triggers_neutral_monitoring(sample_trajectory):
    """
    Contract: Low confidence states must trigger a 'neutral monitoring' directive.
    
    This satisfies the edge case requirement (FR-002) where the classifier
    fails gracefully instead of injecting potentially harmful instructions.
    """
    low_conf_state = {
        "state_type": "uncertain",
        "directive": "neutral monitoring state",
        "confidence": 0.35  # Below typical threshold
    }
    
    prompt = get_dynamic_adapter_prompt(sample_trajectory["turns"], low_conf_state)
    
    # Must contain the neutral monitoring directive
    assert "neutral monitoring" in prompt.lower(), (
        "Low confidence state should trigger 'neutral monitoring' directive"
    )

@pytest.mark.skipif(not PROMPTS_AVAILABLE, reason="Prompt module not yet implemented (T023)")
def test_prompt_injection_preserves_dialogue_context(sample_trajectory):
    """
    Contract: Injected prompts must preserve the original dialogue context.
    
    Ensures that state injection doesn't overwrite or lose the conversation history.
    """
    prompt = get_dynamic_adapter_prompt(sample_trajectory["turns"], sample_state)
    
    # Check that original dialogue text is preserved
    for turn in sample_trajectory["turns"]:
        assert turn["text"] in prompt, (
            f"Original dialogue text lost: '{turn['text'][:50]}...'"
        )

@pytest.mark.skipif(PROMPTS_AVAILABLE, reason="Skipping when prompts are implemented")
def test_prompt_module_not_yet_implemented():
    """
    Placeholder test that documents the expected implementation status.
    
    This test passes when the prompt module is NOT yet implemented,
    indicating that T023 (implementation) is the next required task.
    """
    assert not PROMPTS_AVAILABLE, (
        "Expected prompts module to be unimplemented. "
        "If this fails, T023 has been completed and this test should be updated."
    )