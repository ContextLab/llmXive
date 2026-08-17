"""
Smoke test to verify pre-commit configuration exists and is valid YAML.
This satisfies the requirement to have a test for T003.
"""
import yaml
import os

def test_precommit_config_exists():
    """Assert .pre-commit-config.yaml exists in the project root."""
    assert os.path.exists(".pre-commit-config.yaml"), ".pre-commit-config.yaml not found"

def test_precommit_config_valid_yaml():
    """Assert .pre-commit-config.yaml is valid YAML and contains expected hooks."""
    with open(".pre-commit-config.yaml", "r") as f:
        config = yaml.safe_load(f)

    assert "repos" in config, "Config must contain 'repos' key"
    repo_urls = [repo["repo"] for repo in config["repos"]]

    # Check for Ruff (linting + formatting)
    assert any("astral-sh/ruff-pre-commit" in url for url in repo_urls), \
        "Ruff pre-commit hook not found"

    # Check for Mypy (type checking)
    assert any("mirrors-mypy" in url for url in repo_urls), \
        "Mypy pre-commit hook not found"