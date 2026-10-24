"""Setup script for the project.

This script performs the following steps:

1. Computes a SHA‑256 checksum of the top‑level ``requirements.txt`` file
   and writes it to ``requirements_checksum.txt`` (project root).

2. Installs the pinned requirements using ``pip install -r requirements.txt``
   inside the current Python environment.

3. Captures the output of the installation as well as the output of
   ``pip list`` and writes both to ``setup_log.txt`` (project root).

The script is intended to be run from the project root with:
    python code/setup_requirements.py
"""

import hashlib
import subprocess
import sys
from pathlib import Path


def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def run_command(command: list[str]) -> str:
    """Run ``command`` and return its combined stdout+stderr."""
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return result.stdout


def main() -> None:
    # Resolve project‑root (two levels up from this file: code/ -> project root)
    project_root = Path(__file__).resolve().parents[2]

    # ------------------------------------------------------------------
    # 1. Compute and write requirements checksum
    # ------------------------------------------------------------------
    req_path = project_root / "requirements.txt"
    if not req_path.is_file():
        sys.exit(f"Error: requirements.txt not found at {req_path}")

    checksum = compute_sha256(req_path)
    checksum_path = project_root / "requirements_checksum.txt"
    checksum_path.write_text(f"{checksum}\\n")
    print(f"SHA‑256 checksum written to {checksum_path}")

    # ------------------------------------------------------------------
    # 2. Install requirements and capture log
    # ------------------------------------------------------------------
    install_cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_path)]
    print("Installing requirements…")
    install_output = run_command(install_cmd)

    # ------------------------------------------------------------------
    # 3. Capture pip list output
    # ------------------------------------------------------------------
    pip_list_cmd = [sys.executable, "-m", "pip", "list"]
    print("Gathering pip list…")
    pip_list_output = run_command(pip_list_cmd)

    # ------------------------------------------------------------------
    # 4. Write combined log
    # ------------------------------------------------------------------
    log_path = project_root / "setup_log.txt"
    log_contents = (
        f"Python version: {sys.version}\\n"
        f"{'='*40} pip install output {'='*40}\\n"
        f"{install_output}\\n"
        f"{'='*40} pip list output {'='*40}\\n"
        f"{pip_list_output}\\n"
    )
    log_path.write_text(log_contents)
    print(f"Setup log written to {log_path}")


if __name__ == "__main__":
    main()