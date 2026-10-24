import json
import re
from pathlib import Path

import pytest
from llmxive_toolkit import paths

@pytest.mark.contract
def test_docker_digest_matches_plan():
    """
    Verify that the Docker image digest recorded in data/env_config.json
    matches the digest documented in specs/001-evaluating-the-impact-of-code-generation/plan.md.
    """
    # Load env_config.json
    env_path = paths.data("env_config.json")
    with env_path.open("r", encoding="utf-8") as f:
        env_cfg = json.load(f)

    recorded_digest = env_cfg.get("docker_digest")
    assert recorded_digest, "docker_digest missing from env_config.json"

    # Locate plan.md
    plan_path = Path(__file__).resolve().parents[2] / "specs" / "001-evaluate-the-impact-of-code-generation" / "plan.md"
    assert plan_path.is_file(), f"plan.md not found at expected location: {plan_path}"

    # Extract digest from plan.md (look for a line containing the sha256 hash)
    digest_pattern = re.compile(r"sha256:[a-f0-9]{64}")
    with plan_path.open("r", encoding="utf-8") as f:
        plan_text = f.read()
    match = digest_pattern.search(plan_text)
    assert match, "Docker digest not found in plan.md"
    plan_digest = match.group(0)

    assert recorded_digest == plan_digest, (
        f"Docker digest mismatch: env_config.json has {recorded_digest} "
        f"but plan.md documents {plan_digest}"
    )