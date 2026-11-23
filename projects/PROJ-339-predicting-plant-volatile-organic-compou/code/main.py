import os
import sys
import subprocess
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent
CODE_DIR = PROJECT_ROOT
DATA_DIR = PROJECT_ROOT.parent / "data"

def run_step(script_name):
    """Runs a specific script in the code directory."""
    script_path = CODE_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    print(f"Running {script_name}...")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        check=True
    )
    return result.returncode

def main():
    """
    Orchestrates the full pipeline execution.
    This script is invoked by quickstart.md.
    """
    try:
        # Step 1: Ingest and Merge (Produces merged_dataset.csv)
        # Note: 01_ingest.py and 02_merge.py are separate steps in the spec,
        # but often 01_ingest handles the full raw->processed flow or calls merge.
        # Based on the error logs, 01_ingest.py is expected to produce merged_data or call merge.
        # However, tasks.md shows T014 (TPM) and T015 (Merge) as separate.
        # We will run them sequentially.
        
        # T012/T014: Ingest and Normalize
        run_step("01_ingest.py")
        
        # T015: Merge
        run_step("02_merge.py")
        
        # T016/T017: Aggregate and Validate
        run_step("03_aggregate.py")
        run_step("05_validate.py")
        
        # T020/T021/T023/T024: Train Model (Produces model_metrics.json, random_forest.pkl)
        run_step("03_train.py")
        
        # T028/T029/T030: Interpret
        run_step("04_interpret.py")
        
        # T031: Overlap
        run_step("05_overlap_analysis.py")
        
        # T033: Stability
        run_step("05_validate_stability.py")
        
        # T025/T032: Generate Report (Produces interpretation_report.json)
        run_step("06_generate_report.py")
        
        print("Pipeline execution completed successfully.")
        
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed at step: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
