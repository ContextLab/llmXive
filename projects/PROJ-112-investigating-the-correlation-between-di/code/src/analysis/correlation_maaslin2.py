import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import subprocess
import tempfile
import json

import pandas as pd
import numpy as np
from scipy.stats import spearmanr

from src.utils.logger import get_logger

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROCESSED_DIR / "results"

INPUT_FILE = PROCESSED_DIR / "clr_transformed.tsv"
OUTPUT_FILE = RESULTS_DIR / "association_results.tsv"
FDR_LOG = RESULTS_DIR / "fdr_validation_log.txt"

# MaAsLin2 R script template
MAASLIN2_R_SCRIPT = """
library(Maaslin2)
library(data.table)

args <- commandArgs(trailingOnly = TRUE)
input_file <- args[1]
output_dir <- args[2]
metadata_file <- args[3]

# Load data
input_data <- read.table(input_file, header = TRUE, sep = '\\t', row.names = 1, check.names = FALSE)
metadata <- read.table(metadata_file, header = TRUE, sep = '\\t', row.names = 1, check.names = FALSE)

# Ensure metadata index matches data columns (samples are columns in input_data for MaAsLin2)
# Note: The input_data from CLR transform is likely samples as rows. MaAsLin2 expects features as rows, samples as columns.
# We need to transpose if our data is samples x features.
if (nrow(input_data) > ncol(input_data)) {
    # Likely samples x features, transpose to features x samples
    input_data <- t(input_data)
}

# Check for matching sample IDs
common_samples <- intersect(colnames(input_data), rownames(metadata))
if (length(common_samples) == 0) {
    stop("No common samples found between data and metadata.")
}

input_data <- input_data[, common_samples]
metadata <- metadata[common_samples, , drop = FALSE]

# Run MaAsLin2
# Fixed effects: fiber_g_day, age, BMI, antibiotic_use
# Random effects: cohort_id (if present)
fixed_effects <- c("fiber_g_day", "age", "BMI", "antibiotic_use")
random_effects <- NULL
if ("cohort_id" %in% colnames(metadata)) {
    random_effects <- "cohort_id"
}

out <- Maaslin2(
    input_data = input_data,
    input_metadata = metadata,
    output = output_dir,
    fixed_effects = fixed_effects,
    random_effects = if (!is.null(random_effects)) random_effects else NULL,
    normalization = 'NONE', # Already CLR transformed
    transform = 'NONE',
    min_abundance = 0,
    min_prevalence = 0,
    max_significance = 1.0,
    plot_heatmap = FALSE,
    plot_scatter = FALSE,
    save_object = TRUE
)

# Write results to TSV for Python to parse
if (exists("out") && !is.null(out$results)) {
    write.table(out$results, file.path(output_dir, "maaslin2_results_raw.tsv"), sep = '\\t', quote = FALSE, row.names = FALSE)
} else {
    stop("MaAsLin2 did not produce results.")
}
"""

def get_project_root() -> Path:
    return PROJECT_ROOT

def calculate_fisher_se(rho: float, n: int) -> float:
    """
    Calculate Standard Error for Spearman's rho using Fisher's z-transformation.
    SE_z = 1 / sqrt(n - 3)
    SE_rho approx = SE_z * (1 - rho^2)
    """
    if n <= 3:
        return np.inf
    z = 0.5 * np.log((1 + rho) / (1 - rho))
    se_z = 1.0 / np.sqrt(n - 3)
    # Delta method approximation for SE of rho
    se_rho = se_z * (1 - rho ** 2)
    return se_rho

def run_maaslin2(input_data_path: Path, metadata_path: Path, output_dir: Path) -> pd.DataFrame:
    """
    Run MaAsLin2 via subprocess.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    r_script_path = output_dir / "run_maaslin2.R"

    with open(r_script_path, "w") as f:
        f.write(MAASLIN2_R_SCRIPT)

    cmd = [
        "Rscript", str(r_script_path),
        str(input_data_path),
        str(output_dir),
        str(metadata_path)
    ]

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=3600 # 1 hour timeout
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"MaAsLin2 failed: {e.stderr}")
        raise RuntimeError(f"MaAsLin2 execution failed: {e.stderr}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("MaAsLin2 execution timed out.")
    except FileNotFoundError:
        raise RuntimeError("Rscript not found. MaAsLin2 requires R to be installed.")

    # Parse results
    results_file = output_dir / "maaslin2_results_raw.tsv"
    if not results_file.exists():
        raise RuntimeError("MaAsLin2 did not produce the expected output file.")

    df = pd.read_csv(results_file, sep='\t')
    return df

def compute_spearman_correlations(data_df: pd.DataFrame, metadata_df: pd.DataFrame, target_feature: str = "fiber_g_day") -> pd.DataFrame:
    """
    Compute Spearman correlations between target feature and all taxon columns.
    Returns a DataFrame with taxon, rho, p-value.
    """
    # Align indices
    common_idx = data_df.index.intersection(metadata_df.index)
    if len(common_idx) == 0:
        raise ValueError("No common samples between data and metadata.")

    data_aligned = data_df.loc[common_idx]
    meta_aligned = metadata_df.loc[common_idx]

    if target_feature not in meta_aligned.columns:
        raise ValueError(f"Target feature '{target_feature}' not found in metadata.")

    x = meta_aligned[target_feature].values
    n = len(x)

    results = []
    taxon_cols = [col for col in data_aligned.columns if col != 'sample_id' and col != 'cohort_id']
    # If data_df has sample_id as index, we need to handle it.
    # Assuming data_df index is sample_id.

    logging.info(f"Computing Spearman correlations for {len(taxon_cols)} taxa against {target_feature}...")

    for taxon in taxon_cols:
        y = data_aligned[taxon].values
        # Handle potential NaNs in data
        mask = ~(np.isnan(x) | np.isnan(y))
        if np.sum(mask) < 3:
            rho = np.nan
            p_val = np.nan
        else:
            rho, p_val = spearmanr(x[mask], y[mask])
        
        se = calculate_fisher_se(rho, np.sum(mask)) if not np.isnan(rho) else np.nan
        results.append({
            'taxon': taxon,
            'spearman_rho': rho,
            'spearman_p_value': p_val,
            'spearman_se': se
        })

    return pd.DataFrame(results)

def merge_and_finalize_results(
    maaslin2_df: pd.DataFrame,
    spearman_df: pd.DataFrame,
    metadata_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge MaAsLin2 and Spearman results.
    MaAsLin2 results typically have columns: feature, coefficient, std_error, pval, qval, etc.
    """
    # Standardize MaAsLin2 column names
    # Expected MaAsLin2 output columns: feature, coefficient, std_error, pval, qval, ...
    maaslin2_df = maaslin2_df.rename(columns={
        'feature': 'taxon',
        'coefficient': 'maaslin2_beta',
        'std_error': 'maaslin2_se',
        'pval': 'maaslin2_p_value',
        'qval': 'maaslin2_q_value'
    })

    # Select required columns from MaAsLin2
    maaslin2_subset = maaslin2_df[['taxon', 'maaslin2_beta', 'maaslin2_se', 'maaslin2_p_value', 'maaslin2_q_value']]

    # Merge with Spearman results
    merged = maaslin2_subset.merge(spearman_df, on='taxon', how='outer')

    # Ensure all required columns exist
    required_cols = [
        'taxon', 'maaslin2_beta', 'maaslin2_se', 'maaslin2_p_value', 'maaslin2_q_value',
        'spearman_rho', 'spearman_se', 'spearman_p_value'
    ]

    for col in required_cols:
        if col not in merged.columns:
            merged[col] = np.nan

    # Reorder
    merged = merged[required_cols]

    # Apply Benjamini-Hochberg FDR if MaAsLin2 didn't do it (check if q_value is NaN or 1.0 for all)
    # MaAsLin2 usually outputs qval. If it's missing or suspicious, we re-calculate.
    if merged['maaslin2_q_value'].isna().all() or (merged['maaslin2_q_value'] == 1.0).all():
        logging.warning("MaAsLin2 q-values missing or uniform. Applying BH correction manually.")
        from statsmodels.stats.multitest import multipletests
        pvals = merged['maaslin2_p_value'].dropna()
        if len(pvals) > 0:
            _, qvals, _, _ = multipletests(pvals, method='fdr_bh')
            # Map back
            qval_map = dict(zip(pvals.index, qvals))
            merged['maaslin2_q_value'] = merged['maaslin2_p_value'].map(qval_map)

    return merged

def run_correlation_analysis(
    input_path: Path = INPUT_FILE,
    output_path: Path = OUTPUT_FILE
) -> None:
    """
    Main orchestration function.
    """
    logger = get_logger(__name__)
    logger.info(f"Starting correlation analysis. Input: {input_path}")

    # Load CLR transformed data
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load data (samples as rows)
    data_df = pd.read_csv(input_path, sep='\t', index_col=0)
    
    # Extract metadata from data_df if it contains covariates, or load from a separate file
    # Assuming the harmonized data (T014) was merged and we have covariates in the same file or a derived one.
    # For this task, we assume the input file contains both taxa and covariates.
    # We need to separate taxa from covariates.
    # Taxa columns usually have specific prefixes or are identified by the CLR transform task.
    # Let's assume columns starting with 'taxon_' or specific list are taxa.
    # Better: Use the same logic as T020 to identify taxa.
    # For robustness, we'll assume all numeric columns not in a known covariate list are taxa.
    
    known_covariates = ['sample_id', 'cohort_id', 'fiber_g_day', 'age', 'BMI', 'antibiotic_use', 'read_count']
    # Filter out known covariates and non-numeric
    possible_taxa = [col for col in data_df.columns if col not in known_covariates and data_df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if not possible_taxa:
        raise ValueError("No taxon columns found in input data.")

    taxa_df = data_df[possible_taxa]
    metadata_df = data_df[known_covariates[2:]] # fiber_g_day, age, BMI, antibiotic_use, cohort_id, read_count
    # Ensure sample_id is index
    metadata_df = metadata_df.reset_index()
    metadata_df.set_index('sample_id', inplace=True)
    if 'sample_id' in taxa_df.columns:
        taxa_df.set_index('sample_id', inplace=True)

    # Prepare temp directory for MaAsLin2
    temp_dir = tempfile.mkdtemp()
    temp_input = os.path.join(temp_dir, "input.tsv")
    temp_meta = os.path.join(temp_dir, "metadata.tsv")
    
    # MaAsLin2 expects features as rows, samples as columns.
    # Our data is samples as rows. Transpose.
    maaslin2_input = taxa_df.T
    maaslin2_input.to_csv(temp_input, sep='\t')
    metadata_df.to_csv(temp_meta, sep='\t')

    # Run MaAsLin2
    maaslin2_results = run_maaslin2(
        Path(temp_input),
        Path(temp_meta),
        Path(temp_dir)
    )

    # Compute Spearman
    spearman_results = compute_spearman_correlations(taxa_df, metadata_df, target_feature="fiber_g_day")

    # Merge
    final_results = merge_and_finalize_results(maaslin2_results, spearman_results, metadata_df)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_results.to_csv(output_path, sep='\t', index=False)
    logger.info(f"Results written to {output_path}")

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run correlation analysis using MaAsLin2 and Spearman.")
    parser.add_argument("--input", type=Path, default=INPUT_FILE, help="Input CLR transformed TSV file.")
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE, help="Output association results TSV file.")
    return parser

def main():
    parser = build_arg_parser()
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        run_correlation_analysis(args.input, args.output)
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
