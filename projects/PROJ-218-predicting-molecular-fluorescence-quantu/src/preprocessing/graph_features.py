"""
Graph Features Extraction Script
--------------------------------

This script reads a CSV file produced by the ``src.preprocessing.join`` step
(named ``joined.csv``) that contains at least a ``smiles`` column.  For each
SMILES string it:

1. Parses the SMILES into an RDKit ``Mol`` object.
2. Extracts node (atom) features:
   * atomic number
   * element symbol
   * hybridization (string)
   * formal charge
3. Extracts edge (bond) features:
   * start atom index
   * end atom index
   * bond type (string)
   * conjugation flag
4. Discards molecules that cannot be parsed, logging the SMILES string and
   a short reason to ``invalid_smiles.log``.
5. Writes a Parquet file where each row corresponds to a *valid* molecule.
   The row contains the original columns from ``joined.csv`` plus two new
   columns – ``node_features`` and ``edge_features`` – which store JSON
   strings representing the extracted feature dictionaries.

The script is deliberately lightweight and does not perform any stochastic
operation; it therefore does not need to re‑seed random number generators.

Usage
-----
The script can be invoked directly via the module interface used in the
quick‑start guide:

    python -m src.preprocessing.graph_features \
        --input data/processed/joined.csv \
        --output data/processed/graph_features.parquet \
        --log data/processed/invalid_smiles.log

The command above is the exact one requested by the CI runner (see the
``execute`` block in the task description).

Dependencies
------------
* ``pandas`` – for CSV/Parquet I/O.
* ``rdkit`` – for chemistry parsing.
* ``pyarrow`` – Parquet writer backend (installed via ``requirements.txt``).

All other imports are part of the standard library or the project’s
``llmxive_toolkit`` utilities.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional

import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdchem

# Project‑wide utilities
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# -------------------------------------------------------------------------
# Helper functions – these mirror the public API already declared in the
# source file (src/preprocessing/graph_features.py).  They are implemented
# here because the original stub only contained type signatures.
# -------------------------------------------------------------------------

def _smiles_to_mol(smiles: str) -> Optional[Chem.Mol]:
    """
    Convert a SMILES string to an RDKit Mol object.

    Returns ``None`` if the SMILES cannot be parsed.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        # Sanitise to catch chemically invalid structures
        Chem.SanitizeMol(mol)
        return mol
    except Exception:
        return None

def _extract_node_features(mol: Chem.Mol) -> List[dict]:
    """
    Extract atom‑level features from an RDKit Mol.

    Returns a list of dictionaries, one per atom.
    """
    features = []
    for atom in mol.GetAtoms():
        features.append(
            {
                "atom_num": atom.GetAtomicNum(),
                "symbol": atom.GetSymbol(),
                "hybridization": str(atom.GetHybridization()),
                "formal_charge": atom.GetFormalCharge(),
            }
        )
    return features

def _extract_edge_features(mol: Chem.Mol) -> List[dict]:
    """
    Extract bond‑level features from an RDKit Mol.

    Returns a list of dictionaries, one per bond.
    """
    features = []
    for bond in mol.GetBonds():
        features.append(
            {
                "begin_atom_idx": bond.GetBeginAtomIdx(),
                "end_atom_idx": bond.GetEndAtomIdx(),
                "bond_type": str(bond.GetBondType()),
                "is_conjugated": bond.GetIsConjugated(),
            }
        )
    return features

def _process_row(row: pd.Series) -> Tuple[Optional[dict], Optional[str]]:
    """
    Process a single dataframe row.

    Parameters
    ----------
    row: pd.Series
        Must contain a ``smiles`` column.

    Returns
    -------
    (features_dict, error_message)
        * ``features_dict`` – ``None`` if the SMILES is invalid,
          otherwise a dictionary with ``node_features`` and ``edge_features``.
        * ``error_message`` – ``None`` for successful rows, otherwise a short
          description of why parsing failed.
    """
    smiles = row.get("smiles")
    if not isinstance(smiles, str):
        return None, "SMILES column missing or not a string"

    mol = _smiles_to_mol(smiles)
    if mol is None:
        return None, "RDKit failed to parse SMILES"

    node_feats = _extract_node_features(mol)
    edge_feats = _extract_edge_features(mol)

    return {"node_features": node_feats, "edge_features": edge_feats}, None

# -------------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse SMILES → graph features and store as Parquet."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the joined CSV file (must contain a 'smiles' column).",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Destination Parquet file for the extracted graph features.",
    )
    parser.add_argument(
        "--log",
        required=False,
        type=Path,
        default=paths.data("processed", "invalid_smiles.log"),
        help="Path to the log file listing discarded SMILES strings.",
    )
    return parser

def main(argv: List[str] | None = None) -> int:
    """
    CLI driver for the graph‑feature extraction step.

    The function returns ``0`` on success and a non‑zero exit code on failure.
    """
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    # Ensure output directories exist
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.log.parent.mkdir(parents=True, exist_ok=True)

    # Set up a simple file logger for invalid SMILES
    file_handler = logging.FileHandler(args.log, mode="w")
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    invalid_logger = logging.getLogger("invalid_smiles")
    invalid_logger.setLevel(logging.INFO)
    invalid_logger.handlers.clear()
    invalid_logger.addHandler(file_handler)

    try:
        df = pd.read_csv(args.input)
    except Exception as e:
        log.error(f"Failed to read input CSV '{args.input}': {e}")
        return 1

    if "smiles" not in df.columns:
        log.error("Input CSV does not contain a required 'smiles' column.")
        return 1

    feature_rows = []
    for idx, row in df.iterrows():
        features, error = _process_row(row)
        if features is None:
            # Log the problematic SMILES and the reason
            smiles_val = row.get("smiles", "<MISSING>")
            invalid_logger.info(f"{smiles_val}\t{error}")
            continue

        # Merge the original row (excluding the SMILES column to avoid duplication)
        # with the extracted features.  The original columns are kept for downstream
        # use (e.g., target values, metadata).
        merged = row.to_dict()
        merged.update(features)
        feature_rows.append(merged)

    if not feature_rows:
        log.error("No valid SMILES were found – nothing to write.")
        return 1

    # Convert the list of dicts into a DataFrame.
    out_df = pd.DataFrame(feature_rows)

    # ``node_features`` and ``edge_features`` are lists of dicts; store them as
    # JSON strings so that Parquet can serialize them without special handling.
    out_df["node_features"] = out_df["node_features"].apply(json.dumps)
    out_df["edge_features"] = out_df["edge_features"].apply(json.dumps)

    try:
        out_df.to_parquet(args.output, engine="pyarrow", index=False)
    except Exception as e:
        log.error(f"Failed to write Parquet file '{args.output}': {e}")
        return 1

    log.info(
        f"Graph feature extraction complete: {len(feature_rows)} molecules written to '{args.output}'."
    )
    log.info(f"Invalid SMILES logged to '{args.log}'.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
