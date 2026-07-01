"""
Task T002: Initialize Python 3 project with requirements.txt.

This script creates the requirements.txt file with the exact dependencies
specified in the task description and verifies installability via dry-run.
"""
import subprocess
import sys
import os
from pathlib import Path

REQUIRED_DEPS = [
    "pandas==2.0.3",
    "openml==0.14.2",
    "statsmodels==0.14.1",
    "requests==2.31.0",
    "matplotlib==3.8.0",
    "pytest==7.4.0",
    "beautifulsoup4==4.12.2",
]

def create_requirements_file() -> Path:
    """Create requirements.txt with the exact specified dependencies."""
    root = Path(__file__).resolve().parent.parent
    req_path = root / "requirements.txt"
    
    content = "\n".join(REQUIRED_DEPS) + "\n"
    
    with open(req_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return req_path

def verify_installability(req_path: Path) -> bool:
    """Verify that requirements.txt is installable using pip dry-run."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_path), "--dry-run"],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Verification failed: {e.stderr}")
        return False

def main():
    """Main entry point for T002."""
    print("Creating requirements.txt...")
    req_path = create_requirements_file()
    print(f"Created: {req_path}")
    
    print("Verifying installability (dry-run)...")
    if verify_installability(req_path):
        print("SUCCESS: requirements.txt is valid and installable.")
        return 0
    else:
        print("FAILED: requirements.txt verification failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())