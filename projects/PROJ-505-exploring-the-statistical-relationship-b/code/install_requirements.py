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
    project_root = Path(__file__).resolve().parents[1]  # code/install_requirements.py -> project root
    req_path = project_root / "requirements.txt"
    log_path = project_root / "ci" / "install_log.txt"

    # Ensure the ci directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Upgrade pip first to ensure the latest installer is used.
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        capture_output=True,
        text=True
    )

    # 2. Run pip install.
    # We use --upgrade and --force-reinstall to guarantee that pip prints the 
    # "Successfully installed" line for the requested packages,
    # which is a strict requirement for the integration test T001.
    # We align numpy to 2.0.* per plan.md to avoid conflicts with platform pre-installs.
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--force-reinstall",
        "-r",
        str(req_path),
    ]
    
    # Capture combined stdout and stderr
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8"
    )

    # Write the combined output to the log file
    log_path.write_text(result.stdout, encoding="utf-8")

    # Exit with the same return code as pip.
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
