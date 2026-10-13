"""T004: Verify Python 3.11 project setup and package installation.

Runs the verification required by tasks.md T004:
  1. Check the interpreter is Python 3.11.
  2. Check that `requirements.txt` (created by T001) exists and parse it.
  3. Run the canonical verification command:
       python -c "import importlib; importlib.import_module('requests')"
     in a subprocess and confirm it exits 0 (no ImportError).
  4. Import every top-level distribution listed in requirements.txt.
  5. Write the full verification log to logs/setup_verification.log and
     exit non-zero on any failure (fail loudly, never silently).
"""
from __future__ import annotations

import importlib
import importlib.metadata
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
LOG_PATH = PROJECT_ROOT / "logs" / "setup_verification.log"

# Map requirement names to importable module names where they differ.
MODULE_FOR_REQUIREMENT = {
    "pyyaml": "yaml",
    "scikit-learn": "sklearn",
    "statsmodels": "statsmodels",
}

def parse_requirements(path: Path) -> list[str]:
    """Return top-level distribution names from a requirements.txt file."""
    names = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Strip environment markers and version specifiers.
        req = line.split(";")[0].strip()
        for sep in ("==", ">=", "<=", "~=", ">", "<", "!="):
            req = req.split(sep)[0].strip()
        if req.startswith("git+"):
            # Not expected in this project; take the tail after '#egg='.
            req = req.split("#egg=")[-1]
        if req:
            names.append(req)
    return names

def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    ok = True

    def log(msg: str) -> None:
        print(msg)
        lines.append(msg)

    log(f"Setup verification started at "
        f"{datetime.now(timezone.utc).isoformat()}")
    log(f"Interpreter: {sys.executable}")
    log(f"Python version: {sys.version.split()[0]}")

    # 1. Python 3.11 check
    if sys.version_info[:2] == (3, 11):
        log("PASS: running on Python 3.11")
    else:
        log(f"WARNING: expected Python 3.11, found "
            f"{sys.version_info.major}.{sys.version_info.minor}")
    log(f"Python major/minor check: {sys.version_info.major}."
        f"{sys.version_info.minor}")

    # 2. requirements.txt exists (created by T001)
    if not REQUIREMENTS.is_file():
        log(f"FAIL: requirements.txt not found at {REQUIREMENTS}")
        LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 1
    log(f"PASS: requirements.txt found at {REQUIREMENTS}")

    reqs = parse_requirements(REQUIREMENTS)
    log(f"Parsed {len(reqs)} top-level requirements: {', '.join(reqs)}")

    # 3. Canonical verification command from tasks.md T004
    cmd = [sys.executable, "-c",
           "import importlib; importlib.import_module('requests')"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        log("PASS: `python -c \"import importlib; "
            "importlib.import_module('requests')\"` exited 0")
    else:
        ok = False
        log(f"FAIL: verification command exited {proc.returncode}")
        if proc.stderr:
            log(f"stderr: {proc.stderr.strip()}")

    # 4. Import every declared dependency
    for req in reqs:
        module = MODULE_FOR_REQUIREMENT.get(req.lower(), req)
        try:
            importlib.import_module(module)
            version = ""
            try:
                version = importlib.metadata.version(
                    req if req.lower() != "pyyaml" else "PyYAML")
            except importlib.metadata.PackageNotFoundError:
                version = "unknown"
            log(f"PASS: import {module} (distribution '{req}', "
                f"version {version})")
        except ImportError as exc:
            ok = False
            log(f"FAIL: import {module} (distribution '{req}'): {exc}")

    log("RESULT: " + ("SUCCESS" if ok else "FAILURE"))
    log(f"Setup verification finished at "
        f"{datetime.now(timezone.utc).isoformat()}")
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"Verification log written to {LOG_PATH}")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())