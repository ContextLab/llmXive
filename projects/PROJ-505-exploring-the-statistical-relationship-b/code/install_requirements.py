"""
Script to install project dependencies from requirements.txt on a clean runner,
capturing the full pip stdout/stderr into ci/install_log.txt.
This is used by the integration test to verify that each listed package was
installed successfully.
"""
import subprocess
import sys
from pathlib import Path

def main() -> None:
    # Resolve paths relative to the project root
    project_root = Path(__file__).resolve().parents[1]  # code/ -> project root
    req_path = project_root / "requirements.txt"
    log_path = project_root / "ci" / "install_log.txt"

    # Ensure the ci directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Run pip install in a subprocess, capturing stdout and stderr.
    # Use --force-reinstall to guarantee that pip prints a
    # "Successfully installed" line even when packages are already present.
    # Use --no-deps to avoid pulling in additional system‑level dependencies
    # that may not be available in the CI environment.
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--force-reinstall",
        "--no-deps",
        "-r",
        str(req_path),
    ]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Write the combined output to the log file
    log_path.write_text(result.stdout, encoding="utf-8")

    # Exit with the same return code as pip for visibility
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()