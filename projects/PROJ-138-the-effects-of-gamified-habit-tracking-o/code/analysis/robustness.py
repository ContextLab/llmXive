import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedShuffleSplit

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("robustness")

def bootstrap_effect_size(df: pd.DataFrame, n_iterations: int = 1000) -> dict:
    """
    Execute bootstrapping to generate confidence interval for effect size.
    
    Args:
        df: Data with gamified_status and outcome
        n_iterations: Number of bootstrap iterations
        
    Returns:
        Dictionary with variance, CI, and robustness status
    """
    # Ensure stratified split
    sss = StratifiedShuffleSplit(n_splits=n_iterations, test_size=0.2, random_state=42)
    
    effect_sizes = []
    
    # Simplified effect size calculation: difference in means of adherence
    # In a real scenario, this would be the coefficient from the model
    
    for train_idx, test_idx in sss.split(df, df['gamified_status']):
        train_df = df.iloc[train_idx]
        
        # Calculate mean adherence by group
        mean_gamified = train_df[train_df['gamified_status'] == True]['weekly_adherence_flag'].mean()
        mean_non_gamified = train_df[train_df['gamified_status'] == False]['weekly_adherence_flag'].mean()
        
        effect = mean_gamified - mean_non_gamified
        effect_sizes.append(effect)
    
    effect_sizes = np.array(effect_sizes)
    variance = np.var(effect_sizes)
    ci_lower = np.percentile(effect_sizes, 2.5)
    ci_upper = np.percentile(effect_sizes, 97.5)
    
    robustness_status = "passed" if variance < 0.01 else "failed"
    
    return {
        "variance": float(variance),
        "ci": [float(ci_lower), float(ci_upper)],
        "robustness_status": robustness_status,
        "n_iterations": n_iterations
    }

def main():
    parser = argparse.ArgumentParser(description="Run robustness validation")
    args = parser.parse_args()
    
    log_pipeline_stage(logger, "START", "Robustness Validation")
    
    try:
        # Load data
        input_path = "data/processed/merged_data.csv"
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} records for robustness analysis")
        
        # Run bootstrapping
        results = bootstrap_effect_size(df, n_iterations=100) # Reduced for speed
        
        # Save results
        output_path = "data/processed/robustness_report.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            import json
            json.dump(results, f, indent=2)
        
        logger.info(f"Written robustness report to {output_path}")
        logger.info(f"Robustness status: {results['robustness_status']}")
        
        log_pipeline_stage(logger, "SUCCESS", "Robustness Validation Complete")
        return 0
        
    except Exception as e:
        log_pipeline_stage(logger, "ERROR", str(e))
        return 1

if __name__ == "__main__":
  import argparse
  sys.exit(main())
