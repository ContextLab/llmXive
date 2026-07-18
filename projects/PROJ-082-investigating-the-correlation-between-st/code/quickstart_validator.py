import argparse
import json
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Add project root to path to allow imports if run as script
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger, log_error_context
from utils.config import get_project_root, ensure_directory

logger = get_logger(__name__)

REQUIRED_DIRS = [
    "code",
    "tests",
    "data",
    "docs"
]

REQUIRED_ARTIFACTS = [
    "data/processed/extracted_studies.csv",
    "data/derived/results.json",
    "data/derived/narrative_summary.md",
    "data/derived/forest_plot.png",
    "data/derived/funnel_plot.png",
    "data/derived/correlation_summary.png",
    "data/logs/exclusion_log.csv",
    "data/logs/conversion_log.csv"
]

def check_directories() -> Tuple[bool, List[str]]:
    """Verify that required project directories exist."""
    missing = []
    root = get_project_root()
    for dir_name in REQUIRED_DIRS:
        dir_path = root / dir_name
        if not dir_path.exists():
            missing.append(str(dir_path))
        elif not any(dir_path.iterdir()):
            # Check if directory is empty (optional strictness)
            # For T036 validation, we just check existence primarily,
            # but logs might be empty if no exclusions.
            pass
    
    if missing:
        logger.error(f"Missing directories: {missing}")
        return False, missing
    return True, []

def run_pipeline_execution(timeout_seconds: int = 600) -> Tuple[bool, str]:
    """
    Execute the main pipeline script (code/main.py).
    Returns (success, output_message).
    """
    root = get_project_root()
    main_script = root / "code" / "main.py"
    
    if not main_script.exists():
        return False, f"Main script not found: {main_script}"

    logger.info(f"Executing pipeline: {main_script}")
    start_time = time.time()
    
    try:
        # Run the pipeline
        result = subprocess.run(
            [sys.executable, str(main_script)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        
        elapsed = time.time() - start_time
        output_msg = f"Pipeline execution took {elapsed:.2f}s\n"
        
        if result.returncode != 0:
            output_msg += f"STDOUT:\n{result.stdout}\n"
            output_msg += f"STDERR:\n{result.stderr}\n"
            logger.error(f"Pipeline failed with code {result.returncode}")
            return False, output_msg
        
        output_msg += "Pipeline completed successfully.\n"
        output_msg += f"STDOUT:\n{result.stdout}\n"
        return True, output_msg

    except subprocess.TimeoutExpired:
        return False, f"Pipeline execution timed out after {timeout_seconds}s"
    except Exception as e:
        logger.error(f"Error running pipeline: {e}")
        return False, str(e)

def verify_artifacts() -> Tuple[bool, List[str]]:
    """Verify that all required output artifacts exist."""
    root = get_project_root()
    missing = []
    
    for artifact in REQUIRED_ARTIFACTS:
        path = root / artifact
        if not path.exists():
            missing.append(artifact)
        else:
            # Check file size > 0 for non-log files if applicable
            if "log" not in artifact and "md" not in artifact and "json" not in artifact:
                if path.stat().st_size == 0:
                    missing.append(f"{artifact} (empty)")
            elif "json" in artifact or "csv" in artifact:
                if path.stat().st_size == 0:
                    missing.append(f"{artifact} (empty)")
    
    if missing:
        logger.error(f"Missing artifacts: {missing}")
        return False, missing
    return True, []

def validate_json_content() -> Tuple[bool, str]:
    """Validate the content of the main results JSON."""
    root = get_project_root()
    results_path = root / "data" / "derived" / "results.json"
    
    if not results_path.exists():
        return False, "results.json not found"
    
    try:
        with open(results_path, 'r') as f:
            data = json.load(f)
        
        required_keys = ["synthesis_mode", "study_count"]
        missing_keys = [k for k in required_keys if k not in data]
        
        if missing_keys:
            return False, f"Missing keys in results.json: {missing_keys}"
        
        if data["synthesis_mode"] not in ["narrative", "quantitative"]:
            return False, f"Invalid synthesis_mode: {data['synthesis_mode']}"
        
        if not isinstance(data["study_count"], int) or data["study_count"] < 0:
            return False, f"Invalid study_count: {data['study_count']}"
        
        return True, f"results.json validated. Mode: {data['synthesis_mode']}, Count: {data['study_count']}"
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in results.json: {e}"
    except Exception as e:
        return False, f"Error reading results.json: {e}"

def main():
    parser = argparse.ArgumentParser(description="Validate quickstart pipeline execution.")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout for pipeline execution in seconds")
    args = parser.parse_args()

    logger.info("Starting Quickstart Validation (T036)")
    all_passed = True
    report = []

    # 1. Check Directories
    logger.info("Step 1: Checking directory structure...")
    dirs_ok, missing_dirs = check_directories()
    if not dirs_ok:
        all_passed = False
        report.append(f"FAILED: Missing directories: {missing_dirs}")
    else:
        report.append("PASSED: Directory structure verified.")

    # 2. Run Pipeline
    if all_passed:
        logger.info("Step 2: Executing pipeline...")
        exec_ok, exec_msg = run_pipeline_execution(args.timeout)
        if not exec_ok:
            all_passed = False
            report.append(f"FAILED: Pipeline execution failed.\n{exec_msg}")
        else:
            report.append("PASSED: Pipeline executed successfully.")
            # Log the output briefly
            for line in exec_msg.split('\n')[:10]:
                logger.info(f"  > {line}")

    # 3. Verify Artifacts
    if all_passed:
        logger.info("Step 3: Verifying output artifacts...")
        artifacts_ok, missing_artifacts = verify_artifacts()
        if not artifacts_ok:
            all_passed = False
            report.append(f"FAILED: Missing artifacts: {missing_artifacts}")
        else:
            report.append("PASSED: All required artifacts exist.")

    # 4. Validate JSON Content
    if all_passed:
        logger.info("Step 4: Validating JSON content...")
        json_ok, json_msg = validate_json_content()
        if not json_ok:
            all_passed = False
            report.append(f"FAILED: {json_msg}")
        else:
            report.append(f"PASSED: {json_msg}")

    # Final Summary
    print("\n" + "="*50)
    print("QUICKSTART VALIDATION REPORT (T036)")
    print("="*50)
    for line in report:
        print(line)
    print("="*50)
    
    if all_passed:
        print("STATUS: SUCCESS")
        logger.info("Quickstart validation completed successfully.")
        sys.exit(0)
    else:
        print("STATUS: FAILED")
        logger.error("Quickstart validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()