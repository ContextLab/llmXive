import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import cross_val_score, LeaveOneOut, KFold
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

# Import from local utils for VIF
from utils import calculate_vif

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_processed_taxon_data(
    feature_table_path: str,
    metadata_path: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load processed feature table and metadata.
    Assumes the feature table has samples as rows and taxa as columns.
    Assumes metadata has sample IDs and nutrient removal rates.
    """
    if not os.path.exists(feature_table_path):
        logger.error(f"Feature table not found: {feature_table_path}")
        sys.exit(1)
    if not os.path.exists(metadata_path):
        logger.error(f"Metadata not found: {metadata_path}")
        sys.exit(1)

    feature_table = pd.read_csv(feature_table_path, index_col=0)
    metadata = pd.read_csv(metadata_path)

    # Ensure sample alignment
    common_samples = list(set(feature_table.index) & set(metadata['sample_id']))
    if len(common_samples) == 0:
        logger.error("No common samples between feature table and metadata.")
        sys.exit(1)

    feature_table = feature_table.loc[common_samples]
    metadata = metadata[metadata['sample_id'].isin(common_samples)].set_index('sample_id')

    return feature_table, metadata

def calculate_spearman_correlations(
    feature_table: pd.DataFrame,
    metadata: pd.DataFrame,
    nutrient_col: str = 'nutrient_removal_rate'
) -> pd.DataFrame:
    """
    Calculate Spearman correlation between each taxon and the nutrient removal rate.
    Returns a DataFrame with correlation coefficients and p-values.
    """
    correlations = []
    p_values = []
    taxa = feature_table.columns

    for taxon in taxa:
        x = feature_table[taxon]
        y = metadata[nutrient_col]

        # Handle constant columns
        if x.std() == 0 or y.std() == 0:
            corr, p_val = 0.0, 1.0
        else:
            corr, p_val = spearmanr(x, y)
            if np.isnan(corr):
                corr, p_val = 0.0, 1.0

        correlations.append(corr)
        p_values.append(p_val)

    results = pd.DataFrame({
        'taxon': taxa,
        'correlation': correlations,
        'p_value': p_values
    })

    return results

def calculate_vif_for_predictors(
    feature_table: pd.DataFrame,
    metadata: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for taxa used as predictors.
    Flags taxa with VIF > 5.
    """
    # Prepare data: samples x taxa
    X = feature_table.values
    taxa = feature_table.columns

    vif_data = []
    for i, taxon in enumerate(taxa):
        # VIF calculation requires a matrix of predictors.
        # Here we calculate VIF for each taxon against all others.
        # If n_samples < n_taxa, VIF calculation might be unstable or impossible.
        # We handle this by checking dimensions.
        if X.shape[0] < X.shape[1]:
            # Under-determined case, VIF is not well-defined in standard OLS sense
            # We assign a high flag or NaN, but task T033 handles the flagging logic.
            # For this function, we return a placeholder or NaN if under-determined.
            vif_val = np.nan
        else:
            try:
                # Standard VIF calculation: regress one variable on others
                X_other = np.delete(X, i, axis=1)
                reg = LinearRegression().fit(X_other, X[:, i])
                r_squared = reg.score(X_other, X[:, i])
                if r_squared >= 1.0:
                    vif_val = np.inf
                else:
                    vif_val = 1 / (1 - r_squared)
            except Exception as e:
                logger.warning(f"Could not calculate VIF for {taxon}: {e}")
                vif_val = np.nan

        vif_data.append({'taxon': taxon, 'vif': vif_val})

    return pd.DataFrame(vif_data)

def perform_cross_validation(
    feature_table: pd.DataFrame,
    metadata: pd.DataFrame,
    nutrient_col: str = 'nutrient_removal_rate',
    k: int = 3
) -> Dict[str, Any]:
    """
    Perform k-fold cross-validation on the taxa-nutrient correlation model.
    If n_samples < 2*k (making k-fold impossible), fallback to LOO.
    Returns a dictionary with mean R2 and std dev.
    """
    X = feature_table.values
    y = metadata[nutrient_col].values
    n_samples = X.shape[0]

    # Fallback logic
    if n_samples < 2 * k:
        logger.warning(f"Sample size ({n_samples}) is too small for {k}-fold CV. Fallback to Leave-One-Out.")
        cv = LeaveOneOut()
        cv_type = "LOO"
    else:
        # Ensure we have at least k folds
        if n_samples < k:
            logger.error(f"Sample size ({n_samples}) is less than k ({k}). Cannot perform CV.")
            sys.exit(1)
        cv = KFold(n_splits=k, shuffle=True, random_state=42)
        cv_type = f"{k}-fold"

    model = LinearRegression()
    scaler = StandardScaler()

    # Scale features
    X_scaled = scaler.fit_transform(X)

    # Perform cross-validation
    # We use negative mean squared error or r2 directly
    # cross_val_score returns scores. For R2, we ask for 'r2'
    try:
        scores = cross_val_score(
            model, X_scaled, y, cv=cv, scoring='r2', n_jobs=-1
        )
    except Exception as e:
        logger.error(f"Cross-validation failed: {e}")
        sys.exit(1)

    mean_r2 = float(np.mean(scores))
    std_r2 = float(np.std(scores))

    return {
        "cv_type": cv_type,
        "n_samples": n_samples,
        "n_folds": k if cv_type != "LOO" else n_samples,
        "mean_r2": mean_r2,
        "std_r2": std_r2
    }

def save_correlation_results(
    results_df: pd.DataFrame,
    vif_df: pd.DataFrame,
    output_path: str,
    threshold_r: float = 0.5,
    threshold_p: float = 0.05
) -> None:
    """
    Save the final correlation report.
    Filters for |r| >= 0.5 and p <= 0.05.
    """
    # Merge VIF data
    final_df = results_df.merge(vif_df, on='taxon', how='left')

    # Filter significant correlations
    significant_df = final_df[
        (final_df['correlation'].abs() >= threshold_r) &
        (final_df['p_value'] <= threshold_p)
    ]

    report = {
        "threshold_r": threshold_r,
        "threshold_p": threshold_p,
        "total_taxa_tested": len(final_df),
        "significant_taxa_count": len(significant_df),
        "significant_taxa": significant_df.to_dict(orient='records')
    }

    if len(significant_df) == 0:
        report["message"] = "No taxa met the criteria |r|>=0.5 and p<=0.05."
        logger.info("No significant taxa found meeting the criteria.")

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Correlation results saved to {output_path}")

def save_cv_results(cv_data: Dict[str, Any], output_path: str) -> None:
    """
    Save cross-validation results to JSON.
    """
    with open(output_path, 'w') as f:
        json.dump(cv_data, f, indent=2)
    logger.info(f"CV results saved to {output_path}")

def main():
    """
    Main entry point for T034: Cross-validation and correlation reporting.
    """
    # Paths
    base_path = Path("data/processed")
    feature_table_path = base_path / "filtered_feature_table.csv"
    metadata_path = base_path / "filtered_metadata.csv"
    cv_output_path = base_path / "correlation_cv_results.json"
    correlation_output_path = base_path / "correlation_results.json"

    # Check dependencies
    if not feature_table_path.exists() or not metadata_path.exists():
        logger.error("Required processed data files missing. Run T012/T013 first.")
        sys.exit(1)

    # Load data
    logger.info("Loading processed taxon data and metadata...")
    feature_table, metadata = load_processed_taxon_data(
        str(feature_table_path), str(metadata_path)
    )

    # 1. Calculate Spearman correlations
    logger.info("Calculating Spearman correlations...")
    corr_results = calculate_spearman_correlations(feature_table, metadata)

    # 2. Calculate VIF
    logger.info("Calculating VIF for predictors...")
    vif_results = calculate_vif_for_predictors(feature_table, metadata)

    # 3. Perform Cross-Validation (T034 Core)
    logger.info("Performing Cross-Validation (k=3)...")
    cv_data = perform_cross_validation(feature_table, metadata, k=3)
    save_cv_results(cv_data, str(cv_output_path))

    # 4. Save Final Correlation Report
    logger.info("Saving correlation results...")
    save_correlation_results(
        corr_results, vif_results, str(correlation_output_path)
    )

    logger.info("T034 completed successfully.")

if __name__ == "__main__":
    main()
