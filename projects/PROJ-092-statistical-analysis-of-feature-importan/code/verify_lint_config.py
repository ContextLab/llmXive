"""Verify that linting/formatting configuration files exist and parse correctly.

Checks (T003):
- code/pyproject.toml contains [tool.black], [tool.isort], [tool.pylint.*] sections
- code/.flake8 contains a non-empty [flake8] section

Writes a JSON verification report to outputs/lint_config_check.json.
"""
import configparser
import json
import sys
import tomllib
from pathlib import Path

from llmxive_toolkit import paths

CODE_DIR = Path(__file__).resolve().parent
PYPROJECT = CODE_DIR / "pyproject.toml"
FLAKE8 = CODE_DIR / ".flake8"


def verify_pyproject() -> dict:
    if not PYPROJECT.exists():
        return {"file": str(PYPROJECT), "exists": False, "ok": False, "reason": "missing"}
    if PYPROJECT.stat().st_size == 0:
        return {"file": str(PYPROJECT), "exists": True, "ok": False, "reason": "empty"}
    with open(PYPROJECT, "rb") as f:
        data = tomllib.load(f)
    tools = data.get("tool", {})
    required = ["black", "isort", "pylint"]
    missing = [t for t in required if t not in tools]
    if missing:
        return {
            "file": str(PYPROJECT),
            "exists": True,
            "ok": False,
            "reason": f"missing tool sections: {missing}",
        }
    return {
        "file": str(PYPROJECT),
        "exists": True,
        "ok": True,
        "sections": sorted(tools.keys()),
    }


def verify_flake8() -> dict:
    if not FLAKE8.exists():
        return {"file": str(FLAKE8), "exists": False, "ok": False, "reason": "missing"}
    if FLAKE8.stat().st_size == 0:
        return {"file": str(FLAKE8), "exists": True, "ok": False, "reason": "empty"}
    parser = configparser.ConfigParser()
    parser.read(FLAKE8)
    if "flake8" not in parser:
        return {
            "file": str(FLAKE8),
            "exists": True,
            "ok": False,
            "reason": "no [flake8] section",
        }
        # unreachable
    opts = dict(parser["flake8"])
    if not opts:
        return {
            "file": str(FLAKE8),
            "exists": True,
            "ok": False,
            "reason": "[flake8] section is empty",
        }
    return {"file": str(FLAKE8), "exists": True, "ok": True, "options": sorted(opts.keys())}


def main() -> int:
    results = {
        "pyproject": verify_pyproject(),
        "flake8": verify_flake8(),
    }
    results["all_ok"] = all(r.get("ok", False) for r in results.values())
    out_path = paths.outputs("lint_config_check.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))
    if not results["all_ok"]:
        print(f"LINT CONFIG VERIFICATION FAILED; report at {out_path}", file=sys.stderr)
        return 1
    print(f"Lint configuration verified. Report written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())