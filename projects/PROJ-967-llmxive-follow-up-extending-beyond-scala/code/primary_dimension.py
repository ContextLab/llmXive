"""
Primary Dimension Identification Task (T014)

Derives `primary_dimension` via `hash(species_id) % 4` using the fixed rule
"species_id_hash_mod_4_v1".

Generates:
  - data/processed/lineage_report.json
  - data/processed/exclusions_log.json
"""
import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd

# Constants
DERIVATION_RULE = "species_id_hash_mod_4_v1"
RULE_HASH = hashlib.sha256(DERIVATION_RULE.encode("utf-8")).hexdigest()
NUM_DIMENSIONS = 4

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger(__name__)

def setup_directories(base_path: Path):
    """Ensure required output directories exist."""
    (base_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
    return base_path

def load_raw_data(input_path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Load the raw dataset from Parquet."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    logger.info(f"Loading raw data from {input_path}")
    try:
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
        return df
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        raise

def derive_primary_dimension(species_id) -> int:
    """
    Derive primary dimension using hash(species_id) % 4.
    Handles both string and integer species_ids.
    """
    # Python's hash() is deterministic within a single process run but can vary
    # across runs due to hash randomization (PYTHONHASHSEED).
    # To ensure reproducibility, we convert to string and use a stable hash function.
    s_id = str(species_id)
    # Use a stable hash (SHA256 of the string representation) then mod 4
    # This ensures the result is consistent across different Python runs/environments.
    h = int(hashlib.sha256(s_id.encode("utf-8")).hexdigest(), 16)
    return h % NUM_DIMENSIONS

def process_dataframe_primary_dimensions(df: pd.DataFrame, logger: logging.Logger) -> tuple:
    """
    Process the dataframe to derive primary dimensions.
    Returns (df_with_dim, lineage_entries, exclusion_entries).
    """
    lineage_entries = []
    exclusion_entries = []
    df = df.copy()

    if "species_id" not in df.columns:
        raise ValueError("Input dataframe must contain 'species_id' column")

    # Ensure we have a sample_id or generate one if missing
    if "sample_id" not in df.columns:
        logger.warning("No 'sample_id' column found. Generating temporary IDs.")
        df["sample_id"] = [f"sample_{i}" for i in range(len(df))]

    # Apply derivation
    def get_dim(row):
        sample_id = row["sample_id"]
        species_id = row["species_id"]
        try:
            dim = derive_primary_dimension(species_id)
            return dim, None
        except Exception as e:
            logger.warning(f"Failed to derive dimension for sample {sample_id}: {e}")
            return None, str(e)

    results = df.apply(get_dim, axis=1)
    df["primary_dimension"] = [r[0] for r in results]
    errors = [r[1] for r in results]

    # Populate lineage report
    for idx, row in df.iterrows():
        sid = row["sample_id"]
        dim = row["primary_dimension"]
        if dim is not None:
            lineage_entries.append({
                "sample_id": sid,
                "source_type": "metadata",
                "dimension": dim,
                "derivation_rule": DERIVATION_RULE,
                "derivation_rule_hash": RULE_HASH
            })
        else:
            exclusion_entries.append({
                "sample_id": sid,
                "reason": f"primary_dimension_derivation_failed: {errors[idx]}"
            })

    # Log exclusions for null primary dimensions
    null_mask = df["primary_dimension"].isna()
    if null_mask.any():
        null_samples = df[null_mask]["sample_id"].tolist()
        for sid in null_samples:
            if not any(e["sample_id"] == sid for e in exclusion_entries):
                exclusion_entries.append({
                    "sample_id": sid,
                    "reason": "null_primary_dimension"
                })

    return df, lineage_entries, exclusion_entries

def save_lineage_report(lineage_entries: list, output_path: Path, logger: logging.Logger):
    """Save lineage report to JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(lineage_entries, f, indent=2)
    logger.info(f"Saved lineage report to {output_path} ({len(lineage_entries)} entries)")

def save_exclusions_log(exclusion_entries: list, output_path: Path, logger: logging.Logger):
    """Save exclusions log to JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(exclusion_entries, f, indent=2)
    logger.info(f"Saved exclusions log to {output_path} ({len(exclusion_entries)} entries)")

def parse_args():
    parser = argparse.ArgumentParser(description="T014: Primary Dimension Identification")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input raw data parquet file (e.g., data/processed/raw_data.parquet)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to write output files"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()

    base_path = Path(args.output_dir).parent.parent  # Assume project root is two levels up
    # Or just use current working directory if relative paths are used
    # The task spec says: "relative to the project root"
    # Let's assume the script is run from the project root
    project_root = Path.cwd()

    input_path = project_root / args.input
    lineage_path = project_root / "data" / "processed" / "lineage_report.json"
    exclusions_path = project_root / "data" / "processed" / "exclusions_log.json"

    setup_directories(project_root)

    logger.info(f"Starting Primary Dimension Identification (T014)")
    logger.info(f"Input: {input_path}")
    logger.info(f"Derivation Rule: {DERIVATION_RULE}")
    logger.info(f"Rule Hash: {RULE_HASH}")

    df = load_raw_data(input_path, logger)
    df_processed, lineage, exclusions = process_dataframe_primary_dimensions(df, logger)

    save_lineage_report(lineage, lineage_path, logger)
    save_exclusions_log(exclusions, exclusions_path, logger)

    logger.info("T014 completed successfully.")
    logger.info(f"Total samples processed: {len(df)}")
    logger.info(f"Samples with valid primary dimension: {len(lineage)}")
    logger.info(f"Samples excluded: {len(exclusions)}")

if __name__ == "__main__":
    main()
