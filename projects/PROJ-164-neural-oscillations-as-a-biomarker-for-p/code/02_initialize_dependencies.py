"""
T002: Initialize Python 3.11 project with requirements.txt.

This script ensures the requirements.txt file exists with the exact content
specified in the task, and attempts to install the dependencies.
"""
import os
import subprocess
import sys
from pathlib import Path

REQUIREMENTS_CONTENT = """mne==1.7.0
scikit-learn==1.4.0
numpy==1.26.0
pandas==2.1.0
scipy==1.12.0
statsmodels==0.14.1
pyyaml==6.0.1
pytest==7.4.0
"""

def main():
    project_root = Path(__file__).resolve().parent.parent
    req_file = project_root / "requirements.txt"

    # 1. Write requirements.txt with exact content
    print(f"Writing requirements.txt to: {req_file}")
    req_file.write_text(REQUIREMENTS_CONTENT.strip())

    # 2. Verify file content matches exactly
    current_content = req_file.read_text()
    expected_content = REQUIREMENTS_CONTENT.strip()

    if current_content != expected_content:
        print("ERROR: requirements.txt content mismatch after writing.")
        print(f"Expected:\n{expected_content}")
        print(f"Got:\n{current_content}")
        sys.exit(1)
    
    print("requirements.txt content verified.")

    # 3. Install dependencies
    print("Installing dependencies via pip...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            check=True,
            capture_output=False,
            text=True
        )
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies. Exit code: {e.returncode}")
        sys.exit(1)

    print("T002 Initialization complete.")

if __name__ == "__main__":
    main()