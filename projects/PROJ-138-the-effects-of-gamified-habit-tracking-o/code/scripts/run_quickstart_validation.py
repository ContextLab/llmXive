import os
import sys
import subprocess
import json
import shutil
from pathlib import Path

def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: Command failed with return code {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        raise RuntimeError(f"Command failed: {cmd}")
    return result

def check_file_exists(path: str) -> bool:
    """Check if a file exists."""
    exists = os.path.exists(path)
    if not exists:
        print(f"Missing file: {path}")
    return exists

def check_dependency_files() -> bool:
    """Check that all dependency files required for the pipeline exist."""
    required_files = [
        "contracts/dataset.schema.yaml",       # T009
        "code/data/power_analysis.py",         # T048
        "code/data/ingestion.py",              # T013b
        "code/data/aggregation.py",            # T014
        "code/data/synthetic_generator.py",    # T013a
        "code/data/validation.py",             # T012a
        "code/utils/config.py",                # T005
        "code/utils/logging.py",               # T006
        "code/data/models.py",                 # T007
    ]
    
    all_exist = True
    for f in required_files:
        if not check_file_exists(f):
            all_exist = False
    
    return all_exist

def run_quickstart():
    """Execute the quickstart validation steps."""
    print("=== Quickstart Validation ===")
    
    # 1. Pre-flight checks
    print("\n1. Checking dependency files...")
    if not check_dependency_files():
        raise RuntimeError("Dependency check failed. Cannot proceed.")
    
    # 2. Ensure directories exist (T001)
    print("\n2. Ensuring directory structure...")
    dirs = [
        "code/data", "code/analysis", "code/reports", "code/utils", "code/tests",
        "data/raw", "data/processed", "data/consent"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        # Ensure gitkeep exists
        gitkeep = os.path.join(d, ".gitkeep")
        if not os.path.exists(gitkeep):
            Path(gitkeep).touch()
    
    # 3. Run Power Analysis (T048)
    print("\n3. Running Power Analysis...")
    run_command("python code/data/power_analysis.py")
    
    # 4. Run Consent Check (T012a)
    print("\n4. Running Consent Check...")
    run_command("python code/data/validation.py")
    
    # 5. Generate Synthetic Data (T013a-1, T013a-2)
    # Note: Using a fixed seed for reproducibility in validation
    print("\n5. Generating Synthetic Data...")
    # The quickstart.md might have used [RANDOM_SEED], but we use a fixed seed for validation
    # to ensure the run is deterministic and reproducible.
    run_command("python code/data/synthetic_generator.py --seed 42 --n_users 500 --weeks 50")
    
    # 6. Run Ingestion (T013b)
    print("\n6. Running Ingestion...")
    run_command("python code/data/ingestion.py")
    
    # 7. Run Aggregation (T014)
    print("\n7. Running Aggregation...")
    run_command("python code/data/aggregation.py")
    
    # 8. Run Validation (T012b, T012c)
    print("\n8. Running Validation (Cronbach's Alpha)...")
    run_command("python code/data/validation.py") # This might need a specific subcommand if implemented, but main() handles it
    
    # 9. Verify Output Artifacts
    print("\n9. Verifying Output Artifacts...")
    required_outputs = [
        "data/processed/merged_data.csv",
        "data/processed/psychometrics.json",
        "data/raw/synthetic_data.csv",
        "data/raw/synthetic_data_marker.json"
    ]
    
    all_exist = True
    for f in required_outputs:
        if not check_file_exists(f):
            all_exist = False
        else:
            # Check if file is non-empty
            if os.path.getsize(f) == 0:
                print(f"Error: File {f} is empty.")
                all_exist = False
    
    if not all_exist:
        raise RuntimeError("Required output artifacts are missing or empty.")
    
    print("\n=== Quickstart Validation SUCCESSFUL ===")
    return 0

def main():
    try:
        exit_code = run_quickstart()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Validation FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
