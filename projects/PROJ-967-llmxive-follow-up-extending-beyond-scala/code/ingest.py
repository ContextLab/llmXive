import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Project root handling
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Logging setup
def setup_logging() -> logging.Logger:
    """Configure logging for the ingest module."""
    logger = logging.getLogger(__name__)
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

def setup_directories() -> None:
    """Ensure required directories exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directories ensured: {RAW_DIR}, {PROCESSED_DIR}")

def load_and_align_data(
    raw_path: Optional[Path] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Load the raw dataset and align teacher scores, student scalars, and human annotations.

    Args:
        raw_path: Path to the raw parquet/parquet-like data file. Defaults to
                  RAW_DIR / "imagenet_rewards.parquet".

    Returns:
        Tuple of (aligned_data_list, stats_dict).
        aligned_data_list: List of dicts with normalized keys.
        stats_dict: Summary statistics (counts, missing flags).
    """
    if raw_path is None:
        raw_path = RAW_DIR / "imagenet_rewards.parquet"

    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")

    logger.info(f"Loading data from {raw_path}")

    # Attempt to load using pandas (assuming parquet format based on T037)
    try:
        import pandas as pd
        df = pd.read_parquet(raw_path)
    except ImportError:
        raise ImportError("pandas is required to load parquet files. Install with 'pip install pandas pyarrow'.")
    except Exception as e:
        raise RuntimeError(f"Failed to load parquet file: {e}")

    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")

    aligned_data = []
    missing_flags = {
        "teacher_scores": 0,
        "student_scalar": 0,
        "human_annotations": 0,
        "primary_dimension": 0,
    }

    # Determine column mappings dynamically based on T038 schema discovery results
    # We assume standard naming conventions or look for common variants if needed.
    # For robustness, we check for the expected columns.
    required_cols = ["prompt", "image_url"]
    optional_cols = ["teacher_scores", "student_scalar", "human_annotations", "primary_dimension"]

    # Normalize column names (lowercase, strip whitespace)
    df.columns = df.columns.str.strip().str.lower()

    # Verify critical columns exist
    missing_critical = [c for c in required_cols if c not in df.columns]
    if missing_critical:
        raise ValueError(f"Missing critical columns: {missing_critical}")

    for idx, row in df.iterrows():
        record = {
            "sample_id": idx,
            "prompt": row.get("prompt", ""),
            "image_url": row.get("image_url", ""),
        }

        # Extract teacher scores (expecting a dict or JSON string)
        t_scores = row.get("teacher_scores")
        if isinstance(t_scores, str):
            try:
                import json
                t_scores = json.loads(t_scores)
            except json.JSONDecodeError:
                t_scores = None
        
        if t_scores is None:
            missing_flags["teacher_scores"] += 1
            t_scores = {}
        
        record["teacher_scores"] = t_scores

        # Extract student scalar
        s_scalar = row.get("student_scalar")
        if pd.isna(s_scalar):
            missing_flags["student_scalar"] += 1
            s_scalar = None
        record["student_scalar"] = s_scalar

        # Extract human annotations
        h_ann = row.get("human_annotations")
        if isinstance(h_ann, str):
            try:
                import json
                h_ann = json.loads(h_ann)
            except json.JSONDecodeError:
                h_ann = None
        
        if h_ann is None:
            missing_flags["human_annotations"] += 1
            h_ann = {}
        
        record["human_annotations"] = h_ann

        # Extract primary dimension
        p_dim = row.get("primary_dimension")
        if pd.isna(p_dim) or p_dim is None:
            missing_flags["primary_dimension"] += 1
            p_dim = None
        record["primary_dimension"] = p_dim

        aligned_data.append(record)

    stats = {
        "total_rows": len(df),
        "missing_teacher_scores": missing_flags["teacher_scores"],
        "missing_student_scalar": missing_flags["student_scalar"],
        "missing_human_annotations": missing_flags["human_annotations"],
        "missing_primary_dimension": missing_flags["primary_dimension"],
    }

    logger.info(f"Alignment complete. Stats: {stats}")
    return aligned_data, stats

def identify_primary_quality_dimension(
    aligned_data: List[Dict[str, Any]],
) -> str:
    """
    Identify the primary quality dimension from the dataset metadata.

    Rule: Use the value of the column `primary_dimension` if present in the dataset.
    CRITICAL: If `primary_dimension` is missing, raise a `RuntimeError` with a
    descriptive message stating that metadata is required for independent validation.
    DO NOT default to 'Alignment'.

    Args:
        aligned_data: List of aligned records from load_and_align_data.

    Returns:
        The string value of the primary dimension.

    Raises:
        RuntimeError: If `primary_dimension` is missing or null for all samples.
    """
    primary_dimension_value = None
    missing_count = 0
    total_count = len(aligned_data)

    for record in aligned_data:
        val = record.get("primary_dimension")
        if val is not None and str(val).strip() != "":
            # We assume consistency across the dataset; take the first valid one
            primary_dimension_value = str(val).strip()
            break
        else:
            missing_count += 1

    if primary_dimension_value is None:
        raise RuntimeError(
            f"Primary dimension metadata is missing for all {total_count} samples. "
            "Independent validation requires the 'primary_dimension' column to be present "
            "and populated in the dataset. This is a hard requirement for T014."
        )

    logger.info(f"Identified primary quality dimension: '{primary_dimension_value}'")
    return primary_dimension_value

def print_summary(
    aligned_data: List[Dict[str, Any]], 
    stats: Dict[str, int], 
    primary_dim: str
) -> None:
    """Print a summary of the ingestion process."""
    print("\n" + "="*50)
    print("INGESTION SUMMARY")
    print("="*50)
    print(f"Total Samples: {stats['total_rows']}")
    print(f"Missing Teacher Scores: {stats['missing_teacher_scores']}")
    print(f"Missing Student Scalar: {stats['missing_student_scalar']}")
    print(f"Missing Human Annotations: {stats['missing_human_annotations']}")
    print(f"Missing Primary Dimension: {stats['missing_primary_dimension']}")
    print(f"Primary Quality Dimension: {primary_dim}")
    print("="*50 + "\n")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest and align Z-Reward dataset.")
    parser.add_argument(
        "--raw-path",
        type=str,
        default=None,
        help="Path to the raw data file (default: data/raw/imagenet_rewards.parquet)",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/processed/aligned_data.json",
        help="Path to save the aligned data JSON (default: data/processed/aligned_data.json)",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    setup_directories()

    raw_path = Path(args.raw_path) if args.raw_path else None
    
    try:
        aligned_data, stats = load_and_align_data(raw_path)
        primary_dim = identify_primary_quality_dimension(aligned_data)
        
        # Save aligned data to JSON for downstream tasks (T015, T025)
        output_path = Path(args.output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(aligned_data, f, indent=2)
        logger.info(f"Aligned data saved to {output_path}")

        print_summary(aligned_data, stats, primary_dim)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()