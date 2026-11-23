"""
Task T106: Physical Cleanup of legacy data/results/ directory.

This script physically removes the legacy `data/results/` directory and its contents,
ensuring all results are migrated to `data/processed/results/` as per specification.

Verification:
- Executes `rm -rf data/results/`
- Runs `ls -la data/ | grep results` to verify only `processed/results` remains
- Logs output to `data/data_provenance_report.md`
"""
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/t106_cleanup.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"
    legacy_results_dir = data_dir / "results"
    processed_results_dir = data_dir / "processed" / "results"
    provenance_report_path = data_dir / "data_provenance_report.md"

    logger.info("=" * 80)
    logger.info("Task T106: Physical Cleanup of data/results/ directory")
    logger.info("=" * 80)

    # Check if legacy directory exists
    if not legacy_results_dir.exists():
        logger.info(f"Legacy directory {legacy_results_dir} does not exist. Skipping cleanup.")
        # Still verify current state and update report
    else:
        logger.warning(f"Legacy directory found: {legacy_results_dir}")
        logger.info("Executing: rm -rf data/results/")
        
        try:
            # Execute physical removal
            result = subprocess.run(
                ["rm", "-rf", str(legacy_results_dir)],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Removal command executed successfully.")
            if result.stdout:
                logger.info(f"stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"stderr: {result.stderr}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to remove directory: {e}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            sys.exit(1)

    # Verification Step
    logger.info("Verification: Running `ls -la data/ | grep results`")
    try:
        # Use find to list matching entries to be robust against shell variations
        # We want to see what 'results' strings exist in the data directory listing
        ls_result = subprocess.run(
            ["ls", "-la", str(data_dir)],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Filter for lines containing 'results'
        lines = ls_result.stdout.splitlines()
        matching_lines = [line for line in lines if 'results' in line]
        
        verification_output = "\n".join(matching_lines)
        
        logger.info("Verification Output:")
        logger.info(verification_output)

        # Assert constraint: Only processed/results should appear
        # We expect to see 'processed/results' and NOT a standalone 'results' directory
        # A standalone 'results' would appear as a directory entry like 'drwxr-xr-x ... results'
        
        has_standalone_results = False
        for line in matching_lines:
            # Check if 'results' appears as a directory entry (not part of 'processed/results')
            # The line usually ends with the name or has the name as a distinct token
            if line.strip().endswith('results') and not 'processed' in line:
                has_standalone_results = True
                logger.error(f"Violation detected: Standalone 'results' directory still exists: {line}")
            elif 'processed/results' in line:
                logger.info(f"Valid entry found: {line}")

        if has_standalone_results:
            logger.error("VERIFICATION FAILED: Legacy results directory still exists.")
            sys.exit(1)
        
        logger.info("VERIFICATION PASSED: Only processed/results directory exists.")

    except subprocess.CalledProcessError as e:
        logger.error(f"Verification command failed: {e}")
        sys.exit(1)

    # Update Data Provenance Report
    logger.info(f"Updating provenance report: {provenance_report_path}")
    
    report_content = f"""# Data Provenance Report: T106 Results Directory Cleanup
Generated: {datetime.now().isoformat()}

## Task: T106
Physical Cleanup of legacy `data/results/` directory.

## Action Taken
- Executed `rm -rf data/results/`
- Verified removal via `ls -la data/ | grep results`

## Verification Command Output
```bash
ls -la {data_dir} | grep results
```

**Output:**
```
{verification_output}
```

**Status:** {"SUCCESS" if not has_standalone_results else "FAILED"}
- Legacy `data/results/` directory: {"REMOVED" if not legacy_results_dir.exists() else "PRESENT (ERROR)"}
- Valid `data/processed/results/` directory: {"PRESENT" if processed_results_dir.exists() else "MISSING"}

## Constraint Check
- Constraint: `output` must contain only `processed/results`.
- Result: {"PASS" if not has_standalone_results else "FAIL"}
"""
    
    # Append to existing report or create new
    if provenance_report_path.exists():
        with open(provenance_report_path, 'a') as f:
            f.write("\n\n" + report_content)
    else:
        with open(provenance_report_path, 'w') as f:
            f.write(report_content)
    
    logger.info("Provenance report updated.")
    logger.info("=" * 80)
    logger.info("Task T106 Completed Successfully")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()