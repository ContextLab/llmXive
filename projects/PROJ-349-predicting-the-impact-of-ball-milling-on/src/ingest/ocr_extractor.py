"""
OCR fallback extraction module.

This module attempts to extract particle size distribution (PSD) metrics (D10, D50, D90)
from images (e.g., scanned PSD curves) using OCR. It never drops rows; if OCR
fails or the required libraries are unavailable, the original row is preserved
with missing PSD values left as NaN.

Expected input format:
  - A CSV/Parquet file containing at least the columns:
      * experiment_id
      * psd_image_path (optional, path to an image file containing the PSD curve)
      * d10, d50, d90 (may be NaN)
  - Additional columns are ignored by this module.

The module writes the enriched DataFrame to the supplied output path.

The script can be invoked as a module:
    python -m src.ingest.ocr_extractor --input <path> --output <path>

If the optional OCR dependencies (`pytesseract` and `Pillow`) are not installed,
the script logs a warning and proceeds without performing OCR.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

# Local imports – use the project's API surface
from src.utils.logger import get_logger
from src.utils.exceptions import DataIngestionError
from llmxive_toolkit import paths

log = get_logger(__name__)

# Regular expression to capture floating‑point numbers (including integers) from OCR text
_NUMBER_RE = re.compile(r"[-+]?\d*\.\d+|\d+")

def _extract_numbers_from_text(text: str) -> list[float]:
    """
    Extract all numbers from a string and return them as floats.
    The OCR output often contains the three PSD values in order;
    the caller is responsible for interpreting the order.
    """
    numbers = _NUMBER_RE.findall(text)
    return [float(num) for num in numbers]

def _attempt_ocr_on_image(image_path: Path) -> Optional[dict[str, float]]:
    """
    Run OCR on the supplied image and try to parse D10, D50, D90 values.

    Returns a dictionary with keys ``d10``, ``d50``, ``d90`` if at least
    three numbers are found; otherwise returns ``None``.
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError as e:
        log.warning(
            "OCR libraries not available (pytesseract or Pillow). "
            "Skipping OCR for %s: %s",
            image_path,
            e,
        )
        return None

    if not image_path.is_file():
        log.warning("Image file not found for OCR: %s", image_path)
        return None

    try:
        img = Image.open(image_path)
        ocr_text = pytesseract.image_to_string(img)
        nums = _extract_numbers_from_text(ocr_text)
        if len(nums) < 3:
            log.info(
                "OCR did not return enough numeric values for %s (found %d).",
                image_path,
                len(nums),
            )
            return None
        # Assume the first three numbers correspond to D10, D50, D90
        d10, d50, d90 = nums[:3]
        return {"d10": d10, "d50": d50, "d90": d90}
    except Exception as exc:
        log.error("Unexpected error during OCR of %s: %s", image_path, exc)
        return None

def process_ocr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a DataFrame, attempting OCR for rows where PSD values are missing
    but an image path is provided.

    The function never drops rows; it only fills missing PSD columns when
    OCR succeeds.

    Parameters
    ----------
    df : pd.DataFrame
        Input data. Must contain at least the columns ``psd_image_path``,
        ``d10``, ``d50`` and ``d90`` (the PSD columns may be NaN).

    Returns
    -------
    pd.DataFrame
        The DataFrame with any successfully extracted PSD values filled in.
    """
    required_cols = {"psd_image_path", "d10", "d50", "d90"}
    missing = required_cols - set(df.columns)
    if missing:
        raise DataIngestionError(
            f"Input DataFrame is missing required columns for OCR: {missing}"
        )

    # Work on a copy to avoid side‑effects
    result_df = df.copy()

    for idx, row in result_df.iterrows():
        # Check if any PSD metric is missing
        if pd.isna(row["d10"]) or pd.isna(row["d50"]) or pd.isna(row["d90"]):
            img_path = Path(row["psd_image_path"])
            if not img_path:
                log.info(
                    "Row %s has missing PSD but no image path; skipping OCR.", idx
                )
                continue

            ocr_result = _attempt_ocr_on_image(img_path)
            if ocr_result:
                # Fill only the missing values to avoid overwriting existing data
                for metric in ("d10", "d50", "d90"):
                    if pd.isna(row[metric]) and metric in ocr_result:
                        result_df.at[idx, metric] = ocr_result[metric]
                log.info(
                    "OCR succeeded for row %s; filled missing PSD values.", idx
                )
            else:
                log.info(
                    "OCR did not produce usable results for row %s; leaving NaNs.", idx
                )
        else:
            log.debug("Row %s already has complete PSD; OCR not required.", idx)

    return result_df

def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OCR fallback extraction for PSD images."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input CSV or Parquet file containing experiment data.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path where the enriched CSV will be written.",
    )
    return parser.parse_args(argv)

def main(argv: Optional[list[str]] = None) -> int:
    """Entry‑point for ``python -m src.ingest.ocr_extractor``."""
    args = _parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        log.error("Input file does not exist: %s", input_path)
        raise DataIngestionError(f"Input file not found: {input_path}")

    # Load input – support CSV and Parquet
    try:
        if input_path.suffix.lower() == ".parquet":
            df = pd.read_parquet(input_path)
        else:
            df = pd.read_csv(input_path)
    except Exception as exc:
        log.error("Failed to read input file %s: %s", input_path, exc)
        raise DataIngestionError(f"Could not read input file: {exc}")

    log.info("Starting OCR fallback extraction on %d rows.", len(df))
    enriched_df = process_ocr(df)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        enriched_df.to_csv(output_path, index=False)
        log.info("OCR‑enriched data written to %s", output_path)
    except Exception as exc:
        log.error("Failed to write output file %s: %s", output_path, exc)
        raise DataIngestionError(f"Could not write output file: {exc}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
