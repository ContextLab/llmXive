"""
Data Integrity Hash
-------------------
Small helper that writes a JSON mapping of file paths to their SHA‑256
hashes. This is used after dataset extraction to record checksums for
downstream validation.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict

from .corruption_handler import compute_sha256

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def write_integrity_hashes(root_dir: Path, output_path: Path) -> None:
    """
    Walk ``root_dir`` recursively, compute SHA‑256 for each file,
    and write a JSON dictionary ``{relative_path: hash}`` to
    ``output_path``.

    Parameters
    ----------
    root_dir : Path
        Directory containing the extracted dataset.
    output_path : Path
        Destination JSON file.
    """
    hashes: Dict[str, str] = {}
    for file_path in root_dir.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(root_dir))
            hashes[rel_path] = compute_sha256(file_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    logger.info(f"Wrote integrity hashes for {len(hashes)} files to {output_path}")
