import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.linear_model import ElasticNet
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from utils import get_project_root_path, get_data_processed_path, get_data_qc_path, setup_logger, write_json_log

logger = setup_logger("regression")

def load_merged_data():
    """Load the merged dataset if it exists."""
    merged_path = get_data_processed_path() / "merged_dataset.parquet"
    if not merged_path.exists():
        logger.warning("Merged dataset not found at %s. Skipping regression analysis.", merged_path)
        return None
    return pd.read_parquet(merged_path)

def apply_clr_transform(df, taxa_cols):
    """Apply Centered Log-Ratio transform to taxa columns."""
    df_transformed = df.copy()
    for col in taxa_cols:
        if col in df_transformed.columns:
            # Add small constant to avoid log(0)
            df_transformed[col] = df_transformed[col] + 1e-6
            # CLR transform
            log_vals = np.log(df_transformed[col])
            geometric_mean = np.exp(log_vals.mean())
            df_transformed[col] = log_vals - np.log(geometric_mean)
    return df_transformed

def prepare_features(df, taxa_cols, covariates=['age', 'sex', 'bmi']):
    """Prepare features for regression."""
    # Filter out rows with missing values in key columns
    required_cols = taxa_cols + covariates + ['cognitive_score_z']
    available_cols = [col for col in required_cols if col in df.columns]
    df_clean = df[available_cols].dropna()

    if len(df_clean) == 0:
        logger.error("No valid data points after cleaning.")
        return None, None, None

    X = df_clean[taxa_cols + covariates]
    y = df_clean['cognitive_score_z']

    # Standardize covariates (not taxa, as they are already CLR transformed)
    scaler = StandardScaler()
    covariates_data = df_clean[covariates]
    if covariates_data.shape[1] > 0:
        covariates_scaled = scaler.fit_transform(covariates_data)
        X_scaled = pd.DataFrame(
            np.hstack([X[taxa_cols].values, covariates_scaled]),
            columns=X[taxa_cols].columns.tolist() + covariates,
            index=X.index
        )
    else:
        X_scaled = X

    return X_scaled, y, df_clean.index

def fit_lasso_elasticnet(X, y, alphas=[0.01, 0.1, 1.0], l1_ratios=[0.5]):
    """Fit LASSO/Elastic Net models and select best based on CV."""
    best_model = None
    best_score = -np.inf
    best_alpha = None
    best_l1_ratio = None

    for alpha in alphas:
        for l1_ratio in l1_ratios:
            model = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=42, max_iter=10000)
            try:
                scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
                mean_score = scores.mean()
                if mean_score > best_score:
                    best_score = mean_score
                    best_model = model
                    best_alpha = alpha
                    best_l1_ratio = l1_ratio
            except Exception as e:
                logger.warning("Failed to fit model with alpha=%s, l1_ratio=%s: %s", alpha, l1_ratio, e)
                continue

    if best_model is None:
        logger.error("No valid model could be fitted.")
        return None, None, None, None

    best_model.fit(X, y)
    return best_model, best_alpha, best_l1_ratio, best_score

def save_results(model, X, y, alpha, l1_ratio, cv_score):
    """Save regression results with associational framing."""
    output_dir = get_data_processed_path()
    output_dir.mkdir(parents=True, exist_ok=True)

    if model is None:
        logger.warning("No model to save.")
        return

    # Extract coefficients
    feature_names = X.columns
    coefficients = model.coef_
    intercept = model.intercept_

    results_df = pd.DataFrame({
        'feature': feature_names,
        'coefficient': coefficients,
        'framing': 'associational',
        'interpretation_note': 'Coefficients represent statistical associations, not causal effects.'
    })

    # Save to parquet
    output_file = output_dir / "regression_results.parquet"
    results_df.to_parquet(output_file, index=False)
    logger.info("Regression results saved to %s", output_file)

    # Save metadata with associational framing
    metadata = {
        "analysis_type": "Elastic Net Regression",
        "framing": "associational",
        "interpretation": "Regression coefficients indicate statistical associations between predictors and cognitive scores. No causal inference should be made.",
        "alpha": alpha,
        "l1_ratio": l1_ratio,
        "cross_validation_score": float(cv_score),
        "n_samples": len(y),
        "n_features": len(feature_names),
        "significant_features": int((np.abs(coefficients) > 0.01).sum()),
        "generated_at": pd.Timestamp.now().isoformat()
    }

    metadata_file = output_dir / "regression_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info("Regression metadata saved to %s", metadata_file)

def main():
    """Main execution function for regression analysis."""
    logger.info("Starting regression analysis...")

    # Load merged data
    df = load_merged_data()
    if df is None:
        logger.info("No merged data available. Skipping regression analysis.")
        # Create a placeholder report indicating data gap
        output_dir = get_data_processed_path()
        output_dir.mkdir(parents=True, exist_ok=True)
        metadata = {
            "analysis_type": "Elastic Net Regression",
            "status": "SKIPPED",
            "reason": "Data Gap - No merged dataset available",
            "framing": "associational",
            "interpretation": "Analysis skipped due to inability to link individual-level microbiome and cognitive data.",
            "generated_at": pd.Timestamp.now().isoformat()
        }
        metadata_file = output_dir / "regression_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        return

    # Identify taxa columns
    taxa_cols = [col for col in df.columns if col.startswith('taxa_')]
    if not taxa_cols:
        logger.error("No taxa columns found in dataset.")
        return

    # Apply CLR transform
    df_clr = apply_clr_transform(df, taxa_cols)

    # Prepare features
    X, y, indices = prepare_features(df_clr, taxa_cols)
    if X is None:
        return

    # Fit model
    model, alpha, l1_ratio, cv_score = fit_lasso_elasticnet(X, y)
    if model is None:
        return

    # Save results with associational framing
    save_results(model, X, y, alpha, l1_ratio, cv_score)

    logger.info("Regression analysis completed successfully.")

if __name__ == "__main__":
    main()
