"""
Feature Engineering Pipeline (T004)

Computes RDKit-based traditional descriptors (MW, atom counts, 1024-bit Morgan
fingerprint radius 2) and merges them with the TDA persistence images from
``data/processed/topological_features_10x10.csv`` to create the final combined
feature matrix.

Requirements:
- Traditional descriptors: MW, atom counts (C, N, O, S, P, Halogens),
  1024-bit Morgan Fingerprint (radius 2).
- Merge on 'molecule_id' (both sides cast to string before merging).
- Output:
  * data/processed/traditional_features.csv
  * data/processed/combined_features.csv
  * durable copies under data/results/ (not gitignored) for reviewers.
- Ensure no missing values.
- Row counts of TDA, Traditional, and Combined matrices must match.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, AllChem

# Project-relative paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"

TDA_FEATURES_PATH = PROCESSED_DIR / "topological_features_10x10.csv"


def setup_logging() -> logging.Logger:
    """Configure logging for the feature engineering pipeline."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("feature_engineering")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # File handler
        fh = logging.FileHandler(LOGS_DIR / "feature_engineering.log")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Stream handler
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    return logger


def compute_traditional_descriptors(
    df_filtered: pd.DataFrame,
    valid_ids: List[str],
    logger: logging.Logger,
) -> pd.DataFrame:
    """
    Compute traditional molecular descriptors for a specific set of molecule IDs.

    Includes:
    - Molecular Weight
    - Atom counts (C, N, O, S, P, Halogens)
    - 1024-bit Morgan Fingerprint (radius 2)
    """
    logger.info(f"Computing traditional descriptors for {len(valid_ids)} molecules...")

    # Filter to only valid IDs to ensure row count match with TDA features
    df_filtered = df_filtered.copy()
    df_filtered["molecule_id"] = df_filtered["molecule_id"].astype(str)
    valid_ids = [str(i) for i in valid_ids]
    df = df_filtered[df_filtered["molecule_id"].isin(valid_ids)].copy()

    records = []
    for _, row in df.iterrows():
        mol_id = row["molecule_id"]
        smiles = row["smiles"]
        mol = Chem.MolFromSmiles(smiles)

        if mol is None:
            logger.warning(f"RDKit failed to parse SMILES for {mol_id}: {smiles}")
            continue

        # 1. Molecular Weight
        mw = Descriptors.MolWt(mol)

        # 2. Atom Counts
        counts = {}
        for symbol in ["C", "N", "O", "S", "P"]:
            counts[f"atom_count_{symbol}"] = sum(
                1 for atom in mol.GetAtoms() if atom.GetSymbol() == symbol
            )
        # Halogens (F, Cl, Br, I)
        counts["atom_count_Hal"] = sum(
            1 for atom in mol.GetAtoms() if atom.GetSymbol() in ["F", "Cl", "Br", "I"]
        )

        # 3. Morgan Fingerprint (1024-bit, radius 2)
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=1024)
        fp_list = list(fp)
        fp_dict = {f"morgan_{i}": val for i, val in enumerate(fp_list)}

        # Combine all
        record = {"molecule_id": mol_id, "MW": mw}
        record.update(counts)
        record.update(fp_dict)
        records.append(record)

    out = pd.DataFrame(records)
    out["molecule_id"] = out["molecule_id"].astype(str)
    return out


def load_tda_features(logger: logging.Logger) -> pd.DataFrame:
    """Load TDA feature vectors from data/processed/topological_features_10x10.csv."""
    if not TDA_FEATURES_PATH.exists():
        logger.error(
              f"TDA features missing at {TDA_FEATURES_PATH}. "
              "Run 02_tda_computation.py --grid 10 first."
        )
        raise SystemExit(1)

    df = pd.read_csv(TDA_FEATURES_PATH)
    df["molecule_id"] = df["molecule_id"].astype(str)
    logger.info(f"Loaded TDA features: {len(df)} molecules from {TDA_FEATURES_PATH.name}.")

    # Keep only the numeric pixel features (drop JSON-string columns such as
    # 'features'/'feature_names' and the constant 'target_property' string,
    # which would break downstream numeric model training).
    pixel_cols = [c for c in df.columns if c.startswith("pixel_")]
    if not pixel_cols:
        pixel_cols = [c for c in df.columns if c.startswith("img_")]
    if not pixel_cols:
        logger.error(
            "No pixel_/img_ feature columns found in the TDA feature matrix."
        )
        raise SystemExit(1)

    keep = ["molecule_id"] + pixel_cols
    df = df[keep].copy()
    df[pixel_cols] = df[pixel_cols].astype(float)
    return df


def merge_features(
    traditional_df: pd.DataFrame,
    tda_df: pd.DataFrame,
    target_df: pd.DataFrame,
    logger: logging.Logger,
) -> pd.DataFrame:
    """
    Merge traditional descriptors, TDA features, and target values on 'molecule_id'.
    All molecule_id columns are cast to string before merging (type safety).
    """
    logger.info("Merging feature sets...")

    traditional_df = traditional_df.copy()
    tda_df = tda_df.copy()
    target_df = target_df.copy()
    traditional_df["molecule_id"] = traditional_df["molecule_id"].astype(str)
    tda_df["molecule_id"] = tda_df["molecule_id"].astype(str)
    target_df["molecule_id"] = target_df["molecule_id"].astype(str)

    # Merge Traditional and TDA
    merged = pd.merge(traditional_df, tda_df, on="molecule_id", how="inner")

    # Merge with targets (filtered_esol) to get logP
    merged = pd.merge(
        merged,
        target_df[["molecule_id", "logP"]],
        on="molecule_id",
        how="inner",
    )
    merged["logP"] = merged["logP"].astype(float)

    # Reorder: molecule_id, logP, then features
    cols = ["molecule_id", "logP"] + [
        c for c in merged.columns if c not in ["molecule_id", "logP"]
    ]
    merged = merged[cols]

    logger.info(f"Final merged matrix shape: {merged.shape}")
    return merged


def run_feature_engineering() -> None:
    """Orchestration for T004."""
    logger = setup_logging()
    logger.info("Starting Feature Engineering (T004)...")

    # 1. Load filtered dataset
    filtered_path = PROCESSED_DIR / "filtered_esol.csv"
    if not filtered_path.exists():
        logger.error(
            f"Filtered dataset missing at {filtered_path}. Run 01_data_ingestion.py first."
        )
        sys.exit(1)

    df_filtered = pd.read_csv(filtered_path)
    if "molecule_id" not in df_filtered.columns:
        df_filtered["molecule_id"] = df_filtered.index.astype(str)
    df_filtered["molecule_id"] = df_filtered["molecule_id"].astype(str)

    # Load TDA features to determine the set of successfully processed molecules
    df_tda = load_tda_features(logger)
    valid_ids = df_tda["molecule_id"].tolist()

    # 2. Compute Traditional Descriptors for those valid IDs
    df_trad = compute_traditional_descriptors(df_filtered, valid_ids, logger)

    # Save traditional descriptors using the name required by the specification
    trad_output_path = PROCESSED_DIR / "traditional_features.csv"
    df_trad.to_csv(trad_output_path, index=False)
    logger.info(
        f"Saved traditional descriptors to {trad_output_path} ({len(df_trad)} rows)."
    )

    # 3. Merge into Combined Matrix
    df_combined = merge_features(df_trad, df_tda, df_filtered, logger)

    # 4. Validation: Check for NaNs and Row Counts
    nan_count = df_combined.isnull().sum().sum()
    if nan_count > 0:
        logger.error(f"Combined matrix contains {nan_count} NaNs!")
        sys.exit(1)

    # Verify row counts match
    if not (len(df_trad) == len(df_tda) == len(df_combined)):
        logger.error(
            f"Row count mismatch: Trad({len(df_trad)}), TDA({len(df_tda)}), "
            f"Combined({len(df_combined)})"
        )
        sys.exit(1)

    logger.info("Verification passed: Row counts match and no missing values.")

    # 5. Save Combined Features
    combined_output_path = PROCESSED_DIR / "combined_features.csv"
    df_combined.to_csv(combined_output_path, index=False)
    logger.info(f"Saved combined feature matrix to {combined_output_path}")

    # 6. Durable (non-gitignored) copies + summary for reviewers
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df_trad.to_csv(RESULTS_DIR / "traditional_features.csv", index=False)
    df_combined.to_csv(RESULTS_DIR / "combined_features.csv", index=False)

    pixel_cols = [c for c in df_combined.columns if c.startswith("pixel_")]
    trad_cols = [
        c for c in df_combined.columns
        if c not in ["molecule_id", "logP"] and not c.startswith("pixel_")
    ]
    summary = {
        "task": "T004",
        "n_molecules": int(len(df_combined)),
        "n_traditional_features": len(trad_cols),
        "n_topological_features": len(pixel_cols),
        "n_total_features": len(trad_cols) + len(pixel_cols),
        "nan_count": int(df_combined.isnull().sum().sum()),
        "row_counts_match": bool(
            len(df_trad) == len(df_tda) == len(df_combined)
        ),
        "target_property": "logP",
        "logp_mean": float(df_combined["logP"].mean()),
        "logp_std": float(df_combined["logP"].std()),
        "durable_copies": [
            "data/results/traditional_features.csv",
            "data/results/combined_features.csv",
        ],
    }
    with (RESULTS_DIR / "feature_engineering_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Wrote durable summary to data/results/feature_engineering_summary.json")

    logger.info("Feature Engineering (T004) completed successfully.")


def main() -> None:
    try:
        run_feature_engineering()
    except SystemExit:
        raise
    except Exception as e:
        logging.getLogger("feature_engineering").exception(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()