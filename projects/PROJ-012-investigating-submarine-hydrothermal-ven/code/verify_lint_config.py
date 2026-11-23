"""Verify that ruff and black are configured for this project (Task T003).

Fails loudly (non-zero exit) if configuration files are missing, empty,
or internally inconsistent. Run as:
    python code/verify_lint_config.py
"""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if not pyproject.is_file():
        fail(f"{pyproject} does not exist")
    raw = pyproject.read_text(encoding="utf-8")
    if not raw.strip():
        fail(f"{pyproject} is empty")

    try:
        config = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        fail(f"{pyproject} is not valid TOML: {exc}")

    ruff_cfg = config.get("tool", {}).get("ruff")
    black_cfg = config.get("tool", {}).get("black")
    if not ruff_cfg:
        fail("[tool.ruff] section missing or empty in pyproject.toml")
    if not black_cfg:
        fail("[tool.black] section missing or empty in pyproject.toml")

    # ruff must select at least the core rule families
    select = ruff_cfg.get("lint", {}).get("select", [])
    for family in ("E", "W", "F"):
        if family not in select:
            fail(f"ruff lint select must include rule family '{family}'")

    # black and ruff must agree on line length to avoid conflicts
    ruff_line = ruff_cfg.get("line-length")
    black_line = black_cfg.get("line-length")
    if ruff_line is None or black_line is None:
        fail("line-length must be set for both ruff and black")
    if ruff_line != black_line:
        fail(
            f"line-length mismatch: ruff={ruff_line}, black={black_line}"
        )

    # target versions must match the project's Python 3.11 requirement
    if "py311" not in str(ruff_cfg.get("target-version", "")):
        fail("ruff target-version must be py311")
    if "py311" not in str(black_cfg.get("target-version", "")):
        fail("black target-version must include py311")

    # If the tools are installed, confirm they accept the configuration.
    for tool, cmd in (("ruff", ["ruff", "check", "--statistics", "code"]),
                      ("black", ["black", "--check", "--quiet", "code"])):
        try:
            proc = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except FileNotFoundError:
            print(f"NOTE: {tool} not installed; skipping live check")
            continue
        except subprocess.TimeoutExpired:
            fail(f"{tool} check timed out")
        # exit 0 = clean, exit 1 = findings (config still valid),
        # exit 2+ = configuration/invocation error
        if proc.returncode >= 2:
            fail(
                f"{tool} rejected the configuration "
                f"(exit {proc.returncode}): {proc.stderr.strip()}"
            )
        print(f"OK: {tool} accepted the configuration (exit {proc.returncode})")

    print(
        "PASS: ruff and black are configured "
        f"(line-length={black_line}, target py311)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
