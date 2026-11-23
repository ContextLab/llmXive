"""
Unit tests for prompt templates defined in templates/prompts.yaml.
Verifies that prompts load successfully and contain required keys.
"""
import os
import yaml
import pytest
from pathlib import Path

# Project root is assumed to be the parent of 'tests'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROMPTS_FILE = PROJECT_ROOT / "templates" / "prompts.yaml"

REQUIRED_KEYS = ["gatekeeper_prompt", "retrieval_only_prompt", "long_context_prompt"]

@pytest.fixture
def prompts():
    """Load prompts from the YAML file."""
    if not PROMPTS_FILE.exists():
        pytest.fail(f"Prompt file not found at {PROMPTS_FILE}")
    
    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data

def test_prompts_load_successfully(prompts):
    """Test that the prompts file loads without error and contains required keys."""
    assert isinstance(prompts, dict), "Prompts must be a dictionary."
    
    missing_keys = [key for key in REQUIRED_KEYS if key not in prompts]
    assert not missing_keys, f"Missing required prompt keys: {missing_keys}"
    
    for key in REQUIRED_KEYS:
        assert isinstance(prompts[key], str), f"Prompt '{key}' must be a string."
        assert len(prompts[key].strip()) > 0, f"Prompt '{key}' cannot be empty."

def test_prompt_placeholders(prompts):
    """Test that prompts contain the expected placeholders for dynamic content."""
    required_placeholders = ["{context}", "{query}", "{role}"]
    
    for key in REQUIRED_KEYS:
        prompt_text = prompts[key]
        for placeholder in required_placeholders:
            assert placeholder in prompt_text, f"Prompt '{key}' missing placeholder: {placeholder}"

def test_prompt_consistency(prompts):
    """
    Verify that the system instructions and core structure are identical across prompts.
    This ensures that differences in results are due to the pipeline logic, not prompt engineering.
    """
    # Extract the part before the "Context:" section for comparison
    # This assumes the structure defined in templates/prompts.yaml
    def get_system_block(prompt_text):
        if "Context:" in prompt_text:
            return prompt_text.split("Context:")[0]
        return prompt_text

    sys_blocks = [get_system_block(prompts[key]) for key in REQUIRED_KEYS]
    
    # All system blocks should be identical
    first_block = sys_blocks[0]
    for i, block in enumerate(sys_blocks[1:], start=1):
        assert block == first_block, (
            f"System instruction in prompt '{REQUIRED_KEYS[i]}' differs from '{REQUIRED_KEYS[0]}'. "
            "All prompts must use identical system instructions."
        )
