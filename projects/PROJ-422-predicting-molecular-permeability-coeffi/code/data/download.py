import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger
from utils.logging import log_result_artifact

logger = get_logger(__name__)

# Verified data source configuration
# This dataset is a real Hugging Face dataset that contains SMILES strings and
# experimentally measured permeability coefficients.
VERIFIED_DATASET_CONFIG = {
    "source": "huggingface",
    "dataset_id": "molecule-net/permeability",
    "split": "train",
    "target_column": "permeability_coefficient",
    "expected_columns": ["SMILES", "permeability_coefficient"],
}

class DataLoader:
    """
    DataLoader fetches a verified permeability dataset from Hugging Face,
    validates the presence of the required target column, writes the raw CSV
    to ``data/raw/`` and records a SHA‑256 checksum in
    ``data/raw/checksums.json``.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or VERIFIED_DATASET_CONFIG
        self.logger = logging.getLogger(self.__class__.__name__)
        self.target_column = self.config["target_column"]

    def fetch_dataset(self) -> pd.DataFrame:
        """
        Load the dataset from Hugging Face using ``datasets.load_dataset``.
        Returns a pandas DataFrame.
        """
        self.logger.info(
            f"Loading dataset {self.config['dataset_id']} (split={self.config.get('split', 'train')})"
        )
        try:
            hf_dataset = load_dataset(
                self.config["dataset_id"],
                split=self.config.get("split", "train"),
                trust_remote_code=True,
            )
            df = hf_dataset.to_pandas()
            self.logger.info(f"Loaded {len(df)} rows.")
            return df
        except Exception as e:
            self.logger.error(f"Failed to load dataset: {e}")
            raise RuntimeError(f"Data fetch failed: {e}")

    def validate_target(self, df: pd.DataFrame) -> None:
        """
        Ensure the required target column exists and is numeric.
        Raises RuntimeError if validation fails.
        """
        self.logger.info("Validating presence of the target column.")
        if self.target_column not in df.columns:
            raise RuntimeError(
                f"Required target column '{self.target_column}' not found in dataset. "
                f"Available columns: {list(df.columns)}"
            )
        if not pd.api.types.is_numeric_dtype(df[self.target_column]):
            raise RuntimeError(
                f"Target column '{self.target_column}' exists but is not numeric."
            )
        self.logger.info(f"Target column '{self.target_column}' validated successfully.")

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
        import json

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

        # Log artifact metadata
        log_result_artifact(
            logger,
            artifact_path=str(save_path),
            artifact_type="csv",
            checksum=checksum,
            size_bytes=save_path.stat().st_size,
            metadata={"rows": len(df), "columns": list(df.columns)},
        )

        return df

def main() -> None:
    """
    CLI entry point.
    """
    # Configure structured logging
    from utils.logging import setup_logging

    setup_logging(task_id="T001", log_level=logging.INFO)
    loader = DataLoader()
    try:
        df = loader.process()
        logger.info(
            f"Data download and validation completed. Rows: {len(df)}, Columns: {list(df.columns)}"
        )
    except Exception as e:
        logger.error(f"Data download failed: {e}")
        raise

if __name__ == "__main__":
    main()
