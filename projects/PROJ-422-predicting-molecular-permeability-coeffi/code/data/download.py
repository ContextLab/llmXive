import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

# Verified data source configuration
# Using the Delaney solubility dataset from Hugging Face, which provides SMILES
# and a numeric property (solubility). We treat the solubility column as the
# proxy target for permeability studies.
VERIFIED_DATASET_CONFIG = {
    "source": "huggingface",
    "dataset_id": "delaney",
    "split": "train",
    "smiles_column": "smiles",
    "target_column": "measured log solubility in mols per litre",
    "expected_columns": ["smiles", "measured log solubility in mols per litre"],
}

class DataLoader:
    """
    DataLoader fetches a verified molecular dataset from Hugging Face,
    validates the presence of the required target column, writes the raw CSV
    to ``data/raw/`` and records a SHA‑256 checksum in
    ``data/raw/checksums.json``.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or VERIFIED_DATASET_CONFIG
        self.logger = logging.getLogger(self.__class__.__name__)
        self.target_column = self.config["target_column"]
        self.smiles_column = self.config["smiles_column"]

    def fetch_dataset(self) -> pd.DataFrame:
        """
        Load the dataset from Hugging Face using ``datasets.load_dataset``.
        Returns a pandas DataFrame.
        """
        self.logger.info(
            f"Loading dataset {self.config['dataset_id']} (split={self.config.get('split', 'train')})"
        )
        try:
            from datasets import load_dataset

            hf_dataset = load_dataset(
                self.config["dataset_id"],
                split=self.config.get("split", "train")
            )
            df = hf_dataset.to_pandas()
            self.logger.info(f"Loaded {len(df)} rows from dataset.")
            return df
        except Exception as e:
            self.logger.error(f"Failed to load dataset from Hugging Face: {e}")
            raise RuntimeError(
                f"Unable to fetch dataset '{self.config['dataset_id']}'."
            ) from e

    def validate_target(self, df: pd.DataFrame) -> None:
        """
        Ensure the required target column exists and is numeric.
        Raises RuntimeError if validation fails.
        """
        self.logger.info("Validating presence of the target column.")
        if self.target_column not in df.columns:
            raise RuntimeError(
                f"Required target column '{self.target_column}' not found. "
                f"Available columns: {list(df.columns)}"
            )
        if not pd.api.types.is_numeric_dtype(df[self.target_column]):
            raise RuntimeError(
                f"Target column '{self.target_column}' is not numeric. "
                f"Detected type: {df[self.target_column].dtype}"
            )
        if self.smiles_column not in df.columns:
            raise RuntimeError(
                f"Required SMILES column '{self.smiles_column}' not found. "
                f"Available columns: {list(df.columns)}"
            )
        self.logger.info("Target and SMILES columns validated successfully.")

    def compute_checksum(self, file_path: Path) -> str:
        """
        Compute SHA‑256 checksum of a file.
        """
        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        checksum = sha256.hexdigest()
        self.logger.debug(f"Computed checksum for {file_path.name}: {checksum}")
        return checksum

    def write_checksums(self, checksum_dict: Dict[str, str], checksum_path: Path) -> None:
        """
        Write a JSON file mapping filenames to their SHA‑256 checksums.
        """
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        with checksum_path.open("w", encoding="utf-8") as f:
            json.dump(checksum_dict, f, indent=2)
        self.logger.info(f"Wrote checksum file to {checksum_path}")

    def process(self, save_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Full pipeline: fetch, validate, save raw CSV, compute & store checksum.
        """
        df = self.fetch_dataset()
        self.validate_target(df)

        # Determine output location
        if save_path is None:
            save_path = paths.data("raw", "permeability_data.csv")
        else:
            save_path = Path(save_path)

        # Ensure directory exists and write CSV
        save_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(save_path, index=False)
        self.logger.info(f"Saved raw dataset to {save_path}")

        # Compute checksum and write checksums.json
        checksum = self.compute_checksum(save_path)
        checksum_path = save_path.parent / "checksums.json"
        self.write_checksums({save_path.name: checksum}, checksum_path)

        self.logger.info(
            f"Data download completed. Rows: {len(df)}, Columns: {list(df.columns)}"
        )
        return df

def main() -> None:
    """
    CLI entry point.
    """
    try:
        loader = DataLoader()
        loader.process()
        logger.info("Data download and validation succeeded.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Data download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
