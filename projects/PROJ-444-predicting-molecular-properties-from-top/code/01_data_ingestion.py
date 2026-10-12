import os
import sys
import logging
import random
import json
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import requests
import yaml
from statsmodels.stats.power import TTestPower

from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.Chem.Descriptors import MolWt
from sklearn.model_selection import GroupKFold

# ----------------------------------------------------------------------
# Logging utilities
# ----------------------------------------------------------------------
def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("data_ingestion")
    logger.setLevel(level)
    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setLevel(level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger

# ----------------------------------------------------------------------
# Seed handling
# ----------------------------------------------------------------------
def pin_random_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)

# ----------------------------------------------------------------------
# Molecular weight calculation (correct RDKit implementation)
# ----------------------------------------------------------------------
def calculate_molecular_weight(smiles: str) -> Optional[float]:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return MolWt(mol)

# ----------------------------------------------------------------------
# Scaffold extraction
# ----------------------------------------------------------------------
def get_bemis_murcko_scaffold(smiles: str) -> Optional[str]:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    scaffold = MurckoScaffold.GetScaffoldForMol(mol)
    return Chem.MolToSmiles(scaffold)

# ----------------------------------------------------------------------
# Scaffold integrity check
# ----------------------------------------------------------------------
def check_scaffold_integrity(df: pd.DataFrame, min_scaffolds: int = 100) -> Tuple[int, bool]:
    logger = logging.getLogger("data_ingestion")
    logger.info("Calculating unique Bemis-Murcko scaffolds...")
    scaffolds = df['smiles'].apply(get_bemis_murcko_scaffold).dropna()
    unique_scaffolds = set(scaffolds)
    count = len(unique_scaffolds)
    logger.info(f"Found {count} unique scaffolds.")
    is_valid = count >= min_scaffolds
    if not is_valid:
        logger.error(f"Scaffold Insufficient: {count} < {min_scaffolds}")
    return count, is_valid

# ----------------------------------------------------------------------
# Molecular weight integrity check (excludes >1000 Da)
# ----------------------------------------------------------------------
def verify_data_integrity_mw(df: pd.DataFrame, exclusion_log_path: Path) -> Tuple[pd.DataFrame, bool]:
    """
    Re‑calculates MW for every molecule. Molecules >1000 Da are excluded
    and their SMILES are written to the exclusion log.
    Returns the filtered DataFrame and a flag indicating whether any
    exclusion occurred.
    """
    logger = logging.getLogger("data_ingestion")
    logger.info("Verifying molecular weights and filtering >1000 Da...")
    large_molecules = []
    keep_mask = []

    for idx, row in df.iterrows():
        mw = calculate_molecular_weight(row['smiles'])
        if mw is None:
            # Invalid SMILES will be handled later; keep for now
            keep_mask.append(True)
            continue
        if mw > 1000:
            large_molecules.append(row['smiles'])
            keep_mask.append(False)
        else:
            keep_mask.append(True)

    filtered_df = df.loc[keep_mask].reset_index(drop=True)

    if large_molecules:
        logger.info(f"Logging {len(large_molecules)} large molecules (>1000 Da).")
        exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
        with exclusion_log_path.open("a") as f:
            for smi in large_molecules:
                f.write(f"{smi}\n")
    else:
        # Ensure the log file exists (empty) for verification steps
        exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
        exclusion_log_path.touch()

    return filtered_df, bool(large_molecules)

# ----------------------------------------------------------------------
# Power analysis (paired‑t, effect size d=0.5, α=0.05, power=0.8)
# ----------------------------------------------------------------------
def perform_power_analysis(actual_n: int, output_path: Path) -> None:
    """
    Computes the minimum sample size required for a paired‑t test with
    effect size d=0.5, α=0.05, power=0.8 and writes a JSON report.
    """
    power_solver = TTestPower()
    min_n_float = power_solver.solve_power(effect_size=0.5,
                                           alpha=0.05,
                                           power=0.8,
                                           alternative='two-sided')
    min_n = int(np.ceil(min_n_float))
    passes = actual_n >= min_n
    report = {
        "min_n": min_n,
        "actual_n": actual_n,
        "passes": passes
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(report, f, indent=2)

# ----------------------------------------------------------------------
# Scaffold‑based stratified split (GroupKFold)
# ----------------------------------------------------------------------
def stratified_scaffold_split(df: pd.DataFrame, n_splits: int = 5, seed: int = 42) -> Dict[str, List[int]]:
    """
    Performs a scaffold‑based split using GroupKFold.
    Returns a dict with keys 'train' and 'test' each containing a list
    of index lists for every fold.
    """
    logger = logging.getLogger("data_ingestion")
    logger.info(f"Performing {n_splits}-fold scaffold split with seed {seed}...")
    scaffolds = df['smiles'].apply(get_bemis_murcko_scaffold).fillna(lambda: f"unknown_{np.random.randint(1e9)}")
    gkf = GroupKFold(n_splits=n_splits)
    split_indices = {'train': [], 'test': []}
    for fold, (train_idx, test_idx) in enumerate(gkf.split(df, groups=scaffolds)):
        split_indices['train'].append(train_idx.tolist())
        split_indices['test'].append(test_idx.tolist())
        logger.info(f"Fold {fold}: Train size={len(train_idx)}, Test size={len(test_idx)}")
    return split_indices

# ----------------------------------------------------------------------
# SHA‑256 checksum utility
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 hash of a file."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def append_checksum(file_path: Path, checksums_path: Path) -> None:
    """Append the checksum line to checksums.txt."""
    checksum = compute_sha256(file_path)
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    with checksums_path.open("a") as f:
        f.write(f"{file_path.name}: {checksum}\n")

# ----------------------------------------------------------------------
# Schema validation (columns only)
# ----------------------------------------------------------------------
def validate_schema(df: pd.DataFrame, schema_path: Path) -> bool:
    """
    Very lightweight validation: ensure the DataFrame has exactly the
    required columns as defined in the YAML schema.
    """
    with schema_path.open() as f:
        schema = yaml.safe_load(f)
    required = set(schema.get("required", []))
    present = set(df.columns)
    return present == required

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main():
    logger = setup_logging()
    pin_random_seed(42)

    # ------------------------------------------------------------------
    # 1. Download ESOL dataset (default URL)
    # ------------------------------------------------------------------
    default_url = "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/dataset_esol.csv"
    import argparse
    parser = argparse.ArgumentParser(description="Data ingestion for ESOL dataset")
    parser.add_argument("--url", type=str, default=default_url, help="URL to download the ESOL CSV")
    args = parser.parse_args()

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "esol.csv"

    if not raw_path.exists():
        logger.info(f"Downloading ESOL dataset from {args.url}...")
        response = requests.get(args.url, stream=True, timeout=30)
        response.raise_for_status()
        with raw_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info(f"Saved raw dataset to {raw_path}")
    else:
        logger.info(f"Raw dataset already present at {raw_path}")

    # ------------------------------------------------------------------
    # 2. Compute and record checksum
    # ------------------------------------------------------------------
    checksum_path = Path("data/checksums.txt")
    append_checksum(raw_path, checksum_path)
    logger.info(f"Appended SHA‑256 checksum to {checksum_path}")

    # ------------------------------------------------------------------
    # 3. Load CSV and validate schema
    # ------------------------------------------------------------------
    try:
        df = pd.read_csv(raw_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        sys.exit(1)

    schema_path = Path("specs/001-predicting-molecular-properties-from-top/contracts/dataset.schema.yaml")
    if not validate_schema(df, schema_path):
        logger.error("Schema validation failed: CSV does not contain exactly the required columns.")
        sys.exit(1)
    logger.info("Schema validation passed.")

    # ------------------------------------------------------------------
    # 4. Molecular weight filter (>1000 Da)
    # ------------------------------------------------------------------
    exclusion_log_path = Path("data/logs/large_molecule_exclusions.log")
    df, had_exclusions = verify_data_integrity_mw(df, exclusion_log_path)

    # ------------------------------------------------------------------
    # 5. Power analysis
    # ------------------------------------------------------------------
    power_report_path = Path("data/processed/power_analysis_report.json")
    perform_power_analysis(len(df), power_report_path)
    logger.info(f"Wrote power analysis report to {power_report_path}")

    # ------------------------------------------------------------------
    # 6. Scaffold count check
    # ------------------------------------------------------------------
    scaffold_count, scaffold_ok = check_scaffold_integrity(df, min_scaffolds=100)
    scaffold_counts_path = Path("data/processed/scaffold_counts.json")
    scaffold_counts_path.parent.mkdir(parents=True, exist_ok=True)
    scaffold_status = {
        "unique_scaffolds": scaffold_count,
        "min_required": 100,
        "status": "PASSED" if scaffold_ok else "FAILED"
    }
    with scaffold_counts_path.open("w") as f:
        json.dump(scaffold_status, f, indent=2)
    logger.info(f"Wrote scaffold counts to {scaffold_counts_path}")

    if not scaffold_ok:
        logger.error("Insufficient unique scaffolds; aborting.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 7. Write filtered dataset
    # ------------------------------------------------------------------
    filtered_path = Path("data/processed/filtered_esol.csv")
    filtered_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filtered_path, index=False)
    logger.info(f"Wrote filtered dataset to {filtered_path}")

    # ------------------------------------------------------------------
    # 8. Generate scaffold‑based 5‑fold split
    # ------------------------------------------------------------------
    splits = stratified_scaffold_split(df, n_splits=5, seed=42)
    splits_path = Path("data/processed/splits.json")
    splits_path.parent.mkdir(parents=True, exist_ok=True)
    with splits_path.open("w") as f:
        json.dump(splits, f, indent=2)
    logger.info(f"Wrote split indices to {splits_path}")

    logger.info("Data ingestion (T001) completed successfully.")

if __name__ == "__main__":
    main()
