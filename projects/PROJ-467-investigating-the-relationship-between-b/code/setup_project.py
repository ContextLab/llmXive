"""
Project initialization script for T002.
Validates requirements.txt and pyproject.toml existence and content.
"""
import os
from pathlib import Path

def main():
    """
    Initializes the Python 3.11 project structure for T002.
    Verifies that requirements.txt and pyproject.toml are present and valid.
    """
    project_root = Path(__file__).parent
    requirements_path = project_root / "requirements.txt"
    pyproject_path = project_root / "pyproject.toml"

    print(f"Initializing project in: {project_root}")

    # Verify requirements.txt
    if not requirements_path.exists():
        raise FileNotFoundError(f"Missing requirements.txt at {requirements_path}")

    with open(requirements_path, "r") as f:
        content = f.read()
        required_deps = [
            "numpy", "pandas", "nilearn", "networkx", "scikit-learn",
            "statsmodels", "pingouin", "datasets", "pytest", "jsonschema"
        ]
        missing = [dep for dep in required_deps if not any(dep in line for line in content.splitlines())]
        if missing:
            raise ValueError(f"Missing dependencies in requirements.txt: {missing}")
    
    print("✓ requirements.txt validated successfully.")

    # Verify pyproject.toml
    if not pyproject_path.exists():
        raise FileNotFoundError(f"Missing pyproject.toml at {pyproject_path}")

    with open(pyproject_path, "r") as f:
        content = f.read()
        if "[project]" not in content or "requires-python" not in content:
            raise ValueError("pyproject.toml is missing required [project] section or python version.")
    
    print("✓ pyproject.toml validated successfully.")

    print("Project initialization complete. Ready to run: pip install -e .")
    return 0

if __name__ == "__main__":
    exit(main())
