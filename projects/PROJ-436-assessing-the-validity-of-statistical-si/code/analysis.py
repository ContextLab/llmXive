import logging
from typing import Dict, Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.stats.weightstats as wstats
from scipy import stats

logger = logging.getLogger(__name__)

def _is_binary(series: pd.Series) -> bool:
    """Return True if the series appears binary (<=2 unique non‑missing values)."""
    return series.dropna().nunique() <= 2

def _logistic_regression(df: pd.DataFrame, outcome_col: str, treatment_col: str, weights: np.ndarray = None) -> Dict[str, Any]:
    """
    Fit a logistic regression of outcome ~ treatment (with optional observation weights)
    and return the p‑value and Wald statistic for the treatment coefficient.
    """
    # Prepare design matrix with intercept
    X = df[[treatment_col]].astype(float)
    X = sm.add_constant(X, has_constant='add')
    y = df[outcome_col].astype(float)

    try:
        if weights is None:
            model = sm.Logit(y, X, missing='drop')
            result = model.fit(disp=0)
        else:
            model = sm.GLM(y, X, family=sm.families.Binomial(), var_weights=weights, missing='drop')
            result = model.fit()
    except Exception as e:
        logger.warning(f"Logistic regression failed ({e}); falling back to Fisher/Chi‑square.")
        return _contingency_test(df, outcome_col, treatment_col)

    # Extract p‑value and Wald statistic for the treatment term
    # The treatment coefficient is the second parameter (index 1) after the intercept
    try:
        p_val = float(result.pvalues[treatment_col])
        stat = float(result.tvalues[treatment_col])
    except Exception as e:
        logger.warning(f"Failed to extract logistic regression stats ({e}); using fallback.")
        return _contingency_test(df, outcome_col, treatment_col)

    return {"p_value": p_val, "statistic": stat, "n": int(df.shape[0]), "method": "logistic_regression"}

def _contingency_test(df: pd.DataFrame, outcome_col: str, treatment_col: str) -> Dict[str, Any]:
    """
    Perform a chi‑square test of independence between treatment and binary outcome.
    If any expected cell count < 5, use Fisher's exact test instead.
    """
    table = pd.crosstab(df[treatment_col], df[outcome_col])
    if table.shape != (2, 2):
        # If the outcome is not perfectly binary after dropping NAs, fall back to chi2 on available shape
        chi2, p, dof, _ = stats.chi2_contingency(table, correction=False)
        return {"p_value": p, "statistic": chi2, "n": int(df.shape[0]), "method": "chi2"}
    # Compute expected frequencies
    chi2, p, dof, expected = stats.chi2_contingency(table, correction=False)
    if (expected < 5).any():
        # Fisher's exact test (only works for 2x2)
        _, p = stats.fisher_exact(table)
        return {"p_value": p, "statistic": 0.0, "n": int(df.shape[0]), "method": "fisher_exact"}
    else:
        return {"p_value": p, "statistic": chi2, "n": int(df.shape[0]), "method": "chi2"}

def run_complete_case_analysis(df: pd.DataFrame, outcome_col: str, treatment_col: str) -> Dict[str, Any]:
    """
    Perform Complete‑Case (CC) analysis.
    Drops any row with missing values in the outcome or treatment columns.
    For continuous outcomes runs a two‑sample t‑test.
    For binary outcomes runs logistic regression (fallback to chi‑square/Fisher when cell counts < 5).
    """
    # Drop rows with missing treatment or outcome
    cc_df = df[[treatment_col, outcome_col]].dropna()
    if cc_df.shape[0] < 2:
        logger.warning("Complete‑case analysis: insufficient data after dropping missing values.")
        return {"p_value": 1.0, "statistic": 0.0, "n": 0, "method": "complete_case"}

    if _is_binary(cc_df[outcome_col]):
        # Binary outcome → logistic regression (or fallback)
        return _logistic_regression(cc_df, outcome_col, treatment_col)
    else:
        # Continuous outcome → two‑sample t‑test
        group0 = cc_df[cc_df[treatment_col] == 0][outcome_col]
        group1 = cc_df[cc_df[treatment_col] == 1][outcome_col]

        if len(group0) < 2 or len(group1) < 2:
            logger.warning("Complete‑case analysis: not enough observations per group for t‑test.")
            return {"p_value": 1.0, "statistic": 0.0, "n": int(cc_df.shape[0]), "method": "complete_case"}

        stat, p_val = stats.ttest_ind(group0, group1, equal_var=False)
        return {
            "p_value": float(p_val),
            "statistic": float(stat),
            "n": int(cc_df.shape[0]),
            "method": "complete_case"
        }

def run_multiple_imputation(df: pd.DataFrame, outcome_col: str, treatment_col: str,
                            n_imputations: int = 5, random_state: int = 42) -> Dict[str, Any]:
    """
    Perform Multiple Imputation (MI) using miceforest.
    Imputes missing values, runs the appropriate test on each imputed dataset,
    and pools results via Rubin’s Rules (approximate pooling of coefficients and variances).
    """
    try:
        import miceforest
    except ImportError as e:
        raise ImportError("miceforest is required for Multiple Imputation. Install via: pip install miceforest") from e

    # Select columns needed for imputation (numeric + treatment/outcome)
    cols = [outcome_col, treatment_col] + [c for c in df.columns if df[c].dtype.kind in "biufc" and c not in [outcome_col, treatment_col]]
    impute_data = df[cols].copy()

    # Build the imputation kernel
    kernel = miceforest.ImputationKernel(
        impute_data,
        datasets=n_imputations,
        save_all_iterations=False,
        random_state=random_state
    )
    kernel.mice(iterations=5)

    # Store estimates from each imputed dataset
    estimates = []
    variances = []

    for i in range(n_imputations):
        imp_df = kernel.complete_data(dataset=i)

        # Drop rows where treatment or outcome are still missing after imputation (should be none)
        imp_df = imp_df[[treatment_col, outcome_col]].dropna()
        if imp_df.shape[0] < 2:
            # Skip this imputation
            continue

        if _is_binary(imp_df[outcome_col]):
            # Logistic regression for binary outcome
            res = _logistic_regression(imp_df, outcome_col, treatment_col)
            if "statistic" in res:
                estimates.append(res["statistic"])
                # Approximate variance from Wald statistic: var = (beta / z)^2, where z = stat
                # Since we only have the test statistic, we approximate variance as 1/(stat^2) when stat!=0
                var = 1.0 / (res["statistic"] ** 2) if res["statistic"] != 0 else np.inf
                variances.append(var)
        else:
            # Continuous outcome → t‑test
            g0 = imp_df[imp_df[treatment_col] == 0][outcome_col]
            g1 = imp_df[imp_df[treatment_col] == 1][outcome_col]
            if len(g0) < 2 or len(g1) < 2:
                continue
            stat, _ = stats.ttest_ind(g0, g1, equal_var=False)
            estimates.append(stat)
            # Approximate variance of t‑statistic as 1 (placeholder for pooling)
            variances.append(1.0)

    if not estimates:
        logger.warning("Multiple Imputation produced no valid estimates.")
        return {"p_value": 1.0, "statistic": 0.0, "n": int(df.shape[0]), "method": "multiple_imputation"}

    # Rubin’s Rules (simplified):
    #   Q_bar = mean of estimates
    #   U_bar = mean of within‑imputation variances (here approximated)
    #   B = variance between imputations
    #   T = U_bar + (1 + 1/m) * B
    #   df = (m - 1) * (1 + U_bar / ((1 + 1/m) * B))**2
    #   test statistic = Q_bar / sqrt(T)
    m = len(estimates)
    Q_bar = np.mean(estimates)
    U_bar = np.mean(variances)
    B = np.var(estimates, ddof=1)
    T = U_bar + (1.0 + 1.0 / m) * B
    if T <= 0:
        pooled_stat = 0.0
        pooled_p = 1.0
    else:
        pooled_stat = Q_bar / np.sqrt(T)
        # Two‑sided p‑value from normal approximation
        pooled_p = 2 * (1 - stats.norm.cdf(abs(pooled_stat)))

    return {
        "p_value": float(pooled_p),
        "statistic": float(pooled_stat),
        "n": int(df.shape[0]),
        "method": "multiple_imputation",
        "n_imputations": n_imputations
    }

def run_inverse_probability_weighting(df: pd.DataFrame, outcome_col: str, treatment_col: str) -> Dict[str, Any]:
    """
    Perform Inverse Probability Weighting (IPW) analysis.
    Estimates the probability of being observed using a logistic model on observed covariates,
    computes inverse‑probability weights, and runs a weighted analysis:
    - continuous outcome → weighted two‑sample t‑test
    - binary outcome → weighted logistic regression
    """
    # Indicator for observed outcome
    df = df.copy()
    df['_observed'] = df[outcome_col].notna().astype(int)

    # Identify covariates (numeric, excluding treatment and outcome)
    covariates = [c for c in df.columns
                 if c not in [treatment_col, outcome_col, '_observed']
                 and df[c].dtype.kind in "biufc"]

    # Fit propensity model for observation
    if covariates:
        X = df[covariates].fillna(df[covariates].mean())
        y = df['_observed']
        try:
            prop_model = sm.Logit(y, sm.add_constant(X, has_constant='add'))
            prop_res = prop_model.fit(disp=0)
            prob_obs = prop_res.predict()
        except Exception as e:
            logger.warning(f"Propensity model failed ({e}); falling back to MCAR weights.")
            prob_obs = np.full(len(df), df['_observed'].mean())
    else:
        # No covariates → assume MCAR
        prob_obs = np.full(len(df), df['_observed'].mean())

    # Avoid division by zero
    prob_obs = np.clip(prob_obs, 0.01, 1.0)
    df['_weight'] = df['_observed'] / prob_obs

    # Keep only observed rows for outcome analysis
    obs_df = df[df['_observed'] == 1].copy()
    if obs_df.shape[0] < 2:
        logger.warning("IPW analysis: no observed rows after weighting.")
        return {"p_value": 1.0, "statistic": 0.0, "n": 0, "method": "ipw"}

    if _is_binary(obs_df[outcome_col]):
        # Weighted logistic regression
        X = obs_df[[treatment_col]].astype(float)
        X = sm.add_constant(X, has_constant='add')
        y = obs_df[outcome_col].astype(float)
        weights = obs_df['_weight']
        try:
            model = sm.GLM(y, X, family=sm.families.Binomial(), var_weights=weights)
            result = model.fit()
            p_val = float(result.pvalues[treatment_col])
            stat = float(result.tvalues[treatment_col])
        except Exception as e:
            logger.warning(f"Weighted logistic regression failed ({e}); falling back to contingency test.")
            return _contingency_test(obs_df, outcome_col, treatment_col)
    else:
        # Weighted two‑sample t‑test using statsmodels
        g0 = obs_df[obs_df[treatment_col] == 0][outcome_col]
        w0 = obs_df[obs_df[treatment_col] == 0]['_weight']
        g1 = obs_df[obs_df[treatment_col] == 1][outcome_col]
        w1 = obs_df[obs_df[treatment_col] == 1]['_weight']

        if len(g0) < 2 or len(g1) < 2:
            logger.warning("IPW analysis: insufficient observations per group for weighted t‑test.")
            return {"p_value": 1.0, "statistic": 0.0, "n": int(obs_df.shape[0]), "method": "ipw"}

        # statsmodels weighted t-test
        try:
            tstat, p_val, _ = wstats.ttest_ind(g0, g1, usevar='unequal', weights1=w0, weights2=w1)
        except Exception as e:
            logger.warning(f"Weighted t‑test failed ({e}); falling back to unweighted t‑test.")
            tstat, p_val = stats.ttest_ind(g0, g1, equal_var=False)

    return {
        "p_value": float(p_val),
        "statistic": float(tstat),
        "n": int(obs_df.shape[0]),
        "method": "ipw"
    }