"""
test_env_config.py
------------------
Verifies that the Docker image digest recorded in the environment configuration
matches the digest documented in the implementation plan.
"""

import re
from pathlib import Path

from llmxive_toolkit import paths

def test_docker_digest_consistency():
    # Load env_config.json
    env_path: Path = paths.data("env_config.json")
    assert env_path.is_file(), f"{env_path} does not exist"
    import json
    with env_path.open() as f:
        env_cfg = json.load(f)
    env_digest = env_cfg.get("docker_digest")
    assert env_digest, "docker_digest missing in env_config.json"

    # Load plan.md
    plan_path = Path("specs/001-evaluating-the-impact-of-code-generation/plan.md")
    assert plan_path.is_file(), f"{plan_path} does not exist"
    plan_text = plan_path.read_text()

    # Extract digest from the plan (the fenced block)
    match = re.search(r"sha256:[a-f0-9]{64}", plan_text)
    assert match, "Docker digest not found in plan.md"
    plan_digest = match.group(0)

    assert env_digest == plan_digest, (
        f"Docker digest mismatch: env_config.json has {env_digest}, "
        f"plan.md has {plan_digest}"
    )

# Running this test with `pytest -q` will ensure the verification step passes.