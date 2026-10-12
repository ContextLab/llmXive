"""RDKit graph-descriptor computation (FR-001, FR-008) and target
fallback wiring (T015/T017).

Reads ``data/raw/input.csv`` (or ``data/raw/smiles.csv``), computes the
graph-based descriptor table, derives the target column via
``code.target_proxy.apply_target_fallback`` (which also writes
``data/processed/quantum_proxy_report.json``) and writes
``data/processed/descriptors.csv``.
"""

import os
import sys
import logging
from typing import Optional

import numpy as np
import pandas as pd

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from rdkit import Chem
from rdkit.Chem import Descriptors

from llmxive_toolkit import paths, get_logger
from code.target_proxy import apply_target_fallback

log = get_logger(__name__)

DESCRIPTOR_COLUMNS = [
    "smiles",
    "aromatic_ring_count",
    "conjugation_path_length",
    "average_path_length",
    "degree_mean",
    "degree_std",
    "ring_count",
    "molecular_weight",
    "homo_lumo_gap",
    "is_valid",
]


def _mol_from_smiles(smiles: str):
    """Parse a SMILES string into an RDKit Mol (or None on failure)."""
    if not isinstance(smiles, str) or not smiles.strip():
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
    except Exception:
        return None
    return mol


def _is_conjugated_bond(bond) -> bool:
    """A bond is conjugated when aromatic or bond order >= 2."""
    if bond.GetIsAromatic():
        return True
    return bond.GetBondTypeAsDouble() >= 2.0


def _longest_conjugated_path(mol) -> int:
    """Longest simple path (in bonds) within the conjugated-bond subgraph."""
    n = mol.GetNumAtoms()
    if n == 0:
        return 0
    adj = {i: set() for i in range(n)}
    for bond in mol.GetBonds():
        if _is_conjugated_bond(bond):
            a = bond.GetBeginAtomIdx()
            b = bond.GetEndAtomIdx()
            adj[a].add(b)
            adj[b].add(a)

    best = 0

    def dfs(node: int, visited: set, depth: int):
        nonlocal best
        best = max(best, depth)
        for nb in adj[node]:
            if nb not in visited:
                visited.add(nb)
                dfs(nb, visited, depth + 1)
                visited.remove(nb)

    for start in range(n):
        if adj[start]:
            dfs(start, {start}, 0)
    return best


def _aromatic_ring_count(mol) -> int:
    """Number of rings whose bonds are all aromatic."""
    try:
        rings = Chem.GetSymmSSSR(mol)
    except Exception:
        return 0
    count = 0
    for ring in rings:
        atoms = list(ring)
        bonds = [mol.GetBondBetweenAtoms(atoms[i], atoms[(i + 1) % len(atoms)])
                 for i in range(len(atoms))]
        if bonds and all(b is not None and b.GetIsAromatic() for b in bonds):
            count += 1
    return count


def _average_path_length(mol) -> float:
    """Average topological distance over all atom pairs (heavy atoms)."""
    n = mol.GetNumAtoms()
    if n < 2:
        return 0.0
    dm = Chem.GetDistanceMatrix(mol)
    iu = np.triu_indices(n, k=1)
    return float(dm[iu].mean())


def _compute_descriptors(mol) -> dict:
    """Return a dictionary of descriptor values for a single RDKit Mol."""
    degrees = np.array([a.GetDegree() for a in mol.GetAtoms()], dtype=float)
    try:
        n_rings = mol.GetRingInfo().NumRings()
    except Exception:
        n_rings = 0
    return {
        "aromatic_ring_count": _aromatic_ring_count(mol),
        "conjugation_path_length": _longest_conjugated_path(mol),
        "average_path_length": _average_path_length(mol),
        "degree_mean": float(degrees.mean()) if len(degrees) else 0.0,
        "degree_std": float(degrees.std()) if len(degrees) else 0.0,
        "ring_count": int(n_rings),
        "molecular_weight": float(Descriptors.MolWt(mol)),
        "homo_lumo_gap": np.nan,  # not available from topology alone
        "is_valid": True,
    }


def compute_all_descriptors(df: pd.DataFrame, smiles_col: str = "smiles") -> pd.DataFrame:
    """Compute descriptors for every valid SMILES in ``df``.

    Returns a DataFrame with the schema columns only; molecules whose
    SMILES cannot be parsed are logged as errors and excluded.
    """
    rows = []
    for idx, smiles in df[smiles_col].items():
        mol = _mol_from_smiles(smiles)
        if mol is None or mol.GetNumAtoms() == 0:
            log.error("Invalid SMILES at row %s: %r - excluded", idx, smiles)
            continue
        desc = _compute_descriptors(mol)
        desc["smiles"] = smiles
        rows.append(desc)
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out[DESCRIPTOR_COLUMNS]
    return out


def main() -> int:
    """CLI entry point used by ``code/main.py``.

    Reads ``data/raw/input.csv`` (or ``data/raw/smiles.csv``), computes
    descriptors, applies the target fallback (T015) and writes
    ``data/processed/descriptors.csv`` plus the quantum-proxy report.
    """
    input_csv = paths.data("raw", "input.csv")
    if not input_csv.exists():
        input_csv = paths.data("raw", "smiles.csv")
    if not input_csv.exists():
        raise FileNotFoundError(
            "No raw input found: expected data/raw/input.csv or "
            "data/raw/smiles.csv"
        )
    raw = pd.read_csv(input_csv)
    log.info("Loaded %d rows from %s", len(raw), input_csv)

    desc = compute_all_descriptors(raw)
    log.info("Computed descriptors for %d valid molecules", len(desc))
    if desc.empty:
        raise ValueError("No valid molecules remained after descriptor computation.")

    desc, report = apply_target_fallback(raw, desc)
    log.info("Target type: %s (fallback_used=%s)",
             report["target_type"], report["fallback_used"])

    out_path = paths.data("processed", "descriptors.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    desc.to_csv(out_path, index=False)
    log.info("Descriptors written to %s", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
