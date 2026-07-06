"""
VIF Diagnostic Computation for Perovskite Stability Descriptors.

This module implements Variance Inflation Factor (VIF) analysis to detect
multicollinearity among compositional descriptors. It flags descriptors with
VIF > 5 and implements an Elastic Net fallback strategy for feature selection.

Outputs:
    data/processed/vif_report.csv: Contains VIF scores, flags, and removal decisions.
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.linear_model import ElasticNetCV
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
VIF_THRESHOLD = 5.0
INPUT_FILE = Path("data/processed/descriptors.csv")
OUTPUT_FILE = Path("data/processed/vif_report.csv")
REQUIRED_COLUMNS = ["formula", "T_d"]  # T_d is the target, not a feature


def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.Series:
    """
    Calculate Variance Inflation Factor for each feature.

    VIF_i = 1 / (1 - R_i^2)
    where R_i^2 is the R-squared of regressing feature i against all other features.

    Args:
        df: DataFrame containing feature columns.
        features: List of column names to calculate VIF for.

    Returns:
        pandas Series with VIF values indexed by feature name.
    """
    if not features:
        return pd.Series(dtype=float)

    vif_data = []
    logger.info(f"Calculating VIF for {len(features)} features...")

    for i, feature in enumerate(features):
        # Create X matrix (all features except current)
        X_cols = [f for f in features if f != feature]
        if not X_cols:
            vif_data.append((feature, 1.0))
            continue

        X = df[X_cols].values
        y = df[feature].values

        # Handle constant columns (VIF is undefined, set to infinity or high value)
        if np.std(y) < 1e-9:
            vif_data.append((feature, np.inf))
            continue

        # Fit regression to get R^2
        try:
            # Standardize X and y for numerical stability
            scaler_x = StandardScaler()
            X_scaled = scaler_x.fit_transform(X)
            scaler_y = StandardScaler()
            y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()

            # Fit linear model
            model = ElasticNetCV(l1_ratio=[0.1, 0.5, 0.9], cv=3, random_state=42, n_jobs=-1)
            model.fit(X_scaled, y_scaled)

            # Calculate R^2
            r2 = model.score(X_scaled, y_scaled)

            # Calculate VIF
            if r2 >= 1.0:
                vif = np.inf
            else:
                vif = 1.0 / (1.0 - r2)

            vif_data.append((feature, vif))

        except Exception as e:
            logger.warning(f"Could not calculate VIF for {feature}: {e}")
            vif_data.append((feature, np.nan))

        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(features)} features")

    return pd.Series([v for _, v in vif_data], index=[f for f, _ in vif_data])


def select_features_with_elastic_net(
    df: pd.DataFrame,
    features: List[str],
    target: str,
    alpha: float = 1.0
) -> List[str]:
    """
    Use Elastic Net to select features based on regularization path.

    Args:
        df: DataFrame with features and target.
        features: List of candidate feature names.
        target: Name of the target column.
        alpha: Regularization strength.

    Returns:
        List of selected feature names.
    """
    if not features:
        return []

    X = df[features].dropna()
    y = df.loc[X.index, target].dropna()

    # Align indices
    common_idx = X.index.intersection(y.index)
    if len(common_idx) == 0:
        logger.warning("No overlapping indices for Elastic Net feature selection")
        return []

    X_clean = X.loc[common_idx]
    y_clean = y.loc[common_idx]

    # Handle constant columns
    non_const_cols = X_clean.columns[X_clean.std() > 1e-9]
    if len(non_const_cols) == 0:
        return []

    X_clean = X_clean[non_const_cols]

    try:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_clean)

        # Use ElasticNetCV to find non-zero coefficients
        enet = ElasticNetCV(
            l1_ratio=[0.1, 0.5, 0.9],
            alphas=np.logspace(-4, 2, 20),
            cv=5,
            random_state=42,
            n_jobs=-1,
            max_iter=1000
        )
        enet.fit(X_scaled, y_clean)

        # Get features with non-zero coefficients
        selected = [col for col, coef in zip(non_const_cols, enet.coef_) if abs(coef) > 1e-9]
        logger.info(f"Elastic Net selected {len(selected)} features: {selected}")
        return selected

    except Exception as e:
        logger.error(f"Elastic Net feature selection failed: {e}")
        # Fallback: return all features if Elastic Net fails
        return list(non_const_cols)


def run_vif_diagnostic(
    input_path: Path = INPUT_FILE,
    output_path: Path = OUTPUT_FILE,
    vif_threshold: float = VIF_THRESHOLD
) -> pd.DataFrame:
    """
    Main VIF diagnostic workflow.

    1. Load descriptors.
    2. Identify feature columns (exclude formula, T_d, and metadata).
    3. Calculate VIF for each feature.
    4. Flag features with VIF > threshold.
    5. If high VIFs exist, run Elastic Net to select a reduced set.
    6. Generate report.

    Args:
        input_path: Path to descriptors.csv.
        output_path: Path to write vif_report.csv.
        vif_threshold: Threshold for flagging multicollinearity.

    Returns:
        DataFrame containing the VIF report.
    """
    logger.info(f"Loading descriptors from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    # Identify feature columns (exclude formula, T_d, and any non-numeric)
    exclude_cols = set(REQUIRED_COLUMNS + ["formula"])
    feature_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]

    if not feature_cols:
        logger.warning("No numeric feature columns found to analyze.")
        report = pd.DataFrame(columns=["feature", "vif", "flagged", "removed", "reason"])
        report.to_csv(output_path, index=False)
        return report

    logger.info(f"Analyzing {len(feature_cols)} feature columns: {feature_cols}")

    # Calculate VIF
    vif_series = calculate_vif(df, feature_cols)

    # Build report
    report_data = []
    features_to_remove = []

    for feature in feature_cols:
        vif_val = vif_series.get(feature, np.nan)
        flagged = vif_val > vif_threshold if not np.isnan(vif_val) else False
        reason = ""

        if np.isnan(vif_val):
            reason = "Calculation failed"
            features_to_remove.append(feature)
        elif flagged:
            reason = f"VIF ({vif_val:.2f}) > {vif_threshold}"
            features_to_remove.append(feature)
        else:
            reason = "Acceptable multicollinearity"

        report_data.append({
            "feature": feature,
            "vif": vif_val,
            "flagged": flagged,
            "removed": False,  # Will update later if Elastic Net is used
            "reason": reason
        })

    report_df = pd.DataFrame(report_data)

    # If high VIFs exist, run Elastic Net fallback
    if report_df["flagged"].any():
        logger.warning(f"Detected {report_df['flagged'].sum()} features with VIF > {vif_threshold}. Running Elastic Net fallback.")
        
        # Use non-flagged features + target to run Elastic Net
        # Actually, we should run Elastic Net on ALL features to see which are truly predictive
        selected_features = select_features_with_elastic_net(df, feature_cols, "T_d")
        
        # Mark removed features
        for i, row in report_df.iterrows():
            feature = row["feature"]
            if feature not in selected_features:
                report_df.at[i, "removed"] = True
                if row["flagged"]:
                    report_df.at[i, "reason"] += " -> Removed by Elastic Net"
                else:
                    report_df.at[i, "reason"] += " -> Removed by Elastic Net (redundant)"

    logger.info(f"VIF report written to {output_path}")
    report_df.to_csv(output_path, index=False)

    return report_df


def main():
    """Entry point for VIF diagnostic script."""
    try:
        run_vif_diagnostic()
        logger.info("VIF diagnostic completed successfully.")
    except Exception as e:
        logger.error(f"VIF diagnostic failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
