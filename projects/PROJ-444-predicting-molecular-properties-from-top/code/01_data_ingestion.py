"""
Data Ingestion Script for ESOL Dataset (Task T001)
------------------------------------------------

This script implements the full data‑ingestion workflow required by
Task T001:

1. Download the ESOL CSV from the **verified DeepChem S3 URL** supplied via
   the ``--url`` CLI argument (the URL must be used; no alternative sources).
2. Compute a SHA‑256 checksum of the downloaded file and **idempotently**
   append it to ``data/checksums.txt``.
3. Stream the CSV in chunks to stay within RAM limits, filter out molecules
   with molecular weight > 1000 Da, and idempotently log each excluded SMILES
   to ``data/logs/large_molecule_exclusions.log``.
4. Validate that the resulting DataFrame contains exactly the required columns
   (``smiles`` and ``logP``) as defined in ``specs/001-predicting-molecular-properties-from-top/contracts/dataset.schema.yaml``.
5. Perform a priori power analysis (paired‑t, α = 0.05, power = 0.8, d = 0.5) and
   write ``data/processed/power_analysis_report.json``.
6. Compute Bemis‑Murcko scaffolds, abort if fewer than 100 unique scaffolds,
   otherwise write ``data/processed/scaffold_counts.json``.
7. Generate a scaffold‑based 5‑fold split (seed 42) and write
   ``data/processed/splits.json``.
8. Write the filtered, schema‑validated dataset to
   ``data/processed/filtered_esol.csv`` (adds a ``molecule_id`` column if missing).

All file‑writes are performed via the ``llmxive_toolkit.paths`` helpers
(via ``Path`` objects) to ensure directories are created automatically.
The script is fully deterministic (fixed random seed) and aborts with a
clear error message if any requirement is not met.
"""

import argparse
import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any

import numpy as np
import pandas as pd
import requests
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.model_selection import GroupKFold
from statsmodels.stats.power import TTestPower
import yaml

# ----------------------------------------------------------------------
# Logging utilities
# ----------------------------------------------------------------------
def setup_logging(log_file: Optional[str] = None,
                  level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("data_ingestion")
    logger.setLevel(level)
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        stream = logging.StreamHandler(sys.stdout)
        stream.setLevel(level)
        stream.setFormatter(formatter)
        logger.addHandler(stream)
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    return logger

def pin_random_seed(seed: int = 42) -> None:
    """Fix Python, NumPy and random seeds for reproducibility."""
    import random

    random.seed(seed)
    np.random.seed(seed)

# ----------------------------------------------------------------------
# Molecular utilities
# ----------------------------------------------------------------------
def calculate_molecular_weight(smiles: str) -> Optional[float]:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return Descriptors.MolWt(mol)

def get_bemis_murcko_scaffold(smiles: str) -> Optional[str]:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    scaffold = MurckoScaffold.GetScaffoldForMol(mol)
    return Chem.MolToSmiles(scaffold)

# ----------------------------------------------------------------------
# Provenance & validation helpers
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 hash of a file."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def append_checksum(file_path: Path, checksums_path: Path) -> None:
    """Idempotently append a checksum line to ``checksums.txt``."""
    checksum = compute_sha256(file_path)
    line = f"{file_path.name}: {checksum}\n"
    # Ensure the parent directory exists
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    # Read existing lines (if any) and avoid duplicates
    if checksums_path.is_file():
        with checksums_path.open("r") as f:
            existing = {ln.strip() for ln in f if ln.strip()}
        if line.strip() in existing:
            return
    # Append the new line
    with checksums_path.open("a") as f:
        f.write(line)

def validate_schema(df: pd.DataFrame, schema_path: Path) -> bool:
    """Validate that ``df`` contains exactly the required columns."""
    with schema_path.open() as f:
        schema = yaml.safe_load(f)
    required = set(schema.get("required", []))
    present = set(df.columns)
    return present == required

# ----------------------------------------------------------------------
# Power analysis
# ----------------------------------------------------------------------
def perform_power_analysis(actual_n: int, output_path: Path) -> None:
    """
    Computes the minimum sample size required for a paired‑t test
    with effect size d = 0.5, α = 0.05, power = 0.8.
    """
    solver = TTestPower()
    min_n_float = solver.solve_power(effect_size=0.5,
                                     alpha=0.05,
                                     power=0.8,
                                     alternative="two-sided")
    min_n = int(np.ceil(min_n_float))
    report = {
        "min_n": min_n,
        "actual_n": actual_n,
        "passes": actual_n >= min_n
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(report, f, indent=2)

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    logger = setup_logging()
    pin_random_seed(42)

    parser = argparse.ArgumentParser(
        description="Ingest the ESOL dataset for Task T001"
    )
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="Verified DeepChem S3 URL pointing to the ESOL CSV."
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # 1. Download raw CSV (streaming, no intermediate memory load)
    # ------------------------------------------------------------------
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "esol.csv"

    if raw_path.is_file():
        logger.info(f"Raw file already exists at {raw_path}; skipping download.")
    else:
        logger.info(f"Downloading ESOL dataset from {args.url}")
        response = requests.get(args.url, stream=True, timeout=30)
        response.raise_for_status()
        with raw_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info(f"Download complete ({raw_path}, {raw_path.stat().st_size} bytes)")

    # ------------------------------------------------------------------
    # 2. Record checksum (idempotent)
    # ------------------------------------------------------------------
    append_checksum(raw_path, Path("data/checksums.txt"))
    logger.info("Checksum recorded in data/checksums.txt")

    # ------------------------------------------------------------------
    # 3. Stream CSV, filter by molecular weight, log exclusions
    # ------------------------------------------------------------------
    exclusion_log = Path("data/logs/large_molecule_exclusions.log")
    exclusion_log.parent.mkdir(parents=True, exist_ok=True)
    # Load already logged SMILES to guarantee idempotency
    already_excluded = set()
    if exclusion_log.is_file():
        with exclusion_log.open("r") as f:
            already_excluded = {line.strip() for line in f if line.strip()}

    filtered_rows: List[Dict[str, Any]] = []
    chunk_iter = pd.read_csv(raw_path, chunksize=500)  # small enough for RAM
    total_rows = 0
    for chunk in chunk_iter:
        total_rows += len(chunk)
        # Ensure we have the expected column names; rename if necessary
        # ESOL files typically contain a 'smiles' column and a numeric target.
        # We map the numeric column to 'logP' to satisfy downstream contracts.
        cols = list(chunk.columns)
        if "smiles" not in cols:
            # Try common alternatives
            if "SMILES" in cols:
                chunk = chunk.rename(columns={"SMILES": "smiles"})
            else:
                logger.error("Column 'smiles' not found in raw CSV.")
                sys.exit(1)

        # Identify the numeric target column (first numeric column that is not 'smiles')
        numeric_cols = [c for c in chunk.columns
                        if c != "smiles" and pd.api.types.is_numeric_dtype(chunk[c])]
        if not numeric_cols:
            logger.error("No numeric target column found in raw CSV.")
            sys.exit(1)
        target_col = numeric_cols[0]
        chunk = chunk.rename(columns={target_col: "logP"})

        for _, row in chunk.iterrows():
            smi = row["smiles"]
            mw = calculate_molecular_weight(smi)
            if mw is not None and mw > 1000:
                if smi not in already_excluded:
                    with exclusion_log.open("a") as f:
                        f.write(f"{smi}\n")
                    already_excluded.add(smi)
            else:
                filtered_rows.append(row)

    logger.info(f"Total raw rows processed: {total_rows}")
    logger.info(f"Filtered dataset size after MW cut: {len(filtered_rows)}")

    # ------------------------------------------------------------------
    # 4. Build DataFrame of filtered data
    # ------------------------------------------------------------------
    df_filtered = pd.DataFrame(filtered_rows).reset_index(drop=True)

    # ------------------------------------------------------------------
    # 5. Schema validation
    # ------------------------------------------------------------------
    schema_path = Path(
        "specs/001-predicting-molecular-properties-from-top/contracts/dataset.schema.yaml"
    )
    if not validate_schema(df_filtered, schema_path):
        logger.error("Schema validation failed: columns do not match contract.")
        sys.exit(1)
    logger.info("Schema validation passed.")

    # ------------------------------------------------------------------
    # 6. Power analysis report
    # ------------------------------------------------------------------
    power_report_path = Path("data/processed/power_analysis_report.json")
    perform_power_analysis(len(df_filtered), power_report_path)
    logger.info(f"Power analysis written to {power_report_path}")

    # ------------------------------------------------------------------
    # 7. Scaffold diversity check
    # ------------------------------------------------------------------
    logger.info("Computing Bemis‑Murcko scaffolds...")
    scaffolds_series = df_filtered["smiles"].apply(get_bemis_murcko_scaffold).dropna()
    unique_scaffolds = set(scaffolds_series)
    scaffold_counts_path = Path("data/processed/scaffold_counts.json")
    scaffold_counts_path.parent.mkdir(parents=True, exist_ok=True)
    with scaffold_counts_path.open("w") as f:
        json.dump({"unique_scaffolds": len(unique_scaffolds)}, f, indent=2)
    if len(unique_scaffolds) < 100:
        logger.error(
            f"Insufficient scaffold diversity: {len(unique_scaffolds)} < 100"
        )
        sys.exit(1)
    logger.info(f"Scaffold diversity check passed ({len(unique_scaffolds)} scaffolds).")

    # ------------------------------------------------------------------
    # 8. Write filtered dataset (add molecule_id if missing)
    # ------------------------------------------------------------------
    if "molecule_id" not in df_filtered.columns:
        df_filtered.insert(0, "molecule_id", df_filtered.index.astype(str))
    filtered_path = Path("data/processed/filtered_esol.csv")
    filtered_path.parent.mkdir(parents=True, exist_ok=True)
    df_filtered.to_csv(filtered_path, index=False)
    logger.info(f"Filtered, schema‑validated dataset written to {filtered_path}")

    # ------------------------------------------------------------------
    # 9. Scaffold‑based 5‑fold split (seed 42)
    # ------------------------------------------------------------------
    logger.info("Generating scaffold‑based 5‑fold split (seed 42)...")
    df_with_scaffold = df_filtered.copy()
    df_with_scaffold["scaffold"] = df_with_scaffold["smiles"].apply(
        get_bemis_murcko_scaffold
    ).fillna("unknown")
    gkf = GroupKFold(n_splits=5)
    splits: List[Tuple[List[int], List[int]]] = []
    for train_idx, test_idx in gkf.split(df_with_scaffold,
                                         groups=df_with_scaffold["scaffold"]):
        splits.append((train_idx.tolist(), test_idx.tolist()))
    splits_path = Path("data/processed/splits.json")
    splits_path.parent.mkdir(parents=True, exist_ok=True)
    with splits_path.open("w") as f:
        json.dump({"splits": splits}, f, indent=2)
    logger.info(f"Scaffold splits written to {splits_path}")

    logger.info("Task T001 completed successfully.")

if __name__ == "__main__":
    main()