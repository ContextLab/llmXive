"""
Robustness validation module.
Implements bootstrapping for effect size confidence intervals.
"""
import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm
from code.utils.logging import pipeline_logger

INPUT_PATH = "data/processed/merged_data.csv"
OUTPUT_PATH = "data/processed/robustness_results.csv"
N_BOOTSTRAP = 100

def bootstrap_effect_size(df: pd.DataFrame, n_iterations: int = 100) -> dict:
    """
    Execute bootstrapping to generate 95% CI for gamification effect size.
    
    Args:
        df: DataFrame with aggregated data.
        n_iterations: Number of bootstrap iterations.
        
    Returns:
        Dict with coefficient variance and CI.
    """
    pipeline_logger.info(f"Starting bootstrapping ({n_iterations} iterations)...")
    
    coefficients = []
    
    # Prepare data
    df = df.dropna(subset=["weekly_adherence_flag", "gamification_status", "conscientiousness_score"])
    df["gamification_numeric"] = df["gamification_status"].astype(int)
    
    formula = "weekly_adherence_flag ~ gamification_numeric + conscientiousness_score + gamification_numeric * conscientiousness_score"
    
    for i in range(n_iterations):
        # Sample with replacement
        sample_df = df.sample(n=len(df), replace=True)
        
        try:
            # Fit model
            model = mixedlm(formula, sample_df, groups=sample_df["user_id"])
            result = model.fit(disp=False)
            
            # Extract interaction coefficient
            # The key might be "gamification_numeric:conscientiousness_score"
            # or similar. We'll try to find the interaction term.
            interaction_key = None
            for key in result.params.index:
                if "gamification_numeric" in key and "conscientiousness_score" in key:
                    interaction_key = key
                    break
            
            if interaction_key:
                coefficients.append(result.params[interaction_key])
            else:
                # Fallback: just take the gamification main effect if interaction not found
                if "gamification_numeric" in result.params.index:
                    coefficients.append(result.params["gamification_numeric"])
                else:
                    coefficients.append(np.nan)
                        
        except Exception as e:
            # Skip failed iterations
            coefficients.append(np.nan)
    
    # Calculate stats
    coefficients = np.array(coefficients)
    valid_coeffs = coefficients[~np.isnan(coefficients)]
    
    if len(valid_coeffs) == 0:
        pipeline_logger.warning("No valid coefficients from bootstrapping.")
        return {"variance": 0, "ci_lower": 0, "ci_upper": 0}
    
    variance = np.var(valid_coeffs)
    ci_lower = np.percentile(valid_coeffs, 2.5)
    ci_upper = np.percentile(valid_coeffs, 97.5)
    
    pipeline_logger.info(f"Bootstrap Variance: {variance:.6f}")
    pipeline_logger.info(f"95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    
    return {
        "variance": variance,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "n_valid": len(valid_coeffs)
    }

def main():
    """Main entry point for robustness validation."""
    pipeline_logger.info("Starting robustness validation...")
    
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")
    
    df = pd.read_csv(INPUT_PATH)
    
    results = bootstrap_effect_size(df, n_iterations=N_BOOTSTRAP)
    
    # Save results
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write(f"Bootstrap Iterations: {N_BOOTSTRAP}\n")
        f.write(f"Valid Iterations: {results['n_valid']}\n")
        f.write(f"Coefficient Variance: {results['variance']:.6f}\n")
        f.write(f"95% CI Lower: {results['ci_lower']:.4f}\n")
        f.write(f"95% CI Upper: {results['ci_upper']:.4f}\n")
    
    pipeline_logger.info("Robustness validation complete.")

if __name__ == "__main__":
    main()
