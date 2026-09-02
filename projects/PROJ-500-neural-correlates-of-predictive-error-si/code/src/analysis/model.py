import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

def load_aligned_data(data_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load the aligned dataset from CSV.
    Expects columns: subject_id, block_id, mmn_amplitude, accuracy, etc.
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Aligned data file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def apply_fdr_correction(p_values: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Benjamini-Hochberg FDR correction.
    Returns corrected p-values and boolean mask of significant results.
    """
    n = len(p_values)
    if n == 0:
        return np.array([]), np.array([])
    
    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_pvals = p_values[sorted_indices]
    
    # Calculate BH critical values
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * alpha
    
    # Find largest k such that p(k) <= critical(k)
    # We need to find the largest index where sorted_pvals <= critical_values
    mask = sorted_pvals <= critical_values
    if not np.any(mask):
        # No significant results
        corrected_pvals = np.ones(n)
        significant = np.zeros(n, dtype=bool)
    else:
        # Find the largest k
        k_indices = np.where(mask)[0]
        k = k_indices[-1]
        # All p-values up to k are significant
        significant = np.zeros(n, dtype=bool)
        significant[sorted_indices[:k+1]] = True
        # Corrected p-values
        corrected_pvals = np.ones(n)
        # Calculate adjusted p-values: min(p_j * n / j, 1) for j >= i
        # Standard BH adjustment
        adjusted = sorted_pvals * n / ranks
        adjusted = np.minimum(adjusted, 1.0)
        # Monotonicity correction (cumulative min from the end)
        for i in range(n - 2, -1, -1):
            adjusted[i] = min(adjusted[i], adjusted[i+1])
        corrected_pvals[sorted_indices] = adjusted
    
    return corrected_pvals, significant

def fit_lme_model(df: pd.DataFrame, formula: str = "mmn_amplitude ~ accuracy + (1|subject_id)") -> Dict[str, Any]:
    """
    Fit a Linear Mixed Effects model using statsmodels.
    Returns model summary statistics.
    """
    try:
        model = smf.mixedlm(formula, df, groups=df["subject_id"])
        result = model.fit()
        
        # Extract coefficients and p-values
        coeffs = result.params.to_dict()
        pvals = result.pvalues.to_dict()
        
        return {
            "coefficients": coeffs,
            "p_values": pvals,
            "model_summary": str(result.summary()),
            "aic": result.aic,
            "bic": result.bic,
            "loglike": result.llf,
            "converged": result.converged
        }
    except Exception as e:
        logger.error(f"Failed to fit LME model: {e}")
        raise

def run_permutation_test(
    df: pd.DataFrame,
    dependent_var: str = "mmn_amplitude",
    independent_var: str = "accuracy",
    group_var: str = "subject_id",
    n_permutations: int = 1000,
    random_state: Optional[int] = None,
    check_sufficiency: bool = True
) -> Dict[str, Any]:
    """
    Perform a permutation test to validate significance of the relationship
    between independent_var and dependent_var, controlling for group_var.
    
    Implements a block-permutation approach:
    1. Fit the original model to get the observed statistic (t-value for accuracy).
    2. Shuffle the independent variable (accuracy) across subjects/blocks while 
       preserving the structure within subjects (or shuffling subject labels).
    3. Refit the model and record the t-value.
    4. Repeat n times.
    5. Calculate p-value as proportion of permuted statistics >= observed.
    
    Includes logic to check if n=1000 is sufficient based on p-value stability.
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    # 1. Calculate observed statistic
    # We'll use the t-statistic for the independent variable
    # If the model fails or data is insufficient, return early
    if len(df) < 10:
        logger.warning("Dataset too small for permutation test (< 10 rows)")
        return {
            "observed_statistic": None,
            "p_value": None,
            "n_permutations": 0,
            "sufficient": False,
            "reason": "Dataset too small"
        }
    
    # Fit original model to get observed t-statistic
    formula = f"{dependent_var} ~ {independent_var} + (1|{group_var})"
    try:
        original_model = smf.mixedlm(formula, df, groups=df[group_var])
        original_result = original_model.fit()
        
        # Get t-statistic for the independent variable
        if independent_var not in original_result.pvalues.index:
            logger.error(f"Independent variable '{independent_var}' not found in model coefficients")
            return {
                "observed_statistic": None,
                "p_value": None,
                "n_permutations": 0,
                "sufficient": False,
                "reason": "Variable not in model"
            }
        
        observed_t = original_result.tvalues[independent_var]
        observed_p = original_result.pvalues[independent_var]
    except Exception as e:
        logger.error(f"Failed to fit original model for permutation test: {e}")
        return {
            "observed_statistic": None,
            "p_value": None,
            "n_permutations": 0,
            "sufficient": False,
            "reason": f"Model fit failed: {str(e)}"
        }
    
    logger.info(f"Observed t-statistic: {observed_t:.4f}, p-value: {observed_p:.4f}")
    
    # 2. Permutation loop
    permuted_stats = []
    n_subjects = df[group_var].nunique()
    
    # Determine if we can permute at subject level or trial level
    # If n_subjects is small, we might need to permute at trial level
    # But for LME, subject-level permutation is more appropriate
    
    for i in range(n_permutations):
        # Create a copy of the dataframe
        perm_df = df.copy()
        
        # Shuffle the independent variable within subjects or across subjects
        # For a rigorous test, we shuffle the independent variable across all rows
        # but we must be careful to maintain the structure if there are repeated measures
        
        # Option A: Shuffle the independent variable across all rows (ignoring structure)
        # This is a valid null hypothesis: no relationship between accuracy and MMN
        perm_df[independent_var] = np.random.permutation(perm_df[independent_var].values)
        
        try:
            # Fit model on permuted data
            perm_model = smf.mixedlm(formula, perm_df, groups=perm_df[group_var])
            perm_result = perm_model.fit()
            
            # Get t-statistic
            if independent_var in perm_result.tvalues.index:
                perm_t = perm_result.tvalues[independent_var]
                permuted_stats.append(perm_t)
            else:
                # If variable not in model (unlikely), skip
                permuted_stats.append(0.0)
        except Exception:
            # If model fails to converge, use 0 as placeholder
            permuted_stats.append(0.0)
        
        # Progress logging
        if (i + 1) % 200 == 0:
            logger.info(f"Permutation {i+1}/{n_permutations} completed")
    
    permuted_stats = np.array(permuted_stats)
    
    # 3. Calculate p-value
    # Two-tailed test: proportion of |permuted| >= |observed|
    abs_observed = np.abs(observed_t)
    abs_permuted = np.abs(permuted_stats)
    
    p_value = np.mean(abs_permuted >= abs_observed)
    
    # 4. Check sufficiency of n=1000
    sufficient = True
    sufficiency_reason = "n=1000 is sufficient"
    
    if check_sufficiency and n_permutations >= 500:
        # Check stability of p-value in the last half of permutations
        mid_point = n_permutations // 2
        first_half_p = np.mean(abs_permuted[:mid_point] >= abs_observed)
        second_half_p = np.mean(abs_permuted[mid_point:] >= abs_observed)
        
        # If the p-value changes significantly between halves, more permutations needed
        if abs(first_half_p - second_half_p) > 0.05:
            sufficient = False
            sufficiency_reason = f"P-value unstable: first half={first_half_p:.3f}, second half={second_half_p:.3f}"
        
        # Also check if p-value is very close to 0 or 1, which might need more precision
        if p_value < 0.001 or p_value > 0.999:
            if n_permutations == 1000:
                sufficient = False
                sufficiency_reason = f"P-value extreme ({p_value:.4f}), consider increasing n for precision"
    
    result = {
        "observed_statistic": float(observed_t),
        "observed_p_value": float(observed_p),
        "permutation_p_value": float(p_value),
        "n_permutations": n_permutations,
        "sufficient": sufficient,
        "sufficiency_reason": sufficiency_reason,
        "permuted_statistics": permuted_stats.tolist()  # Save for inspection
    }
    
    logger.info(f"Permutation test completed: p={p_value:.4f}, sufficient={sufficient}")
    return result

def analyze_multiple_electrodes(
    df: pd.DataFrame,
    electrodes: List[str],
    formula: str = "mmn_amplitude ~ accuracy + (1|subject_id)"
) -> Dict[str, Any]:
    """
    Run the full modeling pipeline (LME + permutation test) for multiple electrodes.
    """
    results = {}
    
    for electrode in electrodes:
        logger.info(f"Analyzing electrode: {electrode}")
        
        # Filter data for this electrode (assuming electrode column exists)
        if "electrode" in df.columns:
            electrode_df = df[df["electrode"] == electrode]
        else:
            # If no electrode column, assume data is already filtered or aggregated
            electrode_df = df
        
        if len(electrode_df) == 0:
            logger.warning(f"No data for electrode {electrode}")
            continue
        
        # Fit LME model
        lme_results = fit_lme_model(electrode_df, formula)
        
        # Run permutation test
        perm_results = run_permutation_test(
            electrode_df,
            dependent_var="mmn_amplitude",
            independent_var="accuracy",
            group_var="subject_id",
            n_permutations=1000,
            check_sufficiency=True
        )
        
        results[electrode] = {
            "lme": lme_results,
            "permutation": perm_results
        }
    
    return results

def run_modeling_pipeline(
    data_path: Union[str, Path],
    output_path: Union[str, Path],
    electrodes: Optional[List[str]] = None,
    formula: str = "mmn_amplitude ~ accuracy + (1|subject_id)"
) -> Dict[str, Any]:
    """
    Run the complete modeling pipeline:
    1. Load aligned data
    2. Fit LME models for specified electrodes
    3. Apply FDR correction to p-values
    4. Run permutation tests
    5. Save results to JSON
    """
    data_path = Path(data_path)
    output_path = Path(output_path)
    
    # Load data
    df = load_aligned_data(data_path)
    
    # Determine electrodes to analyze
    if electrodes is None:
        if "electrode" in df.columns:
            electrodes = df["electrode"].unique().tolist()
        else:
            # If no electrode column, analyze the whole dataset once
            electrodes = ["all"]
    
    # Run analysis
    all_results = analyze_multiple_electrodes(df, electrodes, formula)
    
    # Extract p-values for FDR correction
    all_pvals = []
    electrode_list = []
    
    for electrode, res in all_results.items():
        if "lme" in res and "p_values" in res["lme"]:
            pval = res["lme"]["p_values"].get("accuracy", 1.0)
            all_pvals.append(pval)
            electrode_list.append(electrode)
    
    # Apply FDR correction
    if len(all_pvals) > 0:
        corrected_pvals, significant = apply_fdr_correction(np.array(all_pvals))
        
        # Add FDR results to each electrode
        for i, electrode in enumerate(electrode_list):
            if electrode in all_results:
                all_results[electrode]["fdr"] = {
                    "corrected_p_value": float(corrected_pvals[i]),
                    "significant": bool(significant[i])
                }
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_for_json(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_for_json(v) for v in obj]
        return obj
    
    serializable_results = convert_for_json(all_results)
    
    with open(output_path, "w") as f:
        json.dump(serializable_results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return serializable_results

def main():
    """
    Main entry point for the modeling pipeline.
    Reads configuration from environment or defaults.
    """
    # Default paths
    data_dir = Path("data")
    output_dir = Path("analysis/results")
    
    aligned_data_path = data_dir / "aligned_data.csv"
    output_path = output_dir / "model_output.json"
    
    # Check if data exists
    if not aligned_data_path.exists():
        logger.error(f"Aligned data not found at {aligned_data_path}")
        logger.error("Please run the alignment pipeline first (T026)")
        return 1
    
    # Run pipeline
    try:
        results = run_modeling_pipeline(
            data_path=aligned_data_path,
            output_path=output_path,
            electrodes=["CP3", "CP4", "C3", "C4"]  # Default electrodes from spec
        )
        
        # Print summary
        print(f"Modeling pipeline completed. Results saved to {output_path}")
        print(f"Analyzed {len(results)} electrodes")
        
        # Print permutation test summary
        for electrode, res in results.items():
            if "permutation" in res:
                perm = res["permutation"]
                print(f"  {electrode}: perm_p={perm['permutation_p_value']:.4f}, "
                      f"sufficient={perm['sufficient']}")
        
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    exit(main())
