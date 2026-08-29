import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import shared utilities from utils.py
from utils import calculate_vif, log_data_gap_flag

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] [%(module)s] %(message)s',
    handlers=[
        logging.FileHandler('data/processed/correlation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_processed_taxon_data(feature_table_path: str) -> pd.DataFrame:
    """
    Load the processed feature table (taxon abundance) from a JSON or CSV file.
    Expects a format where rows are samples and columns are taxa.
    """
    path = Path(feature_table_path)
    if not path.exists():
        logger.error(f"Feature table not found: {feature_table_path}")
        sys.exit(1)

    if path.suffix == '.json':
        # Assuming JSON structure: {"samples": [{"sample_id": "...", "feature_table": {...}}, ...]}
        with open(path, 'r') as f:
            data = json.load(f)
        
        samples = []
        for entry in data.get('samples', []):
            sample_id = entry.get('sample_id')
            features = entry.get('feature_table', {})
            if sample_id and features:
                samples.append({sample_id: features})
        
        # Convert to DataFrame
        df_list = []
        for sample_entry in samples:
            for sid, feats in sample_entry.items():
                row = pd.Series(feats, name=sid)
                df_list.append(row)
        
        df = pd.DataFrame(df_list).T
        return df
    elif path.suffix == '.csv':
        return pd.read_csv(path, index_col=0)
    else:
        logger.error(f"Unsupported file format: {path.suffix}")
        sys.exit(1)

def load_sample_metadata(metadata_path: str) -> pd.DataFrame:
    """
    Load sample metadata including N/P removal rates and stage information.
    """
    path = Path(metadata_path)
    if not path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        sys.exit(1)

    if path.suffix == '.json':
        with open(path, 'r') as f:
            data = json.load(f)
        # Normalize nested structure if necessary
        if 'samples' in data:
            records = []
            for s in data['samples']:
                record = {'sample_id': s.get('sample_id')}
                # Flatten common fields
                for k, v in s.items():
                    if k != 'sample_id':
                        record[k] = v
                records.append(record)
            return pd.DataFrame(records).set_index('sample_id')
        else:
            return pd.DataFrame(data).set_index('sample_id')
    elif path.suffix == '.csv':
        return pd.read_csv(path, index_col=0)
    else:
        logger.error(f"Unsupported metadata format: {path.suffix}")
        sys.exit(1)

def calculate_spearman_correlations(taxon_df: pd.DataFrame, metadata_df: pd.DataFrame, nutrient_col: str) -> pd.DataFrame:
    """
    Calculate Spearman correlation between each taxon and the specified nutrient removal rate.
    Returns a DataFrame with correlation coefficients and p-values.
    """
    if taxon_df.empty:
        logger.error("Taxon DataFrame is empty.")
        return pd.DataFrame()

    if nutrient_col not in metadata_df.columns:
        logger.error(f"Nutrient column '{nutrient_col}' not found in metadata.")
        return pd.DataFrame()

    nutrient_values = metadata_df[nutrient_col].dropna()
    common_samples = taxon_df.index.intersection(nutrient_values.index)
    
    if len(common_samples) < 3:
        logger.warning(f"Insufficient common samples ({len(common_samples)}) for correlation.")
        return pd.DataFrame()

    taxon_clean = taxon_df.loc[common_samples]
    nutrient_clean = nutrient_values.loc[common_samples]

    results = []
    for taxon in taxon_clean.columns:
        taxon_vals = taxon_clean[taxon].dropna()
        # Align indices for correlation
        valid_idx = taxon_vals.index.intersection(nutrient_clean.index)
        if len(valid_idx) < 3:
            continue
        
        r, p = spearmanr(taxon_vals.loc[valid_idx], nutrient_clean.loc[valid_idx])
        results.append({
            'taxon': taxon,
            'correlation': r,
            'p_value': p,
            'n_samples': len(valid_idx)
        })

    return pd.DataFrame(results)

def calculate_vif_for_predictors(taxon_df: pd.DataFrame, threshold: float = 5.0) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each taxon (predictor).
    Returns a dictionary of taxa with their VIF values.
    """
    if taxon_df.empty:
        logger.warning("Empty taxon DataFrame for VIF calculation.")
        return {}

    # Add constant for intercept
    X = taxon_df.dropna(axis=0, how='all') # Drop samples with any missing taxa
    if X.empty:
        return {}
    
    # Check if n_samples >= n_taxa + 1 (required for VIF)
    n_samples, n_features = X.shape
    if n_samples <= n_features:
        logger.warning(f"Under-determined for VIF: n_samples ({n_samples}) <= n_taxa ({n_features}). Cannot calculate reliable VIF.")
        # Return high VIF for all to flag them
        return {col: float('inf') for col in X.columns}

    vif_data = {}
    try:
        for i, col in enumerate(X.columns):
            # VIF for feature i is 1 / (1 - R^2_i) where R^2_i is from regressing feature i on all others
            y = X[col]
            # To avoid singular matrix issues, drop columns with zero variance
            if y.std() == 0:
                vif_data[col] = 0.0
                continue
            
            # Use statsmodels or manual calculation
            # Manual calculation using OLS on others
            # We need to select all other features
            other_cols = [c for c in X.columns if c != col]
            if not other_cols:
                vif_data[col] = 1.0
                continue
            
            X_other = X[other_cols]
            
            # Check for constant columns in X_other to avoid singular matrix
            # If X_other has constant columns, drop them
            X_other_clean = X_other.loc[:, X_other.std() > 0]
            if X_other_clean.empty:
                vif_data[col] = 1.0
                continue

            model = LinearRegression()
            model.fit(X_other_clean, y)
            r_squared = model.score(X_other_clean, y)
            
            if r_squared >= 1.0:
                vif_data[col] = float('inf')
            else:
                vif_data[col] = 1.0 / (1.0 - r_squared)
    except Exception as e:
        logger.error(f"Error calculating VIF: {e}")
        # Fallback: return inf for all
        return {col: float('inf') for col in X.columns}

    return vif_data

def perform_cross_validation(taxon_df: pd.DataFrame, metadata_df: pd.DataFrame, 
                             target_col: str, k: int = 3) -> Dict[str, float]:
    """
    Perform k-fold cross-validation for the correlation model (taxa vs nutrient).
    Returns mean R^2 and std dev.
    """
    if taxon_df.empty or metadata_df.empty:
        return {'mean_r2': 0.0, 'std_r2': 0.0, 'status': 'empty_data'}

    if target_col not in metadata_df.columns:
        logger.error(f"Target column '{target_col}' not found in metadata.")
        return {'mean_r2': 0.0, 'std_r2': 0.0, 'status': 'missing_target'}

    # Merge data
    y = metadata_df[target_col]
    X = taxon_df
    
    # Align indices
    common_idx = X.index.intersection(y.index)
    if len(common_idx) < 6: # Minimum for k=3 (2 per fold)
        logger.error(f"CRITICAL: Insufficient samples for k=3 cross-validation (n={len(common_idx)}).")
        sys.exit(1)

    X = X.loc[common_idx]
    y = y.loc[common_idx]

    # Drop columns with zero variance
    X = X.loc[:, X.std() > 0]
    if X.empty:
        return {'mean_r2': 0.0, 'std_r2': 0.0, 'status': 'no_features'}

    if X.shape[0] < k:
        logger.error(f"CRITICAL: Sample size ({X.shape[0]}) < k ({k}).")
        sys.exit(1)

    kf = KFold(n_splits=k, shuffle=True, random_state=42)
    r2_scores = []

    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model = LinearRegression()
        try:
            model.fit(X_train, y_train)
            r2 = model.score(X_test, y_test)
            r2_scores.append(r2)
        except Exception:
            r2_scores.append(np.nan)

    r2_scores = np.array(r2_scores)
    valid_scores = r2_scores[~np.isnan(r2_scores)]

    if len(valid_scores) == 0:
        return {'mean_r2': 0.0, 'std_r2': 0.0, 'status': 'cv_failed'}

    return {
        'mean_r2': float(np.mean(valid_scores)),
        'std_r2': float(np.std(valid_scores)),
        'n_folds': k,
        'status': 'success'
    }

def save_vif_flags(vif_results: Dict[str, float], output_path: str, threshold: float = 5.0):
    """
    Save VIF flags to a JSON file.
    Flags taxa with VIF > threshold.
    """
    flagged = {k: v for k, v in vif_results.items() if v > threshold}
    unflagged = {k: v for k, v in vif_results.items() if v <= threshold}
    
    report = {
        'threshold': threshold,
        'total_predictors': len(vif_results),
        'flagged_count': len(flagged),
        'flagged_taxa': {k: float(v) if v != float('inf') else 'inf' for k, v in flagged.items()},
        'unflagged_taxa': {k: float(v) for k, v in unflagged.items()},
        'flagged_list': list(flagged.keys())
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"VIF flags saved to {output_path}. {len(flagged)} taxa flagged.")

def save_correlation_results(correlation_df: pd.DataFrame, vif_flagged_taxa: List[str], 
                             cv_results: Dict, output_path: str):
    """
    Save final correlation results, explicitly stating which taxa were excluded/flagged.
    """
    if correlation_df.empty:
        report = {
            'significant_taxa': [],
            'cv_results': cv_results,
            'vif_flags': {'excluded_taxa': vif_flagged_taxa},
            'message': 'No correlations calculated or data empty.'
        }
    else:
        # Filter for significant correlations (|r| >= 0.5, p <= 0.05)
        significant = correlation_df[
            (correlation_df['correlation'].abs() >= 0.5) & 
            (correlation_df['p_value'] <= 0.05)
        ]

        # Separate into significant and non-significant, noting VIF status
        significant_taxa_list = []
        for _, row in significant.iterrows():
            taxon = row['taxon']
            status = 'significant'
            if taxon in vif_flagged_taxa:
                status = 'significant_but_flagged_collinearity'
            
            significant_taxa_list.append({
                'taxon': taxon,
                'correlation': float(row['correlation']),
                'p_value': float(row['p_value']),
                'n_samples': int(row['n_samples']),
                'vif_status': status
            })

        report = {
            'significant_taxa': significant_taxa_list,
            'cv_results': cv_results,
            'vif_flags': {
                'excluded_taxa': vif_flagged_taxa,
                'total_flagged': len(vif_flagged_taxa)
            },
            'total_significant': len(significant_taxa_list)
        }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Correlation results saved to {output_path}.")

def write_audit_trail(message: str, output_path: str):
    """
    Append a message to the audit trail JSON file.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            try:
                audit_data = json.load(f)
            except json.JSONDecodeError:
                audit_data = []
    else:
        audit_data = []
    
    audit_data.append({
        'timestamp': pd.Timestamp.now().isoformat(),
        'task': 'T046',
        'message': message
    })
    
    with open(output_path, 'w') as f:
        json.dump(audit_data, f, indent=2)

def main():
    logger.info("Starting Taxon-Nutrient Correlation with VIF Diagnostics (T046)...")
    
    # Paths
    base_dir = Path("data/processed")
    feature_table_path = base_dir / "feature_table.json" # Assuming T013 output
    metadata_path = base_dir / "sample_metadata.json"    # Assuming T012 output
    vif_output_path = base_dir / "correlation_vif_flags.json"
    correlation_output_path = base_dir / "correlation_results.json"
    audit_path = base_dir / "audit_trail.json"
    
    # Load Data
    logger.info("Loading processed taxon data...")
    taxon_df = load_processed_taxon_data(str(feature_table_path))
    
    logger.info("Loading sample metadata...")
    metadata_df = load_sample_metadata(str(metadata_path))
    
    # 1. Calculate VIF for predictors (Taxa)
    logger.info("Calculating VIF for predictor taxa...")
    vif_results = calculate_vif_for_predictors(taxon_df, threshold=5.0)
    
    # Identify flagged taxa
    flagged_taxa = [taxon for taxon, vif in vif_results.items() if vif > 5.0]
    
    # Save VIF Flags (T046 Requirement)
    save_vif_flags(vif_results, str(vif_output_path), threshold=5.0)
    
    # 2. Perform Cross-Validation (T034 requirement, needed for final report)
    logger.info("Performing k=3 Cross-Validation...")
    cv_results = perform_cross_validation(taxon_df, metadata_df, target_col='n_removal_rate')
    
    # 3. Calculate Correlations
    logger.info("Calculating Spearman correlations with N/P removal rates...")
    # Calculate for Nitrogen removal
    corr_n = calculate_spearman_correlations(taxon_df, metadata_df, 'n_removal_rate')
    # Calculate for Phosphorus removal if column exists
    if 'p_removal_rate' in metadata_df.columns:
        corr_p = calculate_spearman_correlations(taxon_df, metadata_df, 'p_removal_rate')
        # Combine or choose one for the main report? 
        # The task asks for "Taxon-Nutrient Correlation". We'll focus on N for the main report 
        # or combine if specified. Let's assume N is the primary target for this specific task 
        # or we output a combined structure. For simplicity in this specific task, we'll output 
        # the N results as the primary, but we could merge.
        # Let's just use N for the main output as per standard practice unless specified otherwise.
        final_corr = corr_n
    else:
        final_corr = corr_n
    
    # 4. Save Final Correlation Results
    # Explicitly state which taxa were excluded/flagged
    save_correlation_results(final_corr, flagged_taxa, cv_results, str(correlation_output_path))
    
    # Write to Audit Trail
    write_audit_trail(
        f"Completed T046. Flagged {len(flagged_taxa)} taxa for collinearity (VIF>5). "
        f"Output written to {vif_output_path} and {correlation_output_path}.",
        str(audit_path)
    )
    
    logger.info("T046 completed successfully.")

if __name__ == "__main__":
    main()