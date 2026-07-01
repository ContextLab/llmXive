import os
from pathlib import Path

def main():
    """
    Initialize the Python 3.11 project environment.
    
    This function:
    1. Creates the project directory structure (if not exists).
    2. Ensures requirements.txt exists with the specified dependencies.
    3. Prints instructions for installing dependencies and setting up the environment.
    
    Note: This script does not automatically run `pip install`. It ensures the 
    configuration files are in place so the user can run the installation.
    """
    project_root = Path(__file__).parent.parent
    requirements_path = project_root / "code" / "requirements.txt"
    
    # Ensure directories exist
    dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "results/figures",
        "metadata",
        "contracts",
        "specs"
    ]
    
    for d in dirs:
        (project_root / d).mkdir(parents=True, exist_ok=True)
    
    # Ensure requirements.txt exists
    if not requirements_path.exists():
        print(f"Creating {requirements_path}")
        with open(requirements_path, "w") as f:
            f.write("numpy>=1.24.0\n")
            f.write("pandas>=2.0.0\n")
            f.write("nilearn>=0.10.0\n")
            f.write("networkx>=3.0.0\n")
            f.write("scikit-learn>=1.2.0\n")
            f.write("statsmodels>=0.14.0\n")
            f.write("pingouin>=0.5.0\n")
            f.write("datasets>=2.14.0\n")
            f.write("pytest>=7.0.0\n")
            f.write("jsonschema>=4.17.0\n")
        print("requirements.txt created.")
    else:
        print(f"{requirements_path} already exists.")
    
    print("\nProject structure initialized.")
    print(f"Python version recommended: 3.11")
    print(f"To install dependencies, run: pip install -r {requirements_path}")
    print(f"To run tests, run: pytest tests/")

if __name__ == "__main__":
    main()
