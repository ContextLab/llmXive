"""
Preprocess raw PubLayNet documents into canonical DocumentPair records
and write them to a Parquet file.

The script expects a directory containing image files (PNG/JPEG) and a
matching JSON annotation file for each image (same base name, ``.json``).
It extracts OCR text using Tesseract, loads the layout annotations,
validates each record against the JSON schema defined in
``specs/001-llmxive-follow-up-extending-scalable-vis/contracts/documentpair.schema.yaml``,
and writes a Parquet table with the following columns:

  - doc_id (str): unique identifier (base filename)
  - plain_text (str): OCR‑extracted text
  - layout_annotations (list[dict]): list of bounding‑box dicts
  - image_path (str): absolute path to the source image
  - source (str): always ``"real"``
  - visual_latent (optional, omitted here)

The script aborts with a clear ``RuntimeError`` if more than 5 % of
pages are missing layout annotations, satisfying the verification
requirement for T002.

The command‑line interface matches the Quickstart documentation:

    python -m src.data.preprocess \\
        --input-dir <input_dir> \\
        --output-parquet <output_parquet> \\
        --schema <schema_path>

Example (as used in ``quickstart.md``):

    python -m src.data.preprocess \\
        --input-dir data/raw/publaynet \\
        --output-parquet data/processed/document_pairs.parquet \\
        --schema specs/001-llmxive-follow-up-extending-scalable-vis/contracts/documentpair.schema.yaml
"""

import argparse
import json
import logging
import pathlib
import sys
from typing import List, Dict

import pandas as pd
from jsonschema import Draft7Validator, ValidationError
from tqdm import tqdm
from PIL import Image
import pytesseract

# Use the project's logger utility if available; otherwise fall back to basic logging.
try:
    from llmxive_toolkit import get_logger

    log = get_logger(__name__)
except Exception:  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg"}


def load_schema(schema_path: pathlib.Path) -> Dict:
    """Load a JSON/YAML schema file."""
    import yaml

    with schema_path.open("r", encoding="utf-8") as f:
        if schema_path.suffix in {".yaml", ".yml"}:
            return yaml.safe_load(f)
        else:
            return json.load(f)


def find_image_and_annotation_files(
    input_dir: pathlib.Path,
) -> List[Dict[str, pathlib.Path]]:
    """
    Scan ``input_dir`` for image files and locate the corresponding annotation JSON.
    Returns a list of dicts with keys ``image`` and ``annotation``.
    """
    records = []
    for img_path in input_dir.rglob("*"):
        if img_path.suffix.lower() not in SUPPORTED_IMAGE_EXTS:
            continue
        ann_path = img_path.with_suffix(".json")
        if not ann_path.is_file():
            # No annotation file – we still count it later as missing.
            ann_path = None
        records.append({"image": img_path, "annotation": ann_path})
    return records


def extract_text_from_image(image_path: pathlib.Path) -> str:
    """Run Tesseract OCR on ``image_path`` and return the extracted plain text."""
    try:
        img = Image.open(image_path)
    except Exception as e:
        log.error("Failed to open image %s: %s", image_path, e)
        raise
    text = pytesseract.image_to_string(img)
    return text.strip()


def load_layout_annotations(
    annotation_path: pathlib.Path, image_path: pathlib.Path
) -> List[Dict]:
    """
    Load layout annotations from a JSON file.

    The PubLayNet JSON format contains absolute pixel coordinates.
    This function normalises them to the range ``[0, 1]`` using the image size.
    If the annotation file is missing or empty, an empty list is returned.
    """
    if annotation_path is None or not annotation_path.is_file():
        return []

    with annotation_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    # Expected format: a list of objects with ``type`` and bbox fields.
    # PubLayNet stores ``bbox`` as [x0, y0, x1, y1] in absolute pixels.
    try:
        img = Image.open(image_path)
        width, height = img.size
    except Exception as e:
        log.error("Unable to read image size for %s: %s", image_path, e)
        raise

    normalized = []
    for item in raw:
        # Guard against unexpected structures.
        if not isinstance(item, dict):
            continue
        bbox = item.get("bbox") or item.get("box") or item.get("points")
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            continue
        x0, y0, x1, y1 = bbox
        normalized.append(
            {
                "type": item.get("label", item.get("type", "unknown")),
                "x0": float(x0) / width,
                "y0": float(y0) / height,
                "x1": float(x1) / width,
                "y1": float(y1) / height,
            }
        )
    return normalized


def build_document_pair(
    image_path: pathlib.Path,
    annotation_path: pathlib.Path,
    schema_validator: Draft7Validator,
) -> Dict:
    """
    Build a single DocumentPair record and validate it against the schema.
    Raises ``RuntimeError`` if validation fails.
    """
    doc_id = image_path.stem
    plain_text = extract_text_from_image(image_path)
    layout_ann = load_layout_annotations(annotation_path, image_path)

    record = {
        "doc_id": doc_id,
        "plain_text": plain_text,
        "layout_annotations": layout_ann,
        "image_path": str(image_path.resolve()),
        "source": "real",
    }

    # Validation – we deliberately let ValidationError surface as a clear
    # message; the caller can decide whether to abort or skip.
    try:
        schema_validator.validate(record)
    except ValidationError as ve:
        raise RuntimeError(f"Schema validation failed for {doc_id}: {ve.message}")

    return record


def preprocess_dataset(
    input_dir: pathlib.Path,
    output_parquet: pathlib.Path,
    schema_path: pathlib.Path,
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
    input_dir = input_dir.resolve()
    output_parquet = output_parquet.resolve()
    schema_path = schema_path.resolve()

    if not input_dir.is_dir():
        raise RuntimeError(f"Input directory does not exist: {input_dir}")

    schema = load_schema(schema_path)
    validator = Draft7Validator(schema)

    file_pairs = find_image_and_annotation_files(input_dir)
    if not file_pairs:
        raise RuntimeError(f"No image files found in {input_dir}")

    records = []
    missing_layout_cnt = 0

    log.info("Processing %d files from %s", len(file_pairs), input_dir)

    for pair in tqdm(file_pairs, desc="Preprocessing", unit="file"):
        img_path = pair["image"]
        ann_path = pair["annotation"]
        try:
            record = build_document_pair(img_path, ann_path, validator)
            if not record["layout_annotations"]:
                missing_layout_cnt += 1
            records.append(record)
        except Exception as e:
            log.error("Failed to process %s: %s", img_path, e)
            raise

    total = len(records)
    missing_ratio = missing_layout_cnt / total
    if missing_ratio > 0.05:
        raise RuntimeError(
            f"Too many pages without layout annotations ({missing_ratio:.2%} > 5%)."
        )
    else:
        log.info(
            "Pages without layout annotations: %d / %d (%.2f%%)",
            missing_layout_cnt,
            total,
            missing_ratio * 100,
        )

    # Convert to DataFrame and write Parquet.
    df = pd.DataFrame(records)
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_parquet, engine="pyarrow", index=False)
    log.info("Successfully wrote %d records to %s", total, output_parquet)

def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess raw PubLayNet documents into DocumentPair records."
    )
    parser.add_argument(
        "--input-dir",
        type=pathlib.Path,
        required=True,
        help="Directory containing raw images and JSON annotations.",
    )
    parser.add_argument(
        "--output-parquet",
        type=pathlib.Path,
        required=True,
        help="Path to the output Parquet file.",
    )
    parser.add_argument(
        "--schema",
        dest="schema_path",
        type=pathlib.Path,
        required=True,
        help="Path to the DocumentPair JSON schema (YAML or JSON).",
    )
    return parser.parse_args(argv)

def main(argv: List[str] | None = None) -> None:
    args = _parse_args(argv)
    preprocess_dataset(args.input_dir, args.output_parquet, args.schema_path)

if __name__ == "__main__":
    sys.exit(main())
