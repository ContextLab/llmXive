import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
import logging
import warnings
from scipy import stats

logger = logging.getLogger(__name__)

def run_complete_case_analysis(df: pd.DataFrame, outcome_col: str, treatment_col: str) -> Dict[str, Any]:
    """
    Perform Complete-Case (CC) analysis.
    Drops any row with missing values in the outcome or treatment columns.
    Runs t-test (continuous) or Wilcoxon (binary) as appropriate.
    """
    # Filter for complete cases on the relevant columns
    mask = df[outcome_col].notna() & df[treatment_col].notna()
    cc_df = df[mask]

    if len(cc_df) < 2:
        logger.warning("Complete-case analysis: insufficient samples after dropping missing values.")
        return {"p_value": 1.0, "statistic": 0.0, "n": 0, "method": "complete_case"}

    # Determine outcome type to select test
    # Simple heuristic: if unique values <= 2, treat as binary
    n_unique = cc_df[outcome_col].nunique()
    is_binary = n_unique <= 2

    t0 = cc_df[cc_df[treatment_col] == 0][outcome_col]
    t1 = cc_df[cc_df[treatment_col] == 1][outcome_col]

    if len(t0) < 2 or len(t1) < 2:
        logger.warning("Complete-case analysis: insufficient samples in one or both groups.")
        return {"p_value": 1.0, "statistic": 0.0, "n": len(cc_df), "method": "complete_case"}

    if is_binary:
        # Wilcoxon rank-sum test (Mann-Whitney U) for binary/outcome
        stat, p_val = stats.mannwhitneyu(t0, t1, alternative='two-sided')
    else:
        # Independent t-test for continuous outcome
        stat, p_val = stats.ttest_ind(t0, t1)

    return {
        "p_value": float(p_val),
        "statistic": float(stat),
        "n": int(len(cc_df)),
        "method": "complete_case"
    }

def run_multiple_imputation(df: pd.DataFrame, outcome_col: str, treatment_col: str, 
                            n_imputations: int = 5, random_state: int = 42) -> Dict[str, Any]:
    """
    Perform Multiple Imputation (MI) using miceforest.
    Imputes missing values, runs the test on each imputed dataset, and pools results.
    """
    try:
        import miceforest
    except ImportError:
        raise ImportError("miceforest is required for Multiple Imputation. Install via: pip install miceforest")

    logger.info(f"Starting Multiple Imputation with {n_imputations} datasets...")
    
    # Prepare data: drop non-numeric columns if any, but keep outcome and treatment
    # We assume the dataframe passed here only contains relevant numeric columns
    # or that miceforest can handle the rest.
    # For safety, select numeric cols including outcome and treatment
    cols_to_use = [outcome_col, treatment_col]
    # Add other numeric cols if present to help imputation
    for col in df.columns:
        if col not in cols_to_use and df[col].dtype in ['float64', 'int64']:
            cols_to_use.append(col)
    
    impute_data = df[cols_to_use].copy()
    
    # Create kernel
    kernel = miceforest.ImputationKernel(
        impute_data, 
        datasets=n_imputations, 
        random_state=random_state
    )
    
    # Impute
    kernel.mice()
    
    p_values = []
    statistics = []
    
    for i in range(n_imputations):
        imputed_df = kernel.complete_data(dataset=i)
        
        t0 = imputed_df[imputed_df[treatment_col] == 0][outcome_col]
        t1 = imputed_df[imputed_df[treatment_col] == 1][outcome_col]
        
        if len(t0) < 2 or len(t1) < 2:
            p_values.append(1.0)
            statistics.append(0.0)
            continue

        n_unique = imputed_df[outcome_col].nunique()
        is_binary = n_unique <= 2

        if is_binary:
            stat, p_val = stats.mannwhitneyu(t0, t1, alternative='two-sided')
        else:
            stat, p_val = stats.ttest_ind(t0, t1)
        
        p_values.append(p_val)
        statistics.append(stat)

    # Pool results (Rubin's rules approximation for p-values)
    # For simplicity in this context, we use the average p-value or a combined statistic.
    # A more rigorous approach involves combining statistics and standard errors.
    # Here we combine the test statistics (assuming similar scales) and recalculate p-value?
    # Or simply average the p-values? Standard practice: combine Q and U.
    # Given the constraints, we will average the p-values as a pragmatic approximation 
    # often seen in quick simulations, though Rubin's rules on the statistic is better.
    # Let's implement a simplified Rubin's rule on the statistic if possible, 
    # but since we have different tests (t vs u), averaging p-values is safer for mixed types.
    # However, for t-tests, we can combine t-stats. For U, we can't easily.
    # Let's assume continuous for robust pooling, or fallback to mean p-value.
    
    # Robust fallback: Mean p-value (conservative)
    # Better: If continuous, combine t-stats. If binary, mean p-value.
    
    if len(statistics) > 0:
        # Check if we can treat as continuous (mean of stats is reasonable for t-stats)
        # If binary, we used Mann-Whitney U.
        # We'll use the mean p-value for simplicity and robustness across test types.
        pooled_p = float(np.mean(p_values))
        pooled_stat = float(np.mean(statistics))
    else:
        pooled_p = 1.0
        pooled_stat = 0.0

    return {
        "p_value": pooled_p,
        "statistic": pooled_stat,
        "n": int(len(df)),
        "method": "multiple_imputation",
        "n_imputations": n_imputations
    }

def run_inverse_probability_weighting(df: pd.DataFrame, outcome_col: str, treatment_col: str) -> Dict[str, Any]:
    """
    Perform Inverse Probability Weighting (IPW) analysis.
    Calculates weights based on the probability of being observed (missingness mechanism).
    Assumes missingness depends on observed covariates.
    Uses logistic regression to estimate propensity of being observed.
    """
    # Prepare data
    # We need to model P(Observed | X).
    # If no covariates are available, we assume MCAR and weights are 1/prop(Observed).
    # But typically IPW for missing data uses covariates to model the missingness probability.
    
    # Identify covariates (all numeric columns except outcome and treatment)
    covariates = [col for col in df.columns if col not in [outcome_col, treatment_col] and df[col].dtype in ['float64', 'int64']]
    
    # Create indicator for observed outcome
    df = df.copy()
    df['observed'] = df[outcome_col].notna().astype(int)
    
    # If no covariates, we can only do simple weighting (MCAR assumption)
    if not covariates:
        logger.warning("No covariates found for IPW. Assuming MCAR and using simple inverse probability.")
        prop_observed = df['observed'].mean()
        if prop_observed == 0:
            raise ValueError("No observed outcomes found for IPW.")
        weights = df['observed'] / prop_observed
    else:
        # Fit logistic regression to predict observed status
        # Use only rows where outcome is missing? No, we need to predict for all rows.
        # Actually, we model P(R=1 | X). We have R for all rows.
        
        from sklearn.linear_model import LogisticRegression
        
        X = df[covariates].fillna(df[covariates].mean())
        y = df['observed']
        
        # Avoid perfect separation or singularities
        try:
            model = LogisticRegression(max_iter=1000, solver='lbfgs')
            model.fit(X, y)
            prob_observed = model.predict_proba(X)[:, 1]
        except Exception as e:
            logger.warning(f"Logistic regression failed for IPW: {e}. Falling back to MCAR weights.")
            prop_observed = df['observed'].mean()
            if prop_observed == 0:
                raise ValueError("No observed outcomes found for IPW.")
            prob_observed = np.full(len(df), prop_observed)
        
        # Calculate weights: 1 / P(Observed | X)
        # Clip probabilities to avoid division by zero
        prob_observed = np.clip(prob_observed, 0.01, 1.0)
        weights = df['observed'] / prob_observed

    # Filter to observed data for the actual test (weighted)
    observed_df = df[df['observed'] == 1].copy()
    observed_df['weight'] = weights[df['observed'] == 1]
    
    if len(observed_df) < 2:
        logger.warning("IPW analysis: insufficient observed samples.")
        return {"p_value": 1.0, "statistic": 0.0, "n": 0, "method": "ipw"}

    t0 = observed_df[observed_df[treatment_col] == 0]
    t1 = observed_df[observed_df[treatment_col] == 1]

    if len(t0) < 2 or len(t1) < 2:
        logger.warning("IPW analysis: insufficient samples in one or both groups.")
        return {"p_value": 1.0, "statistic": 0.0, "n": len(observed_df), "method": "ipw"}

    # Weighted t-test or Wilcoxon
    # scipy does not have a direct weighted t-test for independent samples.
    # We can use statsmodels for weighted t-test or approximate.
    # For robustness, we'll use statsmodels if available, otherwise fallback to unweighted on observed (which is CC)
    # But the task requires IPW. Let's try to implement a weighted t-test manually or use statsmodels.
    
    try:
        import statsmodels.stats.weightstats as wstats
        
        # Weighted t-test
        # Note: statsmodels weighted t-test assumes equal variance by default? 
        # We'll use the standard function.
        # We need to pass weights.
        
        # statsmodels weighted t-test: 
        # ttest_ind does not directly take weights. 
        # We use DescrStatsW
        
        w_t0 = wstats.DescrStatsW(t0[outcome_col], weights=t0['weight'], ddof=1)
        w_t1 = wstats.DescrStatsW(t1[outcome_col], weights=t1['weight'], ddof=1)
        
        # Two-sample t-test with weights
        # statsmodels doesn't have a direct weighted ttest_ind for two samples with different weights easily.
        # We can use the t-test on means with pooled variance approximation or use a permutation approach.
        # However, for this pipeline, let's use a simpler approach: 
        # If we can't do weighted t-test easily, we might fall back to a weighted mean difference test.
        # But let's try to use statsmodels's ttest_ind1d or similar? No.
        # Let's use the `ttest_ind` from scipy on the weighted data? No, that's wrong.
        
        # Alternative: Use `statsmodels.stats.weightstats.ttest_ind` if available?
        # Actually, `DescrStatsW` has `ttest_mean` but not two-sample.
        # We can calculate the t-statistic manually:
        # t = (mean1 - mean0) / sqrt(se1^2 + se0^2)
        
        mean0, mean1 = w_t0.mean, w_t1.mean
        var0, var1 = w_t0.var, w_t1.var
        n0, n1 = w_t0.sum_weights, w_t1.sum_weights
        
        # Standard error for weighted mean
        # se = sqrt(var / n_eff) where n_eff is effective sample size?
        # Or use the variance of the weighted mean.
        # Let's use the standard formula for weighted t-test:
        # se = sqrt( var0/n0 + var1/n1 )
        # This is an approximation.
        
        se = np.sqrt(var0/n0 + var1/n1)
        if se == 0:
            stat = 0.0
        else:
            stat = (mean1 - mean0) / se
        
        # Degrees of freedom (Satterthwaite approximation)
        df_num = (var0/n0 + var1/n1)**2
        df_den = (var0/n0)**2 / (n0 - 1) + (var1/n1)**2 / (n1 - 1)
        if df_den == 0:
            df = 1
        else:
            df = df_num / df_den
        
        p_val = 2 * (1 - stats.t.cdf(abs(stat), df))
        
    except ImportError:
        logger.warning("statsmodels not available for weighted t-test. Falling back to unweighted CC (not IPW).")
        # Fallback to unweighted (CC) if statsmodels missing
        t0_vals = t0[outcome_col]
        t1_vals = t1[outcome_col]
        n_unique = df[outcome_col].nunique()
        is_binary = n_unique <= 2
        if is_binary:
            stat, p_val = stats.mannwhitneyu(t0_vals, t1_vals, alternative='two-sided')
        else:
            stat, p_val = stats.ttest_ind(t0_vals, t1_vals)
    except Exception as e:
        logger.warning(f"Weighted t-test failed: {e}. Falling back to unweighted CC.")
        t0_vals = t0[outcome_col]
        t1_vals = t1[outcome_col]
        n_unique = df[outcome_col].nunique()
        is_binary = n_unique <= 2
        if is_binary:
            stat, p_val = stats.mannwhitneyu(t0_vals, t1_vals, alternative='two-sided')
        else:
            stat, p_val = stats.ttest_ind(t0_vals, t1_vals)

    return {
        "p_value": float(p_val),
        "statistic": float(stat),
        "n": int(len(observed_df)),
        "method": "ipw"
    }
