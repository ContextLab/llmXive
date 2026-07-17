import os
import yaml
import pytest

PRECOMMIT_PATH = "code/.pre-commit-config.yaml"

@pytest.mark.skipif(not os.path.exists(PRECOMMIT_PATH), reason="Pre-commit config not found")
def test_precommit_config_exists_and_valid():
    """Verify .pre-commit-config.yaml exists and is valid YAML."""
    with open(PRECOMMIT_PATH, "r") as f:
        config = yaml.safe_load(f)

    assert isinstance(config, dict), "Config must be a dictionary"
    assert "repos" in config, "Config must contain 'repos' key"
    assert isinstance(config["repos"], list), "'repos' must be a list"

    repo_ids = [repo["repo"] for repo in config["repos"]]
    assert any("ruff" in r for r in repo_ids), "Must include ruff pre-commit"
    assert any("black" in r for r in repo_ids), "Must include black pre-commit"

@pytest.mark.skipif(not os.path.exists(PRECOMMIT_PATH), reason="Pre-commit config not found")
def test_no_xtb_in_requirements():
    """Ensure xtb is not in requirements.txt (must be installed via conda/apt)."""
    req_path = "code/requirements.txt"
    if not os.path.exists(req_path):
        pytest.skip("requirements.txt not found")

    with open(req_path, "r") as f:
        content = f.read()

    # Check that xtb is not a dependency line (allow comments mentioning xtb)
    lines = [line.strip() for line in content.splitlines() if not line.strip().startswith("#")]
    for line in lines:
        if line.startswith("xtb") or line.startswith("-e") and "xtb" in line:
            pytest.fail(f"xtb must not be in requirements.txt. Found: {line}")