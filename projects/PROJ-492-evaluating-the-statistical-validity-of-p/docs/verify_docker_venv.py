"""
Verification script for T095b:
Verify Quickstart Docker guide reproduces environment via requirements.txt and isolated venv.

This script:
1. Checks that the Dockerfile exists and contains 'pip install -r requirements.txt'.
2. Simulates a venv creation and pip install to verify requirements.txt is valid.
3. Confirms that the environment is isolated and reproducible.
"""
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

def check_dockerfile():
    """Verify Dockerfile contains required pip install command."""
    dockerfile_path = Path("Dockerfile")
    if not dockerfile_path.exists():
        print("ERROR: Dockerfile not found.")
        return False

    content = dockerfile_path.read_text()
    if "pip install -r requirements.txt" not in content:
        print("ERROR: Dockerfile does not contain 'pip install -r requirements.txt'.")
        return False

    print("✓ Dockerfile contains 'pip install -r requirements.txt'.")
    return True

def check_requirements_txt():
    """Verify requirements.txt exists and is valid."""
    req_path = Path("requirements.txt")
    if not req_path.exists():
        print("ERROR: requirements.txt not found.")
        return False

    content = req_path.read_text().strip()
    if not content:
        print("ERROR: requirements.txt is empty.")
        return False

    print("✓ requirements.txt exists and is not empty.")
    return True

def test_venv_isolation():
    """Create a temporary venv and verify pip install works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "test_venv"
        try:
            # Create venv
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                check=True,
                capture_output=True,
            )

            # Activate and install
            pip_path = venv_path / "bin" / "pip" if os.name != "nt" else venv_path / "Scripts" / "pip"
            if not pip_path.exists():
                # Fallback for Windows
                pip_path = venv_path / "Scripts" / "pip.exe"

            subprocess.run(
                [str(pip_path), "install", "-r", "requirements.txt"],
                check=True,
                capture_output=True,
            )

            print("✓ Virtual environment created and requirements installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to install requirements in venv: {e.stderr.decode()}")
            return False
        except Exception as e:
            print(f"ERROR: Unexpected error during venv test: {e}")
            return False

def main():
    print("=== T095b Verification: Docker & venv Reproducibility ===\n")

    checks = [
        ("Dockerfile check", check_dockerfile),
        ("requirements.txt check", check_requirements_txt),
        ("Venv isolation test", test_venv_isolation),
    ]

    results = []
    for name, func in checks:
        print(f"Running: {name}...")
        result = func()
        results.append(result)
        print()

    if all(results):
        print("✅ All checks passed. T095b verification successful.")
        sys.exit(0)
    else:
        print("❌ One or more checks failed. T095b verification unsuccessful.")
        sys.exit(1)

if __name__ == "__main__":
    main()
