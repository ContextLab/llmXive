import os
from pathlib import Path

def main():
    """
    Creates the results directory for the project.
    Path: projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/results/
    """
    # Determine the project root based on the known structure
    # Assuming this script runs from the project root or code directory
    # We use the absolute path logic to ensure the target is created correctly
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    results_dir = project_root / "results"
    
    if not results_dir.exists():
        results_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created results directory: {results_dir}")
    else:
        print(f"Results directory already exists: {results_dir}")
    
    return results_dir

if __name__ == "__main__":
    main()
