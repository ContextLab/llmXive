"""
Script to copy JSON‑Schema contract files from the specification directory
into the project's top‑level ``contracts`` directory.

This script is idempotent: existing files will be overwritten with the
source versions. It logs its actions to the standard logger.
"""
import shutil
from pathlib import Path
import logging
import sys

# Configure a simple logger that writes to stdout
logger = logging.getLogger("copy_contracts")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)

def copy_contract(src: Path, dst: Path) -> None:
    """Copy a single contract file, creating the destination directory if needed."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    logger.info(f"Copied {src} → {dst}")

def main() -> None:
    """
    Locate the specification contracts directory and copy its contents
    to the project's ``contracts`` folder.
    """
    # Resolve paths relative to this script's location
    script_dir = Path(__file__).resolve().parent
    spec_contracts_dir = script_dir.parent.parent / "specs" / "001-statistical-analysis-of-publicly-availab" / "contracts"
    project_contracts_dir = script_dir.parent.parent / "contracts"

    if not spec_contracts_dir.is_dir():
        logger.error(f"Specification contracts directory not found: {spec_contracts_dir}")
        sys.exit(1)

    contract_files = ["dataset.schema.yaml", "signal.schema.yaml", "soc_cluster.schema.yaml"]
    for fname in contract_files:
        src_path = spec_contracts_dir / fname
        dst_path = project_contracts_dir / fname
        if not src_path.is_file():
            logger.error(f"Source contract file missing: {src_path}")
            sys.exit(1)
        copy_contract(src_path, dst_path)

    logger.info("All contract files have been successfully copied.")

if __name__ == "__main__":
    main()