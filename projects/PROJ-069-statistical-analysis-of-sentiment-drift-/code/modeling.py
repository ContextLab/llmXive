"""
Modeling module for Statistical Analysis of Sentiment Drift.

Implements:
- Augmented Dickey-Fuller (ADF) stationarity tests
- Johansen Cointegration tests (Trace and Max-Eigen)
- VAR/VECM model fitting with AIC-based lag selection
- Granger Causality F-tests
- Variance Inflation Factor (VIF) collinearity diagnostics

Outputs:
- results/model_stats.json: Aggregated statistics from all tests and models
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, grangercausalitytests
from statsmodels.tsa.vector_ar.var_model import VAR
from statsmodels.tsa.vecm.vecm import VECM, coint_johansen
from statsmodels.stats.outliers_influence import variance_inflation_factor

from contracts.model_results import (
    StationarityTestResult,
    CointegrationTestResult,
    GrangerCausalityResult,
    CollinearityDiagnostic,
    ModelResult,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

def ensure_results_directory():
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def run_adf_test(series: pd.Series, variable_name: str) -> StationarityTestResult:
    """
    Run Augmented Dickey-Fuller test for stationarity.
    
    Args:
        series: Time series data
        variable_name: Name of the variable for reporting
        
    Returns:
        StationarityTestResult dataclass
    """
    try:
        result = adfuller(series.dropna(), autolag='AIC')
        is_stationary = result[1] < 0.05
        
        return StationarityTestResult(
            variable=variable_name,
            test="ADF",
            statistic=result[0],
            pvalue=result[1],
            is_stationary=is_stationary,
            lag_order=int(result[4]['aicc']) if isinstance(result[4], dict) else 0,
            critical_values={
                "1%": result[4]["1%"] if isinstance(result[4], dict) else None,
                "5%": result[4]["5%"] if isinstance(result[4], dict) else None,
                "10%": result[4]["10%"] if isinstance(result[4], dict) else None,
            }
        )
    except Exception as e:
        logger.error(f"ADF test failed for {variable_name}: {e}")
        return StationarityTestResult(
            variable=variable_name,
            test="ADF",
            statistic=None,
            pvalue=None,
            is_stationary=False,
            lag_order=0,
            critical_values={},
            error=str(e)
        )

def run_johansen_test(data: pd.DataFrame, variable_names: List[str]) -> CointegrationTestResult:
    """
    Run Johansen Cointegration Test.
    
    Prioritizes the Trace statistic for cointegration rank selection as per Plan.
    
    Args:
        data: DataFrame with time series data (indexed by datetime)
        variable_names: List of column names to test
        
    Returns:
        CointegrationTestResult dataclass
    """
    try:
        # Ensure data is sorted by index
        data_sorted = data.sort_index()
        
        # Run Johansen test
        # max_lag is typically chosen based on AIC/BIC, defaulting to 12 for monthly data
        # We'll use a reasonable default and can be tuned
        max_lag = 12 
        johansen_result = coint_johansen(data_sorted, det_order=0, k_ar_diff=max_lag)
        
        # Extract trace statistics and p-values
        trace_stat = johansen_result.trace_stat
        trace_pval = johansen_result.trace_pvalues
        max_eigen_stat = johansen_result.max_eigen_stat
        max_eigen_pval = johansen_result.max_eigen_pvalues
        
        # Determine cointegration rank using Trace statistic (prioritized per Plan)
        # Rank is the number of cointegrating relationships
        # We look for the first rank where p-value > 0.05 (fail to reject null of r cointegrating vectors)
        coint_rank = 0
        for i, p_val in enumerate(trace_pval):
            if p_val > 0.05:
                coint_rank = i
                break
        else:
            # If all p-values are < 0.05, rank is the maximum possible (number of variables - 1)
            coint_rank = len(variable_names) - 1
        
        # Select model type based on cointegration rank
        model_type = "VECM" if coint_rank > 0 else "VAR"
        
        return CointegrationTestResult(
            variables=variable_names,
            test="Johansen",
            trace_statistics=trace_stat.tolist(),
            trace_pvalues=trace_pval.tolist(),
            max_eigen_statistics=max_eigen_stat.tolist(),
            max_eigen_pvalues=max_eigen_pval.tolist(),
            cointegration_rank=coint_rank,
            selected_model_type=model_type,
            lag_order=max_lag
        )
    except Exception as e:
        logger.error(f"Johansen test failed: {e}")
        return CointegrationTestResult(
            variables=variable_names,
            test="Johansen",
            trace_statistics=[],
            trace_pvalues=[],
            max_eigen_statistics=[],
            max_eigen_pvalues=[],
            cointegration_rank=0,
            selected_model_type="VAR",
            lag_order=0,
            error=str(e)
        )

def fit_var_vecm_model(
    data: pd.DataFrame, 
    model_type: str, 
    coint_rank: int,
    max_lag: int = 12
) -> Tuple[Any, Dict[str, Any]]:
    """
    Fit VAR or VECM model based on cointegration results.
    
    Args:
        data: DataFrame with time series data
        model_type: "VAR" or "VECM"
        coint_rank: Cointegration rank (for VECM)
        max_lag: Maximum lag order to consider
        
    Returns:
        Tuple of (fitted model object, model summary dict)
    """
    try:
        data_sorted = data.sort_index()
        
        if model_type == "VECM":
            # Fit VECM
            # coint_rank is the number of cointegrating relationships
            model = VECM(data_sorted, k_ar_diff=max_lag, coint_rank=coint_rank)
            fitted_model = model.fit()
            summary = {
                "model_type": "VECM",
                "cointegration_rank": coint_rank,
                "lag_order": max_lag,
                "aic": fitted_model.aic,
                "bic": fitted_model.bic,
                "hqic": fitted_model.hqic,
                "params_shape": list(fitted_model.params.shape),
            }
        else:
            # Fit VAR
            # Use AIC to select optimal lag order
            var_model = VAR(data_sorted)
            selected_lag = var_model.select_order(max_lag=max_lag).aic  # Optimal lag based on AIC
            
            fitted_model = var_model.fit(maxlags=selected_lag)
            summary = {
                "model_type": "VAR",
                "optimal_lag_order": int(selected_lag),
                "aic": fitted_model.aic,
                "bic": fitted_model.bic,
                "hqic": fitted_model.hqic,
                "params_shape": list(fitted_model.params.shape),
            }
        
        return fitted_model, summary
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        return None, {"error": str(e)}

def run_granger_causality(
    data: pd.DataFrame, 
    cause_var: str, 
    effect_var: str, 
    max_lag: int = 12
) -> GrangerCausalityResult:
    """
    Run Granger Causality F-test.
    
    Args:
        data: DataFrame with time series data
        cause_var: Variable that might cause the effect
        effect_var: Variable that might be caused
        max_lag: Maximum lag order to test
        
    Returns:
        GrangerCausalityResult dataclass
    """
    try:
        # Prepare data: drop NaNs
        test_data = data[[cause_var, effect_var]].dropna()
        
        if len(test_data) < max_lag + 1:
            raise ValueError("Insufficient data for Granger causality test")
        
        # Run Granger causality test
        # Returns a dict: {lag: (F-statistic, p-value)}
        gc_result = grangercausalitytests(test_data, max_lag=max_lag, verbose=False)
        
        # Extract results for each lag
        results_by_lag = {}
        for lag in range(1, max_lag + 1):
            if lag in gc_result:
                # gc_result[lag][0] is the fitted model, [1] is summary, [2] is residuals
                # The test stats are in gc_result[lag][0].ssr_ftest
                ssr_ftest = gc_result[lag][0].ssr_ftest
                f_stat = ssr_ftest[0]
                p_val = ssr_ftest[1]
                results_by_lag[lag] = {
                    "f_statistic": float(f_stat),
                    "p_value": float(p_val)
                }
        
        # Overall decision: reject null if any lag has p < 0.05
        is_causal = any(r["p_value"] < 0.05 for r in results_by_lag.values())
        
        return GrangerCausalityResult(
            cause_variable=cause_var,
            effect_variable=effect_var,
            test="Granger Causality F-test",
            results_by_lag=results_by_lag,
            is_causal=is_causal,
            max_lag_tested=max_lag
        )
    except Exception as e:
        logger.error(f"Granger causality test failed for {cause_var} -> {effect_var}: {e}")
        return GrangerCausalityResult(
            cause_variable=cause_var,
            effect_variable=effect_var,
            test="Granger Causality F-test",
            results_by_lag={},
            is_causal=False,
            max_lag_tested=max_lag,
            error=str(e)
        )

def calculate_vif(data: pd.DataFrame, variable_names: List[str]) -> CollinearityDiagnostic:
    """
    Calculate Variance Inflation Factor (VIF) for collinearity diagnostics.
    
    Args:
        data: DataFrame with time series data
        variable_names: List of variable names to check
        
    Returns:
        CollinearityDiagnostic dataclass
    """
    try:
        # Prepare data: drop NaNs
        test_data = data[variable_names].dropna()
        
        if test_data.empty:
            raise ValueError("No data available after dropping NaNs")
        
        # Add constant for VIF calculation
        # VIF is calculated for each variable against all others
        vif_results = {}
        for i, var in enumerate(variable_names):
            # VIF for variable i is calculated using all other variables as predictors
            # But typically we calculate VIF for each variable in the set
            # Using the standard approach: VIF_i = 1 / (1 - R_i^2)
            # where R_i^2 is from regressing var_i on all other variables
            
            # For simplicity, we calculate VIF for each variable in the set
            # using the entire set (including itself) as predictors, which is not standard
            # Standard approach: for each variable, regress it on all others
            pass
        
        # Correct approach: calculate VIF for each variable
        vif_values = []
        for i, var in enumerate(variable_names):
            # Regress var on all other variables
            other_vars = [v for v in variable_names if v != var]
            if not other_vars:
                vif_values.append(1.0)  # No other variables, VIF = 1
                continue
            
            X = test_data[other_vars]
            y = test_data[var]
            
            # Add constant
            X_const = sm.add_constant(X)
            
            # Fit OLS
            from statsmodels.regression.linear_model import OLS
            ols_model = OLS(y, X_const).fit()
            
            # VIF = 1 / (1 - R^2)
            r_squared = ols_model.rsquared
            vif = 1.0 / (1.0 - r_squared) if r_squared < 1.0 else np.inf
            vif_values.append(vif)
        
        # Check for high collinearity (VIF > 33)
        high_collinearity = any(v > 33 for v in vif_values)
        max_vif = max(vif_values) if vif_values else 0
        max_vif_var = variable_names[vif_values.index(max_vif)] if vif_values else None
        
        return CollinearityDiagnostic(
            variables=variable_names,
            vif_values=dict(zip(variable_names, vif_values)),
            max_vif=max_vif,
            variable_with_max_vif=max_vif_var,
            is_high_collinearity=high_collinearity,
            threshold=33
        )
    except Exception as e:
        logger.error(f"VIF calculation failed: {e}")
        return CollinearityDiagnostic(
            variables=variable_names,
            vif_values={},
            max_vif=0,
            variable_with_max_vif=None,
            is_high_collinearity=False,
            threshold=33,
            error=str(e)
        )

def load_processed_data() -> pd.DataFrame:
    """Load the aligned monthly data."""
    data_path = PROCESSED_DATA_DIR / "aligned_monthly.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    
    df = pd.read_csv(data_path, parse_dates=["date"], index_col="date")
    df = df.sort_index()
    return df

def run_full_modeling_pipeline() -> ModelResult:
    """
    Execute the full modeling pipeline:
    1. ADF tests for all variables
    2. Johansen cointegration test
    3. VAR/VECM model fitting
    4. Granger causality tests
    5. VIF collinearity diagnostics
    
    Returns:
        ModelResult dataclass with all results
    """
    ensure_results_directory()
    logger.info("Starting full modeling pipeline...")
    
    # Load data
    try:
        df = load_processed_data()
        logger.info(f"Loaded data with {len(df)} rows and columns: {list(df.columns)}")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return ModelResult(
            timestamp=datetime.now().isoformat(),
            status="error",
            error=str(e)
        )
    
    # Define variables of interest
    # Based on the project scope: sentiment, GDP, Unemployment, ConsumerConfidence
    sentiment_cols = [c for c in df.columns if "sentiment" in c.lower()]
    macro_cols = [c for c in df.columns if any(x in c.lower() for x in ["gdp", "unrate", "consumer", "confidence"])]
    
    all_vars = sentiment_cols + macro_cols
    
    if not all_vars:
        logger.error("No relevant variables found in the dataset")
        return ModelResult(
            timestamp=datetime.now().isoformat(),
            status="error",
            error="No relevant variables found"
        )
    
    # 1. ADF Tests
    logger.info("Running ADF tests...")
    adf_results = []
    for var in all_vars:
        adf_res = run_adf_test(df[var], var)
        adf_results.append(adf_res)
    
    # 2. Johansen Test
    logger.info("Running Johansen cointegration test...")
    johansen_res = run_johansen_test(df[all_vars], all_vars)
    
    # 3. VAR/VECM Model Fitting
    logger.info(f"Fitting {johansen_res.selected_model_type} model...")
    model_obj, model_summary = fit_var_vecm_model(
        df[all_vars], 
        johansen_res.selected_model_type, 
        johansen_res.cointegration_rank
    )
    
    # 4. Granger Causality Tests
    logger.info("Running Granger causality tests...")
    granger_results = []
    
    # Test sentiment -> macro variables
    for macro_var in macro_cols:
        for sent_var in sentiment_cols:
            gc_res = run_granger_causality(df, sent_var, macro_var)
            granger_results.append(gc_res)
    
    # Test macro -> sentiment (reverse)
    for sent_var in sentiment_cols:
        for macro_var in macro_cols:
            gc_res = run_granger_causality(df, macro_var, sent_var)
            granger_results.append(gc_res)
    
    # 5. VIF Collinearity Diagnostics
    logger.info("Calculating VIF for collinearity...")
    # Only calculate VIF for macro variables that might be collinear (e.g., GDP vs Unemployment)
    macro_vars_for_vif = [c for c in macro_cols if any(x in c.lower() for x in ["gdp", "unrate"])]
    vif_res = CollinearityDiagnostic(
        variables=[], vif_values={}, max_vif=0, variable_with_max_vif=None, is_high_collinearity=False, threshold=33
    )
    if len(macro_vars_for_vif) >= 2:
        vif_res = calculate_vif(df, macro_vars_for_vif)
    
    # Compile results
    result = ModelResult(
        timestamp=datetime.now().isoformat(),
        status="success",
        stationarity_tests=[r.dict() for r in adf_results],
        cointegration_test=johansen_res.dict(),
        model_fitting=model_summary,
        granger_causality=[r.dict() for r in granger_results],
        collinearity_diagnostic=vif_res.dict()
    )
    
    # Save to JSON
    output_path = RESULTS_DIR / "model_stats.json"
    with open(output_path, "w") as f:
        json.dump(result.dict(), f, indent=2, default=str)
    
    logger.info(f"Model results saved to {output_path}")
    return result

def main():
    """Main entry point for modeling pipeline."""
    logger.info("Executing T010: Modeling pipeline...")
    try:
        result = run_full_modeling_pipeline()
        if result.status == "success":
            logger.info("Modeling pipeline completed successfully.")
        else:
            logger.error(f"Modeling pipeline failed: {result.error}")
    except Exception as e:
        logger.critical(f"Fatal error in modeling pipeline: {e}")
        raise

if __name__ == "__main__":
    main()
