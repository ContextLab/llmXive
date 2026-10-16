"""
T003: Configure linting (ruff) and formatting (black) tools.

This script:
1. Verifies the shared configuration file (code/pyproject.toml) exists
   and parses as valid TOML.
2. Attempts to run `ruff check` and `black --check` against the project
   source and test directories using that configuration.
3. Writes an honest status report to results/lint_report.json.

If ruff/black are not installed in the current environment, the report
records status "not_installed" for that tool (no fabricated results).
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

PROJECT_ROOT = paths.root
CONFIG_PATH = PROJECT_ROOT / "code" / "pyproject.toml"
LINT_TARGETS = ["code/src", "tests"]


def verify_config() -> dict:
    """Verify the pyproject.toml config exists and parses as TOML."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Lint config missing: {CONFIG_PATH}. It is shipped as a "
            "project artifact; it must not be deleted."
        )
    try:
        import tomllib
    except ImportError:  # Python < 3.11
        import tomli as tomllib  # type: ignore

    with open(CONFIG_PATH, "rb") as f:
        config = tomllib.load(f)

    has_ruff = "ruff" in config.get("tool", {})
    has_black = "black" in config.get("tool", {})
    if not (has_ruff and has_black):
        raise ValueError(
            "code/pyproject.toml must contain both [tool.ruff] and "
            "[tool.black] sections."
        )
    return {
        "config_path": str(CONFIG_PATH.relative_to(PROJECT_ROOT)),
        "ruff_section_present": has_ruff,
        "black_section_present": has_black,
        "ruff_line_length": config["tool"]["ruff"]["line-length"],
        "black_line_length": config["tool"]["black"]["line-length"],
    }


def run_tool(tool: str, args: list) -> dict:
    """Run a lint/format tool via subprocess; report honest status."""
    executable = shutil.which(tool)
    if executable is None:
        # Also try module invocation in case it is importable but not on PATH
        probe = subprocess.run(
            [sys.executable, "-m", tool, "--version"],
            capture_output=True,
            text=True,
          )
        if probe.returncode != 0:
            return {
                "tool": tool,
                "status": "not_installed",
                "command": None,
                "note": (
                    f"{tool} is not installed in this environment; "
                    "configuration is in place but the tool was not run."
                ),
            }
        base_cmd = [sys.executable, "-m", tool]
        version = probe.stdout.strip()
    else:
        base_cmd = [executable]
        version = subprocess.run(
            [executable, "--version"], capture_output=True, text=True
        ).stdout.strip()

    cmd = base_cmd + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
    return {
        "tool": tool,
        "status": "ran",
        "version": version,
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }


def main() -> int:
    report = {"task_id": "T003", "tools": {}}

    report["config"] = verify_config()

    report["tools"]["ruff"] = run_tool(
        "ruff",
        ["check", "--config", str(CONFIG_PATH)] + LINT_TARGETS,
    )
    report["tools"]["black"] = run_tool(
        "black",
        [
            "--config",
            str(CONFIG_PATH),
            "--check",
        ]
        + LINT_TARGETS,
    )

    out_path = paths.results("lint_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Lint setup report written to {out_path}")
    for name, info in report["tools"].items():
        print(f"  {name}: {info['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
