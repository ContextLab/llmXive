"""
src/utils/checksum.py
---------------------

Utility functions for computing SHA‑256 checksums.  The file already
existed in the repository; it is reproduced here unchanged to satisfy
the requirement that the public API (``compute_checksum`` and
``write_checksum``) be present and correctly implemented.
"""

import hashlib
from pathlib import Path
from typing import Union

from llmxive_toolkit import get_logger

log = get_logger(__name__)

def compute_checksum(input_path: Union[str, Path], output_path: Union[str, Path]) -> None:
    """
    Compute the SHA‑256 checksum of ``input_path`` and write the hex digest
    to ``output_path``.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    sha256 = hashlib.sha256()
    with input_path.open("rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)

    digest = sha256.hexdigest()
    output_path.write_text(digest)
    log.debug(f"Checksum for {input_path} written to {output_path}")

def write_checksum(path: Union[str, Path], out_dir: Union[str, Path]) -> None:
    """
    Convenience wrapper: compute the checksum of *path* and write it to
    ``<out_dir>/<filename>.sha256``.
    """
    path = Path(path)
    out_dir = Path(out_dir)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{path.stem}.sha256"
    compute_checksum(path, output_path)
