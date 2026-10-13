"""
Data download script for the Molecular Permeability project.

This script fetches a verified public dataset from the Hugging Face Hub,
validates that the required SMILES and target columns are present,
writes the raw CSV file to ``data/raw/`` and records a SHA‑256 checksum
in ``data/raw/checksums.json``.

The chosen dataset is the ESOL solubility dataset, which provides
SMILES strings and a numeric solubility measurement. The solubility
value is used as a proxy target for permeability (as described in the
project plan). The script fails loudly if the expected columns are
missing.
"""
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration for the verified dataset
# ----------------------------------------------------------------------
VERIFIED_DATASET_CONFIG = {
    "source": "huggingface",
    "dataset_id": "esol",  # ESOL solubility dataset
    "split": "train",
    "smiles_column": "smiles",
    "target_column": "measured log solubility in mols per litre",
    "expected_columns": [
        "smiles",
        "measured log solubility in mols per litre",
    ],
}

logger = get_logger(__name__)

class DataLoader:
    """
    Fetches a verified molecular dataset from Hugging Face, validates
    required columns, writes the raw CSV to ``data/raw/`` and records a
    SHA‑256 checksum in ``data/raw/checksums.json``.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or VERIFIED_DATASET_CONFIG
        self.logger = logging.getLogger(self.__class__.__name__)
        self.smiles_column = self.config["smiles_column"]
        self.target_column = self.config["target_column"]

    # ------------------------------------------------------------------
    # Dataset acquisition
    # ------------------------------------------------------------------
    def fetch_dataset(self) -> pd.DataFrame:
        """
        Load the dataset from Hugging Face using ``datasets.load_dataset``.
        Returns a pandas DataFrame.
        """
        self.logger.info(
            f"Loading dataset '{self.config['dataset_id']}' "
            f"(split={self.config.get('split', 'train')})"
        )
        try:
            from datasets import load_dataset

            hf_dataset = load_dataset(
                self.config["dataset_id"],
                split=self.config.get("split", "train"),
            )
            df = hf_dataset.to_pandas()
            self.logger.info(f"Loaded {len(df)} rows.")
            return df
        except Exception as exc:
            self.logger.error(f"Failed to load dataset: {exc}")
            raise RuntimeError(
                f"Unable to fetch dataset '{self.config['dataset_id']}'."
            ) from exc

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate_columns(self, df: pd.DataFrame) -> None:
        """
        Ensure that the SMILES and target columns exist and that the target
        column is numeric. Raises ``RuntimeError`` on failure.
        """
        missing = [
            col
            for col in self.config["expected_columns"]
            if col not in df.columns
        ]
        if missing:
            raise RuntimeError(
                f"Missing required columns: {missing}. "
                f"Available columns: {list(df.columns)}"
            )
        if not pd.api.types.is_numeric_dtype(df[self.target_column]):
            raise RuntimeError(
                f"Target column '{self.target_column}' is not numeric "
                f"(detected type: {df[self.target_column].dtype})"
            )
        self.logger.info("Required columns are present and valid.")

    # ------------------------------------------------------------------
    # Checksum handling
    # ------------------------------------------------------------------
    def compute_checksum(self, file_path: Path) -> str:
        """Compute SHA‑256 checksum of ``file_path``."""
        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        checksum = sha256.hexdigest()
        self.logger.debug(f"Checksum for {file_path.name}: {checksum}")
        return checksum

    def write_checksum_file(
        self, checksums: Dict[str, str], checksum_path: Path
    ) -> None:
        """Write ``checksums`` dictionary as JSON."""
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        with checksum_path.open("w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
        self.logger.info(f"Wrote checksum file to {checksum_path}")

    # ------------------------------------------------------------------
    # Full processing pipeline
    # ------------------------------------------------------------------
    def process(self, save_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Execute the full data‑download pipeline:
          1. Load the dataset.
          2. Validate required columns.
          3. Write the raw CSV to ``data/raw/permeability_data.csv``.
          4. Compute and record the SHA‑256 checksum.
        Returns the loaded DataFrame.
        """
        df = self.fetch_dataset()
        self.validate_columns(df)

        # Determine where to write the raw CSV
        if save_path is None:
            save_path = paths.data("raw", "permeability_data.csv")
        else:
            save_path = Path(save_path)

        # Ensure the directory exists and write CSV
        save_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(save_path, index=False)
        self.logger.info(f"Saved raw dataset to {save_path}")

        # Compute checksum and write checksums.json
        checksum = self.compute_checksum(save_path)
        checksum_path = save_path.parent / "checksums.json"
        self.write_checksum_file({save_path.name: checksum}, checksum_path)

        self.logger.info(
            f"Data download completed successfully (rows={len(df)})"
        )
        return df

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI wrapper that runs the DataLoader and exits with status code 0 on
    success or 1 on any failure.
    """
    try:
        loader = DataLoader()
        loader.process()
        logger.info("Data download and validation succeeded.")
        sys.exit(0)
    except Exception as exc:
        logger.error(f"Data download failed: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
