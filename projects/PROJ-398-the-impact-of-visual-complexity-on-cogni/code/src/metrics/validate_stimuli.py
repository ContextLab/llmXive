"""
validate_stimuli.py
-------------------

This module provides functionality to verify that each stimulus image
downloaded by ``src.metrics.fetch_stimuli`` is:
  1. Readable by OpenCV (i.e., ``cv2.imread`` does not return ``None``).
  2. At least 640 px wide and 360 px tall.

Failures are written to ``logs/validate_stimuli.log``.  The script can be
executed directly:

    python -m src.metrics.validate_stimuli [--stimuli-dir PATH]

The default ``stimuli-dir`` is ``data/stimuli`` relative to the repository
root.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Tuple

import cv2

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "validate_stimuli.log"


def _configure_logger() -> logging.Logger:
    """Configure a file logger for validation failures.

    Returns
    -------
    logging.Logger
        A logger that writes ``ERROR`` level messages to
        ``logs/validate_stimuli.log``.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("validate_stimuli")
    logger.setLevel(logging.ERROR)

    # Avoid adding multiple handlers if this function is called repeatedly
    if not logger.handlers:
        file_handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


# ----------------------------------------------------------------------
# Core validation logic
# ----------------------------------------------------------------------
def _is_image_readable(image_path: Path) -> bool:
    """Return ``True`` if OpenCV can read the image.

    Parameters
    ----------
    image_path: Path
        Path to the image file.

    Returns
    -------
    bool
        ``True`` if ``cv2.imread`` returns a non‑``None`` array.
    """
    try:
        img = cv2.imread(str(image_path))
        return img is not None
    except Exception:  # pragma: no cover – OpenCV rarely raises here
        return False


def _has_minimum_resolution(image_path: Path, min_width: int = 640, min_height: int = 360) -> bool:
    """Check that the image meets the minimum resolution requirements.

    Parameters
    ----------
    image_path: Path
        Path to the image file.
    min_width: int, optional
        Minimum width in pixels (default 640).
    min_height: int, optional
        Minimum height in pixels (default 360).

    Returns
    -------
    bool
        ``True`` if the image size is >= the required dimensions.
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return False
    height, width = img.shape[:2]
    return width >= min_width and height >= min_height


def validate_stimuli(
    stimuli_dir: Path,
) -> Tuple[List[Path], List[Tuple[Path, str]]]:
    """Validate all images in ``stimuli_dir``.

    The function walks the directory (non‑recursively) and checks each file
    that OpenCV can interpret as an image.  Failures are logged and also
    returned to the caller.

    Parameters
    ----------
    stimuli_dir: Path
        Directory containing stimulus image files.

    Returns
    -------
    Tuple[List[Path], List[Tuple[Path, str]]]
        * ``valid_images`` – list of image paths that passed all checks.
        * ``failed_images`` – list of ``(image_path, reason)`` tuples for
          images that failed validation.
    """
    logger = _configure_logger()
    valid_images: List[Path] = []
    failed_images: List[Tuple[Path, str]] = []

    if not stimuli_dir.is_dir():
        logger.error(f"Stimuli directory does not exist: {stimuli_dir}")
        raise FileNotFoundError(f"Stimuli directory does not exist: {stimuli_dir}")

    for entry in stimuli_dir.iterdir():
        if entry.is_file():
            # 1️⃣ Readability check
            if not _is_image_readable(entry):
                reason = "Unreadable / corrupted image"
                logger.error(f"{entry}: {reason}")
                failed_images.append((entry, reason))
                continue

            # 2️⃣ Resolution check
            if not _has_minimum_resolution(entry):
                reason = "Resolution below 640x360"
                logger.error(f"{entry}: {reason}")
                failed_images.append((entry, reason))
                continue

            # Passed all checks
            valid_images.append(entry)

    return valid_images, failed_images


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> None:
    """Command‑line interface for stimulus validation.

    Parameters
    ----------
    argv: List[str] | None, optional
        Argument vector passed to ``argparse``; if ``None`` (the default)
        ``sys.argv[1:]`` is used.
    """
    parser = argparse.ArgumentParser(
        description="Validate stimulus images for readability and minimum resolution."
    )
    parser.add_argument(
        "--stimuli-dir",
        type=Path,
        default=Path("data/stimuli"),
        help="Directory containing stimulus images (default: data/stimuli).",
    )
    args = parser.parse_args(argv)

    try:
        valid, failed = validate_stimuli(args.stimuli_dir)
    except Exception as exc:
        # Unexpected errors (e.g., missing directory) are logged and cause a
        # non‑zero exit code.
        logging.error(f"Validation failed with unexpected error: {exc}")
        sys.exit(1)

    # Print a short summary to stdout for human operators.
    print(f"Validation complete: {len(valid)} valid, {len(failed)} failed.")
    if failed:
        print(f"See '{LOG_FILE}' for details of the failures.")
        sys.exit(1)  # Signal that there were validation issues.
    else:
        # Ensure the log file exists (empty) so downstream steps can rely on its presence.
        LOG_FILE.touch(exist_ok=True)
        sys.exit(0)


if __name__ == "__main__":
    main()