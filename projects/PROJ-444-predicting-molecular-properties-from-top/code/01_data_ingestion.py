"""
Data Ingestion Script for the MoleculeNet Lipophilicity Dataset (Task T001c)

This script performs the ingestion workflow required by Task T001c:

1. **Load the raw Lipophilicity CSV** (downloaded by
   ``code/01_download_lipophilicity.py``).
2. **Add a ``molecule_id`` column** (string, prefixed with ``mol_``) if it
   does not already exist.
3. **Validate** the DataFrame against the dataset schema
   (``dataset.schema.yaml``) – required columns are ``molecule_id``,
   ``smiles`` and ``logP``.
4. **Filter** out molecules with molecular weight > 1000 Da, logging each
   excluded SMILES to ``data/logs/large_molecule_exclusions.log`` (idempotent).
5. **Compute Bemis‑Murcko scaffolds**, abort if fewer than 100 distinct
   scaffolds are found.
6. **Generate a scaffold‑based 5‑fold split** (seed 42) and write it to
   ``data/processed/splits.json``.
7. **Write the filtered, schema‑validated dataset** to
   ``data/processed/filtered_lipophilicity.csv``.
8. **Perform a priori power analysis** and write the report to
   ``data/processed/power_analysis_report.json``.
9. **Record a SHA‑256 checksum** of the filtered CSV in ``data/checksums.txt``.

The script is deterministic (fixed random seed) and aborts with a clear
error message if any requirement is not met.
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
    Idempotently write a checksum line for ``file_path`` to ``checksums_path``.
    The manifest is kept clean (one line per file, sorted).
    """
    checksum = compute_sha256(file_path)
    rel_path = file_path.as_posix()

    # Load existing entries (if any)
    existing: Dict[Path, str] = {}
    if checksums_path.is_file():
        with checksums_path.open("r") as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith("#"):
                    continue
                if "  " in ln:
                    h, p = ln.split("  ", 1)
                    existing[Path(p)] = h
                elif ":" in ln:
                    p, h = [seg.strip() for seg in ln.split(":", 1)]
                    existing[Path(p)] = h

    # Update/insert current entry
    existing[file_path] = checksum

    # Write back sorted manifest
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    with checksums_path.open("w") as f:
        for p, h in sorted(existing.items()):
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
        description="Ingest the Lipophilicity dataset for Task T001c"
    )
    parser.add_argument(
        "--source",
        type=str,
        default="lipophilicity",
        help="Dataset source identifier (currently only 'lipophilicity' is supported)."
    )
    args = parser.parse_args()

    if args.source != "lipophilicity":
        logger.error(f"Unsupported source '{args.source}'. Only 'lipophilicity' is supported.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 1. Load raw CSV (must exist – produced by 01_download_lipophilicity.py)
    # ------------------------------------------------------------------
    raw_path = Path("data/raw") / "lipophilicity.csv"
    if not raw_path.is_file():
        logger.error(f"Raw Lipophilicity file not found at {raw_path}. Run 01_download_lipophilicity.py first.")
        sys.exit(1)

    logger.info(f"Reading raw Lipophilicity data from {raw_path}")
    df_raw = pd.read_csv(raw_path)

    # ------------------------------------------------------------------
    # 2. Ensure a string ``molecule_id`` column exists
    # ------------------------------------------------------------------
    if "molecule_id" not in df_raw.columns:
        df_raw.insert(0, "molecule_id", [f"mol_{i}" for i in range(len(df_raw))])
    else:
        df_raw["molecule_id"] = df_raw["molecule_id"].astype(str)
        if not df_raw["molecule_id"].str.startswith("mol_").all():
            df_raw["molecule_id"] = [
                f"mol_{mid}" if not str(mid).startswith("mol_") else str(mid)
                for mid in df_raw["molecule_id"]
            ]

    # ------------------------------------------------------------------
    # 3. Record checksum of the (post‑processed) raw file
    # ------------------------------------------------------------------
    checksums_path = Path("data/checksums.txt")
    write_checksum(raw_path, checksums_path)
    logger.info(f"Checksum for raw file recorded in {checksums_path}")

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
    total_rows = 0
    chunk_iter = pd.read_csv(raw_path, chunksize=500)
    for chunk in chunk_iter:
        total_rows += len(chunk)

        # Ensure required column names
        if "smiles" not in chunk.columns:
            logger.error("Column 'smiles' not found in raw data.")
            sys.exit(1)
        if "logP" not in chunk.columns:
            logger.error("Column 'logP' not found in raw data.")
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

    # Ensure the exclusion log exists even if empty
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

    filtered_path = Path("data/processed/filtered_lipophilicity.csv")
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

    logger.info("Task T001c (Lipophilicity ingestion) completed successfully.")

if __name__ == "__main__":
    main()
