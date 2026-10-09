"""Run ruff (lint) and black (format) over the project source tree.

T003: Configure linting (ruff) and formatting (black) tools.

This script ensures both tools are available (installing them into the
active environment if missing), formats the codebase with black, applies
safe ruff autofixes, and then verifies the tree is clean. It exits with a
non-zero status if any lint/format issue remains after autofix.

Usage:
    python scripts/run_lint.py
"""

import importlib
import subprocess
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    str(CODE_ROOT / "src"),
    str(CODE_ROOT / "scripts"),
    str(CODE_ROOT / "tests"),
]


def ensure_tool(module_name: str, package: str) -> None:
    """Ensure a linting tool is importable; install it if missing."""
    try:
        importlib.import_module(module_name)
    except ImportError:
        print(f"[lint] {package} not installed; installing...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            check=True,
        )


def run(cmd: list) -> int:
    print(f"[lint] $ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(CODE_ROOT))
    return proc.returncode


def main() -> int:
    targets = [t for t in TARGETS if Path(t).is_dir()]
    if not targets:
        print("[lint] No source directories found to lint.", file=sys.stderr)
        return 1

    ensure_tool("ruff", "ruff")
    ensure_tool("black", "black")

    base = [sys.executable, "-m"]

    # 1) Format with black (write mode).
    rc_black_fmt = run(base + ["black"] + targets)
    if rc_black_fmt != 0:
        return rc_black_fmt

    # 2) Apply safe ruff autofixes.
    rc_ruff_fix = run(base + ["ruff", "check", "--fix"] + targets)

    # 3) Verify: ruff check must pass with no remaining findings.
    rc_ruff = run(base + ["ruff", "check"] + targets)
    if rc_ruff != 0:
        return rc_ruff

    # 4) Verify: black --check confirms formatting is stable.
    rc_black = run(base + ["black", "--check"] + targets)
    if rc_black != 0:
        return rc_black

    if rc_ruff_fix != 0:
        # Autofixes were applied; report success but note changes.
        print("[lint] Autofixes were applied; tree is now clean.")
    print("[lint] OK: ruff and black both pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
