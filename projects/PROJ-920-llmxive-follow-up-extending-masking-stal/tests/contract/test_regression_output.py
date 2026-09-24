import json
import os
import sys
from pathlib import Path

# Add code to path if running from tests
# The project root is assumed to be the parent of the directory containing this file's parent
# Given the structure: project_root/tests/contract/test_regression_output.py
# We need to add project_root/code to sys.path.
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
code_path = project_root / "code"

if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

def test_regression_output_schema():
    """
    Contract test: Verify regression_summary.json has required keys and types.
    This test assumes analyze_results.py has been run and produced the output file.
    """
    output_path = project_root / "output" / "regression_summary.json"
    
    if not output_path.exists():
        # If file doesn't exist, the pipeline hasn't been run successfully.
        # The test must fail to indicate the artifact is missing.
        raise FileNotFoundError(
            f"regression_summary.json not found at {output_path}. "
            "Did you run code/analyze_results.py successfully?"
        )

    with open(output_path, 'r') as f:
        data = json.load(f)

    required_keys = [
        "formula", "coefficients", "p_values", "interaction_terms",
        "min_interaction_p_value", "significant_interaction"
    ]

    for key in required_keys:
        assert key in data, f"Missing required key in regression_summary.json: {key}"

    # Type checks
    assert isinstance(data["formula"], str), "formula must be a string"
    assert isinstance(data["coefficients"], dict), "coefficients must be a dict"
    assert isinstance(data["p_values"], dict), "p_values must be a dict"
    assert isinstance(data["interaction_terms"], list), "interaction_terms must be a list"
    assert isinstance(data["min_interaction_p_value"], (int, float)), "min_interaction_p_value must be numeric"
    assert isinstance(data["significant_interaction"], bool), "significant_interaction must be a boolean"

    # Value check for boolean logic consistency with p-value
    p_val = data["min_interaction_p_value"]
    expected_significance = p_val < 0.05
    assert data["significant_interaction"] == expected_significance, \
        f"Significance boolean logic mismatch. p-value={p_val}, expected significant={expected_significance}, got {data['significant_interaction']}"

def test_hypothesis_summary_md():
    """
    Contract test: Verify hypothesis_summary.md exists and contains expected content.
    """
    output_path = project_root / "output" / "hypothesis_summary.md"
    
    if not output_path.exists():
        raise FileNotFoundError(
            f"hypothesis_summary.md not found at {output_path}. "
            "Did you run code/analyze_results.py successfully?"
        )

    content = output_path.read_text()
    
    assert "# Hypothesis Summary" in content, "Missing '# Hypothesis Summary' header"
    assert "Hypothesis Supported" in content, "Missing 'Hypothesis Supported' section"
    assert "Conclusion" in content, "Missing 'Conclusion' section"
    
    # Check for boolean presence (True/False) indicating the result
    assert "True" in content or "False" in content, \
        "Missing boolean result (True/False) in hypothesis summary content"

if __name__ == "__main__":
    test_regression_output_schema()
    test_hypothesis_summary_md()
    print("All contract tests passed.")