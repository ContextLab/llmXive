"""
Task T002: Initialize Python 3.11 project with requirements.txt.

This script creates the requirements.txt file with the exact content
specified in the task description and installs the dependencies.
"""
import os
import subprocess
import sys
from pathlib import Path


def create_requirements_file():
    """Create requirements.txt with exact content from task specification."""
    requirements_content = (
        "mne==1.7.0\n"
        "scikit-learn==1.4.0\n"
        "numpy==1.26.0\n"
        "pandas==2.1.0\n"
        "scipy==1.12.0\n"
        "statsmodels==0.14.1\n"
        "pyyaml==6.0.1\n"
        "pytest==7.4.0"
    )
    
    project_root = Path(__file__).parent.parent
    requirements_path = project_root / "requirements.txt"
    
    with open(requirements_path, "w", encoding="utf-8") as f:
        f.write(requirements_content)
    
    print(f"Created {requirements_path}")
    return requirements_path


def install_dependencies(requirements_path: Path) -> None:
    """Install dependencies from requirements.txt."""
    print(f"Installing dependencies from {requirements_path}...")
    
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Failed to install dependencies. Exit code: {result.returncode}")
    
    print("Dependencies installed successfully.")


def verify_requirements_content(requirements_path: Path) -> bool:
    """Verify that requirements.txt content matches specification exactly."""
    expected_content = (
        "mne==1.7.0\n"
        "scikit-learn==1.4.0\n"
        "numpy==1.26.0\n"
        "pandas==2.1.0\n"
        "scipy==1.12.0\n"
        "statsmodels==0.14.1\n"
        "pyyaml==6.0.1\n"
        "pytest==7.4.0"
    )
    
    with open(requirements_path, "r", encoding="utf-8") as f:
        actual_content = f.read()
    
    if actual_content == expected_content:
        print("✓ requirements.txt content verified successfully.")
        return True
    else:
        print("✗ requirements.txt content does not match specification.")
        print(f"Expected:\n{expected_content}")
        print(f"Actual:\n{actual_content}")
        return False


def main():
    """Main entry point for T002."""
    print("=== Task T002: Initialize Python 3.11 project with requirements.txt ===")
    
    # Create requirements.txt
    requirements_path = create_requirements_file()
    
    # Install dependencies
    install_dependencies(requirements_path)
    
    # Verify content
    if not verify_requirements_content(requirements_path):
        raise RuntimeError("Requirements file verification failed.")
    
    print("=== Task T002 completed successfully ===")


if __name__ == "__main__":
    main()