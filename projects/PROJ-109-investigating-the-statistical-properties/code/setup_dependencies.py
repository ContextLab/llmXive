import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        raise

def main():
    """
    Initialize Python 3.11 project with dependencies.
    
    1. Ensure pip, setuptools, wheel are installed/upgraded.
    2. Install core research dependencies: pandas, numpy, scipy.
    3. Generate requirements.txt using pip freeze.
    """
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "requirements.txt"

    print(f"Project root: {project_root}")

    # Step 1: Upgrade core build tools
    print("\n--- Step 1: Upgrading pip, setuptools, wheel ---")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])

    # Step 2: Install core dependencies
    print("\n--- Step 2: Installing pandas, numpy, scipy ---")
    run_command([
        sys.executable, "-m", "pip", "install",
        "pandas",
        "numpy",
        "scipy"
    ])

    # Step 3: Generate requirements.txt
    print("\n--- Step 3: Generating requirements.txt ---")
    run_command([sys.executable, "-m", "pip", "freeze"], check=False)
    
    # Capture freeze output to file
    freeze_result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=True
    )
    
    with open(requirements_path, "w") as f:
        f.write(f"# Generated on {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}\n")
        f.write(f"# Python {sys.version}\n\n")
        f.write(freeze_result.stdout)
    
    print(f"Successfully wrote {requirements_path}")
    print(f"Contents:\n{freeze_result.stdout}")

if __name__ == "__main__":
    main()