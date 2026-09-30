"""
T038: Quickstart Validation Script

This script validates the project setup and execution pipeline by:
1. Verifying directory structure exists (T001, T005)
2. Verifying configuration and linting setup (T002, T003)
3. Running the main pipeline entry point (T007)
4. Checking for expected output artifacts (T014c, T019, T027, T032)
5. Validating state files (T004, T010, T031c)

Usage:
    python code/quickstart_validator.py [--config path/to/config.yaml]
"""
import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)

class ValidationResult:
    """Container for validation results."""
    def __init__(self):
        self.passed: List[str] = []
        self.failed: List[str] = []
        self.warnings: List[str] = []
        
    def add_pass(self, check: str):
        self.passed.append(check)
        logger.info(f"✓ PASSED: {check}")
        
    def add_fail(self, check: str, reason: str = ""):
        self.failed.append(f"{check}: {reason}")
        logger.error(f"✗ FAILED: {check} - {reason}")
        
    def add_warning(self, check: str, reason: str = ""):
        self.warnings.append(f"{check}: {reason}")
        logger.warning(f"⚠ WARNING: {check} - {reason}")
        
    def is_successful(self) -> bool:
        return len(self.failed) == 0

def check_directory_structure(root: Path) -> ValidationResult:
    """Validate required directory structure (T001, T005)."""
    result = ValidationResult()
    
    required_dirs = [
        'code',
        'data/raw',
        'data/processed',
        'tests',
        'state',
        'docs',
        'logs',
        'code/data',
        'code/preprocess',
        'code/analysis',
        'code/modeling',
        'code/validation',
        'code/report',
        'code/utils'
    ]
    
    for dir_path in required_dirs:
        full_path = root / dir_path
        if not full_path.exists():
            result.add_fail(f"Directory exists: {dir_path}", f"Path {full_path} does not exist")
        else:
            result.add_pass(f"Directory exists: {dir_path}")
            
    return result

def check_config_files(root: Path) -> ValidationResult:
    """Validate configuration and linting setup (T002, T003)."""
    result = ValidationResult()
    
    # Check requirements.txt
    req_file = root / 'requirements.txt'
    if req_file.exists():
        result.add_pass("requirements.txt exists")
        with open(req_file, 'r') as f:
            content = f.read()
            required_packages = ['numpy', 'scipy', 'scikit-learn', 'pandas', 'matplotlib', 'statsmodels', 'pytest']
            for pkg in required_packages:
                if pkg in content.lower():
                    result.add_pass(f"Package {pkg} in requirements.txt")
                else:
                    result.add_warning(f"Package {pkg} in requirements.txt", "Not found in requirements.txt")
    else:
        result.add_fail("requirements.txt exists", "File not found")
        
    # Check linting config
    linting_configs = ['.ruff.toml', '.flake8', 'pyproject.toml', '.black', 'setup.cfg']
    linting_found = False
    for config in linting_configs:
        if (root / config).exists():
            result.add_pass(f"Linting config {config} exists")
            linting_found = True
            break
            
    if not linting_found:
        result.add_warning("Linting config exists", "No standard linting config file found")
        
    return result

def check_state_files(root: Path) -> ValidationResult:
    """Validate state files (T004, T010)."""
    result = ValidationResult()
    
    # Check main project state file
    state_file = root / 'state' / 'projects' / 'PROJ-204-quantifying-the-impact-of-spatial-correl.yaml'
    if state_file.exists():
        result.add_pass("Project state file exists")
        try:
            with open(state_file, 'r') as f:
                content = yaml.safe_load(f)
                if 'artifact_hashes' in content:
                    result.add_pass("State file contains artifact_hashes")
                else:
                    result.add_warning("State file contains artifact_hashes", "Missing artifact_hashes key")
        except Exception as e:
            result.add_fail("State file is valid YAML", str(e))
    else:
        result.add_fail("Project state file exists", f"File not found: {state_file}")
        
    # Check data feasibility status
    feasibility_file = root / 'state' / 'data_feasibility_status.yaml'
    if feasibility_file.exists():
        result.add_pass("Data feasibility status file exists")
    else:
        result.add_warning("Data feasibility status file exists", "File not found - may need to run T010 first")
        
    return result

def run_pipeline(root: Path, config_path: Optional[Path] = None) -> ValidationResult:
    """Run the main pipeline and check for outputs."""
    result = ValidationResult()
    
    # Construct command
    cmd = [sys.executable, 'code/main_pipeline.py']
    if config_path and config_path.exists():
        cmd.extend(['--config', str(config_path)])
    else:
        # Try default config
        default_config = root / 'config.yaml'
        if default_config.exists():
            cmd.extend(['--config', str(default_config)])
        
    logger.info(f"Running pipeline: {' '.join(cmd)}")
    
    try:
        # Run with timeout (5 minutes)
        process = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if process.returncode == 0:
            result.add_pass("Pipeline execution completed successfully")
            
            # Check for logs
            log_file = root / 'logs' / 'pipeline.log'
            if log_file.exists():
                result.add_pass("Pipeline log file created")
            else:
                result.add_warning("Pipeline log file created", "Log file not found")
        else:
            result.add_fail("Pipeline execution completed successfully", 
                          f"Exit code: {process.returncode}\nStderr: {process.stderr}")
            
    except subprocess.TimeoutExpired:
        result.add_fail("Pipeline execution completed successfully", "Pipeline timed out after 5 minutes")
    except Exception as e:
        result.add_fail("Pipeline execution completed successfully", str(e))
        
    return result

def check_output_artifacts(root: Path) -> ValidationResult:
    """Check for expected output artifacts from completed tasks."""
    result = ValidationResult()
    
    # T014c: unified_dataset.csv
    unified_dataset = root / 'data' / 'processed' / 'unified_dataset.csv'
    if unified_dataset.exists():
        result.add_pass("unified_dataset.csv exists")
        try:
            import pandas as pd
            df = pd.read_csv(unified_dataset)
            required_cols = ['sample_id', 'PCE', 'J_sc', 'V_oc']
            missing_cols = [c for c in required_cols if c not in df.columns]
            if not missing_cols:
                result.add_pass("unified_dataset.csv has required columns")
            else:
                result.add_warning("unified_dataset.csv has required columns", f"Missing: {missing_cols}")
            
            if len(df) > 0:
                result.add_pass(f"unified_dataset.csv contains {len(df)} rows")
            else:
                result.add_warning("unified_dataset.csv contains rows", "File is empty")
        except Exception as e:
            result.add_fail("unified_dataset.csv is valid CSV", str(e))
    else:
        result.add_warning("unified_dataset.csv exists", "File not found - pipeline may not have completed")
        
    # T019/T024: spatial_metrics.csv
    spatial_metrics = root / 'data' / 'processed' / 'spatial_metrics.csv'
    if spatial_metrics.exists():
        result.add_pass("spatial_metrics.csv exists")
    else:
        result.add_warning("spatial_metrics.csv exists", "File not found - spatial metrics analysis may not have run")
        
    # T027: correlation results
    correlation_results = root / 'data' / 'processed' / 'correlation_results.csv'
    if correlation_results.exists():
        result.add_pass("correlation_results.csv exists")
    else:
        result.add_warning("correlation_results.csv exists", "File not found - correlation analysis may not have run")
        
    # T032: summary report
    summary_csv = root / 'data' / 'report' / 'summary.csv'
    if summary_csv.exists():
        result.add_pass("summary.csv exists")
    else:
        result.add_warning("summary.csv exists", "File not found - report generation may not have run")
        
    return result

def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description='Validate quickstart pipeline')
    parser.add_argument('--config', type=Path, help='Path to configuration file')
    args = parser.parse_args()
    
    root = Path.cwd()
    logger.info(f"Starting validation for project at: {root}")
    
    all_results = ValidationResult()
    
    # 1. Check directory structure
    logger.info("=== Checking Directory Structure ===")
    dir_result = check_directory_structure(root)
    all_results.passed.extend(dir_result.passed)
    all_results.failed.extend(dir_result.failed)
    all_results.warnings.extend(dir_result.warnings)
    
    # 2. Check config files
    logger.info("=== Checking Configuration Files ===")
    config_result = check_config_files(root)
    all_results.passed.extend(config_result.passed)
    all_results.failed.extend(config_result.failed)
    all_results.warnings.extend(config_result.warnings)
    
    # 3. Check state files
    logger.info("=== Checking State Files ===")
    state_result = check_state_files(root)
    all_results.passed.extend(state_result.passed)
    all_results.failed.extend(state_result.failed)
    all_results.warnings.extend(state_result.warnings)
    
    # 4. Run pipeline
    logger.info("=== Running Pipeline ===")
    pipeline_result = run_pipeline(root, args.config)
    all_results.passed.extend(pipeline_result.passed)
    all_results.failed.extend(pipeline_result.failed)
    all_results.warnings.extend(pipeline_result.warnings)
    
    # 5. Check output artifacts
    logger.info("=== Checking Output Artifacts ===")
    artifact_result = check_output_artifacts(root)
    all_results.passed.extend(artifact_result.passed)
    all_results.failed.extend(artifact_result.failed)
    all_results.warnings.extend(artifact_result.warnings)
    
    # Summary
    logger.info("=== Validation Summary ===")
    logger.info(f"Passed: {len(all_results.passed)}")
    logger.info(f"Failed: {len(all_results.failed)}")
    logger.info(f"Warnings: {len(all_results.warnings)}")
    
    if all_results.failed:
        logger.error("Validation FAILED")
        for fail in all_results.failed:
            logger.error(f"  - {fail}")
        sys.exit(1)
    else:
        logger.info("Validation PASSED")
        if all_results.warnings:
            logger.warning("With warnings:")
            for warn in all_results.warnings:
                logger.warning(f"  - {warn}")
        sys.exit(0)

if __name__ == '__main__':
    main()
