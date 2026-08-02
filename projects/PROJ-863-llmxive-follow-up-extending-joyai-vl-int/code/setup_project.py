import os
from pathlib import Path

def main():
    """
    Initialize the project directory structure as per T001 and T002 requirements.
    This script creates the necessary folders and ensures the requirements.txt is present.
    """
    base_path = Path(__file__).resolve().parent.parent
    
    # Define required directories
    directories = [
        "code/src/data_synthesis",
        "code/src/feature_extraction",
        "code/src/baseline",
        "code/src/scheduler",
        "code/src/utils",
        "code/tests/unit",
        "code/tests/integration",
        "data/raw",
        "data/features",
        "data/baseline",
        "data/evaluation",
        "models",
        "figures",
        "specs/001-llmxive-vl-intuition"
    ]

    # Create directories
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Verify requirements.txt exists
    requirements_path = base_path / "requirements.txt"
    if not requirements_path.exists():
        print("WARNING: requirements.txt not found in project root.")
        print("Please ensure 'requirements.txt' is present for T002.")
    else:
        print("Found requirements.txt.")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
