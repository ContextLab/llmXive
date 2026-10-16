"""Install project dependencies from requirements.txt (T001).

Runs ``pip install -r requirements.txt`` and records the full
installation log, including a final success message, at
``logs/requirements_install.log`` as required by task T001.

Exits non-zero (and records the failure in the log) if pip fails,
so the run never silently pretends the install succeeded.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
LOG_PATH = PROJECT_ROOT / "logs" / "requirements_install.log"


def main() -> int:
    if not REQUIREMENTS.is_file():
        raise FileNotFoundError(f"requirements.txt not found at {REQUIREMENTS}")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    header = [
        f"# requirements install log (T001)",
        f"# generated: {datetime.now(timezone.utc).isoformat()}",
        f"# command: pip install -r requirements.txt",
        f"# python: {sys.version.split()[0]}",
        "",
    ]

    proc = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)],
        capture_output=True,
        text=True,
    )

    lines = header + [proc.stdout.rstrip(), proc.stderr.rstrip()]

    if proc.returncode == 0:
        lines.append("")
        lines.append(
            "SUCCESS: pip install -r requirements.txt completed without error "
            f"(exit code 0) at {datetime.now(timezone.utc).isoformat()}"
        )
    else:
        lines.append("")
        lines.append(
            f"FAILURE: pip install -r requirements.txt exited with code {proc.returncode}"
        )

    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Echo the log for the runner's console evidence.
    print(f"Wrote install log to {LOG_PATH}")
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())