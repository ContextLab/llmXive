"""
Data Ingestion Script for ESOL Dataset
-------------------------------------

Implements Task T001: download the ESOL dataset, validate schema, 
filter by molecular weight (>1000 Da), perform power analysis, 
check scaffold diversity, and create a scaffold-based 5-fold split.

Key Requirements:
- Download from verified URL.
- Chunked processing for memory efficiency (fallback).
- SHA-256 provenance tracking.
- Scaffold-based splitting to prevent leakage.
"""

import argparse
import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
import requests
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.model_selection import GroupKFold
from statsmodels.stats.power import TTestPower

# ----------------------------------------------------------------------
# Logging utilities
# ----------------------------------------------------------------------
def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("data_ingestion")
    logger.setLevel(level)
    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setLevel(level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger

def pin_random_seed(seed: int = 42) -> None:
    """Fix Python, NumPy and random seeds for reproducibility."""
    import random
    random.seed(seed)
    np.random.seed(seed)

# ----------------------------------------------------------------------
# Molecular Utilities
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
# Provenance & Validation
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
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

def validate_schema(df: pd.DataFrame, schema_path: Path) -> bool:
    """Ensure the DataFrame has exactly the required columns as defined in the YAML schema."""
    import yaml
    with schema_path.open() as f:
        schema = yaml.safe_load(f)
    required = set(schema.get("required", []))
    present = set(df.columns)
    return present == required

# ----------------------------------------------------------------------
# Power Analysis
# ----------------------------------------------------------------------
def perform_power_analysis(actual_n: int, output_path: Path) -> None:
    """
    Computes the minimum sample size required for a paired-t test 
    with effect size d=0.5, alpha=0.05, power=0.8.
    """
    power_solver = TTestPower()
    # For paired t-test, solve_power computes n for the given parameters
    min_n_float = power_solver.solve_power(
        effect_size=0.5, alpha=0.05, power=0.8, alternative="two-sided"
    )
    min_n = int(np.ceil(min_n_float))
    passes = actual_n >= min_n
    report = {"min_n": min_n, "actual_n": actual_n, "passes": passes}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(report, f, indent=2)

# ----------------------------------------------------------------------
# Main Workflow
# ----------------------------------------------------------------------
def main() -> None:
    logger = setup_logging()
    pin_random_seed(42)

    parser = argparse.ArgumentParser(description="Data ingestion for ESOL dataset")
    parser.add_argument(
        "--url", 
        type=str, 
        default="https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/dataset_esol.csv",
        help="URL to download the ESOL CSV."
    )
    args = parser.parse_args()

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "esol.csv"

    # 1. Download Dataset
    logger.info(f"Downloading ESOL dataset from {args.url}...")
    try:
        response = requests.get(args.url, stream=True, timeout=30)
        response.raise_for_status()
        with raw_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        sys.exit(1)

    # 2. Provenance
    append_checksum(raw_path, Path("data/checksums.txt"))
    logger.info("Appended SHA-256 checksum to data/checksums.txt")

    # 3. Chunked Ingestion & MW Filtering (Fallback mechanism for large files)
    # We process in chunks to satisfy the "chunked fallback" requirement
    exclusion_log_path = Path("data/logs/large_molecule_exclusions.log")
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    filtered_records = []
    had_exclusions = False
    
    # Use chunksize to avoid loading massive files into memory at once
    # Even though ESOL is small, this implements the required fallback logic.
    chunk_size = 500 
    for chunk in pd.read_csv(raw_path, chunksize=chunk_size):
        # Ensure required columns are present in the chunk
        if "smiles" not in chunk.columns or "logP" not in chunk.columns:
            logger.error("CSV missing required columns 'smiles' or 'logP'")
            sys.exit(1)
        
        # Keep only required columns
        chunk = chunk[["smiles", "logP"]].copy()
        
        for _, row in chunk.iterrows():
            smi = row["smiles"]
            mw = calculate_molecular_weight(smi)
            if mw is not None and mw > 1000:
                with exclusion_log_path.open("a") as f:
                    f.write(f"{smi}\n")
                had_exclusions = True
            else:
                filtered_records.append(row)
    
    if not had_exclusions:
        exclusion_log_path.touch()

    df = pd.DataFrame(filtered_records).reset_index(drop=True)
    logger.info(f"Filtered dataset size: {len(df)} molecules.")

    # 4. Schema Validation
    schema_path = Path("specs/001-predicting-molecular-properties-from-top/contracts/dataset.schema.yaml")
    if not validate_schema(df, schema_path):
        logger.error("Schema validation failed: Columns do not match contract.")
        sys.exit(1)
    logger.info("Schema validation passed.")

    # 5. Power Analysis
    power_report_path = Path("data/processed/power_analysis_report.json")
    perform_power_analysis(len(df), power_report_path)
    logger.info(f"Wrote power analysis report to {power_report_path}")

    # 6. Scaffold Diversity Check
    logger.info("Calculating unique Bemis-Murcko scaffolds...")
    scaffolds = df["smiles"].apply(get_bemis_murcko_scaffold).dropna()
    unique_scaffolds_count = len(set(scaffolds))
    
    scaffold_counts_path = Path("data/processed/scaffold_counts.json")
    scaffold_counts_path.parent.mkdir(parents=True, exist_ok=True)
    with scaffold_counts_path.open("w") as f:
        json.dump({"unique_scaffolds": unique_scaffolds_count}, f, indent=2)
    
    if unique_scaffolds_count < 100:
        logger.error(f"Scaffold Insufficient: {unique_scaffolds_count} < 100")
        sys.exit(1)
    logger.info(f"Found {unique_scaffolds_count} unique scaffolds. Check passed.")

    # 7. Write Filtered Dataset
    filtered_path = Path("data/processed/filtered_esol.csv")
    filtered_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filtered_path, index=False)
    logger.info(f"Wrote filtered dataset to {filtered_path}")

    # 8. Scaffold-based 5-fold Split
    logger.info("Generating 5-fold scaffold split (seed 42)...")
    # Assign scaffold to each row for GroupKFold
    df_with_scaff = df.copy()
    df_with_scaff["scaffold"] = df_with_scaff["smiles"].apply(get_bemis_murcko_scaffold).fillna("unknown")
    
    gkf = GroupKFold(n_splits=5)
    splits = []
    for train_idx, test_idx in gkf.split(df_with_scaff, groups=df_with_scaff["scaffold"]):
        splits.append((train_idx.tolist(), test_idx.tolist()))
    
    splits_path = Path("data/processed/splits.json")
    with splits_path.open("w") as f:
        json.dump({"splits": splits}, f, indent=2)
    logger.info(f"Wrote split indices to {splits_path}")

    logger.info("Data ingestion (T001) completed successfully.")

if __name__ == "__main__":
    main()