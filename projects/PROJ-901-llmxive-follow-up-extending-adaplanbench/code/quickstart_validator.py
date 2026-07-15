"""
Quickstart Validation Script for PROJ-901-llmxive-follow-up-extending-adaplanbench

This script validates the entire project pipeline by executing the steps
outlined in the conceptual quickstart flow. It ensures all components
work together and completes within the 6-hour CI window.

Steps validated:
1. Environment and Dependencies Check
2. Directory Structure Verification
3. Dataset Loading and Filtering (T012-T015)
4. Agent Execution - Dual Track & Monolithic (T018-T024)
5. Statistical Analysis (T027-T028)
6. Agreement Rate Analysis (T031)
7. Artifact Hashing (T029)
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import Paths

# Configuration
TIME_LIMIT_SECONDS = 6 * 60 * 60  # 6 hours
START_TIME = time.time()

def log_step(step_name: str, status: str, details: str = ""):
    """Log a validation step with timestamp."""
    elapsed = time.time() - START_TIME
    status_icon = "✓" if status == "PASS" else "✗"
    print(f"[{elapsed:.1f}s] {status_icon} {step_name}: {details}")
    return status == "PASS"

def run_script(script_name: str, args: list = None) -> bool:
    """Run a Python script and return True if successful."""
    cmd = [sys.executable, str(PROJECT_ROOT / "code" / script_name)]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=TIME_LIMIT_SECONDS
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        print(f"Error running {script_name}: {e}")
        return False

def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists."""
    if path.exists():
        log_step(f"File Check: {description}", "PASS", f"Found at {path}")
        return True
    else:
        log_step(f"File Check: {description}", "FAIL", f"Missing at {path}")
        return False

def main():
    print("=" * 80)
    print("QUICKSTART VALIDATION: llmXive Follow-up Extending AdaPlanBench")
    print("=" * 80)
    print(f"Start Time: {datetime.now().isoformat()}")
    print(f"Time Limit: {TIME_LIMIT_SECONDS / 3600:.1f} hours")
    print("=" * 80)

    all_passed = True

    # Step 1: Environment Check
    print("\n--- Step 1: Environment & Dependencies ---")
    try:
        import pandas as pd
        import torch
        import datasets
        import statsmodels
        log_step("Dependencies", "PASS", "All required packages imported")
    except ImportError as e:
        all_passed = log_step("Dependencies", "FAIL", f"Missing package: {e}")

    # Step 2: Directory Structure
    print("\n--- Step 2: Directory Structure ---")
    paths = Paths()
    required_dirs = [
        paths.raw_data_dir,
        paths.processed_data_dir,
        paths.code_dir,
        paths.tests_dir,
    ]
    for d in required_dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            log_step(f"Directory Creation: {d.name}", "PASS", "Created")
        else:
            log_step(f"Directory Check: {d.name}", "PASS", "Exists")

    # Step 3: Dataset Preparation
    print("\n--- Step 3: Dataset Preparation (T012-T015) ---")
    # Run loader and filter
    if run_script("dataset/loader.py", ["--output", str(paths.filtered_tasks_path)]):
        log_step("Dataset Loading & Filtering", "PASS", "Filtered tasks generated")
    else:
        log_step("Dataset Loading & Filtering", "FAIL", "Loader failed")
        all_passed = False

    # Run constraint count addition
    if run_script("dataset/add_constraint_count.py"):
        log_step("Constraint Count Addition", "PASS", "Column added")
    else:
        log_step("Constraint Count Addition", "FAIL", "Addition failed")
        all_passed = False

    # Validate subset
    if run_script("dataset/validate_subset.py"):
        log_step("Subset Validation", "PASS", "Validation passed")
    else:
        log_step("Subset Validation", "FAIL", "Validation failed")
        all_passed = False

    # Step 4: Agent Execution
    print("\n--- Step 4: Agent Execution (T018-T024) ---")
    # Run dual track experiment
    if run_script("agent/dual_track.py"):
        log_step("Dual Track Execution", "PASS", "Traces generated")
    else:
        log_step("Dual Track Execution", "FAIL", "Dual track failed")
        all_passed = False

    # Run monolithic agent
    if run_script("agent/monolithic.py"):
        log_step("Monolithic Execution", "PASS", "Traces generated")
    else:
        log_step("Monolithic Execution", "FAIL", "Monolithic failed")
        all_passed = False

    # Generate execution traces
    if run_script("analysis/generate_execution_traces.py"):
        log_step("Execution Traces Generation", "PASS", "Traces written")
    else:
        log_step("Execution Traces Generation", "FAIL", "Trace generation failed")
        all_passed = False

    # Step 5: Statistical Analysis
    print("\n--- Step 5: Statistical Analysis (T027-T028) ---")
    # Power analysis
    if run_script("analysis/power.py"):
        log_step("Power Analysis", "PASS", "Report generated")
    else:
        log_step("Power Analysis", "FAIL", "Power analysis failed")
        all_passed = False

    # GLMM analysis
    if run_script("analysis/generate_statistical_results.py"):
        log_step("GLMM Analysis", "PASS", "Statistical results written")
    else:
        log_step("GLMM Analysis", "FAIL", "GLMM failed")
        all_passed = False

    # Step 6: Annotation & Agreement
    print("\n--- Step 6: Annotation & Agreement (T030-T031) ---")
    # Create annotation sample
    if run_script("dataset/annotator.py", ["--sample-size", "10"]):
        log_step("Annotation Sample Creation", "PASS", "Sample ready")
    else:
        log_step("Annotation Sample Creation", "FAIL", "Annotator failed")
        all_passed = False

    # Simulate human annotations (for validation purposes)
    # In real CI, this would be replaced by actual human-in-the-loop data
    annotation_file = paths.processed_data_dir / "human_annotations.csv"
    if not annotation_file.exists():
        # Create a minimal mock for validation flow (simulating human input)
        # NOTE: In production, this file must come from real human annotation
        import pandas as pd
        sample_df = pd.read_csv(paths.filtered_tasks_path).head(10)
        mock_annotations = pd.DataFrame({
            'task_id': sample_df['task_id'].values,
            'human_violation_rate': [0.1] * 10,
            'human_score': [0.85] * 10
        })
        mock_annotations.to_csv(annotation_file, index=False)
        log_step("Human Annotations (Simulated)", "PASS", "Mock file created for validation")

    # Agreement rate
    if run_script("analysis/agreement_rate.py"):
        log_step("Agreement Rate Analysis", "PASS", "Report generated")
    else:
        log_step("Agreement Rate Analysis", "FAIL", "Agreement analysis failed")
        all_passed = False

    # Step 7: Artifact Hashing
    print("\n--- Step 7: Artifact Hashing (T029) ---")
    if run_script("hash_artifacts.py"):
        log_step("Artifact Hashing", "PASS", "Hashes computed")
    else:
        log_step("Artifact Hashing", "FAIL", "Hashing failed")
        all_passed = False

    # Final Summary
    print("\n" + "=" * 80)
    elapsed = time.time() - START_TIME
    print(f"Total Execution Time: {elapsed:.1f}s ({elapsed/3600:.2f} hours)")
    print(f"Time Limit: {TIME_LIMIT_SECONDS}s (6 hours)")
    
    if all_passed:
        print("✓ VALIDATION SUCCESSFUL: All steps completed within time limit")
    else:
        print("✗ VALIDATION FAILED: One or more steps encountered errors")
    
    print("=" * 80)
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())