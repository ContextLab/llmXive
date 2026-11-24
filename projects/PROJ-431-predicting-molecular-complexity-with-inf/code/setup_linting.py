"""Set up and run linting (flake8) and formatting checks (black).

Task T003: Configure linting (flake8/black) and formatting tools.

This script:
1. Ensures flake8 and black are installed (installing them if missing).
2. Runs flake8 on code/ and tests/ using code/.flake8 as the config.
3. Runs black --check on code/ and tests/ using code/pyproject.toml.
4. Writes an evidence report to results/reports/linting_report.txt.

Exit code is 0 as long as the tools ran and the report was written;
the report records the number of violations found so they can be
addressed incrementally.
"""

import shutil
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

TOOLS = ["flake8", "black"]
TARGETS = ["code", "tests"]


def _ensure_tool(module: str) -> None:
    """Ensure a linting tool is importable; install it if missing."""
    check = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        capture_output=True,
    )
    if check.returncode != 0:
        print(f"[setup_linting] {module} missing, installing...")
        install = subprocess.run(
            [sys.executable, "-m", "pip", "install", module],
            capture_output=True,
            text=True,
        )
        if install.returncode != 0:
            raise RuntimeError(
                f"Failed to install {module}: {install.stderr[-2000:]}"
            )


def run_command(cmd: list, description: str) -> bool:
    """Run a shell command, streaming output; return True on success."""
    print(f"[setup_linting] {description}: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = (result.stdout or "") + (result.stderr or "")
    if output.strip():
        print(output.rstrip())
    return result.returncode == 0


def main() -> int:
    project_root = paths.root
    os_cwd_ok = subprocess.run(["pwd"], capture_output=True, text=True)
    del os_cwd_ok

    for tool in TOOLS:
        _ensure_tool(tool)

    flake8_config = project_root / "code" / ".flake8"
    black_config = project_root / "code" / "pyproject.toml"
    if not flake8_config.exists():
        raise FileNotFoundError(f"Missing flake8 config: {flake8_config}")
    if not black_config.exists():
        raise FileNotFoundError(f"Missing black config: {black_config}")

    report_path = paths.results("reports", "linting_report.txt")
    lines = ["Linting & Formatting Report (T003)", "=" * 40, ""]

    # ---- flake8 ----
    flake8_cmd = [
        sys.executable,
        "-m",
        "flake8",
        "--config",
        str(flake8_config),
    ] + [str(project_root / t) for t in TARGETS if (project_root / t).exists()]
    flake8_ok = run_command(flake8_cmd, "Running flake8")
    flake8_result = subprocess.run(flake8_cmd, capture_output=True, text=True)
    flake8_out = (flake8_result.stdout or "").strip()
    n_flake8 = len(flake8_out.splitlines()) if flake8_out else 0
    lines.append(f"flake8 (config: code/.flake8): "
                  f"{'PASS' if flake8_ok else f'{n_flake8} violation(s)'}")
    if flake8_out:
        lines.extend("  " + l for l in flake8_out.splitlines())
    lines.append("")

    # ---- black ----
    black_cmd = [
        sys.executable,
        "-m",
        "black",
        "--check",
        "--config",
        str(black_config),
    ] + [str(project_root / t) for t in TARGETS if (project_root / t).exists()]
    black_ok = run_command(black_cmd, "Running black --check")
    black_result = subprocess.run(black_cmd, capture_output=True, text=True)
    black_out = (black_result.stdout or "").strip()
    n_black = 0
    if black_out and "would reformat" in black_out:
        n_black = sum(1 for l in black_out.splitlines() if "would reformat" in l)
    lines.append(f"black --check (config: code/pyproject.toml): "
                  f"{'PASS' if black_ok else f'{n_black} file(s) would be reformatted'}")
    if black_out:
        lines.extend("  " + l for l in black_out.splitlines()[:50])
    lines.append("")

    lines.append(
        "Tools configured: flake8 (code/.flake8, max-line-length=100, "
        "black-compatible ignores E203/W503) and black (code/pyproject.toml, "
        "line-length=100, target py310)."
    )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[setup_linting] Report written to {report_path}")

    # Tools ran successfully and evidence was produced; violations are
    # recorded in the report for incremental cleanup.
    return 0


if __name__ == "__main__":
    sys.exit(main())