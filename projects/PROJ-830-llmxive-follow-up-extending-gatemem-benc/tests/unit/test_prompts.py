"""
Unit tests for prompt template loading and consistency.
Verifies that templates/prompts.yaml exists, is valid YAML,
and contains the required keys for Gatekeeper and Baseline configurations.
"""
import os
import yaml
import pytest
from pathlib import Path

# Define the path to the prompts file
PROMPTS_PATH = Path("templates/prompts.yaml")

def test_prompts_load_successfully():
    """
    Test that prompts.yaml exists, is valid YAML, and contains required keys.
    This is the verification test for Task T043.
    """
    # 1. Check if file exists
    assert PROMPTS_PATH.exists(), f"File {PROMPTS_PATH} does not exist."

    # 2. Load and parse YAML
    try:
        with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML syntax in {PROMPTS_PATH}: {e}")
    except Exception as e:
        pytest.fail(f"Failed to read {PROMPTS_PATH}: {e}")

    # 3. Verify required keys are present
    required_keys = ["gatekeeper_prompt", "retrieval_only_prompt", "long_context_prompt"]
    missing_keys = [key for key in required_keys if key not in data]
    
    assert not missing_keys, f"Missing required keys in prompts.yaml: {missing_keys}"

    # 4. Verify content is non-empty strings
    for key in required_keys:
        content = data[key]
        assert isinstance(content, str), f"Key '{key}' must be a string, got {type(content)}"
        assert len(content.strip()) > 0, f"Key '{key}' cannot be empty."

    # 5. Verify consistency: Check for shared placeholders
    # All prompts should use the same placeholders to ensure fair comparison
    expected_placeholders = ["{context}", "{role}", "{query}"]
    
    for key in required_keys:
        content = data[key]
        for placeholder in expected_placeholders:
            assert placeholder in content, (
                f"Prompt '{key}' is missing required placeholder '{placeholder}'. "
                "All prompts must use identical placeholders for valid comparison."
            )

    # 6. Verify the presence of few_shot_examples if defined (optional but recommended)
    if "few_shot_examples" in data:
        assert isinstance(data["few_shot_examples"], str)
        assert len(data["few_shot_examples"].strip()) > 0

    # 7. Verify consistency checks section exists (optional validation metadata)
    if "consistency_checks" in data:
        assert isinstance(data["consistency_checks"], list)
        assert len(data["consistency_checks"]) > 0

    # All checks passed
    assert True
    
def test_prompt_structure_validity():
    """
    Additional test to ensure prompt structure adheres to security guidelines.
    """
    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    gatekeeper_prompt = data.get("gatekeeper_prompt", "")
    
    # Verify security rules are present in the gatekeeper prompt
    security_keywords = [
        "access control",
        "denied",
        "restricted",
        "deletion",
        "bypass"
    ]
    
    prompt_lower = gatekeeper_prompt.lower()
    found_keywords = [kw for kw in security_keywords if kw in prompt_lower]
    
    assert len(found_keywords) >= 3, (
        f"Gatekeeper prompt missing critical security keywords. "
        f"Found: {found_keywords}, Expected at least 3 of: {security_keywords}"
    )

if __name__ == "__main__":
    test_prompts_load_successfully()
    test_prompt_structure_validity()
    print("All prompt tests passed.")
