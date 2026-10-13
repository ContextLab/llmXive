"""Download the Tox21 dataset (real data only).

Primary route: HuggingFace ``datasets.load_dataset("deepchem/tox21")``.
Fallback route (used when the ``datasets``/``pyarrow`` stack cannot be
imported in the current environment, e.g. a NumPy 1.x runtime): the
canonical DeepChem S3 CSV mirror of the same Tox21 dataset. Both routes
serve the REAL dataset; there is no synthetic fallback anywhere.
"""
import gzip
import hashlib
import io
from pathlib import Path
from typing import Tuple

import pandas as pd
import requests

from utils import setup_logging, init_random_seed, get_logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOX21_S3_URL = "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz"


def calculate_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """Calculate the checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """Verify the checksum of a file against an expected value."""
    return calculate_checksum(file_path, algorithm) == expected_checksum


def _fetch_from_s3(output_path: Path) -> pd.DataFrame:
    """Fetch the real Tox21 CSV from the canonical DeepChem S3 location."""
    logger = get_logger(__name__)
    logger.info(f"Fetching Tox21 CSV from canonical DeepChem source: {TOX21_S3_URL}")
    resp = requests.get(TOX21_S3_URL, timeout=180)
    resp.raise_for_status()
    df = pd.read_csv(io.BytesIO(gzip.decompress(resp.content)))
    if df is None or len(df) == 0:
        raise RuntimeError("Downloaded Tox21 dataset is empty; refusing to continue.")
    df.to_csv(output_path, index=False)
    return df


def _normalize_smiles_column(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure the dataframe has a lowercase 'smiles' column."""
    lower = {c.lower(): c for c in df.columns}
    if "smiles" in lower:
        df = df.rename(columns={lower["smiles"]: "smiles"})
    else:
        raise ValueError(
            f"Tox21 dataset has no SMILES column. Found columns: {list(df.columns)}"
        )
    return df


def fetch_tox21_dataset(
    output_dir: str,
    dataset_name: str = "deepchem/tox21",
) -> Tuple[pd.DataFrame, str]:
    """
    Fetch the Tox21 dataset and save it locally as CSV.

    Args:
        output_dir: Directory to save the dataset.
        dataset_name: Name of the dataset on HuggingFace.

    Returns:
        Tuple of (DataFrame with dataset, path to saved file).
    """
    logger = get_logger(__name__)
    output_path = Path(output_dir) / "tox21_raw.csv"

    if output_path.exists():
        logger.info(f"Dataset already exists at {output_path}. Skipping download.")
        df = pd.read_csv(output_path)
        if len(df) == 0:
            raise RuntimeError(f"Cached dataset at {output_path} is empty.")
        return df, str(output_path)

    try:
        from datasets import load_dataset

        logger.info(f"Downloading dataset: {dataset_name}")
        dataset = load_dataset(dataset_name, split="train")
        df = dataset.to_pandas()
        df = _normalize_smiles_column(df)
        df.to_csv(output_path, index=False)
        logger.info(f"Dataset saved to {output_path}")
    except Exception as e:
        # The HuggingFace datasets route can fail at import time
        # (pyarrow requires NumPy >= 2.0 in this environment). Fall back
        # to the canonical DeepChem S3 CSV of the SAME real dataset.
        logger.warning(
            f"HuggingFace 'datasets' route unavailable ({type(e).__name__}: {e}). "
            "Falling back to the canonical DeepChem S3 CSV mirror."
        )
        df = _fetch_from_s3(output_path)
        df = _normalize_smiles_column(df)
        df.to_csv(output_path, index=False)

    return df, str(output_path)


def main():
    """Main entry point for downloading the dataset."""
    setup_logging()
    init_random_seed()
    logger = get_logger(__name__)

    data_dir = PROJECT_ROOT / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_file = data_dir / "tox21_raw.csv"

    logger.info("Starting dataset download...")

    df, _ = fetch_tox21_dataset(str(data_dir))

    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    logger.info(f"Download size: {file_size_mb:.2f} MB ({output_file.stat().st_size} bytes)")

    logger.info(f"Initial dataset size: {len(df)} rows")
    logger.info(f"Columns: {list(df.columns)}")

    endpoint_cols = [c for c in df.columns if c.lower() not in ("smiles", "mol")]
    endpoint_counts = df[endpoint_cols].notna().sum()
    logger.info("Endpoint distribution (non-null counts):")
    for col, count in endpoint_counts.items():
        logger.info(f"  {col}: {count}")

    logger.info("Dataset download and logging complete.")


if __name__ == "__main__":
    main()
