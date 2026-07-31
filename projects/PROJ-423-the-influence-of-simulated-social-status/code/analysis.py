import os
import sys
import json
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from statsmodels.formula.api import ols, glm
from typing import Dict, List, Tuple, Optional, Any
import warnings

# Import local project utilities and models
# Note: Assuming these are available in the PYTHONPATH or relative imports are configured
from logger import get_logger, setup_logger
from config import load_decision_record
from utils import set_seed, load_json, save_json

logger = get_logger(__name__)

def validate_data_structure(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates the data structure (between-subjects vs within-subjects)
    and returns a configuration dictionary.
    """
    if 'participant_id' not in df.columns:
        raise ValueError("Data must contain 'participant_id' column.")
    
    n_subjects = df['participant_id'].nunique()
    n_obs = len(df)
    
    # Check for repetition
    is_within = n_obs > n_subjects
    structure_type = "within" if is_within else "between"
    
    config = {
        "type": structure_type,
        "n_subjects": n_subjects,
        "n_observations": n_obs
    }
    
    # Save to processed directory
    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/structure_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Data structure validated: {structure_type} ({n_subjects} subjects, {n_obs} obs)")
    return config

def fit_fixed_effects(df: pd.DataFrame, formula: str, family=None) -> Any:
    """
    Fits a Fixed-Effects model (OLS or GLM) based on the provided formula.
    """
    if family is None:
        # Default to OLS for continuous outcomes
        model = ols(formula, data=df)
    else:
        # Use GLM for other families (e.g., Binomial)
        model = glm(formula, data=df, family=family)
    
    result = model.fit()
    return result

def fit_mixed_effects(df: pd.DataFrame, formula: str) -> Any:
    """
    Fits a Mixed-Effects model.
    Note: statsmodels mixedlm requires specific handling of the grouping variable.
    """
    from statsmodels.regression.mixed_linear_model import MixedLM
    
    # Parse formula to extract grouping variable if not explicitly handled
    # For simplicity, assuming formula is 'y ~ x1 + x2 + (1|group)' style
    # We need to extract the grouping column manually or use a parser.
    # Given the task context, we assume standard statsmodels mixedlm usage.
    
    # Basic implementation assuming 'participant_id' is the group
    # and the formula provided is the fixed effects part.
    # If the formula includes random effects syntax, we need to parse it.
    # Here we assume the caller passes the fixed effects formula and we handle grouping.
    
    # Re-parsing for statsmodels MixedLM which takes 'endog', 'exog', 'groups'
    # This is a simplified wrapper.
    
    # For this specific task, we assume the formula is fixed effects only
    # and we add the random intercept for participant_id.
    
    # To support formula string like 'risk_taking ~ status_level * observed_behavior'
    # We use patsy to create design matrices.
    import patsy
    
    y, X = patsy.dmatrices(formula, df, return_type='dataframe')
    
    # Grouping variable
    groups = df['participant_id']
    
    # Fit MixedLM
    # Note: MixedLM expects exog to be the design matrix for fixed effects
    # and exog_re for random effects (usually intercept).
    # We will use the standard formula interface if available or manual construction.
    
    # Using MixedLM directly with design matrices
    model = MixedLM(y, X, groups=groups)
    result = model.fit()
    return result

def calculate_vif(df: pd.DataFrame, formula: str) -> pd.DataFrame:
    """
    Calculates Variance Inflation Factors (VIF) for predictors.
    """
    import patsy
    y, X = patsy.dmatrices(formula, df, return_type='dataframe')
    
    # Remove intercept if present for VIF calculation (statsmodels VIF usually excludes intercept)
    # Ensure X is a DataFrame
    if isinstance(X, pd.DataFrame):
        # Drop intercept column if it exists (usually named 'Intercept')
        cols = [c for c in X.columns if c != 'Intercept']
        X_vif = X[cols]
    else:
        X_vif = X[:, 1:] # Skip first column if it's intercept
    
    vif_data = []
    for col in X_vif.columns:
        try:
            vif = sm.stats.variance_inflation_factor(X_vif.values, list(X_vif.columns).index(col))
            vif_data.append({"variable": col, "VIF": vif})
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
    
    vif_df = pd.DataFrame(vif_data)
    
    # Flag high VIF
    if not vif_df.empty:
        high_vif = vif_df[vif_df['VIF'] > 5.0]
        if not high_vif.empty:
            logger.warning(f"High VIF detected (>5.0): {high_vif['variable'].tolist()}")
    
    return vif_df

def analyze_interaction(df: pd.DataFrame, formula: str, family=None) -> Dict[str, Any]:
    """
    Analyzes the interaction term in the model.
    """
    if family:
        result = fit_fixed_effects(df, formula, family)
    else:
        result = fit_fixed_effects(df, formula)
    
    # Extract interaction term coefficient
    # Assuming formula has 'status_level * observed_behavior'
    # The interaction term name depends on the categorical encoding
    # We look for a term containing '*' or ':'
    
    interaction_terms = [term for term in result.params.index if '*' in term or ':' in term]
    
    if not interaction_terms:
        logger.warning("No interaction term found in model summary.")
        return {"interaction_coefficient": None, "p_value": None, "std_err": None}
    
    # Take the first interaction term found (or handle multiple if needed)
    term = interaction_terms[0]
    
    return {
        "interaction_coefficient": float(result.params[term]),
        "std_err": float(result.bse[term]),
        "p_value": float(result.pvalues[term]),
        "term_name": term,
        "model_summary": str(result.summary())
    }

def get_bootstrap_se(df: pd.DataFrame, formula: str, n_boot: int = 1000) -> float:
    """
    Calculates bootstrap standard errors for the interaction term.
    """
    # Simple bootstrap implementation
    interaction_results = []
    
    # Identify interaction term name from full model first
    full_result = ols(formula, data=df).fit()
    interaction_term = [t for t in full_result.params.index if '*' in t or ':' in t][0]
    
    for i in range(n_boot):
        sample = df.sample(n=len(df), replace=True)
        try:
            res = ols(formula, data=sample).fit()
            interaction_results.append(res.params[interaction_term])
        except Exception:
            continue
    
    if not interaction_results:
        return np.nan
    
    return np.std(interaction_results)

def analyze_interaction_with_bootstrap(df: pd.DataFrame, formula: str, n_boot: int = 1000) -> Dict[str, Any]:
    """
    Analyzes interaction with bootstrap standard errors.
    """
    base_analysis = analyze_interaction(df, formula)
    se = get_bootstrap_se(df, formula, n_boot)
    
    base_analysis["bootstrap_se"] = se
    # Recalculate p-value with bootstrap SE if desired, or just report it
    return base_analysis

def run_sensitivity_analysis(df: pd.DataFrame, formula: str, threshold_range: List[float] = None) -> pd.DataFrame:
    """
    Runs sensitivity analysis by sweeping outlier exclusion thresholds.
    Calculates deviations relative to cell means.
    """
    if threshold_range is None:
        threshold_range = [1.0, 1.5, 2.0, 2.5, 3.0]
    
    results = []
    
    # Identify grouping columns for cell means
    # Assuming formula is 'risk_taking ~ status_level * observed_behavior'
    # We need the columns involved in the interaction
    cols = formula.split('~')[1].strip()
    # Simple parsing for 'status_level * observed_behavior'
    # In a real scenario, we'd use patsy to parse the formula structure
    # Here we assume the user knows the columns or we extract them from the dataframe
    
    # For this task, we assume the dataframe has 'status_level' and 'observed_behavior'
    group_cols = ['status_level', 'observed_behavior']
    
    for thresh in threshold_range:
        df_clean = df.copy()
        
        # Calculate residuals from a full model to identify outliers
        # Or calculate based on cell means as per task description
        # "calculating deviations relative to the *cell mean* within each of the experimental conditions"
        
        # Group by condition and calculate mean
        cell_stats = df_clean.groupby(group_cols)['risk_taking'].agg(['mean', 'std']).reset_index()
        cell_stats.columns = group_cols + ['cell_mean', 'cell_std']
        
        # Merge back
        df_clean = df_clean.merge(cell_stats, on=group_cols, how='left')
        
        # Calculate deviation
        df_clean['deviation'] = (df_clean['risk_taking'] - df_clean['cell_mean']).abs()
        
        # Identify outliers: deviation > thresh * cell_std
        # Handle division by zero if std is 0
        df_clean['is_outlier'] = df_clean.apply(
            lambda row: row['deviation'] > (thresh * row['cell_std']) if row['cell_std'] > 0 else False,
            axis=1
        )
        
        df_filtered = df_clean[~df_clean['is_outlier']].copy()
        
        if len(df_filtered) == 0:
            logger.warning(f"No data remaining at threshold {thresh}")
            results.append({
                "threshold": thresh,
                "n_obs": 0,
                "interaction_coefficient": None,
                "p_value": None
            })
            continue
        
        # Re-run analysis
        try:
            analysis = analyze_interaction(df_filtered, formula)
            results.append({
                "threshold": thresh,
                "n_obs": len(df_filtered),
                "interaction_coefficient": analysis['interaction_coefficient'],
                "p_value": analysis['p_value']
            })
        except Exception as e:
            logger.error(f"Analysis failed at threshold {thresh}: {e}")
            results.append({
                "threshold": thresh,
                "n_obs": len(df_filtered),
                "interaction_coefficient": None,
                "p_value": None
            })
    
    return pd.DataFrame(results)

def perform_post_hoc_comparisons(df: pd.DataFrame, formula: str, family=None) -> pd.DataFrame:
    """
    Performs post-hoc pairwise comparisons with Bonferroni correction.
    Executes UNCONDITIONALLY regardless of primary interaction significance (FR-006).
    
    Args:
        df: Processed dataframe
        formula: Model formula string
        family: Optional statsmodels GLM family
    
    Returns:
        DataFrame with pairwise comparison results (contrast, estimate, std_err, p_value, p_adj)
    """
    import statsmodels.stats.api as sms
    from statsmodels.stats.multitest import multipletests
    import itertools
    
    logger.info("Performing post-hoc pairwise comparisons with Bonferroni correction.")
    
    # Fit the model first to get the results object
    if family:
        model = glm(formula, data=df, family=family)
    else:
        model = ols(formula, data=df)
    
    results = model.fit()
    
    # Identify the categorical factors in the formula
    # We assume the formula is something like 'y ~ A * B'
    # We need to test all combinations of levels of A and B
    # This is complex to parse dynamically. We will assume the columns 'status_level' and 'observed_behavior' exist
    # and we want to compare all combinations of their levels.
    
    if 'status_level' not in df.columns or 'observed_behavior' not in df.columns:
        raise ValueError("Post-hoc analysis requires 'status_level' and 'observed_behavior' columns.")
    
    status_levels = df['status_level'].unique()
    behaviors = df['observed_behavior'].unique()
    
    # Create all condition combinations
    conditions = list(itertools.product(status_levels, behaviors))
    condition_names = [f"{s}_{b}" for s, b in conditions]
    
    # Calculate means and SE for each condition
    # We can use the model's predicted values or groupby
    # Using groupby for simplicity and direct interpretation of cell means
    group_stats = df.groupby(['status_level', 'observed_behavior'])['risk_taking'].agg(['mean', 'std', 'count']).reset_index()
    group_stats.columns = ['status_level', 'observed_behavior', 'mean', 'std', 'n']
    
    # Calculate SE
    group_stats['se'] = group_stats['std'] / np.sqrt(group_stats['n'])
    
    # Perform pairwise t-tests (or z-tests) between all conditions
    comparisons = []
    
    for i in range(len(conditions)):
        for j in range(i + 1, len(conditions)):
            cond_a = conditions[i]
            cond_b = conditions[j]
            
            # Filter data for these two conditions
            mask_a = (df['status_level'] == cond_a[0]) & (df['observed_behavior'] == cond_a[1])
            mask_b = (df['status_level'] == cond_b[0]) & (df['observed_behavior'] == cond_b[1])
            
            group_a = df[mask_a]['risk_taking']
            group_b = df[mask_b]['risk_taking']
            
            if len(group_a) < 2 or len(group_b) < 2:
                # Not enough data for test
                comparisons.append({
                    "contrast": f"{cond_a[0]}_{cond_a[1]} vs {cond_b[0]}_{cond_b[1]}",
                    "estimate": None,
                    "std_err": None,
                    "t_stat": None,
                    "p_value": None
                })
                continue
            
            # Welch's t-test (unequal variance)
            t_stat, p_val = sm.stats.ttest_ind(group_a, group_b, equal_var=False)
            
            comparisons.append({
                "contrast": f"{cond_a[0]}_{cond_a[1]} vs {cond_b[0]}_{cond_b[1]}",
                "estimate": float(group_a.mean() - group_b.mean()),
                "std_err": np.sqrt(group_a.var() / len(group_a) + group_b.var() / len(group_b)),
                "t_stat": float(t_stat),
                "p_value": float(p_val)
            })
    
    comparisons_df = pd.DataFrame(comparisons)
    
    if comparisons_df.empty or comparisons_df['p_value'].isna().all():
        logger.warning("No valid comparisons could be made.")
        return comparisons_df
    
    # Apply Bonferroni correction
    # multipletests returns (reject, pvals_corrected, alphacSidak, alphacBonf)
    # We only need pvals_corrected
    p_values = comparisons_df['p_value'].dropna().values
    if len(p_values) > 0:
        _, p_adj, _, _ = multipletests(p_values, method='bonferroni')
        
        # Map back to dataframe
        # Since we dropped NaNs, we need to be careful with alignment
        # Re-calculate without dropping NaNs for alignment
        valid_indices = comparisons_df['p_value'].notna()
        comparisons_df.loc[valid_indices, 'p_adj'] = p_adj
    else:
        comparisons_df['p_adj'] = np.nan
    
    # Fill NaNs with NaN (or a specific value if preferred)
    comparisons_df['p_adj'] = comparisons_df['p_adj'].fillna(np.nan)
    
    logger.info(f"Post-hoc comparisons completed. {len(comparisons_df)} pairs tested.")
    
    return comparisons_df

def main():
    """
    Main execution function for the analysis pipeline.
    Includes the new post-hoc analysis task (T031).
    """
    # Load configuration
    config_path = "data/processed/structure_config.json"
    if not os.path.exists(config_path):
        logger.error("Structure config not found. Run validation first.")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Load data
    data_path = "data/processed/processed_data.csv"
    if not os.path.exists(data_path):
        logger.error("Processed data not found. Run preprocessing first.")
        sys.exit(1)
    
    df = pd.read_csv(data_path)
    
    # Define formula
    # Assuming the standard formula from the project
    formula = "risk_taking ~ status_level * observed_behavior"
    
    # Determine family (from T014b logic if available, else default)
    # For this task, we assume continuous outcome (Gaussian)
    family = None 
    
    # 1. Validate Structure
    validate_data_structure(df)
    
    # 2. Fit Model
    logger.info("Fitting model...")
    if config['type'] == 'within':
        model_result = fit_mixed_effects(df, formula)
    else:
        model_result = fit_fixed_effects(df, formula, family)
    
    # 3. Analyze Interaction
    logger.info("Analyzing interaction...")
    interaction_analysis = analyze_interaction(df, formula, family)
    logger.info(f"Interaction p-value: {interaction_analysis['p_value']}")
    
    # 4. Calculate VIF
    logger.info("Calculating VIF...")
    vif_df = calculate_vif(df, formula)
    print(vif_df)
    
    # 5. Sensitivity Analysis (T030)
    logger.info("Running sensitivity analysis...")
    sensitivity_df = run_sensitivity_analysis(df, formula)
    sensitivity_df.to_csv("data/processed/sensitivity_analysis.csv", index=False)
    
    # 6. Post-Hoc Comparisons (T031) - UNCONDITIONAL
    logger.info("Performing post-hoc pairwise comparisons (T031)...")
    try:
        post_hoc_df = perform_post_hoc_comparisons(df, formula, family)
        post_hoc_path = "data/processed/post_hoc_comparisons.csv"
        post_hoc_df.to_csv(post_hoc_path, index=False)
        logger.info(f"Post-hoc results saved to {post_hoc_path}")
        print(post_hoc_df)
    except Exception as e:
        logger.error(f"Post-hoc analysis failed: {e}")
        # Continue execution even if post-hoc fails, but log error
    
    logger.info("Analysis pipeline completed.")

if __name__ == "__main__":
    main()