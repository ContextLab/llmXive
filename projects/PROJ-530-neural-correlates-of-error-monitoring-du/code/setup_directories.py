import os
from pathlib import Path

def create_project_directories():
    """
    Creates the necessary directory structure for the project.
    Specifically targets the data directories required for T002:
    - projects/PROJ-530-neural-correlates-of-error-monitoring-du/data/raw/
    - projects/PROJ-530-neural-correlates-of-error-monitoring-du/data/processed/
    
    Also ensures other standard directories exist if they don't (based on T003/T008 context).
    """
    project_root = Path("projects/PROJ-530-neural-correlates-of-error-monitoring-du")
    
    # Define the specific paths required by T002
    data_raw = project_root / "data" / "raw"
    data_processed = project_root / "data" / "processed"
    
    # Additional directories to ensure a complete project structure (T003/T008 context)
    results_models = project_root / "results" / "models"
    results_figures = project_root / "results" / "figures"
    results_diagnostics = project_root / "results" / "diagnostics"
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"
    state_dir = project_root / "state"
    
    all_dirs = [
        data_raw,
        data_processed,
        results_models,
        results_figures,
        results_diagnostics,
        code_dir,
        tests_dir,
        state_dir
    ]
    
    created_count = 0
    for directory in all_dirs:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {directory}")
        else:
            # Verify they are actually directories, not files
            if not directory.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {directory}")
    
    print(f"Directory setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    create_project_directories()
