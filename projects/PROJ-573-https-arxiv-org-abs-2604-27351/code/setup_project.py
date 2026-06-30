"""
Project initialization script for llmXive Benchmark.
Sets up virtual environment, installs dependencies, and validates structure.
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main entry point for project setup."""
    root = Path(__file__).parent.resolve()
    print(f"Initializing project at: {root}")

    # Ensure Python 3.11
    if sys.version_info < (3, 11):
        print(f"ERROR: Python 3.11+ required, found {sys.version}")
        sys.exit(1)

    # Create virtual environment if not exists
    venv_path = root / ".venv"
    if not venv_path.exists():
        print("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])

    # Install dependencies
    pip_path = venv_path / "bin" / "pip" if os.name != "nt" else venv_path / "Scripts" / "pip"
    print("Installing dependencies...")
    subprocess.check_call([str(pip_path), "install", "-r", str(root / "requirements.txt")])

    # Verify structure
    required_dirs = [
        "src", "tests", "data", "data/processed", "state",
        "contracts", "src/benchmark", "src/models", "src/tasks",
        "src/evaluation", "src/utils", "src/benchmark/config",
        "src/benchmark/config/modalities", "src/research", "src/validators"
    ]
    for d in required_dirs:
        path = root / d
        if not path.exists():
            print(f"Creating directory: {path}")
            path.mkdir(parents=True, exist_ok=True)

    print("Project initialization complete.")
    print("Run: source .venv/bin/activate (or .venv\\Scripts\\activate on Windows)")

if __name__ == "__main__":
    main()
