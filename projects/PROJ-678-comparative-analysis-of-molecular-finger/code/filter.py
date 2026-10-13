"""Filter the Tox21 dataset for organophosphates (User Story 1).

Extends the filter log (T014) with:
  - download_size_bytes (size of the raw download on disk),
  - filtered_count (number of organophosphate matches),
  - endpoint_distribution (per-endpoint label counts, as a JSON dict).
"""
import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from rdkit import Chem

from constants import SMARTS_PATTERN
from utils import setup_logging, init_random_seed, get_logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent

init_random_seed(42)
logger = get_logger(__name__)


def load_compounds(input_path: str) -> pd.DataFrame:
    """Load the raw dataset from the previous step (download.py)."""
    logger.info(f"Loading compounds from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    missing = [c for c in ["smiles"] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    valid_indices = []
    for idx, row in df.iterrows():
        mol = Chem.MolFromSmiles(row["smiles"])
        if mol is not None:
            valid_indices.append(idx)

    logger.info(f"Loaded {len(df)} rows, {len(valid_indices)} valid SMILES")
    return df.loc[valid_indices].reset_index(drop=True)


def apply_smarts_filter(df: pd.DataFrame, pattern: str = SMARTS_PATTERN) -> pd.DataFrame:
    """Apply the SMARTS pattern to filter for organophosphates."""
    logger.info(f"Applying SMARTS filter: {pattern}")
    mol_pattern = Chem.MolFromSmarts(pattern)
    if mol_pattern is None:
        raise ValueError(f"Invalid SMARTS pattern: {pattern}")

    filtered_indices = []
    for idx, row in df.iterrows():
        mol = Chem.MolFromSmiles(row["smiles"])
        if mol is not None and mol.HasSubstructMatch(mol_pattern):
            filtered_indices.append(idx)

    logger.info(f"Filter matched {len(filtered_indices)} compounds")
    return df.loc[filtered_indices].reset_index(drop=True)


def validate_endpoints(df: pd.DataFrame) -> dict:
    """Count rows per toxicity endpoint to ensure data quality."""
    counts = {}
    for col in df.columns:
        if col != "smiles":
            counts[col] = int(df[col].notna().sum())
    return counts


def save_filtered_data(df: pd.DataFrame, output_path: str):
    """Save the filtered dataframe to CSV."""
    logger.info(f"Saving filtered data to {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")


def write_filter_log(
    output_dir: str,
    total_input: int,
    filtered_count: int,
    endpoint_counts: dict,
    download_size_bytes: int = None,
):
    """Write the filter log to data/processed/filter_log.txt (T014).

    Logs download_size_bytes, filtered_count and the endpoint
    distribution, and handles the sample size warning logic.
    """
    log_path = Path(output_dir) / "filter_log.txt"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    with open(log_path, "w") as f:
        f.write(f"Filter Log - {datetime.now().isoformat()}\n")
        if download_size_bytes is not None:
            f.write(f"download_size_bytes: {int(download_size_bytes)}\n")
        f.write(f"Total input compounds: {total_input}\n")
        f.write(f"filtered_count: {filtered_count}\n")
        f.write("Endpoint Distribution:\n")
        for endpoint, count in endpoint_counts.items():
            f.write(f"  {endpoint}: {count}\n")
        f.write(f"endpoint_distribution: {json.dumps(endpoint_counts, sort_keys=True)}\n")

        if filtered_count < 50:
            f.write("\nWARNING: Low Sample Size (n < 50)\n")
            logger.warning(f"Low sample size detected: {filtered_count} < 50")
        else:
            f.write("\nstatus: OK\n")
            logger.info(f"Sample size OK: {filtered_count} >= 50")

    logger.info(f"Filter log written to {log_path}")


def write_sample_size_status(output_dir: str, count: int):
    """Write sample_size_status.json based on the filtered count."""
    status_path = Path(output_dir) / "sample_size_status.json"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    status = "SKIP_STATS" if count < 50 else "OK"
    with open(status_path, "w") as f:
        json.dump({"status": status}, f)

    logger.info(f"Wrote sample size status: {status} to {status_path}")


def main():
    """Main entry point for the filtering pipeline."""
    setup_logging()
    input_path = str(PROJECT_ROOT / "data" / "raw" / "tox21_raw.csv")
    output_dir = str(PROJECT_ROOT / "data" / "processed")
    output_path = Path(output_dir) / "organophosphates_filtered.csv"

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 1. Load compounds
    df = load_compounds(input_path)
    total_input = len(df)

    # 2. Apply SMARTS filter
    filtered_df = apply_smarts_filter(df)
    filtered_count = len(filtered_df)

    # 3. Validate endpoints
    endpoint_counts = validate_endpoints(filtered_df)

    # 4. Save filtered data
    save_filtered_data(filtered_df, str(output_path))

    # 5. Write logs and status (T014: include raw download size)
    raw_file = Path(input_path)
    download_size_bytes = raw_file.stat().st_size if raw_file.exists() else None
    write_filter_log(
        output_dir,
        total_input,
        filtered_count,
        endpoint_counts,
        download_size_bytes=download_size_bytes,
    )
    write_sample_size_status(output_dir, filtered_count)

    logger.info("Filtering complete.")


if __name__ == "__main__":
    main()