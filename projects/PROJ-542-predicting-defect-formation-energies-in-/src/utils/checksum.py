"""
src/utils/checksum.py
---------------------

Utility to compute a SHA‑256 checksum for a file and write the hexadecimal
digest to a target file. Used by the pipeline to record checksums of raw
and processed data artefacts (Constitution‑III requirement).
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
    Compute the SHA‑256 checksum of ``input_path`` and write the hex digest
    to ``output_path``.

    Parameters
    ----------
    input_path : str or Path
        Path to the file whose checksum should be computed.
    output_path : str or Path
        Destination file that will contain the checksum string.

    The function creates the parent directory of ``output_path`` if it does
    not already exist. It overwrites any existing file.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.is_file():
        raise FileNotFoundError(f"Input file for checksum not found: {input_path}")

    sha256 = hashlib.sha256()
    # Read the file in chunks to avoid excessive memory usage.
    with input_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    digest = sha256.hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as out_f:
        out_f.write(digest)

    log.info(f"Wrote SHA‑256 checksum for {input_path} to {output_path}")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI entry point: ``python -m src.utils.checksum <input> <output>``.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Compute SHA‑256 checksum of a file and write it to another file."
    )
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to the file to checksum.",
    )
    parser.add_argument(
        "output_path",
        type=str,
        help="Path where the checksum will be written.",
    )
    args = parser.parse_args()
    try:
        compute_checksum(args.input_path, args.output_path)
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)

if __name__ == "__main__":
    main()