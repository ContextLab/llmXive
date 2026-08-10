"""
Script to physically remove PEMS-SF files from data/raw/ directory.
Task: T104
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cleanup_pems_files():
    """
    Execute physical cleanup of PEMS-SF files and verify removal.
    Returns the verification output string.
    """
    # Determine project root relative to this script
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    data_raw_dir = project_root / "data" / "raw"

    logger.info(f"Target directory: {data_raw_dir}")
    logger.info(f"Directory exists: {data_raw_dir.exists()}")

    if not data_raw_dir.exists():
        logger.warning(f"Directory {data_raw_dir} does not exist. Creating it.")
        data_raw_dir.mkdir(parents=True, exist_ok=True)

    # Files to remove
    files_to_remove = [
        "pems_sf.csv",
        "pems_sf_synthetic.csv"
    ]

    removed_count = 0
    for filename in files_to_remove:
        file_path = data_raw_dir / filename
        if file_path.exists():
            logger.info(f"Removing file: {file_path}")
            try:
                file_path.unlink()
                removed_count += 1
                logger.info(f"Successfully removed: {filename}")
            except Exception as e:
                logger.error(f"Failed to remove {filename}: {e}")
        else:
            logger.info(f"File not found (skipping): {filename}")

    logger.info(f"Removal complete. Files removed: {removed_count}")

    # Verification: Run ls -la data/raw/ | grep pems
    # We simulate the command output by checking the filesystem directly
    verification_output = []
    try:
        pems_files = list(data_raw_dir.glob("*pems*"))
        if pems_files:
            verification_output.append(f"WARNING: Found {len(pems_files)} PEMS-related files:")
            for f in pems_files:
                verification_output.append(f"  - {f.name}")
        else:
            verification_output.append("No PEMS files found in data/raw/")
    except Exception as e:
        verification_output.append(f"Verification failed: {e}")

    verification_text = "\n".join(verification_output)
    logger.info(f"Verification output:\n{verification_text}")

    return verification_text

def main():
    """Main entry point."""
    logger.info("============================================================")
    logger.info("PEMS-SF Physical Cleanup (Task T104)")
    logger.info("============================================================")

    try:
        verification_output = cleanup_pems_files()

        # Write verification to data_provenance_report.md
        project_root = Path(__file__).resolve().parent.parent.parent
        report_path = project_root / "data" / "data_provenance_report.md"

        report_content = f"""# Data Provenance Report: PEMS-SF Cleanup (T104)
Generated: {Path().cwd()}

## Task: T104
Physical Cleanup: Execute `rm -f data/raw/pems_sf.csv data/raw/pems_sf_synthetic.csv`.

## Verification Command Output
```bash
ls -la data/raw/ | grep pems
```

## Actual Verification Result
{verification_output}

## Status
{"SUCCESS - No PEMS-SF files found" if "No PEMS files found" in verification_output else "FAILED - PEMS files still present"}
"""

        # Ensure data directory exists
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_content)
        logger.info(f"Verification report saved to: {report_path}")

        # Assert constraint
        if "No PEMS files found" not in verification_output:
            logger.error("Constraint violated: PEMS files still present.")
            sys.exit(1)

        logger.info("============================================================")
        logger.info("Cleanup and verification completed successfully.")
        logger.info("============================================================")

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()