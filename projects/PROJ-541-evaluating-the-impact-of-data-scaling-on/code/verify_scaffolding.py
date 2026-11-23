"""T001 verification: scaffolding files exist and linters pass.

Checks that every file required by T001 exists, ensures the lint
tools (ruff, black) are installed (installing the pinned versions
from code/requirements.txt if missing), applies black formatting
once so the tree is format-clean, and then verifies that both
``black --check .`` and ``ruff check .`` exit with code 0.

Writes a log of the verification to ``logs/t001_verification.log``
and exits non-zero on any failure (fail loudly, never silently).
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from llmxive_toolkit import paths

ROOT = paths.root

REQUIRED_FILES = [
    "README.md",
    "code/__init__.py",
    "code/requirements.txt",
    "pyproject.toml",
    "ruff.toml",
    ".pre-commit-config.yaml",
    "code/tests/__init__.py",
]

PINNED_TOOLS = ["ruff==0.8.6", "black==24.10.0"]


def _ensure_tools() -> None:
    """Install ruff/black (pinned) if they are not importable."""
    missing = [
        pkg
        for pkg, mod in (("ruff", "ruff"), ("black", "black"))
        if importlib.util.find_spec(mod) is None
    ]
    if missing:
        specs = [s for s in PINNED_TOOLS if s.split("==")[0] in missing]
        print(f"Installing lint tools: {specs}")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", *specs],
            check=True,
        )


def main() -> int:
    log_path = paths.path("logs", "t001_verification.log")
    lines: list[str] = []
    ok = True

    lines.append(
        f"T001 scaffolding verification {datetime.now(timezone.utc).isoformat()}"
    )

    # 1. All required files exist.
    for rel in REQUIRED_FILES:
        exists = (ROOT / rel).is_file()
        lines.append(f"  {'OK ' if exists else 'MISSING'} {rel}")
        if not exists:
            ok = False
    if not ok:
        lines.append("FAIL: required scaffolding files are missing.")

    if ok:
        _ensure_tools()

        # 2. Apply black once so the tree is format-clean, then verify.
        fmt = subprocess.run(
            [sys.executable, "-m", "black", "."],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        lines.append(f"black .           -> rc={fmt.returncode}")
        if fmt.returncode != 0:
            lines.append(fmt.stdout)
            lines.append(fmt.stderr)
            ok = False

        chk = subprocess.run(
            [sys.executable, "-m", "black", "--check", "."],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        lines.append(f"black --check .   -> rc={chk.returncode}")
        if chk.returncode != 0:
            lines.append(chk.stdout)
            lines.append(chk.stderr)
            ok = False

        # 3. ruff check .
        ruff = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "."],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        lines.append(f"ruff check .      -> rc={ruff.returncode}")
        if ruff.returncode != 0:
            lines.append(ruff.stdout)
            lines.append(ruff.stderr)
            ok = False

    lines.append("RESULT: PASS" if ok else "RESULT: FAIL")
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
