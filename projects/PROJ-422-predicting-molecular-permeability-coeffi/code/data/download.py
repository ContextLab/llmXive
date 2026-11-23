"""
Data download script for the Molecular Permeability project.

This script reads the dataset identifier from ``config/selected_dataset.yaml``,
attempts to stream the dataset from Hugging Face, and falls back to a local
sample CSV (``data/sample_permeability.csv``) when the remote dataset is
unavailable or empty. It validates that the required columns (SMILES and
permeability) are present, writes the raw CSV file to ``data/raw/`` and records
a SHA‑256 checksum in ``data/raw/checksums.json``.
"""
import csv
import hashlib
import json
import logging
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml
from datasets import load_dataset
from llmxive_toolkit import get_logger

# Module‑level logger
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
        self.expected_columns = [
            col.lower() for col in self.config.get("expected_columns", [])
        ]
        if len(self.expected_columns) < 2:
            raise RuntimeError(
                "Config must specify at least two expected columns (SMILES and target)."
            )
        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------
    @staticmethod
    def _compute_checksum(file_path: Path) -> str:
        """Compute SHA‑256 checksum of ``file_path``."""
        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()

    @staticmethod
    def _write_checksum_file(checksums: Dict[str, str], checksum_path: Path) -> None:
        """Write ``checksums`` dictionary as JSON."""
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        with checksum_path.open("w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
        logging.info(f"Wrote checksum file to {checksum_path}")

    # ------------------------------------------------------------------
    # Core download logic
    # ------------------------------------------------------------------
    def _fetch_remote(self) -> Tuple[Path, bool]:
        """
        Attempt to stream the dataset from Hugging Face.

        Returns
        -------
        Tuple[Path, bool]
            (path_to_csv, from_remote)
            ``from_remote`` is True when the HF dataset was successfully streamed.
        """
        hf_path = self.config.get("hf_path")
        split = self.config.get("split", "train")
        filename = self.config.get("filename", "dataset.csv")
        self.logger.info(
            f"Attempting to fetch dataset {hf_path} (split={split}) from Hugging Face..."
        )

        # Stream the dataset; any exception triggers the fallback path.
        dataset = load_dataset(hf_path, split=split, streaming=True)

        # Determine output CSV path under the project’s ``data/raw`` folder.
        csv_path = Path("data") / "raw" / filename
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        iterator = iter(dataset)
        try:
            first_record = next(iterator)
        except StopIteration:
            raise RuntimeError("Hugging Face dataset is empty")

        fieldnames = list(first_record.keys())
        with csv_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(dict(first_record))
            for record in iterator:
                writer.writerow(dict(record))

        self.logger.info(f"Saved remote dataset to {csv_path}")
        return csv_path, True

    def _fallback_to_local(self) -> Tuple[Path, bool]:
        """
        Copy the bundled sample CSV to the raw data directory.
        """
        local_sample = Path("data") / "sample_permeability.csv"
        if not local_sample.is_file():
            raise FileNotFoundError(
                f"Local fallback sample not found at {local_sample}"
            )
        filename = self.config.get("filename", "sample_permeability.csv")
        csv_path = Path("data") / "raw" / filename
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(local_sample, csv_path)
        self.logger.info(f"Copied local sample to {csv_path}")
        return csv_path, False

    def _fetch_dataset(self) -> Tuple[Path, bool]:
        """
        Wrapper that first tries the remote source, then falls back to the local sample.
        """
        try:
            return self._fetch_remote()
        except Exception as exc:
            self.logger.warning(
                f"Failed to fetch remote dataset ({exc}); falling back to local sample."
            )
            return self._fallback_to_local()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def _validate_columns(self, csv_path: Path) -> Tuple[str, str]:
        """
        Ensure that the required SMILES and target columns exist (case‑insensitive).

        Returns the original column names as they appear in the file.
        """
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise RuntimeError(f"CSV file {csv_path} has no headers.")
            cols = [c.lower() for c in reader.fieldnames]

        missing = [c for c in self.expected_columns if c not in cols]
        if missing:
            raise RuntimeError(
                f"Missing required columns: {missing}. "
                f"Found columns: {reader.fieldnames}"
            )

        # Return the canonical column names as they appear in the file.
        smiles_col = next(
            (c for c in reader.fieldnames if c.lower() == self.expected_columns[0]), None
        )
        target_col = next(
            (c for c in reader.fieldnames if c.lower() == self.expected_columns[1]), None
        )
        return smiles_col, target_col

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def process(self) -> Path:
        """
        Execute the full data‑download pipeline:
        * stream the dataset (or copy local fallback),
        * validate column presence,
        * compute and store a SHA‑256 checksum.
        """
        csv_path, from_remote = self._fetch_dataset()

        # Validate required columns
        self._validate_columns(csv_path)

        # Compute checksum and write manifest
        checksum = self._compute_checksum(csv_path)
        checksum_path = csv_path.parent / "checksums.json"
        self._write_checksum_file({csv_path.name: checksum}, checksum_path)

        self.logger.info(
            f"Data download completed successfully (rows written). "
            f"{'Remote' if from_remote else 'Local fallback'} source used."
        )
        return csv_path

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
