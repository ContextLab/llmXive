import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.regression.linear_model import PanelOLS, RandomEffects
from statsmodels.stats.diagnostic import linear_hausman
from logging_config import get_logger

logger = get_logger(__name__)

def detect_time_invariant_countries(df: pd.DataFrame) -> List[str]:
    """
    Detect countries where the 'regime_type' variable is constant over time.
    Returns a list of country codes (ISO3) that are time-invariant.
    """
    if 'country_code' not in df.columns or 'regime_type' not in df.columns:
        logger.error("DataFrame missing required columns: 'country_code', 'regime_type'")
        return []

    # Group by country and check variance of regime_type
    # If variance is 0, the variable is constant (time-invariant)
    grouped = df.groupby('country_code')['regime_type']
    invariant_codes = []

    for code, series in grouped:
        # Check if there is any variation
        if series.nunique() == 1:
            invariant_codes.append(code)
    
    return invariant_codes

def save_time_invariant_report(invariant_codes: List[str], output_path: Path) -> None:
    """Save the list of time-invariant countries to a JSON file."""
    report = {
        "flagged_countries": invariant_codes,
        "count": len(invariant_codes),
        "description": "Countries with constant regime_type over time (cannot be used in Fixed Effects)"
    }
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved time-invariant report to {output_path}")

def filter_time_invariant_countries(df: pd.DataFrame, invariant_codes: List[str]) -> pd.DataFrame:
    """
    Filter the dataframe to exclude countries flagged as time-invariant.
    """
    if not invariant_codes:
        logger.info("No time-invariant countries to filter.")
        return df
    
    filtered_df = df[~df['country_code'].isin(invariant_codes)].copy()
    logger.info(f"Filtered out {len(invariant_codes)} time-invariant countries. Remaining rows: {len(filtered_df)}")
    return filtered_df

def run_fixed_effects_regression(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run Fixed Effects Panel Regression.
    Model: land_use_change ~ regime_type + gdp_per_capita + population_density + CountryFE
    """
    if df.empty:
        raise ValueError("Input dataframe is empty. Cannot run regression.")

    # Ensure numeric types
    df = df.copy()
    for col in ['land_use_change_rate', 'regime_type', 'gdp_per_capita', 'population_density']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=['land_use_change_rate', 'regime_type', 'gdp_per_capita', 'population_density'])

    if len(df) == 0:
        raise ValueError("No valid data remaining after dropping NaNs for regression.")

    # Setup PanelOLS
    # Endog: land_use_change_rate
    # Exog: regime_type, gdp_per_capita, population_density
    # Entity effects: country_code
    
    exog_cols = ['regime_type', 'gdp_per_capita', 'population_density']
    # Ensure exog exists
    if not all(col in df.columns for col in exog_cols):
        missing = [c for c in exog_cols if c not in df.columns]
        raise ValueError(f"Missing exog variables: {missing}")

    model = PanelOLS(
        df['land_use_change_rate'],
        df[exog_cols],
        entity_effects=True,
        time_effects=False, # Usually not needed for this specific cross-country comparison unless specified
        drop_absorbed=True
    )
    
    result = model.fit(cov_type='clustered', cluster_entity=True)
    
    return {
        "coefficients": result.params.to_dict(),
        "pvalues": result.pvalues.to_dict(),
        "rsquared": result.rsquared,
        "nobs": result.nobs,
        "f_statistic": result.f_statistic,
        "f_pvalue": result.f_pvalue
    }

def save_regression_results(results: Dict[str, Any], output_path: Path) -> None:
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved regression results to {output_path}")

def run_sensitivity_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run regression without GDP controls to check sensitivity.
    Returns coefficients for both Full and No-GDP models.
    """
    # Full model (already handled in run_fixed_effects_regression, but we re-run for isolation here if needed)
    # Simplified: Just run the model without GDP
    df = df.copy()
    for col in ['land_use_change_rate', 'regime_type', 'population_density']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['land_use_change_rate', 'regime_type', 'population_density'])

    if len(df) == 0:
        return {"error": "No data for sensitivity analysis"}

    model = PanelOLS(
        df['land_use_change_rate'],
        df[['regime_type', 'population_density']],
        entity_effects=True,
        drop_absorbed=True
    )
    result = model.fit(cov_type='clustered', cluster_entity=True)

    return {
        "no_gdp_coefficients": result.params.to_dict(),
        "no_gdp_pvalues": result.pvalues.to_dict()
    }

def run_nonlinearity_robustness_check(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Add quadratic term for regime_type (or CBNRM index if continuous) and test significance.
    """
    df = df.copy()
    # Assuming regime_type is binary or continuous index. If binary, quadratic is same as linear.
    # We check if it has variance > 1 to make sense of quadratic.
    if df['regime_type'].nunique() < 3:
        logger.warning("Regime type has < 3 unique values. Quadratic term may be redundant.")
    
    df['regime_type_sq'] = df['regime_type'] ** 2
    
    exog_cols = ['regime_type', 'regime_type_sq', 'gdp_per_capita', 'population_density']
    for col in exog_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=['land_use_change_rate'] + exog_cols)

    if len(df) == 0:
        return {"error": "No data for nonlinearity check"}

    model = PanelOLS(
        df['land_use_change_rate'],
        df[exog_cols],
        entity_effects=True,
        drop_absorbed=True
    )
    result = model.fit(cov_type='clustered', cluster_entity=True)

    return {
        "quadratic_coefficient": result.params['regime_type_sq'],
        "quadratic_pvalue": result.pvalues['regime_type_sq'],
        "is_significant": result.pvalues['regime_type_sq'] < 0.05
    }

def run_random_effects_fallback(df: pd.DataFrame, invariant_count: int, total_countries: int) -> Dict[str, Any]:
    """
    Run Random Effects model and perform Hausman test.
    This is triggered if ALL countries are time-invariant.
    """
    if df.empty:
        return {"error": "Empty dataframe for Random Effects"}

    # Ensure numeric
    df = df.copy()
    for col in ['land_use_change_rate', 'regime_type', 'gdp_per_capita', 'population_density']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['land_use_change_rate', 'regime_type', 'gdp_per_capita', 'population_density'])

    if len(df) == 0:
        return {"error": "No valid data for Random Effects"}

    exog_cols = ['regime_type', 'gdp_per_capita', 'population_density']
    
    # Run Fixed Effects (for Hausman comparison)
    try:
        model_fe = PanelOLS(
            df['land_use_change_rate'],
            df[exog_cols],
            entity_effects=True,
            drop_absorbed=True
        )
        res_fe = model_fe.fit()
    except Exception as e:
        logger.error(f"Fixed Effects failed: {e}")
        return {"error": "FE failed", "details": str(e)}

    # Run Random Effects
    try:
        model_re = RandomEffects(
            df['land_use_change_rate'],
            df[exog_cols],
            entity_effects=True, # RE usually handles entity effects via GLS
            time_effects=False
        )
        res_re = model_re.fit()
    except Exception as e:
        logger.error(f"Random Effects failed: {e}")
        return {"error": "RE failed", "details": str(e)}

    # Hausman Test
    # statsmodels linear_hausman requires the two results objects
    try:
        # Note: linear_hausman in statsmodels might need specific setup or manual calculation if wrapper is missing
        # Using manual calculation if wrapper is unstable, but attempting wrapper first.
        # Hausman stat = (b_fe - b_re)' * (V_fe - V_re)^-1 * (b_fe - b_re)
        # We compare coefficients for the main variable of interest or all exog vars.
        
        # Attempting standard statsmodels diagnostic if available, else manual
        # Since linear_hausman is not always stable with PanelOLS, we calculate manually for robustness
        b_fe = res_fe.params
        b_re = res_re.params
        v_fe = res_fe.cov_params()
        v_re = res_re.cov_params()
        
        # Align indices
        common_idx = b_fe.index.intersection(b_re.index)
        diff = b_fe[common_idx] - b_re[common_idx]
        
        # Variance of difference
        var_diff = v_fe.loc[common_idx, common_idx] - v_re.loc[common_idx, common_idx]
        
        # Ensure positive definite (add small epsilon if needed)
        if var_diff.min().min() < 0:
            logger.warning("Variance difference matrix not positive definite. Adding regularization.")
            var_diff = var_diff + np.eye(var_diff.shape[0]) * 1e-6

        try:
            hausman_stat = diff.T @ np.linalg.inv(var_diff) @ diff
            # Chi-squared distribution with degrees of freedom = number of params tested
            from scipy import stats
            p_value = 1 - stats.chi2.cdf(hausman_stat, df=len(common_idx))
            hausman_result = {
                "statistic": float(hausman_stat),
                "p_value": float(p_value),
                "df": len(common_idx),
                "recommendation": "Use RE" if p_value > 0.05 else "Use FE"
            }
        except np.linalg.LinAlgError:
            hausman_result = {"error": "Singular matrix in Hausman test"}

    except Exception as e:
        logger.error(f"Hausman test calculation failed: {e}")
        hausman_result = {"error": str(e)}

    return {
        "model_type": "Random Effects",
        "reason": "All countries were time-invariant",
        "fe_coefficients": res_fe.params.to_dict(),
        "re_coefficients": res_re.params.to_dict(),
        "hausman_test": hausman_result
    }

def count_hypothesis_tests() -> int:
    """Count primary hypothesis tests (Fixed Effects, Interaction, Non-linearity)."""
    return 3

def save_test_count(count: int, output_path: Path) -> None:
    with open(output_path, 'w') as f:
        json.dump({"test_count": count}, f)

def aggregate_p_values_and_correct(p_values: List[float], alpha: float = 0.05) -> List[Dict]:
    """Apply Benjamini-Hochberg FDR correction."""
    n = len(p_values)
    if n == 0: return []
    
    indexed = list(enumerate(p_values))
    sorted_indexed = sorted(indexed, key=lambda x: x[1])
    
    corrected = []
    for i, (idx, p) in enumerate(sorted_indexed):
        rank = i + 1
        threshold = (rank / n) * alpha
        corrected.append({
            "original_index": idx,
            "p_value": p,
            "threshold": threshold,
            "is_significant": p <= threshold
        })
    
    return corrected

def save_regression_metadata(is_associational: bool, output_path: Path) -> None:
    with open(output_path, 'w') as f:
        json.dump({"is_associational": is_associational}, f)

def run_f_test_joint_significance(df: pd.DataFrame, interaction_cols: List[str]) -> Dict[str, Any]:
    """Run F-test for joint significance of interaction terms."""
    # Implementation depends on having the interaction terms in the dataframe
    # Placeholder for logic to construct model with interactions and test
    return {"f_statistic": 0.0, "p_value": 1.0, "is_significant": False}

def main():
    """
    Main entry point for T041: Random Effects Fallback.
    1. Load time-invariant report (T022 output).
    2. Check if ALL countries are time-invariant.
    3. If yes, run Random Effects + Hausman Test.
    4. Save result to data/processed/model_selection.json.
    """
    logger.info("Starting T041: Random Effects Fallback")
    
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load time-invariant report
    time_invariant_path = processed_dir / "time_invariant_countries.json"
    if not time_invariant_path.exists():
        logger.error(f"Time-invariant report not found at {time_invariant_path}. Run T022 first.")
        return

    with open(time_invariant_path, 'r') as f:
        ti_data = json.load(f)
    
    invariant_codes = ti_data.get("flagged_countries", [])
    invariant_count = len(invariant_codes)
    
    # We need total number of countries in the dataset to compare.
    # We assume the dataset used for regression is the merged panel.
    merged_panel_path = processed_dir / "merged_panel.csv"
    if not merged_panel_path.exists():
        logger.error(f"Merged panel not found at {merged_panel_path}. Run T013 first.")
        return
    
    df = pd.read_csv(merged_panel_path)
    total_countries = df['country_code'].nunique()
    
    logger.info(f"Total countries in dataset: {total_countries}")
    logger.info(f"Time-invariant countries: {invariant_count}")
    
    model_selection = {
        "status": "Normal",
        "model_used": "Fixed Effects",
        "reason": "Not all countries are time-invariant",
        "invariant_count": invariant_count,
        "total_countries": total_countries
    }
    
    # Check condition: If ALL countries are time-invariant
    if invariant_count == total_countries:
        logger.warning("ALL countries are time-invariant. Switching to Random Effects model.")
        
        # Filter to keep only valid rows for RE (though all are invariant, we still need data)
        # T040 would have filtered these out for FE, but for RE we use the data as is (or filtered if needed)
        # Since T040 filters out invariant countries, if we are here, T040 would have left 0 rows.
        # However, the task says "If ALL countries are time-invariant... switch to RE".
        # This implies we use the original data (or the data before FE exclusion) for RE.
        # Let's assume we use the original merged panel for RE if FE fails completely.
        
        # We need to run RE on the data.
        # Note: If T040 already ran and filtered everything, we have no data.
        # The logic flow implies T040 filters for FE. If FE is impossible, we skip T040 filter and go to RE.
        # So we use 'df' (the full merged panel) here.
        
        result = run_random_effects_fallback(df, invariant_count, total_countries)
        
        model_selection = {
            "status": "Fallback",
            "model_used": "Random Effects",
            "reason": "All countries were time-invariant, Fixed Effects not possible",
            "invariant_count": invariant_count,
            "total_countries": total_countries,
            "results": result
        }
    else:
        logger.info("Standard Fixed Effects model is viable.")
        # Even if some are invariant, we just run FE (which handles absorbed variables or we filter them out)
        # The task specifically asks for the fallback logic when ALL are invariant.
        
    # Save output
    output_path = processed_dir / "model_selection.json"
    with open(output_path, 'w') as f:
        json.dump(model_selection, f, indent=2)
    
    logger.info(f"Model selection saved to {output_path}")

if __name__ == "__main__":
    main()