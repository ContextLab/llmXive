"""
Preprocess module for the plant disease resistance pipeline.

The script reads the three synthetic CSV files created by
``code.download`` (or real files in a future implementation) and
produces a single combined feature matrix under ``data/processed``.
Minimal preprocessing steps are applied:

* Genotype: ensure numeric dtype, fill missing values with the mode.
* Metabolomics: Z‑score standardisation per metabolite.
* Phenotype: keep as‑is (binary or continuous).

The output file is ``combined_features.csv`` which contains the
``sample_id`` column followed by all SNP and metabolite columns.
"""

import argparse
import logging

import pandas as pd
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _load_csv(name: str) -> pd.DataFrame:
    """Load a CSV from the raw data directory."""
    path = paths.data("raw", name)
    df = pd.read_csv(path)
    log.debug(f"Loaded {name} with shape {df.shape} from {path}")
    return df

def _ensure_processed_dir() -> None:
    """Create the processed data directory if it does not exist."""
    proc_dir = paths.data("processed")
    proc_dir.mkdir(parents=True, exist_ok=True)
    log.debug(f"Created processed data directory at {proc_dir}")

def _preprocess_genotype(df: pd.DataFrame) -> pd.DataFrame:
    """Simple genotype preprocessing."""
    # Ensure SNP columns are numeric (0/1) and fill missing with mode.
    snp_cols = [c for c in df.columns if c != "sample_id"]
    for col in snp_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        mode = df[col].mode().iloc[0] if not df[col].mode().empty else 0
        df[col] = df[col].fillna(mode).astype(int)
    log.debug(f"Genotype preprocessing completed; columns: {snp_cols}")
    return df

def _preprocess_metabolomics(df: pd.DataFrame) -> pd.DataFrame:
    """Z‑score normalisation for metabolomics."""
    metab_cols = [c for c in df.columns if c != "sample_id"]
    for col in metab_cols:
        mean = df[col].mean()
        std = df[col].std(ddof=0)
        if std == 0:
            log.warning(f"Metabolite column {col} has zero variance; setting to 0.")
            df[col] = 0.0
        else:
            df[col] = (df[col] - mean) / std
    log.debug(f"Metabolomics Z‑score normalisation completed; columns: {metab_cols}")
    return df

def _merge_datasets(geno: pd.DataFrame,
                   metab: pd.DataFrame,
                   pheno: pd.DataFrame) -> pd.DataFrame:
    """Inner‑join on ``sample_id`` to keep only fully paired samples."""
    merged = geno.merge(metab, on="sample_id", how="inner")
    merged = merged.merge(pheno, on="sample_id", how="inner")
    log.info(
        f"Merged dataset shape after inner join: {merged.shape} (samples × features)"
    )
    return merged

def main(argv: list | None = None) -> None:
    """Entry point for ``python -m code.preprocess``."""
    parser = argparse.ArgumentParser(
        description="Preprocess raw genotype, metabolomics, and phenotype data."
    )
    parser.add_argument(
        "--ci-mode",
        action="store_true",
        help="Flag kept for API compatibility; no behavioural change needed.",
    )
    args = parser.parse_args(argv)

    _ensure_processed_dir()

    # Load raw tables
    genotype = _load_csv("genotype.csv")
    metabolomics = _load_csv("metabolomics.csv")
    phenotype = _load_csv("phenotype.csv")

    # Apply simple preprocessing steps
    genotype = _preprocess_genotype(genotype)
    metabolomics = _preprocess_metabolomics(metabolomics)

    # Merge into a single feature matrix
    combined = _merge_datasets(genotype, metabolomics, phenotype)

    # Write combined matrix
    out_path = paths.data("processed", "combined_features.csv")
    combined.to_csv(out_path, index=False)
    log.info(f"Preprocessed combined feature matrix written to {out_path}")

if __name__ == "__main__":
    main()
