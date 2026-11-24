"""
code/utils/checksum.py
-----------------------

Utility for computing SHA‑256 checksums of files.

The original project already provides a ``compute_checksum`` function in
``src.utils.checksum`` that writes a checksum to a given output path.
The test suite for this task expects a higher‑level helper named
``write_checksum`` which takes a source file path and a directory where
the checksum file should be created.

This module implements ``write_checksum`` and re‑exports ``compute_checksum``
for backward compatibility.  It does **not** depend on any external
packages beyond the Python standard library and the project's existing
``llmxive_toolkit`` logger.
"""

import hashlib
from pathlib import Path
from typing import Union

from llmxive_toolkit import get_logger

log = get_logger(__name__)

def compute_checksum(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
) -> None:
    """
    Compute the SHA‑256 checksum of ``input_path`` and write the hexadecimal
    digest to ``output_path``.

    Parameters
    ----------
    input_path : str or Path
        Path to the file whose checksum should be computed.
    output_path : str or Path
        Destination file that will contain the checksum string.

    The function creates the parent directory of ``output_path`` if it does
    not already exist and overwrites any existing file.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    log.debug(f"Computing SHA‑256 for {input_path}")

    # Read the file in binary mode and compute the digest.
    sha256 = hashlib.sha256()
    with input_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    digest = sha256.hexdigest()

    # Ensure the output directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(digest, encoding="utf-8")
    log.debug(f"Wrote checksum to {output_path}")

def write_checksum(path: Union[str, Path], out_dir: Union[str, Path]) -> None:
    """
    Convenience wrapper used by the test suite.

    Given a file ``path`` and a target directory ``out_dir``, compute the
    SHA‑256 checksum of the file and write it to ``<out_dir>/<filename>.sha256``.

    The function mirrors the behaviour of the original ``compute_checksum``
    but constructs the output filename automatically.

    Parameters
    ----------
    path : str or Path
        Path to the input file.
    out_dir : str or Path
        Directory where the ``<filename>.sha256`` file will be created.

    Raises
    ------
    FileNotFoundError
        If the input file does not exist.
    """
    input_path = Path(path)
    out_dir_path = Path(out_dir)

    if not input_path.is_file():
        log.error(f"Input file does not exist: {input_path}")
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    # Ensure the output directory exists.
    out_dir_path.mkdir(parents=True, exist_ok=True)

    # Destination file name: <original_name>.sha256
    output_path = out_dir_path / f"{input_path.name}.sha256"

    # Delegate to the core implementation.
    compute_checksum(input_path, output_path)

# The module's public API mirrors the original implementation.
__all__ = ["compute_checksum", "write_checksum"]