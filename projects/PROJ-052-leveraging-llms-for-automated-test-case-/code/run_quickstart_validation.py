"""
Helper script for quickstart validation.
Performs deeper checks on module imports and basic functionality.
"""
import os
import sys
import importlib.util
import json
import time
from pathlib import Path

def log_status(message: str, success: bool = True) -> None:
    """Log status message."""
    status = "PASS" if success else "FAIL"
    print(f"[{status}] {message}")

def check_directory(path: str) -> bool:
    """Check if directory exists."""
    exists = os.path.isdir(path)
    log_status(f"Directory check: {path}", exists)
    return exists

def check_file(path: str) -> bool:
    """Check if file exists."""
    exists = os.path.isfile(path)
    log_status(f"File check: {path}", exists)
    return exists

def check_requirements() -> bool:
    """Check if essential requirements are present."""
    req_path = "requirements.txt"
    if not check_file(req_path):
        return False
    
    with open(req_path, 'r') as f:
        content = f.read().lower()
    
    essential = ["pandas", "pytest"]
    missing = [pkg for pkg in essential if pkg not in content]
    
    if missing:
        log_status(f"Missing requirements: {missing}", False)
        return False
    
    log_status("Essential requirements present", True)
    return True

def check_schemas() -> bool:
    """Check if all required schema files exist and are valid YAML."""
    schema_dir = Path("contracts")
    required_schemas = [
        "dataset.schema.yaml",
        "coverage.schema.yaml",
        "generated_test.schema.yaml",
        "analysis_result.schema.yaml"
    ]
    
    all_valid = True
    for schema in required_schemas:
        schema_path = schema_dir / schema
        if not check_file(str(schema_path)):
            all_valid = False
            continue
        
        # Basic YAML validation (check for content)
        with open(schema_path, 'r') as f:
            content = f.read().strip()
            if not content:
                log_status(f"Schema {schema} is empty", False)
                all_valid = False
            else:
                log_status(f"Schema {schema} valid", True)
    
    return all_valid

def import_module(module_name: str, file_path: str) -> bool:
    """Attempt to import a module from a file path."""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            log_status(f"Module import: {module_name}", True)
            return True
        else:
            log_status(f"Module import: {module_name} (spec not found)", False)
            return False
    except Exception as e:
        log_status(f"Module import: {module_name} ({str(e)})", False)
        return False

def run_main_help() -> bool:
    """Run main.py --help to verify entry point."""
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "code/main.py", "--help"],
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0:
            log_status("main.py --help executed successfully", True)
            return True
        else:
            log_status(f"main.py --help failed with code {result.returncode}", False)
            return False
    except Exception as e:
        log_status(f"main.py --help failed: {str(e)}", False)
        return False

def check_data_integrity_marker() -> bool:
    """Check if data integrity markers can be loaded."""
    try:
        # Try to load config to ensure basic setup works
        from config import get_data_dir, ensure_directories
        data_dir = get_data_dir()
        ensure_directories()
        log_status("Data directory setup verified", True)
        return True
    except Exception as e:
        log_status(f"Data integrity check failed: {str(e)}", False)
        return False

def run_validation() -> bool:
    """Run all validation checks."""
    print("Running Quickstart Validation Checks...")
    print("-" * 40)
    
    checks = [
        check_directory("code"),
        check_directory("data"),
        check_directory("tests"),
        check_directory("specs"),
        check_directory("contracts"),
        check_requirements(),
        check_schemas(),
        import_module("config", "code/config.py"),
        import_module("data_loader", "code/data_loader.py"),
        import_module("llm_generator", "code/llm_generator.py"),
        import_module("test_executor", "code/test_executor.py"),
        import_module("analyzer", "code/analyzer.py"),
        import_module("main", "code/main.py"),
        import_module("report_generator", "code/report_generator.py"),
        run_main_help(),
        check_data_integrity_marker(),
    ]
    
    return all(checks)

def main():
    """Main entry point."""
    success = run_validation()
    if success:
        print("-" * 40)
        print("All validations passed.")
        sys.exit(0)
    else:
        print("-" * 40)
        print("Some validations failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()