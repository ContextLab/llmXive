"""
Validation script for the regime‑map PNG produced by the analysis step.

Checks performed:
  1. The PNG file exists.
  2. Its file size is ≤ 5 MiB.
  3. The image contains the three required axis‑label strings:
     - "Masking Horizon"
     - "Semantic Density"
     - "Success Rate"

The script exits with status 0 on success.
On failure it prints an error message beginning with the corresponding
error code (PNG_SIZE_EXCEEDED or MISSING_LABELS) and exits with a
non‑zero status.
"""

import argparse
import sys
from pathlib import Path

# Pillow is used for reading PNG metadata; it is added to the project's
# requirements.txt in the same task.
from PIL import Image

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
DEFAULT_PNG_PATH = Path(__file__).resolve().parents[1] / "results" / "regime_map.png"
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MiB
REQUIRED_LABELS = [
    "Masking Horizon",
    "Semantic Density",
    "Success Rate",
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _file_size_ok(png_path: Path) -> bool:
    """Return True if the file size is within the allowed limit."""
    return png_path.stat().st_size <= MAX_SIZE_BYTES

def _extract_png_text(png_path: Path) -> str:
    """
    Extract textual information from a PNG.

    Pillow exposes PNG textual chunks via the ``info`` dictionary.
    Not all PNGs contain such chunks; in that case we fall back to a
    raw‑byte search for the required strings.
    """
    try:
        with Image.open(png_path) as img:
            # ``img.info`` contains any tEXt/zTXt/iTXt chunks.
            meta_text = " ".join(str(v) for v in img.info.values())
    except Exception:
        meta_text = ""

    # Fallback: read the raw bytes and decode as latin‑1 to avoid decode errors.
    try:
        raw_bytes = png_path.read_bytes()
        raw_text = raw_bytes.decode("latin-1", errors="ignore")
    except Exception:
        raw_text = ""

    return meta_text + " " + raw_text

def _labels_present(text_blob: str) -> bool:
    """Check that every required label appears in the supplied text."""
    return all(label in text_blob for label in REQUIRED_LABELS)

# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the regime‑map PNG file (size and axis labels)."
    )
    parser.add_argument(
        "png_path",
        nargs="?",
        default=str(DEFAULT_PNG_PATH),
        help="Path to the regime‑map PNG (default: results/regime_map.png)",
    )
    args = parser.parse_args()
    png_path = Path(args.png_path)

    # 1. Existence
    if not png_path.is_file():
        print("MISSING_FILE: PNG file not found at", png_path)
        sys.exit(1)

    # 2. Size check
    if not _file_size_ok(png_path):
        print("PNG_SIZE_EXCEEDED: file size exceeds 5 MiB")
        sys.exit(1)

    # 3. Label presence
    text_blob = _extract_png_text(png_path)
    if not _labels_present(text_blob):
        print("MISSING_LABELS: one or more required axis labels are absent")
        sys.exit(1)

    # Success
    print("Validation passed: PNG size OK and all required labels present.")
    sys.exit(0)

if __name__ == "__main__":
    main()
