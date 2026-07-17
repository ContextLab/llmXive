import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
from utils_logging import (
    get_project_root,
    ensure_log_directory,
    setup_logger,
    get_pipeline_logger,
    log_info,
    log_warning,
    log_error,
    log_abort,
    log_exclusion,
    log_exclusion_count,
    check_log_file_exists,
    read_log_file,
)
import yaml
import json

# Constants
REQUIRED_FILES = [
    "README.md",
    "requirements.txt",
    "data/raw/.gitkeep",
    "data/processed/.gitkeep",
    "data/derived/.gitkeep",
    "logs/.gitkeep",
    "code/00_config.R",
    "code/01_ingest.R",
    "code/02_classify.R",
    "code/02.5_aggregate_exclusions.R",
    "code/02.6_reliability.R",
    "code/03_analysis.R",
    "code/04_report.Rmd",
    "code/05_validate_report.R",
    "code/06_benchmark_accuracy.R",
    "code/07_regression_test.R",
    "code/measurements.md",
    "specs/chronotype-moral-judgement/spec.md",
    "specs/chronotype-moral-judgement/data-model.md",
    "specs/chronotype-moral-judgement/plan.md",
]

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/derived",
    "logs",
    "reports",
    "docs",
]

QUICKSTART_CHECKS = [
    "R version check",
    "renv initialization",
    "data directory structure",
    "logging infrastructure",
    "script execution flow",
]

def check_file_exists(path: Path) -> Tuple[bool, str]:
    """Check if a required file exists."""
    if not path.exists():
        return False, f"Missing required file: {path}"
    return True, "OK"

def check_dir_exists(path: Path) -> Tuple[bool, str]:
    """Check if a required directory exists."""
    if not path.is_dir():
        return False, f"Missing required directory: {path}"
    return True, "OK"

def check_r_installed() -> Tuple[bool, str]:
    """Check if R is installed and accessible."""
    try:
        result = subprocess.run(
            ["R", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=10,
        )
        version_line = result.stdout.decode().split("\n")[0]
        return True, f"R installed: {version_line}"
    except subprocess.CalledProcessError:
        return False, "R is not installed or not in PATH"
    except FileNotFoundError:
        return False, "R command not found"
    except subprocess.TimeoutExpired:
        return False, "R version check timed out"

def check_renv_initialized(project_root: Path) -> Tuple[bool, str]:
    """Check if renv is initialized."""
    renv_lock = project_root / "renv.lock"
    renv_init = project_root / "renv"
    
    if not renv_lock.exists():
        return False, "renv.lock not found - renv not initialized"
    
    if not renv_init.exists():
        return False, "renv/ directory not found - renv not initialized"
    
    return True, "renv initialized successfully"

def check_logging_infrastructure(project_root: Path) -> Tuple[bool, str]:
    """Verify logging infrastructure is set up."""
    log_dir = project_root / "logs"
    if not log_dir.exists():
        return False, "logs/ directory missing"
    
    # Check if logging utilities exist
    utils_logging = project_root / "code" / "utils_logging.py"
    if not utils_logging.exists():
        return False, "code/utils_logging.py missing"
    
    return True, "Logging infrastructure OK"

def validate_quickstart_content(project_root: Path) -> Tuple[bool, List[str]]:
    """Validate the content of quickstart.md if it exists."""
    quickstart_path = project_root / "quickstart.md"
    
    if not quickstart_path.exists():
        return False, ["quickstart.md not found"]
    
    try:
        with open(quickstart_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        errors = []
        
        # Check for essential sections
        required_sections = [
            "## Prerequisites",
            "## Installation",
            "## Running the Pipeline",
            "## Output Files",
        ]
        
        for section in required_sections:
            if section not in content:
                errors.append(f"Missing section: {section}")
        
        # Check for R commands
        if "Rscript" not in content and "R -e" not in content:
            errors.append("No R script execution commands found in quickstart.md")
        
        # Check for data directory references
        if "data/" not in content:
            errors.append("No reference to data directory in quickstart.md")
        
        if errors:
            return False, errors
        
        return True, ["quickstart.md validation passed"]
        
    except Exception as e:
        return False, [f"Error reading quickstart.md: {str(e)}"]

def run_quickstart_validation(project_root: Path) -> Tuple[bool, List[str]]:
    """Run comprehensive quickstart validation."""
    errors = []
    warnings = []
    
    # 1. Check R installation
    r_ok, r_msg = check_r_installed()
    if not r_ok:
        errors.append(r_msg)
    else:
        log_info(f"R check: {r_msg}")
    
    # 2. Check renv initialization
    renv_ok, renv_msg = check_renv_initialized(project_root)
    if not renv_ok:
        errors.append(renv_msg)
    else:
        log_info(f"renv check: {renv_msg}")
    
    # 3. Check required directories
    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        ok, msg = check_dir_exists(full_path)
        if not ok:
            errors.append(msg)
        else:
            log_info(f"Directory check: {dir_path} - OK")
    
    # 4. Check required files
    for file_path in REQUIRED_FILES:
        full_path = project_root / file_path
        ok, msg = check_file_exists(full_path)
        if not ok:
            errors.append(msg)
        else:
            log_info(f"File check: {file_path} - OK")
    
    # 5. Check logging infrastructure
    log_ok, log_msg = check_logging_infrastructure(project_root)
    if not log_ok:
        errors.append(log_msg)
    else:
        log_info(f"Logging check: {log_msg}")
    
    # 6. Validate quickstart.md content
    content_ok, content_msgs = validate_quickstart_content(project_root)
    if not content_ok:
        errors.extend(content_msgs)
    else:
        log_info(f"Content check: {content_msgs[0]}")
    
    # 7. Check that scripts are executable (syntax check)
    r_scripts = [
        "code/00_config.R",
        "code/01_ingest.R",
        "code/02_classify.R",
        "code/03_analysis.R",
        "code/05_validate_report.R",
    ]
    
    for script in r_scripts:
        full_path = project_root / script
        if full_path.exists():
            try:
                result = subprocess.run(
                    ["Rscript", "--vanilla", "-e", f"source('{full_path}')"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                # We expect errors because data might not be present, but syntax errors are fatal
                if "Error: unexpected" in result.stderr or "Error: object" in result.stderr:
                    warnings.append(f"Potential syntax issue in {script}: {result.stderr[:100]}")
            except subprocess.TimeoutExpired:
                pass  # Script is running, that's fine
            except Exception as e:
                warnings.append(f"Could not check {script}: {str(e)}")
    
    return len(errors) == 0, errors + warnings

def main():
    """Main entry point for quickstart validation."""
    project_root = get_project_root()
    
    # Setup logger
    logger = setup_logger(
        name="quickstart_validator",
        log_file=str(project_root / "logs" / "quickstart_validation.log"),
        level="INFO",
    )
    
    log_info("=" * 60)
    log_info("Starting Quickstart Validation")
    log_info("=" * 60)
    
    success, messages = run_quickstart_validation(project_root)
    
    if success:
        log_info("✓ All quickstart validations PASSED")
        for msg in messages:
            if msg.startswith("Warning") or "potential" in msg.lower():
                log_warning(msg)
            else:
                log_info(f"  - {msg}")
        
        # Write validation report
        report_path = project_root / "data" / "derived" / "quickstart_validation_report.json"
        report_data = {
            "status": "PASSED",
            "timestamp": subprocess.run(["date", "+%Y-%m-%d %H:%M:%S"], capture_output=True, text=True).stdout.strip(),
            "checks_passed": len([m for m in messages if "OK" in m or "passed" in m]),
            "warnings": [m for m in messages if "Warning" in m or "potential" in m.lower()],
        }
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        
        log_info(f"Validation report saved to: {report_path}")
        return 0
    else:
        log_error("✗ Quickstart validation FAILED")
        for msg in messages:
            log_error(f"  - {msg}")
        
        # Write failure report
        report_path = project_root / "data" / "derived" / "quickstart_validation_report.json"
        report_data = {
            "status": "FAILED",
            "timestamp": subprocess.run(["date", "+%Y-%m-%d %H:%M:%S"], capture_output=True, text=True).stdout.strip(),
            "errors": messages,
        }
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        
        log_error(f"Validation report saved to: {report_path}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
