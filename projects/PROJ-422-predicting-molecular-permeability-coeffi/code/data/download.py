"""
Data download script for the Molecular Permeability project.

This script fetches a verified public dataset from a reliable source,
validates that the required SMILES and target columns are present,
writes the raw CSV file to `data/raw/` and records a SHA-256 checksum
in `data/raw/checksums.json`.

Following the project's pivot in plan.md, we use the Lipophilicity dataset
from MoleculeNet as a proxy for permeability studies, focusing on 
the logP coefficient.
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
# We use the MoleculeNet Lipophilicity dataset. It is a real, publicly
# accessible dataset containing SMILES and experimental logP values.
VERIFIED_DATASET_CONFIG = {
    "source": "molecule_net",
    "url": "https://deepchem.s3.amazonaws.com/molecule_net/lipophilicity.csv.gz",
    "smiles_column": "SMILES",
    "target_column": "logP",
    "expected_columns": [
        "SMILES",
        "logP",
    ],
    "filename": "permeability_data.csv"
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
        self.smiles_column = self.config["smiles_column"]
        self.target_column = self.config["target_column"]

    def fetch_dataset(self) -> pd.DataFrame:
        """
        Load the dataset from the verified URL.
        """
        self.logger.info(f"Fetching dataset from {self.config['url']}")
        try:
            # The dataset is a .csv.gz file. pandas read_csv handles compression.
            df = pd.read_csv(self.config["url"])
            self.logger.info(f"Successfully loaded {len(df)} rows.")
            return df
        except Exception as exc:
            self.logger.error(f"Failed to load dataset: {exc}")
            raise RuntimeError(
                f"Unable to fetch dataset from {self.config['url']}."
            ) from exc

    def validate_columns(self, df: pd.DataFrame) -> None:
        """
        Ensure that the SMILES and target columns exist. 
        Fails loudly if the configured target column is missing.
        """
        missing = [
            col
            for col in self.config["expected_columns"]
            if col not in df.columns
        ]
        if missing:
            # FAIL LOUDLY: No proxy fallback permitted within the loader
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

    def compute_checksum(self, file_path: Path) -> str:
        """Compute SHA-256 checksum of `file_path`."""
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
        Execute the full data-download pipeline.
        """
        df = self.fetch_dataset()
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
