import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
def setup_logging() -> logging.Logger:
    """Configure and return the project logger."""
    logger = logging.getLogger("llmxive.ingest")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logging()

def setup_directories(project_root: Path) -> Dict[str, Path]:
    """Ensure required directories exist."""
    dirs = {
        "raw": project_root / "data" / "raw",
        "processed": project_root / "data" / "processed",
        "results": project_root / "results",
    }
    for name, path in dirs.items():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {path}")
    return dirs

def load_and_align_data(
    csv_path: Path, schema_path: Path, max_rows: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Load the Z-Reward dataset from CSV, align columns, and validate schema.

    Args:
        csv_path: Path to the raw CSV file.
        schema_path: Path to the schema contract YAML.
        max_rows: Optional limit on rows to load (for memory testing/sampling).

    Returns:
        List of aligned row dictionaries.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {csv_path}")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    # Load schema to get expected columns
    import yaml
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    required_columns = schema.get("required_columns", [])
    optional_columns = schema.get("optional_columns", [])
    all_expected_columns = set(required_columns + optional_columns)

    aligned_data = []
    missing_columns = set()
    missing_data_flags = {"total_samples": 0, "missing_primary_dimension": 0, "missing_annotations": 0}

    logger.info(f"Loading data from {csv_path} with max_rows={max_rows}")

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        actual_columns = set(reader.fieldnames or [])

        # Check for schema compliance
        missing_in_file = all_expected_columns - actual_columns
        if missing_in_file:
            logger.warning(f"Schema columns missing in file: {missing_in_file}")
            missing_columns.update(missing_in_file)

        for i, row in enumerate(reader):
            if max_rows is not None and i >= max_rows:
                logger.info(f"Reached max_rows limit ({max_rows}). Stopping load.")
                break

            aligned_data.append(row)
            missing_data_flags["total_samples"] += 1

            # Check for specific critical missing data based on schema logic
            # T014 logic: primary_dimension comes from metadata or defaults to 'Alignment'
            # We check if the column exists and is populated
            if "primary_dimension" in row and row["primary_dimension"]:
                pass # Has primary dimension
            else:
                missing_data_flags["missing_primary_dimension"] += 1

            # Check human annotations (assuming a JSON string or specific columns)
            # Based on schema: human_annotations is a dict{dim: float}
            if "human_annotations" in row and row["human_annotations"]:
                try:
                    ann = json.loads(row["human_annotations"])
                    if not ann:
                        missing_data_flags["missing_annotations"] += 1
                except json.JSONDecodeError:
                    missing_data_flags["missing_annotations"] += 1
            else:
                missing_data_flags["missing_annotations"] += 1

    if missing_columns:
        logger.error(f"Critical schema mismatch. Missing columns: {missing_columns}")
        # We do not raise here to allow partial stats, but log heavily.
        # In a strict validation task (T038), this would raise.

    return aligned_data, missing_data_flags

def identify_primary_quality_dimension(
    data: List[Dict[str, Any]], default_dim: str = "Alignment"
) -> str:
    """
    Identify the primary quality dimension for the dataset.

    Rule: Use the value of the column `primary_dimension` if present and non-empty
    in the first valid row; otherwise, default to the first dimension in the schema.

    Args:
        data: List of aligned rows.
        default_dim: Default dimension if not found.

    Returns:
        The identified primary dimension string.
    """
    for row in data:
        if "primary_dimension" in row and row["primary_dimension"]:
            val = row["primary_dimension"].strip()
            if val:
                logger.info(f"Primary dimension identified from data: {val}")
                return val

    logger.info(f"Primary dimension not found in data. Using default: {default_dim}")
    return default_dim

def print_summary(
    data: List[Dict[str, Any]],
    missing_flags: Dict[str, int],
    primary_dim: str,
    schema_path: Path,
) -> None:
    """
    Print a summary of the ingested dataset.

    Outputs:
    - Total sample count
    - Missing data flags (primary dimension, annotations)
    - Dimension coverage stats (presence of rubric dimensions)

    Args:
        data: The loaded and aligned dataset.
        missing_flags: Dictionary of missing data counts.
        primary_dim: The identified primary dimension.
        schema_path: Path to the schema to check for expected dimensions.
    """
    import yaml

    total_samples = len(data)
    logger.info("-" * 50)
    logger.info("INGESTION SUMMARY REPORT")
    logger.info("-" * 50)
    logger.info(f"Total Samples Processed: {total_samples}")
    logger.info(f"Primary Quality Dimension: {primary_dim}")

    # Missing Data Flags
    logger.info("\nMissing Data Flags:")
    logger.info(f"  - Missing Primary Dimension: {missing_flags.get('missing_primary_dimension', 0)}")
    logger.info(f"  - Missing Human Annotations: {missing_flags.get('missing_annotations', 0)}")

    # Dimension Coverage Stats
    # Load schema to get rubric dimensions
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    rubric_dims = schema.get("rubric_dimensions", [])
    if not rubric_dims:
        # Fallback if schema doesn't explicitly list them, use known set
        rubric_dims = ["Alignment", "Realism", "Aesthetics", "Plausibility"]

    logger.info(f"\nDimension Coverage (Rubric Dimensions: {rubric_dims}):")

    # Count samples that have annotations for each dimension
    # Assuming human_annotations is a JSON string in the CSV
    dim_coverage = {dim: 0 for dim in rubric_dims}
    total_with_annotations = 0

    for row in data:
        ann_str = row.get("human_annotations", "")
        if not ann_str:
            continue
        try:
            ann = json.loads(ann_str)
            if ann:
                total_with_annotations += 1
                for dim in rubric_dims:
                    if dim in ann and ann[dim] is not None:
                        dim_coverage[dim] += 1
        except json.JSONDecodeError:
            continue

    for dim in rubric_dims:
        count = dim_coverage[dim]
        pct = (count / total_samples * 100) if total_samples > 0 else 0
        logger.info(f"  - {dim}: {count} samples ({pct:.1f}%)")

    logger.info(f"\nTotal samples with any annotations: {total_with_annotations}")
    logger.info("-" * 50)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Ingest and align Z-Reward dataset."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/zreward_dataset.csv",
        help="Path to the input CSV file.",
    )
    parser.add_argument(
        "--schema",
        type=str,
        default="contracts/dataset.schema.yaml",
        help="Path to the schema contract file.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Optional maximum number of rows to process.",
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala",
        help="Path to the project root directory.",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    project_root = Path(args.project_root)
    csv_path = project_root / args.input
    schema_path = project_root / args.schema

    logger.info(f"Starting ingestion for project: {project_root}")

    # Setup directories (ensures data/processed exists for downstream)
    setup_directories(project_root)

    # Load and align
    try:
        data, missing_flags = load_and_align_data(csv_path, schema_path, args.max_rows)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    if not data:
        logger.warning("No data loaded. Exiting.")
        sys.exit(0)

    # Identify primary dimension
    primary_dim = identify_primary_quality_dimension(data)

    # Print Summary (T016 Requirement)
    print_summary(data, missing_flags, primary_dim, schema_path)

    logger.info("Ingestion and summary generation complete.")

if __name__ == "__main__":
    main()