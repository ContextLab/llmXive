"""
Data Ingestion Script for Lipophilicity (logP) Dataset
-----------------------------------------------------

Implements Task T001: download the lipophilicity dataset (default URL),
validate schema, filter by molecular weight, perform power analysis,
check scaffold diversity, create a scaffold‑based 5‑fold split, and
write all artefacts to the declared locations.

The script defaults to using the verified ``scikit‑fingerprints`` loader
(source='skfp'), which provides the canonical MoleculeNet Lipophilicity
dataset with columns ``smiles`` and ``logP``.  For environments where
``skfp`` is unavailable the script can fall back to downloading the raw
CSV from the official URL (source='url').  An additional alias ``pubchem``
is accepted for backward compatibility.
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
from rdkit.Chem import Descriptors
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.model_selection import GroupKFold
from statsmodels.stats.power import TTestPower

# Verified real‑data loader (optional)
try:
    from skfp.datasets.moleculenet import load_lipophilicity
except Exception:  # pragma: no cover
    load_lipophilicity = None  # Will be used only when source='skfp'

# ----------------------------------------------------------------------
# Logging utilities
# ----------------------------------------------------------------------
def setup_logging(log_file: Optional[str] = None,
                  level: int = logging.INFO) -> logging.Logger:
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

# ----------------------------------------------------------------------
# Seed handling
# ----------------------------------------------------------------------
def pin_random_seed(seed: int = 42) -> None:
    """Fix Python, NumPy and random seeds for reproducibility."""
    import random

    random.seed(seed)
    np.random.seed(seed)

# ----------------------------------------------------------------------
# Molecular weight calculation (RDKit)
# ----------------------------------------------------------------------
def calculate_molecular_weight(smiles: str) -> Optional[float]:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return Descriptors.MolWt(mol)

# ----------------------------------------------------------------------
# Scaffold extraction (Bemis‑Murcko)
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
def check_scaffold_integrity(
    df: pd.DataFrame, min_scaffolds: int = 100
) -> Tuple[int, bool]:
    logger = logging.getLogger("data_ingestion")
    logger.info("Calculating unique Bemis‑Murcko scaffolds...")
    scaffolds = df["smiles"].apply(get_bemis_murcko_scaffold).dropna()
    unique_scaffolds = set(scaffolds)
    count = len(unique_scaffolds)
    logger.info(f"Found {count} unique scaffolds.")
    is_valid = count >= min_scaffolds
    if not is_valid:
        logger.error(
            f"Scaffold Insufficient: {count} < {min_scaffolds}"
        )
    return count, is_valid

# ----------------------------------------------------------------------
# Molecular‑weight filter (>1000 Da) and logging
# ----------------------------------------------------------------------
def verify_data_integrity_mw(
    df: pd.DataFrame, exclusion_log_path: Path
) -> Tuple[pd.DataFrame, bool]:
    """
    Re‑calculates MW for every molecule. Molecules >1000 Da are excluded
    and their SMILES are written to the exclusion log.
    Returns the filtered DataFrame and a flag indicating whether any
    exclusion occurred.
    """
    logger = logging.getLogger("data_ingestion")
    logger.info("Verifying molecular weights and filtering >1000 Da...")
    large_molecules: List[str] = []
    keep_mask: List[bool] = []

    for _, row in df.iterrows():
        mw = calculate_molecular_weight(row["smiles"])
        if mw is None:
            # Invalid SMILES – keep for now; later steps will drop them
            keep_mask.append(True)
            continue
        if mw > 1000:
            large_molecules.append(row["smiles"])
            keep_mask.append(False)
        else:
            keep_mask.append(True)

    filtered_df = df.loc[keep_mask].reset_index(drop=True)

    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    if large_molecules:
        logger.info(
            f"Logging {len(large_molecules)} large molecules (>1000 Da)."
        )
        with exclusion_log_path.open("a") as f:
            for smi in large_molecules:
                f.write(f"{smi}\\n")
    else:
        # Ensure an empty log exists for downstream checks
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
# Scaffold‑based stratified split (GroupKFold)
# ----------------------------------------------------------------------
def stratified_scaffold_split(
    df: pd.DataFrame, n_splits: int = 5, seed: int = 42
) -> List[Tuple[List[int], List[int]]]:
    """
    Performs a scaffold‑based split using GroupKFold.
    Returns a list of (train_idx, test_idx) tuples for each fold.
    """
    logger = logging.getLogger("data_ingestion")
    logger.info(
        f"Performing {n_splits}-fold scaffold split with seed {seed}..."
    )
    # Compute scaffold strings; replace missing with a unique placeholder
    scaffolds = df["smiles"].apply(get_bemis_murcko_scaffold).fillna(
        lambda: f"unknown_{np.random.randint(1_000_000_000)}"
    )
    gkf = GroupKFold(n_splits=n_splits)
    split_indices: List[Tuple[List[int], List[int]]] = []
    for fold, (train_idx, test_idx) in enumerate(
        gkf.split(df, groups=scaffolds)
    ):
        split_indices.append((train_idx.tolist(), test_idx.tolist()))
        logger.info(
            f"Fold {fold}: Train size={len(train_idx)}, Test size={len(test_idx)}"
        )
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
        f.write(f"{file_path.name}: {checksum}\\n")

# ----------------------------------------------------------------------
# Schema validation (columns only)
# ----------------------------------------------------------------------
def validate_schema(df: pd.DataFrame, schema_path: Path) -> bool:
    """
    Very lightweight validation: ensure the DataFrame has exactly the
    required columns as defined in the YAML schema.
    """
    import yaml

    with schema_path.open() as f:
        schema = yaml.safe_load(f)
    required = set(schema.get("required", []))
    present = set(df.columns)
    return present == required

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    logger = setup_logging()
    pin_random_seed(42)

    parser = argparse.ArgumentParser(
        description="Data ingestion for Lipophilicity (logP) dataset"
    )
    parser.add_argument(
        "--source",
        type=str,
        default="skfp",
        help=(
            "Data source identifier. 'skfp' (default) loads the dataset via "
            "scikit‑fingerprints. 'url' downloads the CSV from the official URL. "
            "'pubchem' is accepted as an alias for 'skfp' for backward compatibility."
        ),
    )
    parser.add_argument(
        "--url",
        type=str,
        default="https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/lipophilicity.csv",
        help="URL to download the CSV when source='url'.",
    )
    args = parser.parse_args()

    # Normalise source aliases
    source = args.source.lower()
    if source == "pubchem":
        source = "skfp"

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "esol.csv"   # keep filename for downstream scripts

    # ------------------------------------------------------------------
    # 1. Load dataset
    # ------------------------------------------------------------------
    if source == "skfp":
        if load_lipophilicity is None:
            logger.error(
                "scikit-fingerprints not installed. Install it via requirements.txt."
            )
            sys.exit(1)
        logger.info("Loading Lipophilicity dataset via scikit‑fingerprints (verified source)...")
        X, y = load_lipophilicity()
        if isinstance(X, pd.DataFrame):
            smiles_series = X["smiles"] if "smiles" in X.columns else X.iloc[:, 0]
        else:
            smiles_series = pd.Series(list(X))
        df = pd.DataFrame({"smiles": smiles_series, "logP": y})
    elif source == "url":
        logger.info(f"Downloading Lipophilicity dataset from {args.url}...")
        import requests

        response = requests.get(args.url, stream=True, timeout=30)
        response.raise_for_status()
        with raw_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info(f"Saved raw dataset to {raw_path}")
        df = pd.read_csv(raw_path)
    else:
        logger.error(f"Unknown source '{args.source}'. Use 'skfp', 'url', or 'pubchem'.")
        sys.exit(1)

    # Keep only the required columns and enforce exact order
    # Some versions of the CSV use 'exp' as the target column; rename if needed
    if "logP" not in df.columns and "exp" in df.columns:
        df = df.rename(columns={"exp": "logP"})
    df = df[["smiles", "logP"]].copy()

    # ------------------------------------------------------------------
    # 2. Compute and record checksum of the raw CSV
    # ------------------------------------------------------------------
    if not raw_path.exists():
        # When using the skfp loader we need to persist the raw CSV
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(raw_path, index=False)
        logger.info(f"Wrote raw CSV to {raw_path}")

    checksum_path = Path("data/checksums.txt")
    append_checksum(raw_path, checksum_path)
    logger.info(f"Appended SHA‑256 checksum to {checksum_path}")

    # ------------------------------------------------------------------
    # 3. Schema validation
    # ------------------------------------------------------------------
    schema_path = Path(
        "specs/001-predicting-molecular-properties-from-top/contracts/dataset.schema.yaml"
    )
    if not validate_schema(df, schema_path):
        logger.error(
            "Schema validation failed: CSV does not contain exactly the required columns."
        )
        sys.exit(1)
    logger.info("Schema validation passed.")

    # ------------------------------------------------------------------
    # 4. Molecular‑weight filter (>1000 Da)
    # ------------------------------------------------------------------
    exclusion_log_path = Path("data/logs/large_molecule_exclusions.log")
    df, had_exclusions = verify_data_integrity_mw(df, exclusion_log_path)

    # ------------------------------------------------------------------
    # 5. Power analysis
    # ------------------------------------------------------------------
    power_report_path = Path(
        "data/processed/power_analysis_report.json"
    )
    perform_power_analysis(len(df), power_report_path)
    logger.info(f"Wrote power analysis report to {power_report_path}")

    # ------------------------------------------------------------------
    # 6. Scaffold count check
    # ------------------------------------------------------------------
    scaffold_count, scaffold_ok = check_scaffold_integrity(df, min_scaffolds=100)
    scaffold_counts_path = Path(
        "data/processed/scaffold_counts.json"
    )
    scaffold_counts_path.parent.mkdir(parents=True, exist_ok=True)
    scaffold_status = {
        "unique_scaffolds": scaffold_count,
        "min_required": 100,
        "status": "PASSED" if scaffold_ok else "FAILED",
    }
    with scaffold_counts_path.open("w") as f:
        json.dump(scaffold_status, f, indent=2)
    logger.info(f"Wrote scaffold counts to {scaffold_counts_path}")

    if not scaffold_ok:
        logger.error("Insufficient unique scaffolds; aborting.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 7. Write filtered dataset (exact schema columns only)
    # ------------------------------------------------------------------
    filtered_path = Path("data/processed/filtered_esol.csv")
    filtered_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_df = df[["smiles", "logP"]].copy()
    filtered_df.to_csv(filtered_path, index=False)
    logger.info(f"Wrote filtered dataset to {filtered_path}")

    # ------------------------------------------------------------------
    # 8. Generate scaffold‑based 5‑fold split
    # ------------------------------------------------------------------
    splits = stratified_scaffold_split(df, n_splits=5, seed=42)
    splits_path = Path("data/processed/splits.json")
    splits_path.parent.mkdir(parents=True, exist_ok=True)
    with splits_path.open("w") as f:
        json.dump({"splits": splits}, f, indent=2)
    logger.info(f"Wrote split indices to {splits_path}")

    logger.info("Data ingestion (T001) completed successfully.")

if __name__ == "__main__":
    main()
