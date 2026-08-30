"""
Variance Inflation Factor (VIF) Calculator for Perovskite Stability Descriptors.

This module computes VIF scores for all numerical descriptors in the dataset.
It implements an iterative feature removal strategy: if any VIF > 5, the feature
with the highest VIF is removed, and the process repeats until all VIFs are <= 5
or only one feature remains. If removal leads to an empty feature set, it
suggests switching to Elastic Net (handled by the caller or logged).

Output:
  - data/processed/vif_report.csv: A CSV file containing the VIF scores for
    each iteration and the final selected features.
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# Add project root to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate VIF for a list of features in a DataFrame.

    VIF is calculated as 1 / (1 - R^2) where R^2 is from regressing the feature
    against all other features in the list.

    Args:
        df: DataFrame containing the data.
        features: List of feature column names.

    Returns:
        Dictionary mapping feature names to their VIF scores.
    """
    vif_data = {}
    X = df[features].dropna()

    if len(X) == 0:
        return {f: float('inf') for f in features}

    for i, feature in enumerate(features):
        # Regress current feature against all others
        y = X[feature]
        X_other = X.drop(columns=[feature])

        # Handle case where only one feature remains (VIF is 1 by definition, but loop won't run)
        if X_other.shape[1] == 0:
            vif_data[feature] = 1.0
            continue

        try:
            model = LinearRegression()
            model.fit(X_other, y)
            r_squared = model.score(X_other, y)

            # Avoid division by zero if R^2 is 1 (perfect multicollinearity)
            if r_squared >= 1.0:
                vif_data[feature] = float('inf')
            else:
                vif_data[feature] = 1.0 / (1.0 - r_squared)
        except Exception as e:
            logger.warning(f"Error calculating VIF for {feature}: {e}")
            vif_data[feature] = float('inf')

    return vif_data

def run_vif_diagnostic(
    input_path: str,
    output_path: str,
    threshold: float = 5.0,
    target_column: Optional[str] = 'T_d'
) -> Tuple[List[str], pd.DataFrame]:
    """
    Run the VIF diagnostic loop: calculate VIFs, remove highest if > threshold,
    repeat until all <= threshold or features exhausted.

    Args:
        input_path: Path to the input descriptors CSV (e.g., data/processed/descriptors.csv).
        output_path: Path to write the VIF report CSV.
        threshold: VIF threshold for removal (default 5.0).
        target_column: Column to exclude from VIF calculation (the target variable).

    Returns:
        Tuple of (final_features_list, report_dataframe).
    """
    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_path}")
        raise

    # Identify numeric columns excluding the target and non-numeric identifiers
    exclude_cols = [target_column] if target_column and target_column in df.columns else []
    exclude_cols += ['formula', 'perovskite_family', 'source']

    numeric_features = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]

    if not numeric_features:
        logger.error("No numeric features found to calculate VIF.")
        # Create empty report
        report_df = pd.DataFrame(columns=['iteration', 'feature', 'vif_score', 'action'])
        report_df.to_csv(output_path, index=False)
        return [], report_df

    logger.info(f"Starting VIF analysis on {len(numeric_features)} features: {numeric_features}")

    current_features = numeric_features.copy()
    report_rows = []
    iteration = 0

    while len(current_features) > 1:
        iteration += 1
        logger.info(f"Iteration {iteration}: Evaluating {len(current_features)} features")

        vif_scores = calculate_vif(df, current_features)
        
        # Record current state
        for feat, score in vif_scores.items():
            action = "keep"
            report_rows.append({
                'iteration': iteration,
                'feature': feat,
                'vif_score': score,
                'action': action
            })

        max_vif = max(vif_scores.values())
        max_vif_feature = max(vif_scores, key=vif_scores.get)

        logger.info(f"  Max VIF: {max_vif:.4f} for '{max_vif_feature}'")

        if max_vif <= threshold:
            logger.info(f"All VIFs <= {threshold}. Stopping removal process.")
            break

        # Remove the feature with the highest VIF
        logger.warning(f"Removing feature '{max_vif_feature}' (VIF={max_vif:.4f} > {threshold})")
        current_features.remove(max_vif_feature)
        
        # Update action for the removed feature in the report
        for row in report_rows:
            if row['iteration'] == iteration and row['feature'] == max_vif_feature:
                row['action'] = 'removed'
                break

    # Final state record
    iteration += 1
    if len(current_features) > 0:
        final_vif_scores = calculate_vif(df, current_features)
        for feat, score in final_vif_scores.items():
            report_rows.append({
                'iteration': iteration,
                'feature': feat,
                'vif_score': score,
                'action': 'final_kept'
            })
        logger.info(f"Final features kept: {current_features}")
    else:
        logger.warning("All features were removed due to high multicollinearity. Consider switching to Elastic Net.")
        report_rows.append({
            'iteration': iteration,
            'feature': 'NONE',
            'vif_score': 0.0,
            'action': 'all_removed_switch_to_elastic_net'
        })

    report_df = pd.DataFrame(report_rows)
    report_df.to_csv(output_path, index=False)
    
    logger.info(f"VIF report written to {output_path}")
    return current_features, report_df

def main():
    """Main entry point for VIF calculation."""
    # Default paths based on project structure
    input_file = Path("data/processed/descriptors.csv")
    output_file = Path("data/processed/vif_report.csv")

    if not input_file.exists():
        logger.error(f"Required input file not found: {input_file}")
        logger.error("Please ensure T014/T015 have completed and descriptors.csv exists.")
        sys.exit(1)

    features, report = run_vif_diagnostic(str(input_file), str(output_file))
    
    if not features:
        logger.warning("No features survived VIF filtering. The downstream model training should use Elastic Net.")
    
    print(f"VIF Analysis Complete. Report saved to: {output_file}")
    print(f"Final features: {features}")

if __name__ == "__main__":
    main()