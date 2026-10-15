"""
T003 – Graph feature extraction

This script reads a CSV file that contains at least a ``smiles`` column,
parses each SMILES string with RDKit, extracts node and edge features,
discards invalid SMILES (logging them), and writes the resulting data
to a Parquet file.

The output Parquet file contains the original columns plus two new
columns:
  * ``node_features`` – a list of dictionaries, one per atom.
  * ``edge_features`` – a list of dictionaries, one per bond.

Invalid SMILES are written (one per line) to ``invalid_smiles.log`` in
the same directory as the output file.
"""

import argparse
import logging
from pathlib import Path
import pandas as pd

from rdkit import Chem
from rdkit.Chem import rdchem

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def _smiles_to_mol(smiles: str) -> Chem.Mol | None:
    """Convert a SMILES string to an RDKit Mol.

    Returns ``None`` if the SMILES cannot be parsed.
    """
    if not isinstance(smiles, str):
        return None
    mol = Chem.MolFromSmiles(smiles)
    return mol


def _extract_node_features(mol: Chem.Mol) -> list[dict]:
    """Extract atom‑level features from a Mol.

    Features:
      * ``atom_num`` – atomic number (int)
      * ``symbol`` – element symbol (str)
      * ``hybridization`` – string representation of hybridization
      * ``formal_charge`` – formal charge (int)
    """
    nodes = []
    for atom in mol.GetAtoms():
        nodes.append(
            {
                "atom_num": atom.GetAtomicNum(),
                "symbol": atom.GetSymbol(),
                "hybridization": str(atom.GetHybridization()),
                "formal_charge": atom.GetFormalCharge(),
            }
        )
    return nodes


def _extract_edge_features(mol: Chem.Mol) -> list[dict]:
    """Extract bond‑level features from a Mol.

    Features:
      * ``begin_atom_idx`` – index of the start atom (int)
      * ``end_atom_idx`` – index of the end atom (int)
      * ``bond_type`` – string representation of bond type
      * ``is_conjugated`` – bool indicating conjugation
    """
    edges = []
    for bond in mol.GetBonds():
        edges.append(
            {
                "begin_atom_idx": bond.GetBeginAtomIdx(),
                "end_atom_idx": bond.GetEndAtomIdx(),
                "bond_type": str(bond.GetBondType()),
                "is_conjugated": bond.GetIsConjugated(),
            }
        )
    return edges


def _process_row(row: pd.Series) -> tuple[dict | None, str | None]:
    """Process a single DataFrame row.

    Returns a tuple ``(features_dict, error_message)`` where
    ``features_dict`` is ``None`` for invalid SMILES.
    """
    smiles = row.get("smiles")
    mol = _smiles_to_mol(smiles)
    if mol is None:
        return None, f"Invalid SMILES: {smiles!r}"
    node_feats = _extract_node_features(mol)
    edge_feats = _extract_edge_features(mol)
    return {"node_features": node_feats, "edge_features": edge_feats}, None


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI.

    Arguments
    ----------
    argv : list of str, optional
        Command‑line arguments; if ``None`` the arguments are taken from
        ``sys.argv`` (default behaviour of ``argparse``).

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    parser = argparse.ArgumentParser(
        description="Parse SMILES, extract graph features, and write a Parquet file."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the CSV file that contains a ``smiles`` column.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path where the Parquet file with graph features will be written.",
    )
    args = parser.parse_args(argv)

    input_path: Path = args.input
    output_path: Path = args.output

    if not input_path.is_file():
        logger.error("Input CSV file does not exist: %s", input_path)
        return 1

    # Ensure the parent directory for the output exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare log file for invalid SMILES
    log_path = output_path.parent / "invalid_smiles.log"
    if log_path.exists():
        log_path.unlink()  # start fresh for each run

    logger.info("Reading input CSV: %s", input_path)
    df = pd.read_csv(input_path)

    if "smiles" not in df.columns:
        logger.error("Required column ``smiles`` not found in input CSV.")
        return 1

    feature_rows = []
    invalid_count = 0

    logger.info("Processing %d rows...", len(df))
    for idx, row in df.iterrows():
        features, error = _process_row(row)
        if error is not None:
            invalid_count += 1
            with log_path.open("a") as log_f:
                log_f.write(f"{error}\n")
            continue

        # Merge the original row with the extracted features
        merged = row.to_dict()
        merged.update(features)  # adds node_features & edge_features
        feature_rows.append(merged)

    logger.info("Finished processing. Valid molecules: %d, Invalid SMILES: %d",
                len(feature_rows), invalid_count)

    if not feature_rows:
        logger.error("No valid SMILES were found – nothing to write.")
        return 1

    # Create a DataFrame from the processed rows
    out_df = pd.DataFrame(feature_rows)

    # Write to Parquet (using pyarrow)
    logger.info("Writing Parquet output to %s", output_path)
    out_df.to_parquet(output_path, engine="pyarrow", index=False)

    logger.info("Graph feature extraction completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
