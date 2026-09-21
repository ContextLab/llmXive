import os
import sys
import subprocess
import importlib.util
import json
import time
from pathlib import Path

from config import get_data_dir, get_output_dir, ensure_directories
from validate_schemas import validate_all_artifacts

def log_status(message: str, status: str = "INFO") -> None:
    """Log a status message with a timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{status}] {message}")

def check_directory(dir_path: str) -> bool:
    """Check if a directory exists."""
    path = Path(dir_path)
    if not path.exists():
        log_status(f"Directory missing: {dir_path}", "ERROR")
        return False
    if not path.is_dir():
        log_status(f"Path exists but is not a directory: {dir_path}", "ERROR")
        return False
    log_status(f"Directory OK: {dir_path}")
    return True

def check_file(file_path: str) -> bool:
    """Check if a file exists and is non-empty."""
    path = Path(file_path)
    if not path.exists():
        log_status(f"File missing: {file_path}", "ERROR")
        return False
    if path.stat().st_size == 0:
        log_status(f"File is empty: {file_path}", "ERROR")
        return False
    log_status(f"File OK: {file_path}")
    return True

def check_requirements() -> bool:
    """Check if requirements.txt exists and is non-empty."""
    req_path = Path("requirements.txt")
    if not req_path.exists():
        log_status("requirements.txt missing", "ERROR")
        return False
    if req_path.stat().st_size == 0:
        log_status("requirements.txt is empty", "ERROR")
        return False
    log_status("requirements.txt OK")
    return True

def check_schemas() -> bool:
    """Validate all artifacts against schemas."""
    log_status("Validating artifacts against schemas...")
    try:
        # This calls the main validation logic from validate_schemas
        # which reads contracts/ and data/ artifacts
        result = validate_all_artifacts()
        if result:
            log_status("Schema validation PASSED", "SUCCESS")
            return True
        else:
            log_status("Schema validation FAILED", "ERROR")
            return False
    except Exception as e:
        log_status(f"Schema validation error: {e}", "ERROR")
        return False

def import_module(module_name: str, module_path: str):
    """Dynamically import a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {module_name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def run_main_help() -> bool:
    """Run python code/main.py --help to verify CLI entry point."""
    log_status("Running 'python code/main.py --help'...")
    try:
        result = subprocess.run(
            [sys.executable, "code/main.py", "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            log_status("CLI help command OK", "SUCCESS")
            return True
        else:
            log_status(f"CLI help command failed: {result.stderr}", "ERROR")
            return False
    except subprocess.TimeoutExpired:
        log_status("CLI help command timed out", "ERROR")
        return False
    except Exception as e:
        log_status(f"CLI help command error: {e}", "ERROR")
        return False

def check_data_integrity_marker() -> bool:
    """Check if state file contains data integrity checksums."""
    state_path = Path("state/projects/PROJ-052-leveraging-llms-for-automated-test-case-.yaml")
    if not state_path.exists():
        log_status(f"State file missing: {state_path}", "ERROR")
        return False

    try:
        with open(state_path, 'r') as f:
            content = f.read()
            # Check for the presence of the checksum key expected from T006c
            if "artifact_hashes" in content and "data_loader" in content:
                log_status("Data integrity marker found in state", "SUCCESS")
                return True
            else:
                log_status("Data integrity marker (artifact_hashes.data_loader) NOT found in state", "ERROR")
                return False
    except Exception as e:
        log_status(f"Error reading state file: {e}", "ERROR")
        return False

def run_validation() -> dict:
    """Run all validation checks and return a summary."""
    results = {}
    all_passed = True

    log_status("=== Starting Quickstart Validation ===", "INFO")

    # 1. Check Directory Structure
    dirs = ["code", "data", "tests", "specs", "contracts"]
    for d in dirs:
        if not check_directory(d):
            all_passed = False
    results["directories"] = all([check_directory(d) for d in dirs])

    # 2. Check Files
    files = ["requirements.txt", "README.md", "quickstart.md"]
    for f in files:
        if not check_file(f):
            all_passed = False
    results["files"] = all([check_file(f) for f in files])

    # 3. Check Schemas
    results["schemas"] = check_schemas()
    if not results["schemas"]:
        all_passed = False

    # 4. Check Data Integrity
    results["data_integrity"] = check_data_integrity_marker()
    if not results["data_integrity"]:
        all_passed = False

    # 5. Run CLI Help
    results["cli_help"] = run_main_help()
    if not results["cli_help"]:
        all_passed = False

    log_status("=== Validation Complete ===", "INFO")
    log_status(f"Overall Status: {'PASSED' if all_passed else 'FAILED'}", "INFO" if all_passed else "ERROR")

    return {
        "passed": all_passed,
        "details": results,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def main():
    """Entry point for quickstart validation."""
    ensure_directories()
    validation_result = run_validation()

    # Write validation report to data/
    report_path = Path(get_data_dir()) / "quickstart_validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(validation_result, f, indent=2)
    
    log_status(f"Validation report written to {report_path}", "INFO")

    if not validation_result["passed"]:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()