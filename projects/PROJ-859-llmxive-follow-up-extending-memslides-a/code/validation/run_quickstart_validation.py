import sys
import os
import json
import subprocess
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

class QuickstartValidationError(Exception):
    """Raised when quickstart validation fails."""
    pass

def log_step(message: str):
    logger.info(f"STEP: {message}")

def log_success(message: str):
    logger.info(f"✅ SUCCESS: {message}")

def log_error(message: str):
    logger.error(f"❌ ERROR: {message}")

def check_file_exists(path: Path):
    if not path.exists():
        raise QuickstartValidationError(f"File not found: {path}")
    log_success(f"File exists: {path}")

def check_file_not_empty(path: Path):
    if not path.exists():
        raise QuickstartValidationError(f"File not found: {path}")
    if path.stat().st_size == 0:
        raise QuickstartValidationError(f"File is empty: {path}")
    log_success(f"File not empty: {path}")

def validate_json_structure(path: Path, required_keys: Optional[List[str]] = None):
    check_file_exists(path)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if required_keys:
            missing = [k for k in required_keys if k not in data]
            if missing:
                raise QuickstartValidationError(f"Missing keys in {path}: {missing}")
        log_success(f"Valid JSON structure: {path}")
        return data
    except json.JSONDecodeError as e:
        raise QuickstartValidationError(f"Invalid JSON in {path}: {e}")

def validate_csv_structure(path: Path, required_columns: Optional[List[str]] = None):
    check_file_exists(path)
    try:
        import csv
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None:
                raise QuickstartValidationError(f"CSV is empty: {path}")
            if required_columns:
                missing = [c for c in required_columns if c not in header]
                if missing:
                    raise QuickstartValidationError(f"Missing columns in {path}: {missing}")
            # Check for at least one data row
            try:
                next(reader)
            except StopIteration:
                raise QuickstartValidationError(f"CSV has no data rows: {path}")
        log_success(f"Valid CSV structure: {path}")
    except Exception as e:
        raise QuickstartValidationError(f"Failed to validate CSV {path}: {e}")

def run_script(script_name: str, description: str) -> bool:
    log_step(f"Running {description} ({script_name})")
    try:
        # Run the script with a timeout to prevent hanging
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=300, # 5 minutes timeout
            check=False
        )
        
        if result.returncode == 0:
            log_success(f"{description} completed successfully.")
            if result.stdout:
                logger.debug(f"STDOUT:\n{result.stdout}")
            return True
        else:
            log_error(f"{description} failed with exit code {result.returncode}")
            if result.stderr:
                logger.error(f"STDERR:\n{result.stderr}")
            raise QuickstartValidationError(f"Script {script_name} failed")
    except subprocess.TimeoutExpired:
        log_error(f"{description} timed out.")
        raise QuickstartValidationError(f"Script {script_name} timed out")
    except Exception as e:
        log_error(f"Exception running {description}: {e}")
        raise

def validate_pipeline_artifacts(project_root: Path):
    """Validates that all required artifacts from the pipeline exist and are non-empty."""
    log_step("Validating pipeline artifacts...")
    
    artifacts = [
        # T012: Synthetic traces
        {"path": project_root / "data" / "training", "type": "dir", "min_files": 1},
        {"path": project_root / "data" / "held_out", "type": "dir", "min_files": 1},
        
        # T020: Feature matrix
        {"path": project_root / "data" / "processed" / "feature_matrix.csv", "type": "file"},
        
        # T023/T026b: Global rules
        {"path": project_root / "data" / "processed" / "rules" / "global_rules.json", "type": "file"},
        
        # T032: Benchmark results
        {"path": project_root / "data" / "processed" / "benchmark_results.json", "type": "file"},
        
        # T035b: Accuracy deltas
        {"path": project_root / "data" / "processed" / "accuracy_deltas.csv", "type": "file"},
        
        # T035: Statistical analysis
        {"path": project_root / "data" / "processed" / "statistical_analysis.json", "type": "file"},
        
        # T037: Sensitivity sweep
        {"path": project_root / "data" / "processed" / "sensitivity_sweep.csv", "type": "file"},
        
        # T037a: Sweep config
        {"path": project_root / "data" / "processed" / "sweep_config.json", "type": "file"},
    ]

    for artifact in artifacts:
        path = artifact["path"]
        if artifact["type"] == "file":
            check_file_exists(path)
            check_file_not_empty(path)
            if path.suffix == '.json':
                validate_json_structure(path)
            elif path.suffix == '.csv':
                validate_csv_structure(path)
        elif artifact["type"] == "dir":
            if not path.exists():
                raise QuickstartValidationError(f"Directory not found: {path}")
            files = list(path.glob("*"))
            if len(files) < artifact.get("min_files", 1):
                raise QuickstartValidationError(f"Directory {path} has fewer than {artifact['min_files']} files")
            log_success(f"Directory valid: {path} ({len(files)} files)")

    log_success("All pipeline artifacts validated.")

def main():
    """
    Main entry point for T044: Run quickstart.md validation.
    Executes the pipeline scripts in order and validates outputs.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    code_root = project_root / "code"
    
    # Change to project root to ensure relative paths work
    os.chdir(project_root)
    
    log_step("Starting Quickstart Validation (T044)")
    
    # Define the execution order as per quickstart.md (T050)
    pipeline_steps = [
        ("code/generators/run_generation.py", "Synthetic Trace Generation"),
        ("code/metrics/extract.py", "Metric Extraction"),
        ("code/models/rule_induction.py", "Rule Induction"),
        ("code/evaluation/calculate_deltas.py", "Calculate Deltas"),
        ("code/evaluation/benchmark.py", "Benchmarking"),
        ("code/evaluation/stats.py", "Statistical Analysis"),
        ("code/evaluation/sweep_thresholds.py", "Sweep Thresholds"),
        ("code/evaluation/sensitivity_sweep.py", "Sensitivity Sweep"),
        # Note: T036 (Correlation) is often part of stats or separate, 
        # but if it's a separate script not in the main chain, we assume it's covered by stats or skipped if not critical for the core flow.
        # However, if it has its own script, we should run it. 
        # Based on API surface, there is analysis/correlation_analysis.py. 
        # Let's add it if it exists as a main script.
    ]

    # Check for correlation analysis script if it's a standalone step
    corr_script = code_root / "analysis" / "correlation_analysis.py"
    if corr_script.exists():
        pipeline_steps.append(("code/analysis/correlation_analysis.py", "Correlation Analysis"))

    try:
        for script, desc in pipeline_steps:
            full_path = code_root / script.replace("code/", "")
            if not full_path.exists():
                log_error(f"Script not found: {full_path}")
                raise QuickstartValidationError(f"Missing script: {script}")
            run_script(str(full_path), desc)

        # Validate all artifacts
        validate_pipeline_artifacts(project_root)

        log_step("Quickstart Validation Completed Successfully")
        print("\n" + "="*50)
        print("T044 VALIDATION PASSED")
        print("All scripts executed and artifacts validated.")
        print("="*50)
        return 0

    except QuickstartValidationError as e:
        log_error(f"Validation Failed: {e}")
        print("\n" + "="*50)
        print("T044 VALIDATION FAILED")
        print(f"Reason: {e}")
        print("="*50)
        return 1
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
