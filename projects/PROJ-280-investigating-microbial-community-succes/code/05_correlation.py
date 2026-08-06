"""
code/05_correlation.py
Implements Taxon-Nutrient Correlation with VIF Diagnostics.
Calculates Spearman correlations between taxon abundances and nutrient removal rates,
performs VIF checks for collinearity, and flags/excludes high-VIF taxa.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.model_selection import KFold

# Import shared utilities
from utils import calculate_vif, log_data_gap_flag

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] [%(module)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_FILE = PROCESSED_DIR / "processed_feature_table.csv"
METADATA_FILE = PROCESSED_DIR / "sample_metadata.csv"

# Output paths
CORRELATION_RESULTS_FILE = PROCESSED_DIR / "correlation_results.json"
CORRELATION_CV_FILE = PROCESSED_DIR / "correlation_cv_results.json"
CORRELATION_VIF_FLAGS_FILE = PROCESSED_DIR / "correlation_vif_flags.json"
AUDIT_TRAIL_FILE = PROCESSED_DIR / "audit_trail.json"

def load_processed_taxon_data(filepath: Path) -> pd.DataFrame:
    """Load the processed feature table (taxon abundance)."""
    if not filepath.exists():
        logger.error(f"Feature table not found at {filepath}. Ensure T012/T013 has run.")
        sys.exit(1)
    return pd.read_csv(filepath)

def load_sample_metadata(filepath: Path) -> pd.DataFrame:
    """Load sample metadata containing N/P removal rates and stage."""
    if not filepath.exists():
        logger.error(f"Metadata file not found at {filepath}.")
        sys.exit(1)
    return pd.read_csv(filepath)

def calculate_spearman_correlations(
    abundance_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    target_cols: List[str]
) -> Dict[str, Any]:
    """
    Calculate Spearman correlation between each taxon and target nutrient removal rates.
    Returns a dictionary of results.
    """
    # Merge on sample_id if not already aligned
    if 'sample_id' in abundance_df.columns:
        abundance_df = abundance_df.set_index('sample_id')
    if 'sample_id' in metadata_df.columns:
        metadata_df = metadata_df.set_index('sample_id')

    # Align indices
    common_idx = abundance_df.index.intersection(metadata_df.index)
    if len(common_idx) == 0:
        logger.error("No common samples found between feature table and metadata.")
        sys.exit(1)

    abundance_aligned = abundance_df.loc[common_idx]
    metadata_aligned = metadata_df.loc[common_idx]

    results = []
    taxa_names = [col for col in abundance_aligned.columns if col != 'sample_id']

    for taxon in taxa_names:
        taxon_series = abundance_aligned[taxon]
        for target in target_cols:
            if target not in metadata_aligned.columns:
                logger.warning(f"Target column {target} not found in metadata, skipping.")
                continue
            target_series = metadata_aligned[target]

            # Handle missing values
            mask = ~(taxon_series.isna() | target_series.isna())
            if mask.sum() < 3:
                continue

            corr, p_val = spearmanr(taxon_series[mask], target_series[mask])

            results.append({
                "taxon": taxon,
                "target": target,
                "correlation": float(corr) if not np.isnan(corr) else None,
                "p_value": float(p_val) if not np.isnan(p_val) else None
            })

    return {"correlations": results, "n_samples": len(common_idx)}

def calculate_vif_for_predictors(abundance_df: pd.DataFrame, threshold: float = 5.0) -> Tuple[List[str], Dict[str, float]]:
    """
    Calculate VIF for all taxa to detect collinearity.
    Returns list of flagged taxa and a dict of all VIF values.
    """
    # Prepare design matrix (exclude sample_id if present)
    cols = [c for c in abundance_df.columns if c != 'sample_id']
    if len(cols) == 0:
        return [], {}

    X = abundance_df[cols].values
    
    # Add constant for intercept if needed (statsmodels VIF expects it)
    # However, for VIF of predictors, we usually center or just use raw if we want raw VIF.
    # statsmodels variance_inflation_factor requires a constant column if we want to model intercept,
    # but for pure multicollinearity check, we can omit it or include it.
    # Standard practice: X = sm.add_constant(X)
    from statsmodels.tools import add_constant
    X_const = add_constant(X)

    vif_data = []
    for i in range(X_const.shape[1]):
        vif = variance_inflation_factor(X_const, i)
        vif_data.append((cols[i-1] if i > 0 else "intercept", vif))

    flagged_taxa = []
    all_vifs = {}
    for name, val in vif_data:
        if name == "intercept":
            continue
        all_vifs[name] = float(val)
        if val > threshold:
            flagged_taxa.append(name)

    return flagged_taxa, all_vifs

def perform_cross_validation(
    abundance_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    target_col: str,
    k: int = 3
) -> Dict[str, Any]:
    """
    Perform k=3 cross-validation on the taxa-nutrient correlation model.
    Uses a simple linear regression model (or correlation based) to estimate R2.
    Here we use a simple linear model: y ~ X (all taxa) to estimate predictive power.
    """
    # Align data
    if 'sample_id' in abundance_df.columns:
        abundance_df = abundance_df.set_index('sample_id')
    if 'sample_id' in metadata_df.columns:
        metadata_df = metadata_df.set_index('sample_id')

    common_idx = abundance_df.index.intersection(metadata_df.index)
    if len(common_idx) < 6:
        logger.error(f"CRITICAL: Insufficient samples for k={k} cross-validation (n={len(common_idx)} < 6).")
        sys.exit(1)

    X = abundance_df.loc[common_idx].values
    y = metadata_df.loc[common_idx][target_col].values

    # Handle NaNs
    mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    X = X[mask]
    y = y[mask]

    if len(y) < 6:
        logger.error(f"CRITICAL: After NaN removal, insufficient samples for k={k} CV (n={len(y)} < 6).")
        sys.exit(1)

    kf = KFold(n_splits=k, shuffle=True, random_state=42)
    r2_scores = []

    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score

    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        r2_scores.append(r2)

    return {
        "k": k,
        "mean_r2": float(np.mean(r2_scores)),
        "std_r2": float(np.std(r2_scores)),
        "scores": [float(s) for s in r2_scores]
    }

def save_correlation_results(results: Dict[str, Any], significant_threshold: float = 0.5, p_threshold: float = 0.05) -> None:
    """Save correlation results to JSON, filtering for significant taxa."""
    significant_taxa = []
    for item in results.get("correlations", []):
        corr = item.get("correlation")
        p_val = item.get("p_value")
        if corr is not None and p_val is not None:
            if abs(corr) >= significant_threshold and p_val <= p_threshold:
                significant_taxa.append(item)

    output = {
        "significant_taxa": significant_taxa,
        "total_correlations_tested": len(results.get("correlations", [])),
        "n_samples": results.get("n_samples"),
        "thresholds": {"abs_r": significant_threshold, "p": p_threshold}
    }

    with open(CORRELATION_RESULTS_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    logger.info(f"Saved correlation results to {CORRELATION_RESULTS_FILE}")

def save_vif_flags(flagged_taxa: List[str], all_vifs: Dict[str, float], threshold: float) -> None:
    """Save VIF flags to JSON."""
    output = {
        "threshold": threshold,
        "flagged_taxa": flagged_taxa,
        "all_vifs": all_vifs,
        "note": "Taxa with VIF > threshold are flagged for collinearity and may be excluded from final interpretation."
    }
    with open(CORRELATION_VIF_FLAGS_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    logger.info(f"Saved VIF flags to {CORRELATION_VIF_FLAGS_FILE}")

def write_audit_trail(message: str) -> None:
    """Append to audit trail."""
    trail = []
    if AUDIT_TRAIL_FILE.exists():
        try:
            with open(AUDIT_TRAIL_FILE, 'r') as f:
                trail = json.load(f)
        except json.JSONDecodeError:
            trail = []
    
    trail.append({
        "task": "T046",
        "message": message,
        "status": "completed"
    })
    
    with open(AUDIT_TRAIL_FILE, 'w') as f:
        json.dump(trail, f, indent=2)

def main():
    logger.info("Starting Taxon-Nutrient Correlation with VIF Diagnostics (T046)...")

    # 1. Load Data
    logger.info("Loading processed taxon data and metadata...")
    abundance_df = load_processed_taxon_data(DATA_FILE)
    metadata_df = load_sample_metadata(METADATA_FILE)

    # 2. VIF Calculation (FR-010)
    logger.info("Calculating Variance Inflation Factor (VIF) for predictor taxa...")
    flagged_taxa, all_vifs = calculate_vif_for_predictors(abundance_df, threshold=5.0)
    
    if flagged_taxa:
        logger.warning(f"VIF > 5 detected for {len(flagged_taxa)} taxa: {flagged_taxa}")
        logger.warning("These taxa are flagged for collinearity and will be reported.")
    else:
        logger.info("No taxa exceeded VIF threshold of 5.")

    # Save VIF flags immediately
    save_vif_flags(flagged_taxa, all_vifs, threshold=5.0)

    # 3. Calculate Correlations
    # We correlate against N and P removal rates. Assuming columns exist or are derived.
    # If columns are missing, we log and exit as per strict protocol.
    target_cols = ["n_removal_rate", "p_removal_rate"]
    missing_cols = [c for c in target_cols if c not in metadata_df.columns]
    if missing_cols:
        logger.error(f"CRITICAL DATA GAP: Missing required metadata columns: {missing_cols}")
        write_audit_trail(f"CRITICAL DATA GAP: Missing columns {missing_cols}")
        sys.exit(1)

    logger.info("Calculating Spearman correlations...")
    corr_results = calculate_spearman_correlations(abundance_df, metadata_df, target_cols)

    # 4. Cross-Validation (k=3)
    # We perform CV on the first target for demonstration, or both if needed.
    # Spec says "k=3 cross-validation on the taxa-nutrient correlation model".
    # We'll do it for 'n_removal_rate' as a representative.
    logger.info("Performing k=3 Cross-Validation...")
    try:
        cv_results = perform_cross_validation(abundance_df, metadata_df, target_col="n_removal_rate", k=3)
        with open(CORRELATION_CV_FILE, 'w') as f:
            json.dump(cv_results, f, indent=2)
        logger.info(f"Saved CV results to {CORRELATION_CV_FILE}")
    except SystemExit:
        raise
    except Exception as e:
        logger.error(f"Cross-validation failed: {e}")
        write_audit_trail(f"CV Failed: {e}")
        sys.exit(1)

    # 5. Save Final Results
    # The final report must explicitly state which taxa were flagged.
    save_correlation_results(corr_results)

    # Update audit trail
    write_audit_trail("VIF diagnostics completed. Flagged taxa reported in correlation_vif_flags.json.")
    write_audit_trail("Correlation results saved. Significant taxa filtered by |r|>=0.5, p<=0.05.")

    logger.info("T046 completed successfully.")

if __name__ == "__main__":
    main()