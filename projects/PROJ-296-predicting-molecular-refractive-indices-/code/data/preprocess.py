"""
Preprocess the raw refractive‑index dataset.

This script reads ``data/raw/ri_dataset.csv`` (produced by ``data/download.py``),
parses SMILES strings with RDKit, filters out molecules with molecular weight
≥ 500 Da, applies temperature normalisation when a ``temperature`` column is
present, generates node and edge feature dictionaries, adds a global molecular
weight feature, performs a scaffold‑based split (80 % train / 10 % val /
10 % test) with zero scaffold overlap, and writes the three CSV files to
``data/processed/``.

Usage:
    python data/preprocess.py --filter-mw 500 --split-ratio 0.8,0.1,0.1

The script logs counts of total, filtered, and excluded molecules to
``logs/preprocess.log`` and validates every output row against
``contracts/dataset.schema.yaml``.
"""

import argparse
import json
import random
from pathlib import Path

import pandas as pd
import yaml
from jsonschema import Draft7Validator, ValidationError
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
RAW_CSV_PATH = paths.data("raw", "ri_dataset.csv")
PROCESSED_DIR = paths.data("processed")
LOG_PATH = paths.root / "logs" / "preprocess.log"

SCHEMA_PATH = Path(paths.root) / "contracts" / "dataset.schema.yaml"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_schema():
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_row(record: dict, validator: Draft7Validator):
    try:
        validator.validate(record)
    except ValidationError as exc:
        raise ValueError(f"Schema validation error: {exc.message}")

def temperature_normalize(row: pd.Series) -> float:
    """
    Apply a simple linear temperature correction (Edlén equation) to
    refractive index values when a ``temperature`` column is present.
    The coefficient is set to -0.0001 RI / K (typical for organic liquids).
    """
    n = row["refractive_index"]
    if "temperature" in row and pd.notnull(row["temperature"]):
        coeff = -0.0001  # dn/dT approx.
        n20 = n + coeff * (row["temperature"] - 20.0)
        return n20
    return n

def compute_node_features(mol: Chem.Mol) -> list[dict]:
    feats = []
    for atom in mol.GetAtoms():
        hybrid = atom.GetHybridization()
        hybrid_str = {
            Chem.HybridizationType.SP: "SP",
            Chem.HybridizationType.SP2: "SP2",
            Chem.HybridizationType.SP3: "SP3",
        }.get(hybrid, "UNSPECIFIED")
        feats.append(
            {
                "atomic_num": atom.GetAtomicNum(),
                "degree": atom.GetDegree(),
                "hybridization": hybrid_str,
                "is_aromatic": atom.GetIsAromatic(),
            }
        )
    return feats

def compute_edge_features(mol: Chem.Mol) -> list[dict]:
    feats = []
    for bond in mol.GetBonds():
        bond_type = {
            Chem.BondType.SINGLE: "SINGLE",
            Chem.BondType.DOUBLE: "DOUBLE",
            Chem.BondType.TRIPLE: "TRIPLE",
            Chem.BondType.AROMATIC: "AROMATIC",
        }.get(bond.GetBondType(), "SINGLE")
        stereo = {
            Chem.BondStereo.STEREONONE: "NONE",
            Chem.BondStereo.STEREOANY: "STEREOANY",
            Chem.BondStereo.STEREOZ: "STEREOZ",
            Chem.BondStereo.STEREOE: "STEREOE",
        }.get(bond.GetStereo(), "NONE")
        feats.append(
            {
                "bond_type": bond_type,
                "is_conjugated": bond.GetIsConjugated(),
                "stereo": stereo,
            }
        )
    return feats

def get_scaffold_id(mol: Chem.Mol) -> str:
    scaffold = rdMolDescriptors.GetScaffoldForMol(mol)
    return Chem.MolToSmiles(scaffold, isomericSmiles=True)

# ----------------------------------------------------------------------
# Main preprocessing routine
# ----------------------------------------------------------------------
def main(filter_mw: float, split_ratio: tuple[float, float, float]) -> None:
    # Ensure log file exists
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_handler = open(LOG_PATH, "w")
    file_handler.close()

    log.info(f"Reading raw CSV from {RAW_CSV_PATH}")
    df_raw = pd.read_csv(RAW_CSV_PATH)

    total_records = len(df_raw)
    log.info(f"Total records in raw dataset: {total_records}")

    # Apply temperature normalisation
    if "temperature" in df_raw.columns:
        df_raw["refractive_index"] = df_raw.apply(
            temperature_normalize, axis=1
        )
        log.info("Applied temperature normalisation using Edlén equation.")

    # Parse SMILES, filter by molecular weight
    processed_rows = []
    excluded_count = 0
    for idx, row in df_raw.iterrows():
        smiles = row["smiles"]
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                raise ValueError("RDKit returned None")
        except Exception as exc:
            log.error(f"SMILES parsing failed for index {idx}: {exc}")
            excluded_count += 1
            continue

        mw = Chem.Descriptors.ExactMolWt(mol)
        if mw >= filter_mw:
            excluded_count += 1
            continue

        node_feats = compute_node_features(mol)
        edge_feats = compute_edge_features(mol)
        scaffold_id = get_scaffold_id(mol)

        record = {
            "smiles": smiles,
            "molecular_weight": mw,
            "refractive_index": float(row["refractive_index"]),
            "node_features": json.dumps(node_feats),
            "edge_features": json.dumps(edge_feats),
            "scaffold_id": scaffold_id,
        }
        processed_rows.append(record)

    filtered_records = len(processed_rows)
    log.info(f"Records after filtering (MW < {filter_mw} Da): {filtered_records}")
    log.info(f"Excluded records (parse errors or MW filter): {excluded_count}")

    # Convert to DataFrame
    df_processed = pd.DataFrame(processed_rows)

    # ------------------------------------------------------------------
    # Scaffold‑based split with zero overlap
    # ------------------------------------------------------------------
    train_ratio, val_ratio, test_ratio = split_ratio
    scaffold_to_indices = {}
    for idx, scaffold in enumerate(df_processed["scaffold_id"]):
        scaffold_to_indices.setdefault(scaffold, []).append(idx)

    scaffolds = list(scaffold_to_indices.keys())
    random.shuffle(scaffolds)

    n_total = len(df_processed)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    train_idxs, val_idxs, test_idxs = [], [], []

    for scaffold in scaffolds:
        indices = scaffold_to_indices[scaffold]
        if len(train_idxs) + len(indices) <= n_train:
            train_idxs.extend(indices)
        elif len(val_idxs) + len(indices) <= n_val:
            val_idxs.extend(indices)
        else:
            test_idxs.extend(indices)

    df_train = df_processed.iloc[train_idxs].reset_index(drop=True)
    df_val = df_processed.iloc[val_idxs].reset_index(drop=True)
    df_test = df_processed.iloc[test_idxs].reset_index(drop=True)

    log.info(f"Split sizes -> train: {len(df_train)}, val: {len(df_val)}, test: {len(df_test)}")

    # ------------------------------------------------------------------
    # Validate against schema
    # ------------------------------------------------------------------
    schema = load_schema()
    validator = Draft7Validator(schema)

    for split_name, split_df in [("train", df_train), ("val", df_val), ("test", df_test)]:
        for idx, row in split_df.iterrows():
            record = json.loads(
                json.dumps(
                    {
                        "smiles": row["smiles"],
                        "molecular_weight": row["molecular_weight"],
                        "refractive_index": row["refractive_index"],
                        "node_features": json.loads(row["node_features"]),
                        "edge_features": json.loads(row["edge_features"]),
                        "scaffold_id": row["scaffold_id"],
                    }
                )
            )
            validate_row(record, validator)

    # ------------------------------------------------------------------
    # Write CSVs
    # ------------------------------------------------------------------
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df_train.to_csv(PROCESSED_DIR / "train.csv", index=False)
    df_val.to_csv(PROCESSED_DIR / "val.csv", index=False)
    df_test.to_csv(PROCESSED_DIR / "test.csv", index=False)

    log.info(f"Wrote processed splits to {PROCESSED_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Preprocess raw RI dataset and create train/val/test splits."
    )
    parser.add_argument(
        "--filter-mw",
        type=float,
        default=500.0,
        help="Molecular weight cutoff (Da). Molecules with MW >= this value are excluded.",
    )
    parser.add_argument(
        "--split-ratio",
        type=str,
        default="0.8,0.1,0.1",
        help="Comma‑separated train,val,test ratios (must sum to 1).",
    )
    args = parser.parse_args()
    ratios = tuple(map(float, args.split_ratio.split(",")))
    if len(ratios) != 3 or not abs(sum(ratios) - 1.0) < 1e-6:
        raise ValueError("split-ratio must contain three numbers that sum to 1")
    main(filter_mw=args.filter_mw, split_ratio=ratios)
