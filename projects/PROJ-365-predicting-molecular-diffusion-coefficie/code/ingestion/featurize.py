"""
featurize.py
--------------

This module implements the feature extraction step for the diffusion‑coefficient
prediction pipeline (US1). It reads the raw CSV produced by the ingestion step,
converts each SMILES string into a ``torch_geometric.data.Data`` object
(the molecule graph) and extracts solvent descriptors. The resulting records
are written line‑by‑line as JSON to ``data/processed/featurized_data.jsonl``.
Each JSON line conforms to ``contracts/dataset.schema.yaml``.

The script also records peak memory usage during processing to
``artifacts/reports/memory_profile.json`` (SC‑005).
"""

import csv
import json
import math
import hashlib
from pathlib import Path
from typing import Dict, List, Any

import psutil
import torch
from torch_geometric.data import Data
from rdkit import Chem
from rdkit.Chem import rdchem

from llmxive_toolkit import paths, get_logger
from utils.config import get_project_root
from utils.logging import (
    log_invalid_smiles,
    log_missing_data_excluded,
)
from utils.graph_safety import safe_featurization_wrapper, MolecularSafetyError

LOGGER = get_logger(__name__)

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def _hash_record(row: Dict[str, Any]) -> str:
    """
    Compute a deterministic SHA‑256 hash for a CSV row.  The hash is used as
    the ``record_id`` required by the schema.
    """
    # Use a stable ordering of keys
    canonical = json.dumps(row, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _smiles_to_molecule_graph(smiles: str) -> Data:
    """
    Convert a SMILES string into a ``torch_geometric`` ``Data`` object
    with full node and edge features required by the schema.

    Node features (per atom):
        - atomic number (int)
        - hybridization (int, enum value from RDKit)
        - formal charge (int)

    Edge features (per bond):
        - bond type (int, enum value from RDKit)
        - aromatic flag (int, 1 if aromatic else 0)
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Unable to parse SMILES: {smiles}")

    # Ensure explicit hydrogens – many GNN pipelines benefit from them.
    mol = Chem.AddHs(mol)

    # ------------------- node features -------------------
    atom_features: List[List[int]] = []
    for atom in mol.GetAtoms():
        atomic_num = atom.GetAtomicNum()
        hybridization = int(atom.GetHybridization())
        formal_charge = atom.GetFormalCharge()
        atom_features.append([atomic_num, hybridization, formal_charge])

    x = torch.tensor(atom_features, dtype=torch.long)  # shape (N, 3)

    # ------------------- edge index & features -------------------
    src: List[int] = []
    dst: List[int] = []
    edge_features: List[List[int]] = []

    for bond in mol.GetBonds():
        begin_idx = bond.GetBeginAtomIdx()
        end_idx = bond.GetEndAtomIdx()

        # Undirected graph – store both directions
        src.extend([begin_idx, end_idx])
        dst.extend([end_idx, begin_idx])

        bond_type = int(bond.GetBondType())
        is_aromatic = int(bond.GetIsAromatic())
        edge_features.append([bond_type, is_aromatic])
        edge_features.append([bond_type, is_aromatic])  # duplicate for reverse direction

    edge_index = torch.tensor([src, dst], dtype=torch.long)
    edge_attr = torch.tensor(edge_features, dtype=torch.long)  # shape (E, 2)

    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)


def _extract_solvent_descriptor(row: Dict[str, Any]) -> Dict[str, float]:
    """
    Pull viscosity and dielectric constant from a CSV row and return them
    using the field names required by ``contracts/dataset.schema.yaml``.
    The schema expects the keys ``viscosity`` and ``dielectric``.
    """
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

    # The schema calls this field ``dielectric`` (not ``dielectric_constant``)
    return {"viscosity": viscosity, "dielectric": dielectric}


# -------------------------------------------------------------------------
# Main featurization routine
# -------------------------------------------------------------------------

def featurize_row(row: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Featurize a single CSV row.

    Returns a dictionary ready for JSON‑line serialization that matches
    ``contracts/dataset.schema.yaml``.  If the row cannot be processed
    (invalid SMILES or missing solvent data) ``None`` is returned and the
    caller should skip serialization.
    """
    # -----------------------------------------------------------------
    # Basic required columns
    # -----------------------------------------------------------------
    smiles = row.get("smiles") or row.get("SMILES")
    solvent_type = row.get("solvent_type") or row.get("solvent") or row.get("Solvent")
    diffusion_str = row.get("diffusion_coefficient") or row.get("diffusion") or row.get("Diffusion")

    if not smiles:
        log_invalid_smiles(LOGGER, "Missing SMILES column")
        return None
    if not solvent_type:
        log_missing_data_excluded(LOGGER, "Missing solvent_type")
        return None
    if not diffusion_str:
        log_missing_data_excluded(LOGGER, "Missing diffusion coefficient")
        return None

    # -----------------------------------------------------------------
    # Parse diffusion coefficient and compute target (log10 scale)
    # -----------------------------------------------------------------
    try:
        diffusion_val = float(diffusion_str)
        target = math.log10(diffusion_val) if diffusion_val > 0 else 0.0
    except ValueError as exc:
        log_missing_data_excluded(LOGGER, f"Invalid diffusion value: {diffusion_str}")
        return None

    # -----------------------------------------------------------------
    # Graph construction (safety‑wrapped)
    # -----------------------------------------------------------------
    try:
        graph = safe_featurization_wrapper(_smiles_to_molecule_graph)(smiles)
    except (MolecularSafetyError, Exception) as exc:
        log_invalid_smiles(LOGGER, f"SMILES parsing/safety error for '{smiles}': {exc}")
        return None

    # -----------------------------------------------------------------
    # Solvent descriptors
    # -----------------------------------------------------------------
    try:
        solvent = _extract_solvent_descriptor(row)
    except (KeyError, ValueError) as exc:
        log_missing_data_excluded(LOGGER, f"Solvent descriptor missing/invalid: {exc}")
        return None

    # -----------------------------------------------------------------
    # Assemble schema‑compliant record
    # -----------------------------------------------------------------
    record_id = _hash_record(row)

    # Serialize graph components to plain Python structures
    graph_dict = {
        "node_features": graph.x.tolist(),                     # [[atomic_num, hybridization, formal_charge], ...]
        "edge_index": graph.edge_index.t().tolist(),           # [[src, dst], ...]
        "edge_features": graph.edge_attr.tolist(),             # [[bond_type, is_aromatic], ...]
    }

    output = {
        "record_id": record_id,
        "smiles": smiles,
        "solvent_type": solvent_type,
        "target": target,
        "graph": graph_dict,
        "solvent_features": solvent,
        "status": "valid",
        "exclusion_reason": None,
    }
    return output


def main() -> None:
    """
    Entry point for the script.

    Reads ``data/raw/dataset.csv``, featurizes each valid row, writes the
    JSON‑L output to ``data/processed/featurized_data.jsonl`` and records
    peak memory usage to ``artifacts/reports/memory_profile.json``.
    """
    project_root = get_project_root()
    raw_csv_path = project_root / "data" / "raw" / "dataset.csv"
    output_path = paths.data("processed", "featurized_data.jsonl")
    memory_path = paths.artifacts("reports", "memory_profile.json")

    # Ensure output directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.parent.mkdir(parents=True, exist_ok=True)

    process = psutil.Process()
    peak_memory_mb = 0.0

    processed_count = 0
    skipped_count = 0

    with raw_csv_path.open(newline="", encoding="utf-8") as csvfile, \
         output_path.open("w", encoding="utf-8") as outfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Update peak memory after each row (cheap approximation)
            mem_mb = process.memory_info().rss / (1024 * 1024)
            if mem_mb > peak_memory_mb:
                peak_memory_mb = mem_mb

            result = featurize_row(row)
            if result is None:
                skipped_count += 1
                continue

            outfile.write(json.dumps(result) + "\n")
            processed_count += 1

    # Write memory profile
    memory_profile = {"peak_memory_mb": round(peak_memory_mb, 2)}
    memory_path.write_text(json.dumps(memory_profile, indent=2), encoding="utf-8")

    LOGGER.info(
        f"Featurization complete: {processed_count} records written, "
        f"{skipped_count} records skipped. Peak memory: {peak_memory_mb:.2f} MB."
    )

if __name__ == "__main__":
    main()
