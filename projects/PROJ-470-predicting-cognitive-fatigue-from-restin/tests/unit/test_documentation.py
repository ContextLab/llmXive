import os
import yaml
import re
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "code", "config.yaml")
README_PATH = os.path.join(PROJECT_ROOT, "docs", "README.md")

def test_readme_exists():
    """Assert that docs/README.md exists."""
    assert os.path.exists(README_PATH), f"README.md not found at {README_PATH}"

def test_readme_contains_pipeline_parameters_section():
    """Assert that README.md contains the 'Pipeline Parameters' section."""
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "Pipeline Parameters" in content, "README.md missing 'Pipeline Parameters' section"

def test_readme_parameters_match_config():
    """
    Parse code/config.yaml and assert that the values in docs/README.md match exactly.
    The verification parses the YAML and checks for the specific values in the markdown table.
    """
    # Load actual config values
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    # Load README content
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme_content = f.read()
    
    # Define expected parameters and their string representations in the table
    # We check for the specific values in the markdown table rows
    expected_checks = [
        ("filter_low", config.get("filter_low")),
        ("filter_high", config.get("filter_high")),
        ("artifact_threshold", config.get("artifact_threshold")),
        ("random_seed", config.get("random_seed")),
        ("min_participants", config.get("min_participants")),
        ("notch_freq", config.get("notch_freq"))
    ]
    
    for key, value in expected_checks:
        # Create a regex pattern to find the row for this parameter and check the value
        # Pattern looks for: | key | value |
        # We escape the value just in case it contains regex special chars (though they are numbers here)
        value_str = str(value)
        pattern = re.compile(rf"\|\s*{re.escape(key)}\s*\|\s*{re.escape(value_str)}\s*\|")
        
        assert pattern.search(readme_content), (
            f"README.md does not contain the correct value for '{key}'. "
            f"Expected value '{value_str}' in the 'Pipeline Parameters' table, "
            f"but config.yaml has {value}."
        )

def test_readme_contains_required_sections():
    """Assert that README.md contains all required documentation sections."""
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    required_sections = [
        "Overview",
        "Pipeline Parameters",
        "Data Sources",
        "Statistical Interpretation Guidelines",
        "Installation",
        "Usage",
        "Output Artifacts"
    ]
    
    for section in required_sections:
        assert section in content, f"README.md missing required section: '{section}'"