"""
Tests to verify that linting and formatting configurations are valid.
These tests ensure that the project's pyproject.toml contains the required
configurations for black and ruff, and that the pre-commit config is valid.
"""
import os
import tomli
import yaml
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYPROJECT_PATH = os.path.join(BASE_DIR, "pyproject.toml")
PRE_COMMIT_PATH = os.path.join(BASE_DIR, ".pre-commit-config.yaml")


@pytest.fixture
def pyproject_config():
    if not os.path.exists(PYPROJECT_PATH):
        pytest.fail(f"pyproject.toml not found at {PYPROJECT_PATH}")
    with open(PYPROJECT_PATH, "rb") as f:
        return tomli.load(f)


@pytest.fixture
def pre_commit_config():
    if not os.path.exists(PRE_COMMIT_PATH):
        pytest.fail(f".pre-commit-config.yaml not found at {PRE_COMMIT_PATH}")
    with open(PRE_COMMIT_PATH, "r") as f:
        return yaml.safe_load(f)


def test_black_config_exists(pyproject_config):
    """Verify that Black configuration exists in pyproject.toml."""
    assert "tool" in pyproject_config
    assert "black" in pyproject_config["tool"]
    assert "line-length" in pyproject_config["tool"]["black"]
    assert pyproject_config["tool"]["black"]["line-length"] == 88


def test_ruff_config_exists(pyproject_config):
    """Verify that Ruff configuration exists in pyproject.toml."""
    assert "tool" in pyproject_config
    assert "ruff" in pyproject_config["tool"]
    assert "line-length" in pyproject_config["tool"]["ruff"]
    assert pyproject_config["tool"]["ruff"]["line-length"] == 88


def test_ruff_lint_rules_selected(pyproject_config):
    """Verify that Ruff has lint rules selected."""
    lint_config = pyproject_config["tool"]["ruff"].get("lint", {})
    assert "select" in lint_config
    assert isinstance(lint_config["select"], list)
    assert len(lint_config["select"]) > 0


def test_dev_dependencies_include_linters(pyproject_config):
    """Verify that dev dependencies include ruff and black."""
    deps = pyproject_config["project"]["optional-dependencies"]["dev"]
    deps_str = " ".join(deps)
    assert "ruff" in deps_str
    assert "black" in deps_str


def test_pre_commit_hooks_configured(pre_commit_config):
    """Verify that pre-commit is configured with Black and Ruff."""
    assert "repos" in pre_commit_config
    repos = pre_commit_config["repos"]
    assert len(repos) > 0

    hooks_found = {"black": False, "ruff": False}

    for repo in repos:
        if "hooks" in repo:
            for hook in repo["hooks"]:
                if hook.get("id") == "black":
                    hooks_found["black"] = True
                if hook.get("id") == "ruff":
                    hooks_found["ruff"] = True

    assert hooks_found["black"], "Black hook not found in pre-commit config"
    assert hooks_found["ruff"], "Ruff hook not found in pre-commit config"