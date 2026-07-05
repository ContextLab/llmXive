"""
Black formatting configuration for llmXive project.

This file documents the formatting standards. The actual formatting is
applied via the `black` command with default settings matching this config.

Standards:
- Line length: 88
- Target version: Python 3.11
- Quote style: Double quotes
- Magic trailing comma: Enabled
"""

# Black is configured via pyproject.toml or CLI arguments.
# To format the entire project, run:
#   black code/ tests/

# To check formatting without modifying files:
#   black --check code/ tests/

# This file exists to ensure the configuration is version-controlled
# and visible to the team.

def _get_black_config():
    """Return the effective black configuration as a dictionary."""
    return {
        "line_length": 88,
        "target_versions": {3, 11},
        "string_normalization": True,
        "is_python_package": True,
    }
