"""T002c verification: validate .pre-commit-config.yaml structure.

Checks that the pre-commit config exists, parses as YAML, and contains
hooks for both ruff and black as required by the task deliverables.
Writes a verification report to data/results/precommit_verification.json.
"""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".pre-commit-config.yaml"
OUT = ROOT / "data" / "results" / "precommit_verification.json"


def main() -> int:
    if not CONFIG.exists():
        raise FileNotFoundError(f"Missing pre-commit config: {CONFIG}")
    text = CONFIG.read_text()
    if not text.strip():
        raise ValueError(f"Pre-commit config is empty: {CONFIG}")

    cfg = yaml.safe_load(text)
    repos = cfg.get("repos")
    if not repos or not isinstance(repos, list):
        raise ValueError("No 'repos' list found in .pre-commit-config.yaml")

    hook_ids = []
    for repo in repos:
        for hook in repo.get("hooks", []):
            hook_ids.append(hook.get("id"))

    required = {"ruff", "black"}
    missing = sorted(required - set(hook_ids))
    if missing:
        raise ValueError(f"Missing required hooks in config: {missing}")

    report = {
        "config_path": str(CONFIG),
        "repos": [r.get("repo") for r in repos],
        "hook_ids": hook_ids,
        "required_hooks_present": True,
        "valid_yaml": True,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())