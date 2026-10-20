"""
Chunked dataset loader for materials properties.

This script reads a CSV file in chunks (≤ 5 000 rows), validates each row
against the dataset contract, removes rows with missing required fields,
drops duplicate ``material_id`` entries (keeping the first occurrence),
filters outliers using a 1.5 × IQR rule for ``band_gap`` and ``hardness``,
skips materials whose chemical formula contains unknown elements, and
writes the cleaned data to the specified output path.

It also monitors peak RAM usage via ``psutil`` and asserts that it never
exceeds 6 GB (FR‑001).
"""

import argparse
import logging
from pathlib import Path

import pandas as pd
import psutil
import yaml
from jsonschema import validate, ValidationError
from pymatgen.core import Composition

from llmxive_toolkit import paths, get_logger

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------
CHUNK_SIZE = 5_000
RAM_LIMIT_BYTES = 6 * 1024 ** 3  # 6 GB

# -------------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------------
log = get_logger(__name__)

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------
def load_schema() -> dict:
    """Load the JSON‑Schema for the materials dataset."""
    schema_path = paths.root / "contracts" / "materials_dataset.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_row(row: dict, schema: dict) -> bool:
    """Validate a single row against the contract schema."""
    try:
        validate(instance=row, schema=schema)
    except ValidationError as e:
        log.warning("Row failed schema validation: %s – %s", row, e.message)
        return False
    return True

def is_known_formula(formula: str) -> bool:
    """
    Return ``True`` if the chemical formula can be parsed and all elements
    are known to ``pymatgen``. ``Composition`` raises ``ValueError`` for
    unknown symbols.
    """
    try:
        comp = Composition(formula)
        # Access ``elements`` to force parsing; any unknown element raises.
        _ = comp.elements
        return True
    except Exception as exc:  # pylint: disable=broad-except
        log.warning("Unknown element in formula '%s': %s", formula, exc)
        return False

def iqr_filter(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Return a boolean mask indicating rows that are *within* the
    1.5 × IQR bounds for ``column``.
    """
    q1, q3 = df[column].quantile([0.25, 0.75])
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    mask = df[column].between(lower, upper, inclusive="both")
    return mask

# -------------------------------------------------------------------------
# Main loader
# -------------------------------------------------------------------------
def load_and_clean(input_path: Path, output_path: Path) -> None:
    """
    Load ``input_path`` in chunks, clean the data, and write the result to
    ``output_path``.
    """
    required_columns = [
        "material_id",
        "formula",
        "band_gap",
        "hardness",
        "crystal_system",
    ]

    # Verify required columns exist
    sample = pd.read_csv(input_path, nrows=0)
    missing = set(required_columns) - set(sample.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    schema = load_schema()
    seen_ids = set()
    cleaned_chunks = []
    peak_ram = 0

    total_dropped_missing = 0
    total_dropped_duplicate = 0
    total_dropped_outlier = 0
    total_dropped_unknown = 0

    for chunk_idx, chunk in enumerate(
        pd.read_csv(input_path, chunksize=CHUNK_SIZE)
    ):
        log.info("Processing chunk %d (rows: %d)", chunk_idx + 1, len(chunk))

        # Track RAM usage
        current_ram = psutil.Process().memory_info().rss
        peak_ram = max(peak_ram, current_ram)

        # Drop rows with any missing required field
        before_missing = len(chunk)
        chunk = chunk.dropna(subset=required_columns)
        dropped_missing = before_missing - len(chunk)
        total_dropped_missing += dropped_missing
        if dropped_missing:
            log.info(
                "Chunk %d: dropped %d rows with missing required fields",
                chunk_idx + 1,
                dropped_missing,
            )

        # Drop duplicate material_id (keep first occurrence globally)
        before_dup = len(chunk)
        is_new = ~chunk["material_id"].isin(seen_ids)
        duplicate_mask = ~is_new
        total_dropped_duplicate += duplicate_mask.sum()
        if duplicate_mask.any():
            log.info(
                "Chunk %d: dropped %d duplicate material_id rows",
                chunk_idx + 1,
                duplicate_mask.sum(),
            )
        chunk = chunk[is_new]
        seen_ids.update(chunk["material_id"].tolist())

        # Validate schema per row
        valid_mask = chunk.apply(
            lambda row: validate_row(row.to_dict(), schema), axis=1
        )
        before_schema = len(chunk)
        chunk = chunk[valid_mask]
        dropped_schema = before_schema - len(chunk)
        if dropped_schema:
            log.info(
                "Chunk %d: dropped %d rows failing schema validation",
                chunk_idx + 1,
                dropped_schema,
            )

        # Skip unknown elements
        known_mask = chunk["formula"].apply(is_known_formula)
        unknown_mask = ~known_mask
        total_dropped_unknown += unknown_mask.sum()
        if unknown_mask.any():
            log.warning(
                "Chunk %d: skipping %d rows with unknown elements",
                chunk_idx + 1,
                unknown_mask.sum(),
            )
        chunk = chunk[known_mask]

        # Outlier removal using 1.5 × IQR per chunk
        # Apply to both band_gap and hardness
        mask_bg = iqr_filter(chunk, "band_gap")
        mask_h = iqr_filter(chunk, "hardness")
        outlier_mask = mask_bg & mask_h
        dropped_outlier = len(chunk) - outlier_mask.sum()
        total_dropped_outlier += dropped_outlier
        if dropped_outlier:
            log.info(
                "Chunk %d: dropped %d outlier rows (IQR rule)",
                chunk_idx + 1,
                dropped_outlier,
            )
        chunk = chunk[outlier_mask]

        cleaned_chunks.append(chunk)

    # Concatenate all cleaned chunks
    if cleaned_chunks:
        cleaned_df = pd.concat(cleaned_chunks, ignore_index=True)
    else:
        cleaned_df = pd.DataFrame(columns=required_columns)

    # Final RAM assertion
    if peak_ram > RAM_LIMIT_BYTES:
        raise AssertionError(
            f"Peak RAM usage {peak_ram / (1024 ** 3):.2f} GB exceeds limit of 6 GB"
        )
    else:
        log.info(
            "Peak RAM usage during loading: %.2f GB",
            peak_ram / (1024 ** 3),
        )

    # Write cleaned data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(output_path, index=False)
    log.info("Cleaned data written to %s", output_path)

    # Summary log
    log.info(
        "Loader summary – missing: %d, duplicate: %d, schema‑fail: %d, "
        "unknown‑elem: %d, outlier: %d, kept: %d",
        total_dropped_missing,
        total_dropped_duplicate,
        total_dropped_schema,
        total_dropped_unknown,
        total_dropped_outlier,
        len(cleaned_df),
    )

# -------------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chunked loader for materials dataset"
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the raw CSV dataset (must conform to contract)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Path where the cleaned CSV will be written",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    load_and_clean(args.input, args.out)

if __name__ == "__main__":
    main()
