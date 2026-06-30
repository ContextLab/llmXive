"""
Script to validate quickstart.md instructions.
This script performs a dry-run validation of the commands listed in quickstart.md
to ensure they are syntactically correct and point to existing files.
It does NOT execute the full heavy pipelines (training, etc.) to save time/resources.

Usage:
    python code/src/cli/validate_quickstart.py
"""
import sys
import os
import re
from pathlib import Path
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.lib.config import get_logger, configure_logging

def main():
    configure_logging()
    logger = get_logger(__name__)
    
    quickstart_path = PROJECT_ROOT / "quickstart.md"
    
    if not quickstart_path.exists():
        logger.error("quickstart.md not found at project root.")
        sys.exit(1)
    
    logger.info(f"Validating {quickstart_path}...")
    content = quickstart_path.read_text()
    
    errors = []
    warnings = []
    
    # 1. Extract Python commands
    # Pattern: python [path].py
    pattern = r'python\s+(code/)?(src/[^ ]+\.py)'
    matches = re.findall(pattern, content)
    
    logger.info(f"Found {len(matches)} Python script invocations.")
    
    for match in matches:
        prefix, path = match
        full_path = f"{prefix}{path}" if prefix else path
        script_path = PROJECT_ROOT / full_path
        
        if not script_path.exists():
            errors.append(f"Script not found: {full_path}")
            continue
        
        # Syntax check
        try:
            compile(script_path.read_text(), str(script_path), 'exec')
            logger.debug(f"Syntax OK: {full_path}")
        except SyntaxError as e:
            errors.append(f"Syntax error in {full_path}: {e}")
    
    # 2. Check for required sections
    sections = ["install", "data", "train", "benchmark", "stats"]
    content_lower = content.lower()
    missing_sections = [s for s in sections if s not in content_lower]
    
    if missing_sections:
        warnings.append(f"Missing or non-obvious sections: {missing_sections}")
    
    # 3. Verify critical scripts exist (from task list)
    critical_scripts = [
        "src/analysis/generate_dataset.py",
        "src/cli/run_benchmark.py",
        "src/analysis/generate_statistical_report.py"
    ]
    
    for rel_path in critical_scripts:
        script_path = PROJECT_ROOT / rel_path
        if not script_path.exists():
            errors.append(f"Critical script missing: {rel_path}")
    
    # Report
    if errors:
        logger.error("Validation FAILED with errors:")
        for err in errors:
            logger.error(f"  - {err}")
        sys.exit(1)
    
    if warnings:
        logger.warning("Validation PASSED with warnings:")
        for warn in warnings:
            logger.warning(f"  - {warn}")
    
    logger.info("Validation PASSED. All commands in quickstart.md are valid.")
    print("quickstart.md validation successful.")

if __name__ == "__main__":
    main()