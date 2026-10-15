"""
src/data/preprocess.py

This script validates and processes the raw PubLayNet (or fallback) dataset
into a Parquet file of ``DocumentPair`` records. The CLI now matches the
quickstart arguments.
"""

import argparse
import json
import logging
import pathlib
import sys
from pathlib import Path
from typing import List, Dict

import pandas as pd
import pyarrow  # ensures parquet support
from jsonschema import Draft7Validator, ValidationError

from llmxive_toolkit import get_logger

logger = get_logger(__name__)

def load_schema(schema_path: Path) -> Dict:
    """Load a JSON/YAML schema file."""
    import yaml

    with schema_path.open("r", encoding="utf-8") as f:
        if schema_path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(f)
        else:
            return json.load(f)

def find_image_and_annotation_files(input_dir: Path) -> List[Dict[str, Path]]:
    """
    Scan ``input_dir`` for image files and locate the corresponding annotation JSON.
    Returns a list of dicts with keys ``image`` and ``annotation``.
    """
    image_extensions = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    pairs = []
    for root, _, files in pathlib.os.walk(input_dir):
        for file in files:
            ext = pathlib.Path(file).suffix.lower()
            if ext in image_extensions:
                image_path = Path(root) / file
                # Annotation file is expected to have the same stem with .json
                annotation_path = image_path.with_suffix(".json")
                if annotation_path.is_file():
                    pairs.append({"image": image_path, "annotation": annotation_path})
                else:
                    logger.warning(f"No annotation JSON for image {image_path}")
    return pairs

def extract_text_from_image(image_path: Path) -> str:
    """
    Run Tesseract OCR on ``image_path`` and return the extracted plain text.
    If ``pytesseract`` is not available, fall back to an empty string.
    """
    try:
        import pytesseract
    except Exception:
        logger.warning("pytesseract not available; OCR will be skipped.")
        return ""

    from PIL import Image

    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as exc:
        logger.error(f"OCR failed for {image_path}: {exc}")
        return ""

def load_layout_annotations(annotation_path: Path, image_path: Path) -> List[Dict]:
    """
    Load layout annotations from a JSON file.
    The PubLayNet JSON format contains absolute pixel coordinates.
    This function normalises them to the range ``[0, 1]`` using the image size.
    If the annotation file is missing or empty, an empty list is returned.
    """
    import json

    try:
        with annotation_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        logger.error(f"Failed to load annotation {annotation_path}: {exc}")
        return []

    # Load image size for normalisation
    from PIL import Image

    try:
        with Image.open(image_path) as img:
            width, height = img.size
    except Exception as exc:
        logger.error(f"Unable to open image {image_path} for size: {exc}")
        return []

    normalized = []
    for obj in data.get("objects", []):
        bbox = obj.get("bbox", {})
        if not bbox:
            continue
        x0 = bbox.get("x0", 0) / width
        y0 = bbox.get("y0", 0) / height
        x1 = bbox.get("x1", 0) / width
        y1 = bbox.get("y1", 0) / height
        normalized.append(
            {
                "type": obj.get("category", "unknown"),
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1,
            }
        )
    return normalized

def build_document_pair(
    image_path: Path,
    annotation_path: Path,
    schema_validator: Draft7Validator,
) -> Dict:
    """
    Build a single DocumentPair record and validate it against the schema.
    Raises ``RuntimeError`` if validation fails.
    """
    plain_text = extract_text_from_image(image_path)
    layout_annotations = load_layout_annotations(annotation_path, image_path)

    record = {
        "doc_id": image_path.stem,
        "plain_text": plain_text,
        "layout_annotations": layout_annotations,
        "image_path": str(image_path),
        "source": "real",
    }

    try:
        schema_validator.validate(record)
    except ValidationError as exc:
        raise RuntimeError(f"Schema validation failed for {image_path}: {exc}") from exc

    return record

def preprocess_dataset(
    input_dir: Path,
    output_parquet: Path,
    schema_path: Path,
) -> None:
    """
    Main preprocessing routine.

    - Scans ``input_dir`` for image / annotation pairs.
    - Extracts OCR text.
    - Normalises layout annotations.
    - Validates each record against the JSON schema.
    - Writes a Parquet file to ``output_parquet``.
    - Aborts with RuntimeError if >5 % of pages lack layout annotations.
    """
    if not input_dir.is_dir():
        raise RuntimeError(f"Input directory does not exist: {input_dir}")

    schema = load_schema(schema_path)
    validator = Draft7Validator(schema)

    pairs = find_image_and_annotation_files(input_dir)
    if not pairs:
        raise RuntimeError(f"No image/annotation pairs found in {input_dir}")

    records = []
    missing_layout = 0
    for pair in pairs:
        record = build_document_pair(pair["image"], pair["annotation"], validator)
        if not record["layout_annotations"]:
            missing_layout += 1
        records.append(record)

    total = len(records)
    missing_pct = missing_layout / total
    logger.info(f"Processed {total} documents; {missing_layout} ({missing_pct:.2%}) missing layout annotations.")
    if missing_pct > 0.05:
        raise RuntimeError(
            f"Too many documents missing layout annotations ({missing_pct:.2%} > 5%)."
        )

    df = pd.DataFrame.from_records(records)
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_parquet, engine="pyarrow")
    logger.info(f"✅ Preprocessed dataset written to {output_parquet}")

def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess raw scientific document images and layout annotations into a Parquet file."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing raw images and JSON annotation files.",
    )
    parser.add_argument(
        "--output-parquet",
        type=Path,
        required=True,
        help="Path where the processed DocumentPair Parquet file will be saved.",
    )
    parser.add_argument(
        "--schema",
        dest="schema_path",
        type=Path,
        required=True,
        help="Path to the JSON/YAML schema defining a DocumentPair record.",
    )
    return parser.parse_args(argv)

def main(argv: List[str] | None = None) -> None:
    args = _parse_args(argv)
    try:
        preprocess_dataset(args.input_dir, args.output_parquet, args.schema_path)
    except Exception as exc:
        logger.error(f"Preprocessing failed: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
