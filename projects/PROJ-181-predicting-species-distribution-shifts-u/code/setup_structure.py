import os
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure for PROJ-181-predicting-species-distribution-shifts-u.
    Creates the required Data, Code, and Reports directory trees.
    """
    # Define the project root relative to the script location or current working directory
    # Assuming the script is run from the project root or code/ directory
    current_path = Path(__file__).resolve().parent
    project_root = current_path.parent

    project_name = "PROJ-181-predicting-species-distribution-shifts-u"
    project_dir = project_root / "projects" / project_name

    # Phase 1: Data Directories
    data_root = project_dir / "data"
    data_raw = data_root / "raw"
    data_processed = data_root / "processed"
    data_artifacts = data_root / "artifacts"

    # Phase 1: Code Directories
    code_root = project_dir / "code"
    code_utils = code_root / "utils"
    tests_unit = project_dir / "tests" / "unit"
    tests_integration = project_dir / "tests" / "integration"

    # Phase 1: Reports/Metrics Directories
    metrics_root = project_dir / "metrics"
    reports_root = project_dir / "reports"
    logs_root = project_dir / "logs"
    state_root = project_dir / "state"
    contracts_root = project_dir / "contracts"

    # Define all directories to create
    directories = [
        # Data
        data_root,
        data_raw,
        data_processed,
        data_artifacts,
        
        # Code
        code_root,
        code_utils,
        tests_unit,
        tests_integration,
        
        # Reports/Metrics
        metrics_root,
        reports_root,
        logs_root,
        state_root,
        contracts_root,
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created: {directory}")
            created_count += 1
        else:
            print(f"Exists: {directory}")

    print(f"\nProject structure initialization complete.")
    print(f"Created {created_count} new directories under {project_dir}")

    # Return the project path for potential downstream usage
    return project_dir

if __name__ == "__main__":
    main()