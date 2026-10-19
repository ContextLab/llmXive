"""
Pre‑processing utilities for metabolite and BGC data.
Includes:
- Mapping BGC types to metabolite classes (via a minimal static map).
- Harmonising metabolite tables (pseudo‑count + log‑transform).
- A thin wrapper around antiSMASH (placeholder implementation).
"""

import logging
from pathlib import Path
from typing import Any, Dict, Union

import numpy as np
import pandas as pd

from utils.logging import get_logger

logger = get_logger(__name__)


# ----------------------------------------------------------------------
# Simple static mapping – in a real project this would be loaded from
# the MIBiG 3.0 ontology file.
# ----------------------------------------------------------------------
_BGC_TO_METABOLITE = {
    "polyketide": "polyketide",
    "nonribosomal_peptide": "nonribosomal_peptide",
    "terpene": "terpene",
    "alkaloid": "alkaloid",
    "saccharide": "saccharide",
}


def map_bgc_to_metabolite(bgc_type: str) -> str:
    """
    Map a BGC type string to a metabolite class.
    Returns ``'unknown'`` if the type is not present in the static map.
    """
    return _BGC_TO_METABOLITE.get(bgc_type.lower(), "unknown")


def map_bgc_to_metabolite_dataframe(
    bgc_df: pd.DataFrame, metabolite_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge BGC and metabolite data frames and add a ``mapped_class`` column.

    The function performs a simple inner join on the ``species`` column.
    ``mapped_class`` is derived from the first BGC type column found in
    ``bgc_df`` (if any); otherwise it is set to ``'unknown'``.
    """
    if "species" not in bgc_df.columns or "species" not in metabolite_df.columns:
        raise ValueError("Both data frames must contain a 'species' column.")

    merged = pd.merge(
        bgc_df,
        metabolite_df,
        on="species",
        how="inner",
        suffixes=("_bgc", "_meta"),
    )

    # Determine a representative BGC type column (first non‑species column)
    bgc_type_cols = [c for c in bgc_df.columns if c != "species"]
    if bgc_type_cols:
        first_type = bgc_type_cols[0]
        merged["mapped_class"] = merged[first_type].apply(
            lambda x: map_bgc_to_metabolite(str(x))
        )
    else:
        merged["mapped_class"] = "unknown"

    return merged


def run_antiasmh_wrapper(genome_paths: Any, confidence: float = 0.5) -> pd.DataFrame:
    """
    Placeholder wrapper for antiSMASH execution.
    In CI mode this simply returns an empty DataFrame with the expected columns.
    """
    ci_mode = int(os.getenv("CI_MODE", "0"))
    if ci_mode:
        # Return a minimal DataFrame that downstream code can handle.
        df = pd.DataFrame(
            {
                "species": [],
                "total_bgc_count": [],
            }
        )
        logger.info("CI mode – returning empty antiSMASH placeholder DataFrame.")
        return df
    else:
        raise NotImplementedError(
            "Real antiSMASH execution is not implemented in this sandbox."
        )


# Backwards‑compatible alias expected by the CLI
def run_antiSMASH_wrapper(genome_paths: Any, confidence: float = 0.5) -> pd.DataFrame:
    """
    Public wrapper that forwards to :func:`run_antiasmh_wrapper`.
    """
    return run_antiasmh_wrapper(genome_paths, confidence)


def harmonize_metabolites(
    input_path: Union[str, Path], output_path: Union[str, Path]
) -> None:
    """
    Load a metabolite abundance table, add a pseudo‑count of 1, apply a
    log‑transformation, and write the result to *output_path*.

    The input table is expected to contain columns:
    - ``species``
    - ``abundance`` (numeric)
    - ``inchikey`` (or ``InChIKey``)

    The output adds a ``log_abundance`` column and drops the original
    ``abundance`` column.
    """
    df = pd.read_csv(input_path)

    # Ensure required columns are present
    required = {"species", "abundance", "inchikey"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input metabolite file missing columns: {missing}")

    # Pseudo‑count and log‑transform
    df["log_abundance"] = np.log(df["abundance"] + 1)

    # Keep only necessary columns
    out_df = df[["species", "inchikey", "log_abundance"]]

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    logger.info(f"Harmonised metabolite data written to {out_path}")


def main() -> None:
    """
    Simple command‑line entry point that demonstrates the harmonisation
    routine on a mock file.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Harmonise metabolite abundance tables."
    )
    parser.add_argument("input", help="Path to input CSV")
    parser.add_argument("output", help="Path to write harmonised CSV")
    args = parser.parse_args()

    harmonize_metabolites(args.input, args.output)

if __name__ == "__main__":
    main()
