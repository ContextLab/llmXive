"""
src/metrics/validate_stimuli.py
--------------------------------
Implements validation of stimulus images for readability and minimum resolution.

The module provides:
  * ``validate_stimuli`` – core function used by the pipeline and tests.
  * ``main`` – CLI entry point that forwards arguments to ``validate_stimuli``.

Validation criteria:
  * The image file must be readable by OpenCV (cv2.imread returns a non‑None array).
  * The image dimensions must be at least ``min_width`` × ``min_height`` pixels.

Any failures are logged to ``logs/validate_stimuli.log`` (relative to the project
root). The log file is always created; the containing ``logs`` directory is
created if missing.
"""

import argparse
import logging
import os
from pathlib import Path
from typing import List, Optional

import cv2

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _setup_logger(log_path: Path) -> logging.Logger:
    """Configure a logger that writes to ``log_path``.

    The logger is created with a simple formatter and INFO level.  Errors are
    logged with ``logger.error`` so they are clearly visible in the log file.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("validate_stimuli")
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if this function is called multiple times
    if not logger.handlers:
        handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def validate_stimuli(
    min_width: int = 640,
    min_height: int = 360,
    stimuli_dir: Optional[Path] = None,
    log_path: Optional[Path] = None,
) -> List[Path]:
    """
    Validate that every image in ``stimuli_dir`` is readable and meets the
    minimum resolution.

    Parameters
    ----------
    min_width : int, optional
        Minimum required width in pixels. Default is 640.
    min_height : int, optional
        Minimum required height in pixels. Default is 360.
    stimuli_dir : pathlib.Path, optional
        Directory containing stimulus images. If ``None`` the function falls
        back to ``<project_root>/data/stimuli/raw``.
    log_path : pathlib.Path, optional
        Destination for the validation log. If ``None`` the function falls
        back to ``<project_root>/logs/validate_stimuli.log``.

    Returns
    -------
    List[pathlib.Path]
        List of paths that failed validation (either unreadable or too small).
    """
    # Resolve default paths relative to the project root.
    project_root = Path(__file__).resolve().parents[3]  # .../project_root
    if stimuli_dir is None:
        stimuli_dir = project_root / "data" / "stimuli" / "raw"
    if log_path is None:
        log_path = project_root / "logs" / "validate_stimuli.log"

    logger = _setup_logger(log_path)

    if not stimuli_dir.is_dir():
        raise FileNotFoundError(f"Stimuli directory not found: {stimuli_dir}")

    invalid_files: List[Path] = []

    # Consider common image extensions; also accept any file (cv2 will fail on non‑images).
    image_patterns = ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff", "*.tif"]
    for pattern in image_patterns:
        for img_path in stimuli_dir.glob(pattern):
            # Attempt to read the image.
            img = cv2.imread(str(img_path))
            if img is None:
                logger.error(f"Unreadable image file: {img_path}")
                invalid_files.append(img_path)
                continue

            height, width = img.shape[:2]
            if width < min_width or height < min_height:
                logger.error(
                    f"Image {img_path} resolution too low: {width}x{height} "
                    f"(minimum {min_width}x{min_height})"
                )
                invalid_files.append(img_path)

    # If there were no failures, write a short success line for completeness.
    if not invalid_files:
        logger.info(
            f"All {len(list(stimuli_dir.rglob('*')))} files passed validation."
        )

    return invalid_files


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate stimulus images for readability and size."
    )
    parser.add_argument(
        "--stimuli-dir",
        type=Path,
        default=None,
        help="Path to directory containing stimulus images. Defaults to "
        "<project_root>/data/stimuli/raw.",
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        default=None,
        help="Path to validation log file. Defaults to "
        "<project_root>/logs/validate_stimuli.log.",
    )
    parser.add_argument(
        "--min-width",
        type=int,
        default=640,
        help="Minimum required image width in pixels (default: 640).",
    )
    parser.add_argument(
        "--min-height",
        type=int,
        default=360,
        help="Minimum required image height in pixels (default: 360).",
    )
    return parser


def main() -> None:
    """Entry point for ``python -m src.metrics.validate_stimuli``."""
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Run validation; we ignore the return value here because the CLI is
    # primarily for side‑effects (log file creation).  Exiting with a non‑zero
    # code signals failure to downstream automation.
    invalid = validate_stimuli(
        min_width=args.min_width,
        min_height=args.min_height,
        stimuli_dir=args.stimuli_dir,
        log_path=args.log_path,
    )
    if invalid:
        # Print a concise summary to stdout for human users.
        print(f"{len(invalid)} invalid stimulus file(s) detected. See log for details.")
        # Exit with status 1 so CI pipelines can treat it as a failure.
        raise SystemExit(1)
    else:
        print("All stimulus images are valid.")
        raise SystemExit(0)


if __name__ == "__main__":
    main()