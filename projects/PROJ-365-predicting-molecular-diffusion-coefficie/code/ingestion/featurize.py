"""
featurize.py
--------------

This module implements the feature extraction step for the diffusion‑coefficient
prediction pipeline (US1).  It reads the raw CSV produced by the ingestion step,
converts each SMILES string into a ``torch_geometric.data.Data`` object (the
``MoleculeGraph``) and extracts a minimal solvent descriptor (viscosity and
dielectric constant) from the same row.

The resulting records are written line‑by‑line as JSON to
``data/processed/featurized.jsonl``.  Each JSON line has the shape::

    {
        "id": "<original row identifier>",
        "graph": {
            "x": [<atomic numbers ...>],
            "edge_index": [[src1, dst1], [src2, dst2], ...]
        },
        "solvent": {
            "viscosity": <float>,
            "dielectric_constant": <float>
        }
    }

Invalid SMILES strings or rows missing required solvent information are
skipped and the incident is logged using the project's logging utilities.
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Any

import torch
from torch_geometric.data import Data

from rdkit import Chem

# Project utilities
from utils.config import get_project_root
from utils.logging import (
    get_logger,
    log_invalid_smiles,
    log_missing_data_excluded,
)
from utils.graph_safety import safe_featurization_wrapper

LOGGER = get_logger(__name__)

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def _smiles_to_molecule_graph(smiles: str) -> Data:
    """
    Convert a SMILES string into a ``torch_geometric`` ``Data`` object.

    Node features:
        - Atomic number (int) stored as a single‑column tensor ``x``.

    Edge representation:
        - Undirected bond edges are stored in ``edge_index`` as a
          ``[2, num_edges]`` ``torch.LongTensor`` where each column
          contains ``[source, target]`` node indices.

    Parameters
    ----------
    smiles: str
        The SMILES representation of the molecule.

    Returns
    -------
    Data
        A ``torch_geometric.data.Data`` instance representing the molecule.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Unable to parse SMILES: {smiles}")

    # Ensure explicit hydrogens are added – they are useful for GNNs.
    mol = Chem.AddHs(mol)

    atom_nums: List[int] = []
    for atom in mol.GetAtoms():
        atom_nums.append(atom.GetAtomicNum())
    x = torch.tensor(atom_nums, dtype=torch.long).unsqueeze(1)  # shape (N, 1)

    src: List[int] = []
    dst: List[int] = []
    for bond in mol.GetBonds():
        begin_idx = bond.GetBeginAtomIdx()
        end_idx = bond.GetEndAtomIdx()
        # Add both directions for an undirected graph
        src.extend([begin_idx, end_idx])
        dst.extend([end_idx, begin_idx])

    edge_index = torch.tensor([src, dst], dtype=torch.long)

    return Data(x=x, edge_index=edge_index)


def _extract_solvent_descriptor(row: Dict[str, Any]) -> Dict[str, float]:
    """
    Pull viscosity and dielectric constant from a CSV row.

    The CSV produced by the ingestion step may contain the columns under
    several possible names (e.g. ``viscosity`` vs ``solvent_viscosity``).
    This function looks for the most common variants and raises ``KeyError``
    if they cannot be found.

    Parameters
    ----------
    row: dict
        Mapping of column names to string values as read from ``csv.DictReader``.

    Returns
    -------
    dict
        ``{'viscosity': float, 'dielectric_constant': float}``
    """
    # Possible column name variants
    viscosity_keys = ["viscosity", "solvent_viscosity", "visc"]
    dielectric_keys = ["dielectric_constant", "solvent_dielectric_constant", "dielectric"]

    def _find_key(candidates: List[str]) -> str:
        for key in candidates:
            if key in row and row[key].strip() != "":
                return key
        raise KeyError(f"None of {candidates} present in row")

    viscosity_key = _find_key(viscosity_keys)
    dielectric_key = _find_key(dielectric_keys)

    try:
        viscosity = float(row[viscosity_key])
        dielectric = float(row[dielectric_key])
    except ValueError as exc:
        raise ValueError(
            f"Non‑numeric solvent descriptor values: {viscosity_key}={row[viscosity_key]}, "
            f"{dielectric_key}={row[dielectric_key]}"
        ) from exc

    return {"viscosity": viscosity, "dielectric_constant": dielectric}


# -------------------------------------------------------------------------
# Main featurization routine
# -------------------------------------------------------------------------

def featurize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Featurize a single CSV row.

    Returns a dictionary ready for JSON‑line serialization.  If the row
    cannot be processed (invalid SMILES or missing solvent data) a ``None``
    value is returned and the caller should skip serialization.
    """
    smiles = row.get("smiles") or row.get("SMILES")
    if not smiles:
        log_invalid_smiles(LOGGER, "Missing SMILES column")
        return None

    # Safely build the molecule graph – safety wrapper will raise a
    # ``MolecularSafetyError`` for excessively large molecules.
    try:
        graph = safe_featurization_wrapper(_smiles_to_molecule_graph)(smiles)
    except Exception as exc:  # includes MolecularSafetyError and RDKit parsing errors
        log_invalid_smiles(LOGGER, f"SMILES parsing/safety error for '{smiles}': {exc}")
        return None

    # Extract solvent descriptor – missing data causes the row to be omitted.
    try:
        solvent = _extract_solvent_descriptor(row)
    except (KeyError, ValueError) as exc:
        log_missing_data_excluded(LOGGER, f"Solvent descriptor missing/invalid: {exc}")
        return None

    # Serialize the PyG Data object into a plain‑dict for JSON output.
    graph_dict = {
        "x": graph.x.squeeze(1).tolist(),  # list of atomic numbers
        "edge_index": graph.edge_index.t().tolist(),  # list of [src, dst] pairs
    }

    # Keep an identifier if present (e.g. a primary key column)
    record_id = row.get("id") or row.get("sample_id") or row.get("index") or None

    output = {
        "id": record_id,
        "graph": graph_dict,
        "solvent": solvent,
    }
    return output


def main() -> None:
    """
    Entry point for the script.

    Reads ``data/raw/dataset.csv`` (or the path configured by the user),
    featurizes each row, and writes the resulting JSONL file to
    ``data/processed/featurized.jsonl``.
    """
    project_root = get_project_root()
    raw_csv_path = project_root / "data" / "raw" / "dataset.csv"
    output_path = project_root / "data" / "processed" / "featurized.jsonl"

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    processed_count = 0
    skipped_count = 0

    with raw_csv_path.open(newline="", encoding="utf-8") as csvfile, \
         output_path.open("w", encoding="utf-8") as outfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            result = featurize_row(row)
            if result is None:
                skipped_count += 1
                continue
            json_line = json.dumps(result)
            outfile.write(json_line + "\n")
            processed_count += 1

    LOGGER.info(
        f"Featurization complete: {processed_count} records written, {skipped_count} records skipped."
    )


if __name__ == "__main__":
    main()