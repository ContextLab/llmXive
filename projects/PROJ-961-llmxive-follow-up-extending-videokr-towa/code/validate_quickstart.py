"""
Quickstart Validation Script for PROJ-961-llmxive-follow-up-extending-videokr-towa

This script validates the reproducibility of the project by checking:
1. Directory structure existence
2. Placeholder files (.gitkeep)
3. Data artifacts existence and validity
4. Docstring coverage
5. Import validity (syntax check)
6. Lint and Type check logs existence
"""

import ast
import json
import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def check_directory_structure(root: Path) -> Tuple[bool, List[str]]:
    """Check if required directory structure exists."""
    required_dirs = [
        'code', 'tests', 'data',
        'code/ingest', 'code/analysis', 'code/utils',
        'tests/unit', 'tests/integration',
        'data/raw', 'data/processed'
    ]
    missing = []
    for dir_path in required_dirs:
        full_path = root / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing.append(str(full_path))
            logger.error(f"Missing directory: {full_path}")
        else:
            logger.info(f"Found directory: {full_path}")
    
    return len(missing) == 0, missing

def check_placeholder_files(root: Path) -> Tuple[bool, List[str]]:
    """Check if required .gitkeep files exist."""
    required_files = [
        'data/raw/.gitkeep',
        'data/processed/.gitkeep'
    ]
    missing = []
    for file_path in required_files:
        full_path = root / file_path
        if not full_path.exists():
            missing.append(str(full_path))
            logger.error(f"Missing placeholder file: {full_path}")
        else:
            logger.info(f"Found placeholder file: {full_path}")
    
    return len(missing) == 0, missing

def check_data_artifacts(root: Path) -> Tuple[bool, List[str]]:
    """Check if critical data artifacts exist and are non-empty."""
    # These are the critical outputs expected from the pipeline
    critical_artifacts = [
        'data/processed/annotated_videokr.csv',
        'data/processed/annotation_coverage.json',
        'data/processed/bin_config.json',
        'data/processed/threshold_results.json',
        'data/processed/accuracy_vs_hop_raw.csv',
        'data/processed/accuracy_vs_hop_raw.png',
        'data/processed/accuracy_binned.png',
        'data/processed/sensitivity_intermediate.json',
        'data/processed/sensitivity_thresholds.csv',
        'data/processed/sensitivity_summary.md',
        'data/processed/sensitivity_overlay.png',
        'data/processed/stability_metric.json',
        'data/processed/runtime_log.json',
        'data/processed/memory_log.json',
        'data/processed/final_report.md',
        'data/processed/lint_log.txt',
        'data/processed/type_log.txt'
    ]
    
    missing = []
    for file_path in critical_artifacts:
        full_path = root / file_path
        if not full_path.exists():
            missing.append(str(full_path))
            logger.warning(f"Missing critical artifact: {full_path}")
        elif full_path.stat().st_size == 0:
            missing.append(str(full_path) + " (empty)")
            logger.warning(f"Empty critical artifact: {full_path}")
        else:
            logger.info(f"Found artifact: {full_path} ({full_path.stat().st_size} bytes)")
    
    return len(missing) == 0, missing

def check_docstrings(root: Path) -> Tuple[bool, List[str]]:
    """Check if Python files have docstrings."""
    errors = []
    code_dir = root / 'code'
    
    for py_file in code_dir.rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(py_file))
            
            # Check module docstring
            if not ast.get_docstring(tree):
                errors.append(f"{py_file}: Missing module docstring")
                logger.warning(f"Missing module docstring: {py_file}")
            
            # Check function and class docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        errors.append(f"{py_file}: Missing docstring for {node.name}")
                        logger.warning(f"Missing docstring: {py_file} - {node.name}")
        
        except SyntaxError as e:
            errors.append(f"{py_file}: Syntax error - {e}")
            logger.error(f"Syntax error in {py_file}: {e}")
        except Exception as e:
            errors.append(f"{py_file}: Error parsing - {e}")
            logger.error(f"Error parsing {py_file}: {e}")
    
    return len(errors) == 0, errors

def check_imports(root: Path) -> Tuple[bool, List[str]]:
    """Check if all Python files have valid imports (syntax check)."""
    errors = []
    code_dir = root / 'code'
    
    for py_file in code_dir.rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                compile(f.read(), str(py_file), 'exec')
            logger.debug(f"Valid imports: {py_file}")
        except SyntaxError as e:
            errors.append(f"{py_file}: Import/Syntax error - {e}")
            logger.error(f"Import/Syntax error in {py_file}: {e}")
        except Exception as e:
            errors.append(f"{py_file}: Error checking imports - {e}")
            logger.error(f"Error checking imports in {py_file}: {e}")
    
    return len(errors) == 0, errors

def check_lint_and_type_logs(root: Path) -> Tuple[bool, List[str]]:
    """Check if lint and type check logs exist and are non-empty."""
    required_logs = [
        'data/processed/lint_log.txt',
        'data/processed/type_log.txt'
    ]
    missing = []
    
    for log_path in required_logs:
        full_path = root / log_path
        if not full_path.exists():
            missing.append(str(full_path))
            logger.error(f"Missing required log file: {full_path}")
        elif full_path.stat().st_size == 0:
            missing.append(str(full_path) + " (empty)")
            logger.warning(f"Empty required log file: {full_path}")
        else:
            logger.info(f"Found log file: {full_path}")
    
    return len(missing) == 0, missing

def run_quickstart_validation() -> Dict[str, Any]:
    """Run all validation checks and return results."""
    root = get_project_root()
    logger.info(f"Starting quickstart validation for project at: {root}")
    
    results = {
        'project_root': str(root),
        'checks': {},
        'overall_success': True,
        'errors': []
    }
    
    # Run all checks
    checks = [
        ('directory_structure', check_directory_structure),
        ('placeholder_files', check_placeholder_files),
        ('data_artifacts', check_data_artifacts),
        ('docstrings', check_docstrings),
        ('imports', check_imports),
        ('lint_type_logs', check_lint_and_type_logs)
    ]
    
    for check_name, check_func in checks:
        success, errors = check_func(root)
        results['checks'][check_name] = {
            'success': success,
            'errors': errors
        }
        if not success:
            results['overall_success'] = False
            results['errors'].extend(errors)
            logger.error(f"Check '{check_name}' failed with {len(errors)} errors")
        else:
            logger.info(f"Check '{check_name}' passed")
    
    # Write summary
    summary_path = root / 'data/processed/quickstart_validation_summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Validation summary written to: {summary_path}")
    
    return results

def main():
    """Main entry point for validation."""
    try:
        results = run_quickstart_validation()
        
        if results['overall_success']:
            logger.info("✅ Quickstart validation PASSED - All checks successful")
            print("\n✅ Quickstart validation PASSED")
            print("All directory structures, artifacts, docstrings, and logs are present and valid.")
            return 0
        else:
            logger.error("❌ Quickstart validation FAILED")
            print("\n❌ Quickstart validation FAILED")
            print(f"Found {len(results['errors'])} issues:")
            for error in results['errors']:
                print(f"  - {error}")
            return 1
            
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        print(f"\n❌ Unexpected error: {e}")
        return 2

if __name__ == '__main__':
    sys.exit(main())
