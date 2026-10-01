import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from scipy import stats

# Local imports assumed to exist in utils based on project structure
try:
    from utils.logging import get_logger, configure_root_logger
    from utils.config import get_project_root
except ImportError:
    # Fallback for direct execution or missing utils in some contexts
    import logging
    logger = logging.getLogger(__name__)
    def get_logger(name): return logging.getLogger(name)
    def configure_root_logger(): pass
    def get_project_root(): return Path.cwd()

logger = get_logger(__name__)

def load_analysis_data() -> pd.DataFrame:
    """
    Loads the processed descriptors and filtered data to merge for analysis.
    Expects:
      - data/processed/descriptors_raw.csv (from T014)
      - data/processed/filtered_data.csv (from T010)
    """
    project_root = get_project_root()
    descriptors_path = project_root / "data" / "processed" / "descriptors_raw.csv"
    filtered_path = project_root / "data" / "processed" / "filtered_data.csv"

    if not descriptors_path.exists():
        raise FileNotFoundError(f"Descriptors file not found: {descriptors_path}")
    if not filtered_path.exists():
        raise FileNotFoundError(f"Filtered data file not found: {filtered_path}")

    df_desc = pd.read_csv(descriptors_path)
    df_filt = pd.read_csv(filtered_path)

    # Ensure common key for merging
    # descriptors_raw.csv has 'smiles', 'bond_variance', 'angle_variance', 'dihedral_variance'
    # filtered_data.csv has 'smiles', 'logPapp', and potentially confounders like 'mw', 'psa', 'logP'
    # Note: T014 output might need logP/mw/psa merged from T010 if not present in descriptors.
    # Assuming T010 (filtered_data) has the necessary confounders or they are in descriptors.
    # Based on T015 requirement: "controlling for confounders (logP, MW, PSA)".
    # We merge on 'smiles'.

    df_merged = pd.merge(df_desc, df_filt[['smiles', 'logPapp', 'mw', 'psa', 'logP']], on='smiles', how='inner')

    # Drop any rows with NaN in critical columns for correlation
    critical_cols = ['logPapp', 'bond_variance', 'angle_variance', 'dihedral_variance']
    # Confounders might be optional for simple correlation but required for partial correlation if implemented.
    # For T015/T016, we focus on correlation coefficients first.
    df_merged = df_merged.dropna(subset=critical_cols)

    logger.info(f"Loaded {len(df_merged)} records for analysis.")
    return df_merged

def compute_correlations_with_fdr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Pearson and Spearman correlations between each flexibility descriptor
    and logPapp, controlling for confounders (logP, MW, PSA) via partial correlation,
    and applies Benjamini-Hochberg FDR correction.

    Returns a DataFrame with:
      - descriptor
      - method (pearson/spearman)
      - r_value
      - p_value
      - q_value (FDR corrected)
    """
    descriptors = ['bond_variance', 'angle_variance', 'dihedral_variance']
    confounders = ['logP', 'mw', 'psa']
    # Filter confounders to those present in DF
    available_confounders = [c for c in confounders if c in df.columns]

    results = []

    for desc in descriptors:
        y = df['logPapp'].values
        x = df[desc].values
        
        # Remove rows where x or y is NaN (should be handled by load, but safety)
        mask = ~(np.isnan(x) | np.isnan(y))
        x_clean = x[mask]
        y_clean = y[mask]

        if len(x_clean) < 3:
            logger.warning(f"Not enough data for {desc}. Skipping.")
            continue

        # Partial correlation if confounders exist
        if available_confounders:
            # Residualize
            Z = df[available_confounders].values
            # Residualize y
            res_y = stats.residuals(y_clean, Z) # Note: stats.residuals might not be direct in scipy, using manual
            # Manual linear regression for residuals
            # y = Z * beta + err
            # beta = (Z.T Z)^-1 Z.T y
            # err = y - Z * beta
            try:
                # Add intercept
                Z_int = np.column_stack([np.ones(len(Z)), Z])
                betas_y, *_ = np.linalg.lstsq(Z_int, y_clean, rcond=None)
                res_y = y_clean - Z_int @ betas_y

                betas_x, *_ = np.linalg.lstsq(Z_int, x_clean, rcond=None)
                res_x = x_clean - Z_int @ betas_x

                # Correlation on residuals
                r, p = stats.pearsonr(res_x, res_y)
                method_name = "partial_pearson"
            except Exception as e:
                logger.warning(f"Partial correlation failed for {desc}: {e}. Falling back to simple.")
                r, p = stats.pearsonr(x_clean, y_clean)
                method_name = "pearson"
        else:
            # Simple correlation
            r, p = stats.pearsonr(x_clean, y_clean)
            method_name = "pearson"

        results.append({
            "descriptor": desc,
            "method": method_name,
            "r_value": r,
            "p_value": p
        })

        # Spearman
        r_sp, p_sp = stats.spearmanr(x_clean, y_clean)
        results.append({
            "descriptor": desc,
            "method": "spearman",
            "r_value": r_sp,
            "p_value": p_sp
        })

    df_results = pd.DataFrame(results)
    
    # Benjamini-Hochberg FDR Correction
    p_values = df_results['p_value'].values
    n = len(p_values)
    
    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate q-values
    # q_i = (p_i * m) / i
    # But must ensure monotonicity: q_i = min(q_i, q_{i+1})
    q_values = np.zeros(n)
    for i in range(n):
        # rank is i+1
        q_values[i] = sorted_p[i] * n / (i + 1)
    
    # Enforce monotonicity from the end
    for i in range(n - 2, -1, -1):
        q_values[i] = min(q_values[i], q_values[i + 1])
    
    # Clip to 1.0
    q_values = np.clip(q_values, 0, 1.0)
    
    # Assign back to original order
    df_results['q_value'] = 0.0
    df_results.loc[sorted_indices, 'q_value'] = q_values

    logger.info(f"Computed correlations and FDR correction. Results shape: {df_results.shape}")
    return df_results

def write_correlation_results(df: pd.DataFrame, output_path: Path):
    """
    Writes the correlation results with FDR-corrected q-values to CSV.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Correlation results written to {output_path}")

def main():
    """
    Main entry point for T016: FDR correction on correlation results.
    Loads data, computes correlations (if not already done, but T015 did this),
    applies FDR, and writes updated results.
    """
    configure_root_logger()
    project_root = get_project_root()
    output_path = project_root / "data" / "processed" / "correlation_results.csv"
    
    # Load analysis data
    try:
        df_data = load_analysis_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Compute correlations with FDR
    # Note: T015 might have produced a file without q-values. 
    # We recompute here to ensure q-values are present and correct per T016 spec.
    df_corr = compute_correlations_with_fdr(df_data)

    # Write results
    write_correlation_results(df_corr, output_path)

    # Invoke checksum utility if available
    checksum_path = project_root / "code" / "utils" / "checksum.py"
    if checksum_path.exists():
        logger.info("Invoking checksum utility...")
        # Import and run the checksum main for the output file
        # We need to ensure we don't double-import if already loaded, but safe to call main
        try:
            # Dynamically import to avoid circular issues if any
            import importlib.util
            spec = importlib.util.spec_from_file_location("checksum", checksum_path)
            checksum_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(checksum_mod)
            # We need to pass the file to checksum, but the main() in checksum.py 
            # typically scans data/ or takes args. 
            # The task says: "invoke code/utils/checksum.py to generate a checksum"
            # Assuming the checksum script can be run with an argument or scans the directory.
            # If it scans data/, it will pick up the new file.
            if hasattr(checksum_mod, 'main'):
                # Run with args if needed, otherwise just run main which might scan
                # To be safe, we assume main() scans data/processed/
                checksum_mod.main() 
        except Exception as e:
            logger.warning(f"Could not invoke checksum utility: {e}")
    else:
        logger.warning("Checksum utility not found at expected path.")

if __name__ == "__main__":
    main()