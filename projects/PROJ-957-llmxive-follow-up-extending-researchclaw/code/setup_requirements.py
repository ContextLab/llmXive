"""
setup_requirements.py
Generates the requirements.txt file for the llmXive project.
Ensures the project has all necessary dependencies for Python 3.11.
"""
from pathlib import Path

REQUIRED_DEPENDENCIES = [
    "pandas>=2.0.0",
    "scipy>=1.11.0",
    "pytest>=7.4.0",
    "pyyaml>=6.0.1",
    "jsonschema>=4.19.0",
    "datasets>=2.14.0",
    "tqdm>=4.66.0",
    "numpy>=1.24.0",
    "statsmodels>=0.14.0",
]

def ensure_requirements(project_root: Path) -> None:
    """
    Creates or updates the requirements.txt file in the project root
    with the list of required dependencies.
    
    Args:
        project_root: The root directory of the project.
    """
    requirements_path = project_root / "requirements.txt"
    
    content = "# llmXive Project Dependencies\n"
    content += "# Generated for Python 3.11+\n"
    content += "\n".join(REQUIRED_DEPENDENCIES) + "\n"
    
    with open(requirements_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Successfully wrote requirements to: {requirements_path}")

if __name__ == "__main__":
    import sys
    # Default to current directory if no argument provided
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    ensure_requirements(root)
