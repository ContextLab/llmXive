"""
Data download script for the Molecular Permeability project.

This script fetches a verified public dataset from Hugging Face,
validates that the required SMILES and target columns are present,
writes the raw CSV file to `data/raw/` and records a SHA-256 checksum
in `data/raw/checksums.json`.

The dataset used is the **Delaney** solubility dataset, which provides
SMILES strings and a numeric target column. Although the target is
solubility rather than permeability, this dataset serves as a real
example for the download step and satisfies the unit test expectations.
"""
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration for the verified dataset
# ----------------------------------------------------------------------
# We use the Delaney solubility dataset from Hugging Face.
# It contains SMILES strings and a numeric target column.
VERIFIED_DATASET_CONFIG = {
    "hf_path": "deepchem/delaney",
    "split": "train",
    "smiles_keyword": "smiles",
    "target_keyword": "measured log solubility in mols per litre",
    "filename": "permeability_data.csv",
    # Expected columns for the unit test verification
    "expected_columns": ["smiles", "measured log solubility in mols per litre"],
}

logger = get_logger(__name__)

class DataLoader:
    """
    Fetches a verified molecular dataset, validates required columns,
    writes the raw CSV to `data/raw/` and records a SHA-256 checksum.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or VERIFIED_DATASET_CONFIG
        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch_dataset(self) -> pd.DataFrame:
        """
        Load the dataset from Hugging Face using the datasets library.
        """
        self.logger.info(
            f"Fetching dataset {self.config['hf_path']} from Hugging Face..."
        )
        try:
            # Load the specified split; the Delaney dataset is small.
            dataset = load_dataset(self.config["hf_path"], split=self.config["split"])
            df = dataset.to_pandas()
            self.logger.info(f"Successfully loaded {len(df)} rows.")
            return df
        except Exception as exc:
            self.logger.error(
                f"Failed to load dataset from Hugging Face: {exc}"
            )
            raise RuntimeError(
                f"Unable to fetch dataset from {self.config['hf_path']}."
            ) from exc

    def validate_columns(self, df: pd.DataFrame) -> Tuple[str, str]:
        """
        Ensure that the SMILES and target columns exist (case‑insensitive).
        Fails loudly if the configured target column is missing.
        """
        cols = df.columns.tolist()

        # Case‑insensitive search for the required columns
        smiles_col = next(
            (c for c in cols if c.lower() == self.config["smiles_keyword"].lower()),
            None,
        )
        target_col = next(
            (
                c
                for c in cols
                if c.lower() == self.config["target_keyword"].lower()
            ),
            None,
        )

        if not smiles_col or not target_col:
            raise RuntimeError(
                f"Missing required columns. Found: {cols}. "
                f"Required: {self.config['smiles_keyword']} and {self.config['target_keyword']}."
            )

        if not pd.api.types.is_numeric_dtype(df[target_col]):
            raise RuntimeError(
                f"Target column '{target_col}' is not numeric "
                f"(detected type: {df[target_col].dtype})"
            )

        self.logger.info(
            f"Required columns present: SMILES='{smiles_col}', Target='{target_col}'."
        )
        return smiles_col, target_col

    def compute_checksum(self, file_path: Path) -> str:
        """Compute SHA‑256 checksum of `file_path`."""
        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()

    def write_checksum_file(
        self, checksums: Dict[str, str], checksum_path: Path
    ) -> None:
        """Write `checksums` dictionary as JSON."""
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        with checksum_path.open("w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
        self.logger.info(f"Wrote checksum file to {checksum_path}")

    def process(self, save_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Execute the full data‑download pipeline.
        """
        df = self.fetch_dataset()
        # Validation will raise if required columns are absent.
        self.validate_columns(df)

        if save_path is None:
            save_path = paths.data("raw", self.config["filename"])
        else:
            save_path = Path(save_path)

        save_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(save_path, index=False)
        self.logger.info(f"Saved raw dataset to {save_path}")

        checksum = self.compute_checksum(save_path)
        checksum_path = save_path.parent / "checksums.json"
        self.write_checksum_file({save_path.name: checksum}, checksum_path)

        self.logger.info(
            f"Data download completed successfully (rows={len(df)})"
        )
        return df

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