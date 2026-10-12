"""
Script to copy contract schema files from the specification directory
into the runtime location `code/contracts/`. This ensures that downstream
validation scripts can locate the schemas without requiring hard‑coded paths.
"""

import shutil
from pathlib import Path
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """
    Locate the source schema directory (under `specs/`) and copy the three
    required schema files into `code/contracts/`. If a source file does not
    exist, the script raises a RuntimeError to enforce the "fail loudly"
    principle.
    """
    # Determine project root (assumes this script lives in code/contracts/)
    project_root = Path(__file__).resolve().parents[2]

    # Expected source location (as described in the project layout)
    source_dir = project_root / "specs" / "001-emotional-contagion-decisions" / "contracts"
    target_dir = project_root / "code" / "contracts"

    logger.info(f"Source schema directory: {source_dir}")
    logger.info(f"Target schema directory: {target_dir}")

    # Ensure target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    # List of schema filenames to copy
    schema_files = [
        "thread.schema.yaml",
        "sentiment.schema.yaml",
        "result.schema.yaml"
    ]

    missing = []
    for filename in schema_files:
        src_path = source_dir / filename
        dst_path = target_dir / filename

        if not src_path.is_file():
            missing.append(str(src_path))
            continue

        # Copy file, overwriting any existing version
        shutil.copy2(src_path, dst_path)
        logger.info(f"Copied {src_path} → {dst_path}")

    if missing:
        missing_list = "\n".join(missing)
        raise RuntimeError(
            f"The following schema files were not found in the source directory:\n{missing_list}\n"
            "Ensure that the specification repository includes the contract schemas."
        )

    logger.info("All contract schemas have been successfully copied.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Failed to copy contract schemas: {e}")
        sys.exit(1)