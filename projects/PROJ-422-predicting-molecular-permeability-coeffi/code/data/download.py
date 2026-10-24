"""
Data download script for the Molecular Permeability project.

This script reads the dataset identifier from ``config/selected_dataset.yaml``,
streams the dataset from Hugging Face, validates that the required columns
(SMILES and permeability) are present, writes the raw CSV file to
``data/raw/`` and records a SHA‑256 checksum in ``data/raw/checksums.json``.
"""
import csv
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

logger = get_logger(__name__)

class DataLoader:
    """
    Fetches a verified molecular dataset, validates required columns,
    writes the raw CSV to ``data/raw/`` and records a SHA‑256 checksum.
    """

    def __init__(self, config_path: Path = None):
        """
        Parameters
        ----------
        config_path: Path, optional
            Path to the YAML configuration file that specifies the dataset.
            If omitted, defaults to ``config/selected_dataset.yaml``.
        """
        if config_path is None:
            config_path = Path("config") / "selected_dataset.yaml"
        if not config_path.is_file():
            raise FileNotFoundError(f"Dataset config not found at {config_path}")
        with config_path.open("r", encoding="utf-8") as f:
            self.config: Dict[str, Any] = yaml.safe_load(f)

        # Normalise expected columns to lower‑case for case‑insensitive checks
        self.expected_columns = [c.lower() for c in self.config.get("expected_columns", [])]
        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch_dataset(self):
        """
        Load the dataset from Hugging Face using the ``datasets`` library in
        streaming mode.
        """
        self.logger.info(
            f"Fetching dataset {self.config['hf_path']} (split={self.config['split']}) "
            f"from Hugging Face with streaming..."
        )
        try:
            dataset = load_dataset(
                self.config["hf_path"],
                split=self.config["split"],
                streaming=True,
            )
            self.logger.info("Streaming dataset iterator obtained.")
            return dataset
        except Exception as exc:
            self.logger.error(f"Failed to load dataset: {exc}")
            raise RuntimeError(
                f"Unable to fetch dataset from {self.config['hf_path']}."
            ) from exc

    def validate_columns(self, first_record: Dict[str, Any]) -> Tuple[str, str]:
        """
        Ensure that the required SMILES and target columns exist (case‑insensitive).
        Raises if any required column is missing.
        """
        cols = [c.lower() for c in first_record.keys()]

        # Required columns are defined in the YAML config
        required = self.expected_columns
        missing = [c for c in required if c not in cols]
        if missing:
            raise RuntimeError(
                f"Missing required columns: {missing}. "
                f"Found columns: {list(first_record.keys())}"
            )

        # Return the *original* column names as they appear in the data
        smiles_col = next(
            (c for c in first_record.keys() if c.lower() == required[0]), None
        )
        target_col = next(
            (c for c in first_record.keys() if c.lower() == required[1]), None
        )
        return smiles_col, target_col

    def compute_checksum(self, file_path: Path) -> str:
        """Compute SHA‑256 checksum of ``file_path``."""
        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()

    def write_checksum_file(
        self, checksums: Dict[str, str], checksum_path: Path
    ) -> None:
        """Write ``checksums`` dictionary as JSON."""
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        with checksum_path.open("w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
        self.logger.info(f"Wrote checksum file to {checksum_path}")

    def process(self, save_path: Path = None):
        """
        Execute the full data‑download pipeline:
        * stream the dataset,
        * validate column presence,
        * write a CSV file to ``data/raw/``,
        * compute and store a SHA‑256 checksum.
        """
        dataset = self.fetch_dataset()

        # Stream the first record to obtain column names and perform validation
        try:
            first_record = next(iter(dataset))
        except StopIteration:
            raise RuntimeError("The streamed dataset is empty.")

        smiles_col, target_col = self.validate_columns(first_record)

        # Determine output CSV path
        if save_path is None:
            save_path = paths.data("raw", self.config["filename"])
        else:
            save_path = Path(save_path)

        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Write CSV header and rows (including the first record)
        fieldnames = list(first_record.keys())
        with save_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(first_record)

            for record in dataset:
                # ``record`` is a dict‑like object; convert to plain dict
                writer.writerow(dict(record))

        self.logger.info(f"Saved raw dataset to {save_path}")

        # Compute checksum and write manifest
        checksum = self.compute_checksum(save_path)
        checksum_path = save_path.parent / "checksums.json"
        self.write_checksum_file({save_path.name: checksum}, checksum_path)

        self.logger.info(
            f"Data download completed successfully (rows written)."
        )
        return save_path

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
