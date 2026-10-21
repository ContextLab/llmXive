"""
Preprocess the raw refractive‑index dataset.

This script reads ``data/raw/ri_dataset.csv`` (produced by ``data/download.py``),
parses SMILES strings with RDKit, filters out molecules with molecular weight
≥ 500 Da, applies temperature normalisation when a ``temperature`` column is
present, generates node and edge feature dictionaries, adds a
z‑score‑normalised global ``molecular_weight`` feature, and writes the
processed data to ``data/processed/filtered.csv``.

Usage:
    python data/preprocess.py

The script logs total rows, filtered rows, and excluded rows to
``logs/preprocess_summary.log`` and validates every output row against
``contracts/dataset.schema.yaml``.
"""

import json
import logging
from pathlib import Path

import pandas as pd
import yaml
from jsonschema import Draft7Validator, ValidationError
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
RAW_CSV_PATH = paths.data("raw", "ri_dataset.csv")
PROCESSED_DIR = paths.data("processed")
LOG_PATH = paths.root / "logs" / "preprocess_summary.log"

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

# ----------------------------------------------------------------------
# Main preprocessing routine
# ----------------------------------------------------------------------
def main() -> None:
    # Ensure log file exists
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)

    logger.info(f"Reading raw CSV from {RAW_CSV_PATH}")
    df_raw = pd.read_csv(RAW_CSV_PATH)

    total_records = len(df_raw)
    logger.info(f"Total records in raw dataset: {total_records}")

    # Apply temperature normalisation if needed
    if "temperature" in df_raw.columns:
        df_raw["refractive_index"] = df_raw.apply(temperature_normalize, axis=1)
        logger.info("Applied temperature normalisation using Edlén equation.")

    processed_rows = []
    excluded_count = 0

    for idx, row in df_raw.iterrows():
        smiles = row["smiles"]
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                raise ValueError("RDKit returned None")
        except Exception as exc:
            logger.error(f"SMILES parsing failed for index {idx}: {exc}")
            excluded_count += 1
            continue

        mw = Descriptors.ExactMolWt(mol)
        if mw >= 500.0:
            excluded_count += 1
            continue

        node_feats = compute_node_features(mol)
        edge_feats = compute_edge_features(mol)

        record = {
            "smiles": smiles,
            "molecular_weight": mw,
            "refractive_index": float(row["refractive_index"]),
            "node_features": json.dumps(node_feats),
            "edge_features": json.dumps(edge_feats),
        }
        processed_rows.append(record)

    filtered_records = len(processed_rows)
    logger.info(f"Records after filtering (MW < 500 Da): {filtered_records}")
    logger.info(f"Excluded records (parse errors or MW filter): {excluded_count}")

    df_processed = pd.DataFrame(processed_rows)

    # Add z‑score normalised molecular weight feature
    mw_mean = df_processed["molecular_weight"].mean()
    mw_std = df_processed["molecular_weight"].std(ddof=0)
    if mw_std == 0:
        # Avoid division by zero – all values identical (unlikely)
        df_processed["molecular_weight_z"] = 0.0
    else:
        df_processed["molecular_weight_z"] = (df_processed["molecular_weight"] - mw_mean) / mw_std

    # ------------------------------------------------------------------
    # Validate against schema
    # ------------------------------------------------------------------
    schema = load_schema()
    validator = Draft7Validator(schema)

    for idx, row in df_processed.iterrows():
        record = {
            "smiles": row["smiles"],
            "molecular_weight": row["molecular_weight"],
            "refractive_index": row["refractive_index"],
            "node_features": json.loads(row["node_features"]),
            "edge_features": json.loads(row["edge_features"]),
        }
        validate_row(record, validator)

    # ------------------------------------------------------------------
    # Write CSV
    # ------------------------------------------------------------------
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / "filtered.csv"
    df_processed.to_csv(output_path, index=False)
    logger.info(f"Wrote filtered dataset to {output_path}")

    # Also log a short summary to console
    log.info(f"Preprocessing completed: {filtered_records} rows kept, {excluded_count} rows excluded.")

if __name__ == "__main__":
    main()
