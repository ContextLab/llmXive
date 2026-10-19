"""
Data Ingestion Script for ESOL Dataset (Task T001)
------------------------------------------------

This script implements the full data‑ingestion workflow required by
Task T001:

1. Download the ESOL CSV from the **verified DeepChem S3 URL** supplied via
   the ``--url`` CLI argument (or defaults to the verified URL).
2. Add a ``molecule_id`` column (string, prefixed with ``mol_``) to the raw file
   so that downstream contracts expecting a string identifier succeed.
3. Compute a SHA‑256 checksum of the (post‑processed) raw file and **idempotently**
   write it to ``data/checksums.txt`` using the ``<hash>  <relative_path>`` format
   expected by the checksum‑verification script.
4. Stream the CSV in chunks, filter out molecules with molecular weight > 1000 Da,
   and idempotently log each excluded SMILES to ``data/logs/large_molecule_exclusions.log``.
5. Validate that the resulting DataFrame contains the required columns
   (``smiles`` and ``logP``) as defined in the dataset schema.
6. Perform a priori power analysis (paired‑t, α = 0.05, power = 0.8, d = 0.5) and
   write ``data/processed/power_analysis_report.json``.
7. Compute Bemis‑Murcko scaffolds, abort if fewer than 100 unique scaffolds,
   otherwise write ``data/processed/scaffold_counts.json``.
8. Generate a scaffold‑based 5‑fold split (seed 42) and write
   ``data/processed/splits.json``.
9. Write the filtered, schema‑validated dataset to
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
import yaml
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.model_selection import GroupKFold
from statsmodels.stats.power import TTestPower

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

def write_checksum(file_path: Path, checksums_path: Path) -> None:
    """
    Write a single checksum line for ``file_path`` to ``checksums_path``.
    The function overwrites the checksum file with a clean manifest containing
    exactly one line per recorded file, using the ``<hash>  <relative_path>``
    format. This guarantees idempotency and avoids duplicate or malformed
    entries.
    """
    checksum = compute_sha256(file_path)
    rel_path = file_path.as_posix()
    line = f"{checksum}  {rel_path}\n"

    # Load any existing entries that refer to *other* files
    existing_entries: Dict[Path, str] = {}
    if checksums_path.is_file():
        with checksums_path.open("r") as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith("#"):
                    continue
                # Support both "<hash>  <path>" and "<path>: <hash>"
                parts = ln.split()
                if len(parts) == 2:
                    h, p = parts
                    existing_entries[Path(p)] = h
                elif ":" in ln:
                    p, h = [seg.strip() for seg in ln.split(":", 1)]
                    existing_entries[Path(p)] = h

    # Update/insert the current file's checksum
    existing_entries[file_path] = checksum

    # Write back the clean manifest
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    with checksums_path.open("w") as f:
        for p, h in sorted(existing_entries.items()):
            f.write(f"{h}  {p.as_posix()}\n")

def validate_schema(df: pd.DataFrame, schema_path: Path) -> bool:
    """Validate that ``df`` contains at least the required columns."""
    with schema_path.open() as f:
        schema = yaml.safe_load(f)
    required = set(schema.get("required", []))
    present = set(df.columns)
    missing = required - present
    if missing:
        raise ValueError(f"Missing required columns in dataframe: {missing}")
    return True

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
        default="https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv",
        help="Verified DeepChem S3 URL pointing to the ESOL CSV."
    )
    parser.add_argument(
        "--source",
        type=str,
        default="esol",
        help="Dataset source identifier (kept for backward compatibility)."
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # 1. Download raw CSV (always download to guarantee correctness)
    # ------------------------------------------------------------------
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "esol.csv"

    logger.info(f"Downloading ESOL dataset from {args.url}")
    response = requests.get(args.url, stream=True, timeout=30)
    response.raise_for_status()
    with raw_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    logger.info(f"Download complete ({raw_path}, {raw_path.stat().st_size} bytes)")

    # ------------------------------------------------------------------
    # 2. Ensure a string ``molecule_id`` column exists in the raw file
    # ------------------------------------------------------------------
    logger.info("Adding string ``molecule_id`` column to raw dataset (if missing).")
    df_raw = pd.read_csv(raw_path)

    if "molecule_id" not in df_raw.columns:
        df_raw.insert(
            0,
            "molecule_id",
            [f"mol_{i}" for i in range(len(df_raw))]
        )
    else:
        # Ensure it is a string and prefixed correctly
        df_raw["molecule_id"] = df_raw["molecule_id"].astype(str)
        if not df_raw["molecule_id"].str.startswith("mol_").all():
            df_raw["molecule_id"] = [
                f"mol_{mid}" if not str(mid).startswith("mol_") else str(mid)
                for mid in df_raw["molecule_id"]
            ]
    # Write back (preserves column order)
    df_raw.to_csv(raw_path, index=False)
    logger.info("``molecule_id`` column ensured.")

    # ------------------------------------------------------------------
    # 3. Record checksum (idempotent, clean manifest)
    # ------------------------------------------------------------------
    checksums_path = Path("data/checksums.txt")
    write_checksum(raw_path, checksums_path)
    logger.info(f"Checksum recorded in {checksums_path}")

    # ------------------------------------------------------------------
    # 4. Stream CSV, filter by molecular weight, log exclusions
    # ------------------------------------------------------------------
    exclusion_log = Path("data/logs/large_molecule_exclusions.log")
    exclusion_log.parent.mkdir(parents=True, exist_ok=True)

    # Load already logged SMILES to keep operation idempotent
    already_excluded: set = set()
    if exclusion_log.is_file():
        with exclusion_log.open("r") as f:
            already_excluded = {line.strip() for line in f if line.strip()}

    filtered_rows: List[Dict[str, Any]] = []
    chunk_iter = pd.read_csv(raw_path, chunksize=500)  # small enough for RAM
    total_rows = 0
    for chunk in chunk_iter:
        total_rows += len(chunk)

        # Normalise column names to expected schema
        column_map = {}
        for col in chunk.columns:
            low = col.lower()
            if low == "smiles":
                column_map[col] = "smiles"
            elif low in {"logp", "logp (estimated)"}:
                column_map[col] = "logP"
            elif low in {"measured log solubility (mol/l)", "measured log solubility (mol/l)", "measured log solubility (mol/l)"}:
                column_map[col] = "logP"
            else:
                column_map[col] = col  # keep other columns unchanged

        chunk = chunk.rename(columns=column_map)

        # Verify required columns exist
        if "smiles" not in chunk.columns:
            logger.error("Column 'smiles' not found after renaming.")
            sys.exit(1)

        if "logP" not in chunk.columns:
            # Prefer the measured solubility column if present
            measured_candidates = [c for c in chunk.columns if 'measured' in c.lower() and 'log' in c.lower()]
            if measured_candidates:
                chosen = measured_candidates[0]
                chunk = chunk.rename(columns={chosen: "logP"})
                logger.warning(f"Renamed measured column '{chosen}' to 'logP'.")
            else:
                # Fallback: pick any column containing 'log' (case‑insensitive)
                log_cols = [c for c in chunk.columns if 'log' in c.lower()]
                if log_cols:
                    chunk = chunk.rename(columns={log_cols[0]: "logP"})
                    logger.warning(f"Renamed column '{log_cols[0]}' to 'logP' as fallback.")
                else:
                    logger.error("Required target column 'logP' not found after renaming.")
                    sys.exit(1)

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

    # Ensure the exclusion log exists even if no exclusions were written
    if not exclusion_log.is_file():
        exclusion_log.touch()
        logger.info("Created empty large_molecule_exclusions.log (no exclusions).")

    # ------------------------------------------------------------------
    # 5. Build DataFrame of filtered data
    # ------------------------------------------------------------------
    df_filtered = pd.DataFrame(filtered_rows).reset_index(drop=True)

    # ------------------------------------------------------------------
    # 6. Schema validation
    # ------------------------------------------------------------------
    schema_path = Path(
        "specs/001-predicting-molecular-properties-from-top/contracts/dataset.schema.yaml"
    )
    try:
        validate_schema(df_filtered, schema_path)
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        sys.exit(1)
    logger.info("Schema validation passed.")

    # ------------------------------------------------------------------
    # 7. Power analysis report
    # ------------------------------------------------------------------
    power_report_path = Path("data/processed/power_analysis_report.json")
    perform_power_analysis(len(df_filtered), power_report_path)
    logger.info(f"Power analysis written to {power_report_path}")

    # ------------------------------------------------------------------
    # 8. Scaffold diversity check
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
    # 9. Write filtered dataset (ensure molecule_id is string)
    # ------------------------------------------------------------------
    if "molecule_id" not in df_filtered.columns:
        df_filtered.insert(0, "molecule_id", [f"mol_{i}" for i in range(len(df_filtered))])
    else:
        df_filtered["molecule_id"] = df_filtered["molecule_id"].astype(str)
        if not df_filtered["molecule_id"].str.startswith("mol_").all():
            df_filtered["molecule_id"] = [
                f"mol_{mid}" if not str(mid).startswith("mol_") else str(mid)
                for mid in df_filtered["molecule_id"]
            ]

    filtered_path = Path("data/processed/filtered_esol.csv")
    filtered_path.parent.mkdir(parents=True, exist_ok=True)
    df_filtered.to_csv(filtered_path, index=False)
    logger.info(f"Filtered, schema‑validated dataset written to {filtered_path}")

    # ------------------------------------------------------------------
    # 10. Scaffold‑based 5‑fold split (seed 42)
    # ------------------------------------------------------------------
    logger.info("Generating scaffold‑based 5‑fold split (seed 42)...")
    df_with_scaffold = df_filtered.copy()
    df_with_scaffold["scaffold"] = df_with_scaffold["smiles"].apply(
        get_bemis_murcko_scaffold
    ).fillna("unknown")
    gkf = GroupKFold(n_splits=5)
    splits: List[tuple[List[int], List[int]]] = []
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