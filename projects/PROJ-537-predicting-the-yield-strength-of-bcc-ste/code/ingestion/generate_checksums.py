"""
Generate SHA‑256 checksums for all files under ``data/raw`` and ``data/intermediate``
and write them to ``data/provenance/checksums.txt``.
"""

import os
import sys
import logging
from pathlib import Path

from config import CONFIG
from utils.checksums import generate_checksums_for_directory
from utils.logging import get_logger, log_data_artifact

logger = get_logger(__name__)

def generate_all_checksums() -> dict:
    """
    Walk ``data/raw`` and ``data/intermediate`` and return a dict mapping
    relative POSIX paths to SHA‑256 digests.
    """
    raw_checksums = generate_checksums_for_directory(Path(CONFIG.DATA_RAW_DIR))
    interm_checksums = generate_checksums_for_directory(Path(CONFIG.DATA_INTERMEDIATE_DIR))
    combined = {**raw_checksums, **interm_checksums}
    logger.info(f"Generated checksums for {len(combined)} files")
    return combined

def write_checksums_file(checksums: dict, output_path: Path):
    """
    Write the ``checksums`` mapping to ``output_path`` using the conventional
    ``<hash>  <relative_path>`` format.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for rel_path, digest in sorted(checksums.items()):
            fh.write(f"{digest}  {rel_path}\n")
    logger.info(f"Wrote checksums file to {output_path}")
    log_data_artifact(output_path, action="created")

def main():
    """
    CLI entry point – produces ``data/provenance/checksums.txt``.
    """
    try:
        checksums = generate_all_checksums()
        write_checksums_file(checksums, Path(CONFIG.CHECKSUMS_PATH))
    except Exception as exc:
        logger.error(f"Failed to generate/write checksums: {exc}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
