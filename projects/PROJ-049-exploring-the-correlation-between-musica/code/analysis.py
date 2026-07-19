"""
Statistical Analysis Module.

Computes Spearman correlations, runs multiple linear regressions, applies FDR correction,
calculates effect sizes, and generates visualizations and reports.
"""

import os
import logging
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, pearsonr
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.formula.api import ols
from statsmodels.stats.multitest import multipletests
from pathlib import Path

from utils import setup_logging, load_config

logger = setup_logging(__name__)
CONFIG = load_config()
RESULTS_DIR = Path("results")
PROCESSED_DIR = Path("data/processed")

def log_transform_column(series: pd.Series) -> pd.Series:
    """Apply log transformation to a series, handling zeros."""
    return np.log1p(series)

def compute_spearman_correlations(df: pd.DataFrame, trait_cols: list, genre_col: str) -> pd.DataFrame:
    """
    Compute Spearman correlations between traits and a specific genre variable.
    
    Args:
        df: Input DataFrame.
        trait_cols: List of personality trait column names.
        genre_col: Column name for the genre variable (standardized).
        
    Returns:
        DataFrame with correlation results.
    """
    results = []
    # Assuming genre_col contains numeric encoding or we iterate unique values
    # For simplicity, we assume we are correlating with a binary indicator or we group by genre
    # A more robust approach: iterate unique genres and correlate trait with binary presence
    
    unique_genres = df[genre_col].unique()
    
    for trait in trait_cols:
        for genre in unique_genres:
            if pd.isna(genre): continue
            binary_genre = (df[genre_col] == genre).astype(int)
            
            rho, p_value = spearmanr(df[trait], binary_genre)
            results.append({
                "trait": trait,
                "genre": genre,
                "rho": rho,
                "p_value": p_value
            })
    
    return pd.DataFrame(results)

def detect_collinearity(df: pd.DataFrame, features: list) -> dict:
    """
    Detect collinear predictors using VIF.
    
    Args:
        df: DataFrame with features.
        features: List of feature column names.
        
    Returns:
        Dict with VIF values and list of dropped features.
    """
    vif_data = {}
    dropped_features = []
    
    X = df[features].dropna()
    if X.empty:
        return {"vif": vif_data, "dropped": dropped_features}
        
    for i, col in enumerate(X.columns):
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[col] = vif
            if vif > 5:
                dropped_features.append(col)
                logger.warning(f"High collinearity detected for {col} (VIF={vif:.2f})")
        except Exception as e:
            logger.warning(f"Could not compute VIF for {col}: {e}")
    
    return {"vif": vif_data, "dropped": dropped_features}

def run_multiple_linear_regression(df: pd.DataFrame, target: str, features: list) -> pd.DataFrame:
    """
    Run multiple linear regression.
    
    Args:
        df: Input DataFrame.
        target: Target variable name.
        features: List of feature names.
        
    Returns:
        DataFrame with regression coefficients.
    """
    # One-hot encode categorical features if necessary
    df_encoded = pd.get_dummies(df, columns=features, drop_first=True)
    
    # Filter to available columns
    available_features = [f for f in features if f in df_encoded.columns]
    # Add dummy columns
    dummy_cols = [c for c in df_encoded.columns if c.startswith(tuple(features))]
    all_predictors = list(set(available_features + dummy_cols))
    
    if not all_predictors:
        return pd.DataFrame()
    
    formula = f"{target} ~ " + " + ".join(all_predictors)
    model = ols(formula, data=df_encoded).fit()
    
    results = []
    for param_name, param_val in model.params.items():
        if param_name != "Intercept":
            results.append({
                "trait": target,
                "predictor": param_name,
                "beta": param_val,
                "p_value": model.pvalues[param_name]
            })
    
    return pd.DataFrame(results)

def apply_fdr_correction(results_df: pd.DataFrame, p_col: str = "p_value", alpha: float = 0.05) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Args:
        results_df: DataFrame with p-values.
        p_col: Column name containing p-values.
        alpha: Significance level.
        
    Returns:
        DataFrame with adjusted p-values and significance flags.
    """
    if results_df.empty:
        return results_df
        
    p_values = results_df[p_col].values
    rejected, p_adj, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    
    results_df["p_adj"] = p_adj
    results_df["is_significant"] = rejected
    return results_df

def calculate_effect_sizes(df: pd.DataFrame, trait: str, genre: str) -> dict:
    """
    Calculate Pearson's r effect size and Fisher's z confidence interval.
    
    Args:
        df: Input DataFrame.
        trait: Trait column name.
        genre: Genre value.
        
    Returns:
        Dict with effect size and CI.
    """
    binary_genre = (df['standard_genre'] == genre).astype(int)
    r, _ = pearsonr(df[trait], binary_genre)
    
    # Fisher's Z transformation
    z = 0.5 * np.log((1 + r) / (1 - r))
    n = len(df)
    se_z = 1 / np.sqrt(n - 3)
    
    z_lower = z - 1.96 * se_z
    z_upper = z + 1.96 * se_z
    
    r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
    
    return {
        "pearson_r": r,
        "ci_lower": r_lower,
        "ci_upper": r_upper
    }

def generate_correlation_heatmap(results_df: pd.DataFrame, output_path: Path):
    """
    Generate a correlation heatmap using seaborn.
    
    Args:
        results_df: DataFrame with correlation results.
        output_path: Path to save the plot.
    """
    logger.info("Generating correlation heatmap...")
    
    # Pivot data for heatmap
    pivot_df = results_df.pivot(index='trait', columns='genre', values='rho')
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot_df, annot=True, cmap='coolwarm', center=0, fmt=".2f", 
                cbar_kws={'label': 'Spearman Rho'})
    plt.title('Correlation between Personality Traits and Music Genres')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Heatmap saved to {output_path}")

def generate_results_report(results_df: pd.DataFrame, output_path: Path):
    """
    Generate a comprehensive results report CSV.
    
    Args:
        results_df: DataFrame with analysis results.
        output_path: Path to save the report.
    """
    logger.info("Generating results report...")
    
    report_data = []
    traits = results_df['trait'].unique()
    genres = results_df['genre'].unique()
    
    for trait in traits:
        for genre in genres:
            row = results_df[(results_df['trait'] == trait) & (results_df['genre'] == genre)]
            if not row.empty:
                row = row.iloc[0]
                effect_sizes = calculate_effect_sizes(
                    pd.read_csv(PROCESSED_DIR / "merged_data.csv"), 
                    trait, genre
                )
                
                report_data.append({
                    "trait": trait,
                    "genre": genre,
                    "rho": row['rho'],
                    "p_value": row['p_value'],
                    "p_adj": row['p_adj'],
                    "is_significant": row['is_significant'],
                    "pearson_r": effect_sizes['pearson_r'],
                    "ci_lower": effect_sizes['ci_lower'],
                    "ci_upper": effect_sizes['ci_upper'],
                    "status": "Significant" if row['is_significant'] else "Non-significant"
                })
            else:
                report_data.append({
                    "trait": trait,
                    "genre": genre,
                    "rho": np.nan,
                    "p_value": np.nan,
                    "p_adj": np.nan,
                    "is_significant": False,
                    "pearson_r": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "status": "Non-significant"
                })
    
    report_df = pd.DataFrame(report_data)
    report_df.to_csv(output_path, index=False)
    logger.info(f"Results report saved to {output_path}")

def run_analysis() -> Optional[Path]:
    """
    Main analysis orchestration.
    
    Returns:
        Path to analysis results, or None if failed.
    """
    try:
        # Load data
        df = pd.read_csv(PROCESSED_DIR / "merged_data.csv")
        
        # Define traits and genre column
        traits = ['Extraversion', 'Agreeableness', 'Conscientiousness', 'Neuroticism', 'Openness']
        genre_col = 'standard_genre'
        
        # 1. Correlations
        corr_results = compute_spearman_correlations(df, traits, genre_col)
        
        # 2. FDR Correction
        corr_results = apply_fdr_correction(corr_results)
        
        # Save intermediate
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        corr_results.to_csv(PROCESSED_DIR / "correlation_results.csv", index=False)
        
        # 3. Regression (Simplified for example)
        # In a full implementation, we would iterate and run regressions with controls
        # Here we simulate the structure
        regression_results = []
        for trait in traits:
            # Dummy regression for demonstration
            reg_df = run_multiple_linear_regression(df, trait, ['age', 'gender', 'country'])
            if not reg_df.empty:
                regression_results.append(reg_df)
        
        if regression_results:
            full_regression = pd.concat(regression_results, ignore_index=True)
        else:
            full_regression = pd.DataFrame(columns=['trait', 'predictor', 'beta', 'p_value'])
        
        # 4. Generate Visualizations
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        generate_correlation_heatmap(corr_results, RESULTS_DIR / "correlation_heatmap.png")
        
        # 5. Generate Report
        generate_results_report(corr_results, RESULTS_DIR / "results_report.csv")
        
        # 6. Save Final Analysis Results
        final_results = pd.merge(corr_results, full_regression, on=['trait'], how='left')
        final_results.to_csv(PROCESSED_DIR / "analysis_results.csv", index=False)
        
        logger.info("Analysis completed successfully.")
        return PROCESSED_DIR / "analysis_results.csv"
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return None

def main():
    """Entry point for script execution."""
    result = run_analysis()
    if result:
        print(f"Success: {result}")
    else:
        print("Failed to complete analysis.")
        exit(1)

if __name__ == "__main__":
    main()
