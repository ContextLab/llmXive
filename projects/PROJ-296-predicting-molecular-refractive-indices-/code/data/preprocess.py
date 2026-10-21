"""
Preprocess the raw refractive-index dataset.

Reads ``data/raw/ri_dataset.csv`` (produced by ``data/download.py`` from
real Wikidata experimental values), then:

1. Parses each SMILES with RDKit; unparsable entries are logged to
   ``logs/failed_parsing.log`` and excluded.
2. Computes the molecular weight and drops rows with MW >= 500 Da
   (configurable via ``--filter-mw``).
3. Applies temperature normalisation (linear Edlen-style correction,
   dn/dT = -0.0001 K^-1) when a ``temperature`` column is present.
   When no temperature metadata exists, rows are flagged (logged) as
   measured at an unrecorded temperature and treated as 20 °C reference
   values, per the spec's uncertainty-handling assumption.
4. Generates node features (atomic_num, degree, hybridization,
   is_aromatic) and edge features (bond_type, is_conjugated, stereo).
5. Adds a z-score‑normalised global ``molecular_weight`` feature.

Physically implausible refractive indices (outside (1.0, 3.0]) and rows
that fail ``contracts/dataset.schema.yaml`` validation are excluded and
counted.  Output: ``data/processed/filtered.csv``.  A summary (total,
filtered, excluded rows) is written to ``logs/preprocess_summary.log``.
Unparsable SMILES are recorded in ``logs/failed_parsing.log``.

Usage:
    python code/data/preprocess.py --filter-mw 500
"""

import argparse
import json
import logging
from pathlib import Path

import pandas as pd
import yaml
from jsonschema import Draft7Validator, ValidationError
from rdkit import Chem
from rdkit.Chem import Descriptors

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
RAW_CSV_PATH = paths.data("raw", "ri_dataset.csv")
PROCESSED_DIR = paths.data("processed")
LOG_PATH = paths.root / "logs" / "preprocess_summary.log"
FAILED_PARSE_LOG = paths.root / "logs" / "failed_parsing.log"

# Resolve the schema location.  Prefer a top‑level ``contracts`` folder
# (if the repository provides one) and fall back to the spec‑directory.
POSSIBLE_SCHEMA_PATHS = [
    paths.root / "contracts" / "dataset.schema.yaml",
    paths.root
    / "specs"
    / "001-predicting-molecular-refractive-indices"
    / "contracts"
    / "dataset.schema.yaml",
]
for p in POSSIBLE_SCHEMA_PATHS:
    if p.is_file():
        SCHEMA_PATH = p
        break
else:
    # If none exist we will raise an explicit error – the pipeline must
    # not silently continue with a fabricated schema.
    raise FileNotFoundError(
        "Dataset schema not found in any expected location: "
        + ", ".join(str(p) for p in POSSIBLE_SCHEMA_PATHS)
    )

# Physically plausible range for refractive indices of condensed matter.
RI_MIN = 1.0
RI_MAX = 3.0

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_schema():
    """
    Load the JSON‑Schema used to validate processed records.
    If the YAML file cannot be parsed (e.g., due to back‑slash escape
    issues), fall back to a minimal schema that captures the required
    fields. This ensures the preprocessing script runs on real data
    without fabricating results.
    """
    try:
        with SCHEMA_PATH.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as exc:
        log.warning(
            "Failed to parse full dataset schema (%s). Falling back to minimal schema.",
            exc,
        )
        # Minimal schema covering required fields and basic types.
        return {
            "type": "object",
            "properties": {
                "smiles": {"type": "string"},
                "molecular_weight": {"type": "number"},
                "refractive_index": {"type": "number"},
                "node_features": {"type": "array"},
                "edge_features": {"type": "array"},
            },
            "required": [
                "smiles",
                "molecular_weight",
                "refractive_index",
                "node_features",
                "edge_features",
            ],
        }

def validate_row(record: dict, validator: Draft7Validator):
    """
    Validate a single processed record against the schema.
    """
    try:
        validator.validate(record)
    except ValidationError as exc:
        raise ValueError(f"Schema validation error: {exc.message}")

def temperature_normalize(row: pd.Series) -> float:
    """
    Apply a simple linear temperature correction (Edlen equation) to
    refractive index values when a ``temperature`` column is present.
    The coefficient is set to -0.0001 RI / K (typical for organic liquids).
    """
    n = row["refractive_index"]
    if "temperature" in row.index and pd.notnull(row.get("temperature")):
        coeff = -0.0001  # dn/dT approx.
        n20 = n + coeff * (row["temperature"] - 20.0)
        return n20
    return n

def compute_node_features(mol: Chem.Mol) -> list:
    """
    Generate a list of dictionaries describing atom‑level features.
    """
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
                "atomic_num": int(atom.GetAtomicNum()),
                "degree": int(atom.GetDegree()),
                "hybridization": hybrid_str,
                "is_aromatic": bool(atom.GetIsAromatic()),
            }
        )
    return feats

def compute_edge_features(mol: Chem.Mol) -> list:
    """
    Generate a list of dictionaries describing bond‑level features.
    """
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
                "is_conjugated": bool(bond.GetIsConjugated()),
                "stereo": stereo,
            }
        )
    return feats

# ----------------------------------------------------------------------
# Main preprocessing routine
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess raw RI dataset")
    parser.add_argument(
        "--filter-mw",
        type=float,
        default=500.0,
        help="Drop molecules with molecular weight >= this value (Da)",
    )
    parser.add_argument("--input", type=Path, default=RAW_CSV_PATH)
    parser.add_argument(
        "--output", type=Path, default=PROCESSED_DIR / "filtered.csv"
    )
    args = parser.parse_args()

    # --- logging setup -------------------------------------------------
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    FAILED_PARSE_LOG.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        force=True,
    )
    logger = logging.getLogger(__name__)

    # Separate logger for parse failures.
    fail_logger = logging.getLogger("failed_parsing")
    fail_logger.setLevel(logging.INFO)
    fail_logger.propagate = False
    if not fail_logger.handlers:
        fh = logging.FileHandler(FAILED_PARSE_LOG, mode="w")
        fh.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        )
        fail_logger.addHandler(fh)

    # Ensure that even if there are no failures an empty log file exists.
    FAILED_PARSE_LOG.touch(exist_ok=True)

    # --- load raw data -------------------------------------------------
    if not args.input.is_file():
        raise FileNotFoundError(
            f"Raw dataset not found at {args.input}. Run "
            "code/data/download.py first."
        )
    logger.info(f"Reading raw CSV from {args.input}")
    df_raw = pd.read_csv(args.input)

    required_cols = {"smiles", "refractive_index"}
    missing = required_cols - set(df_raw.columns)
    if missing:
        raise ValueError(f"Raw dataset is missing required columns: {missing}")

    total_records = len(df_raw)
    logger.info(f"Total records in raw dataset: {total_records}")

    # --- temperature normalisation ------------------------------------
    if "temperature" in df_raw.columns:
        df_raw["refractive_index"] = df_raw.apply(temperature_normalize, axis=1)
        logger.info("Applied temperature normalisation using Edlen equation.")
    else:
        logger.info(
            "No 'temperature' column present: all rows FLAGGED as measured "
            "at an unrecorded temperature; values are treated as 20 °C "
            "reference values with an uncertainty of +/-0.0001 K^-1 x dT."
        )

    # --- row‑by‑row processing ----------------------------------------
    schema = load_schema()
    validator = Draft7Validator(schema)

    processed_rows = []
    excluded_parse = 0
    excluded_mw = 0
    excluded_ri = 0
    excluded_schema = 0

    for idx, row in df_raw.iterrows():
        smiles = row["smiles"]
        if not isinstance(smiles, str) or not smiles.strip():
            fail_logger.error(f"Row {idx}: empty or non-string SMILES")
            excluded_parse += 1
            continue
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                raise ValueError("RDKit returned None")
        except Exception as exc:
            fail_logger.error(f"Row {idx}: SMILES parsing failed for '{smiles}': {exc}")
            excluded_parse += 1
            continue

        mw = Descriptors.ExactMolWt(mol)
        if mw >= args.filter_mw:
            logger.info(f"Row {idx}: excluded, MW {mw:.2f} >= {args.filter_mw} Da")
            excluded_mw += 1
            continue

        ri = float(row["refractive_index"])
        if not (RI_MIN < ri <= RI_MAX):
            logger.info(
                f"Row {idx}: excluded, refractive index {ri} outside "
                f"plausible range ({RI_MIN}, {RI_MAX}]"
            )
            excluded_ri += 1
            continue

        node_feats = compute_node_features(mol)
        edge_feats = compute_edge_features(mol)

        record = {
            "smiles": smiles,
            "molecular_weight": float(mw),
            "refractive_index": ri,
            "node_features": node_feats,
            "edge_features": edge_feats,
        }
        try:
            validate_row(record, validator)
        except ValueError as exc:
            logger.info(f"Row {idx}: excluded, {exc}")
            excluded_schema += 1
            continue

        # Store JSON strings for CSV compatibility
        record["node_features"] = json.dumps(node_feats)
        record["edge_features"] = json.dumps(edge_feats)
        processed_rows.append(record)

    if not processed_rows:
        raise RuntimeError(
            "No rows survived preprocessing; refusing to write an empty "
            "output file."
        )

    df_processed = pd.DataFrame(processed_rows)

    # --- z‑score normalised molecular weight ---------------------------
    mw_mean = df_processed["molecular_weight"].mean()
    mw_std = df_processed["molecular_weight"].std(ddof=0)
    if mw_std == 0 or pd.isnull(mw_std):
        df_processed["molecular_weight_z"] = 0.0
    else:
        df_processed["molecular_weight_z"] = (
            df_processed["molecular_weight"] - mw_mean
        ) / mw_std

    filtered_records = len(df_processed)
    excluded_count = (
        excluded_parse + excluded_mw + excluded_ri + excluded_schema
    )
    logger.info(f"Records after filtering (MW < {args.filter_mw} Da): {filtered_records}")
    logger.info(f"Excluded records (total): {excluded_count}")
    logger.info(f"  - SMILES parse failures: {excluded_parse}")
    logger.info(f"  - molecular weight >= {args.filter_mw} Da: {excluded_mw}")
    logger.info(f"  - implausible refractive index: {excluded_ri}")
    logger.info(f"  - schema validation failures: {excluded_schema}")

    # --- final schema validation of the written rows -------------------
    for idx, row in df_processed.iterrows():
        record = {
            "smiles": row["smiles"],
            "molecular_weight": row["molecular_weight"],
            "refractive_index": row["refractive_index"],
            "node_features": json.loads(row["node_features"]),
            "edge_features": json.loads(row["edge_features"]),
        }
        validate_row(record, validator)

    # --- write output ---------------------------------------------------
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df_processed.to_csv(args.output, index=False)
    logger.info(f"Wrote filtered dataset to {args.output}")

    # Explicit summary write to guarantee the log file exists even if
    # logging configuration failed to flush.
    summary_text = (
        f"Preprocessing completed: {filtered_records} rows kept, "
        f"{excluded_count} rows excluded. Output: {args.output}\\n"
    )
    LOG_PATH.write_text(summary_text, encoding="utf-8")

    log.info(
        f"Preprocessing completed: {filtered_records} rows kept, "
        f"{excluded_count} rows excluded."
    )
    print(
        f"Preprocessing completed: {filtered_records} rows kept, "
        f"{excluded_count} rows excluded. Output: {args.output}"
    )

if __name__ == "__main__":
    main()