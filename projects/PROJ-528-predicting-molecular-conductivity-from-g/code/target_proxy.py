"""
Quantum-proxy detection and topological target fallback (T013/T014/T015).

Detects whether quantum-derived descriptors (HOMO-LUMO gap) are present
in the dataset, writes ``data/processed/quantum_proxy_report.json``, and
provides the empirical topological proxy used when both measured
conductivity and HOMO-LUMO gap are missing (T015).
"""

import os
import sys
import json
import logging
from typing import Optional, Tuple

import numpy as np
import pandas as pd

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

HOMO_LUMO_CANDIDATES = ("homo_lumo_gap", "HOMO_LUMO_gap", "homo-lumo gap", "gap")
CONDUCTIVITY_CANDIDATES = ("conductivity", "charge_carrier_mobility")


def detect_homo_lumo_column(df: pd.DataFrame) -> Optional[str]:
    """Return the name of the HOMO-LUMO gap column, or None if absent."""
    for cand in HOMO_LUMO_CANDIDATES:
        if cand in df.columns:
            return cand
    return None


def detect_conductivity_column(df: pd.DataFrame) -> Optional[str]:
    """Return the name of the measured conductivity column, or None."""
    for cand in CONDUCTIVITY_CANDIDATES:
        if cand in df.columns:
            return cand
    return None


def homo_lumo_data_present(df: pd.DataFrame) -> bool:
    """True if a HOMO-LUMO column exists AND contains at least one finite value."""
    col = detect_homo_lumo_column(df)
    if col is None:
        return False
    vals = pd.to_numeric(df[col], errors="coerce").dropna()
    return not vals.empty


def compute_topological_proxy(aromatic_ring_count: float,
                              conjugation_path_length: float) -> float:
    """Empirical topological proxy for log-conductivity (T015/T100).

    Linear combination of aromatic ring count and conjugation path
    length, the two resonance-related structural proxies highlighted
    in the spec (FR-008, FR-014).
    """
    return float(0.6 * aromatic_ring_count + 0.4 * conjugation_path_length)


def build_quantum_proxy_report(raw_df: pd.DataFrame,
                               descriptors_df: pd.DataFrame = None) -> dict:
    """Assemble the quantum-proxy report dictionary.

    ``fallback_used`` is True only when BOTH measured conductivity and
    HOMO-LUMO gap are unavailable, in which case the topological proxy
    must be used as target (target_type = topological_proxy).
    """
    homo_lumo_col = detect_homo_lumo_column(raw_df)
    homo_present = homo_lumo_col is not None and homo_lumo_data_present(raw_df)

    cond_col = detect_conductivity_column(raw_df)
    cond_present = cond_col is not None and pd.to_numeric(
        raw_df[cond_col], errors="coerce"
    ).notna().any()

    if cond_present:
        target_type = "measured_conductivity"
        fallback_used = False
    elif homo_present:
        target_type = "homo_lumo_gap"
        fallback_used = False
    else:
        target_type = "topological_proxy"
        fallback_used = True
        log.warning(
            "Neither measured conductivity nor HOMO-LUMO gap data are "
            "available; falling back to the topological proxy target."
        )

    if not homo_present:
        log.warning(
            "Quantum-derived descriptors (HOMO-LUMO gap) are absent from "
            "the dataset; quantum validation is pending and topological "
            "proxies (aromaticity, conjugation) are used instead (FR-014)."
        )

    report = {
        "homo_lumo_present": bool(homo_present),
        "homo_lumo_column": homo_lumo_col,
        "measured_conductivity_present": bool(cond_present),
        "fallback_used": bool(fallback_used),
        "target_type": target_type,
        "n_molecules": int(len(raw_df)),
    }
    if descriptors_df is not None:
        report["n_valid_descriptor_rows"] = int(len(descriptors_df))
    return report


def write_quantum_proxy_report(report: dict, path=None) -> None:
    """Write the quantum-proxy report JSON to data/processed/."""
    if path is None:
        path = paths.data("processed", "quantum_proxy_report.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(report, fh, indent=2)
    log.info("Quantum proxy report written to %s", path)


def apply_target_fallback(raw_df: pd.DataFrame,
                          descriptors_df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Derive the ``log_conductivity`` target column (T015/T017).

    Priority order:
    1. Measured conductivity  -> log10(conductivity),
       target_type = measured_conductivity.
    2. HOMO-LUMO gap          -> -log10(gap),
       target_type = homo_lumo_gap.
    3. Topological proxy      -> linear combination of
       aromatic_ring_count and conjugation_path_length,
       target_type = topological_proxy (fallback_used = True).

    Returns the descriptors DataFrame extended with the non-null
    ``log_conductivity`` and ``target_type`` columns, plus the report
    dictionary (also written to data/processed/quantum_proxy_report.json).
    """
    out = descriptors_df.copy()
    cond_col = detect_conductivity_column(raw_df)
    homo_col = detect_homo_lumo_column(raw_df)

    cond_vals = (pd.to_numeric(raw_df[cond_col], errors="coerce")
                 if cond_col is not None else None)
    cond_present = cond_vals is not None and cond_vals.notna().any()
    homo_vals = (pd.to_numeric(raw_df[homo_col], errors="coerce")
                 if homo_col is not None else None)
    homo_present = homo_vals is not None and homo_vals.notna().any()

    if cond_present:
        target_map = pd.DataFrame({
            "smiles": raw_df["smiles"].astype(str),
            "log_conductivity": np.log10(cond_vals.clip(lower=1e-300)),
        })
        out = out.merge(target_map, on="smiles", how="left")
        target_type = "measured_conductivity"
        fallback_used = False
    elif homo_present:
        target_map = pd.DataFrame({
            "smiles": raw_df["smiles"].astype(str),
            "log_conductivity": -np.log10(homo_vals.clip(lower=1e-300)),
        })
        out = out.merge(target_map, on="smiles", how="left")
        target_type = "homo_lumo_gap"
        fallback_used = False
    else:
        out["log_conductivity"] = out.apply(
            lambda row: compute_topological_proxy(
                row.get("aromatic_ring_count", 0.0),
                row.get("conjugation_path_length", 0.0),
            ),
            axis=1,
        )
        target_type = "topological_proxy"
        fallback_used = True
        log.warning(
            "Target fallback engaged: log_conductivity computed as the "
            "topological proxy 0.6*aromatic_ring_count + "
            "0.4*conjugation_path_length (target_type=topological_proxy)."
        )

    out["target_type"] = target_type
    if out["log_conductivity"].isna().any():
        n_missing = int(out["log_conductivity"].isna().sum())
        log.warning(
            "%d descriptor rows could not be matched to a target value; "
            "they are retained with NaN log_conductivity and will be "
            "excluded downstream (FR-012).", n_missing
        )

    report = build_quantum_proxy_report(raw_df, out)
    report["fallback_used"] = bool(fallback_used)
    report["target_type"] = target_type
    write_quantum_proxy_report(report)
    return out, report


def main() -> int:
    """CLI entry point: read raw input, write quantum_proxy_report.json."""
    input_csv = paths.data("raw", "input.csv")
    if not input_csv.exists():
        input_csv = paths.data("raw", "smiles.csv")
    if not input_csv.exists():
        raise FileNotFoundError(
            "No raw input found: expected data/raw/input.csv or data/raw/smiles.csv"
        )
    raw = pd.read_csv(input_csv)
    report = build_quantum_proxy_report(raw)
    write_quantum_proxy_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
