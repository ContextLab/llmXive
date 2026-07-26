"""
Robustness validation module.
Executes bootstrapping for effect size confidence intervals.
"""
import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedShuffleSplit
from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("robustness")

def bootstrap_effect_size(df: pd.DataFrame, n_iterations: int = 100):
    """
    Bootstrap effect size estimation.
    
    Args:
        df: Merged data
        n_iterations: Number of bootstrap iterations
    
    Returns:
        List of effect sizes
    """
    effect_sizes = []
    
    # Simple effect size: difference in mean adherence between groups
    for i in range(n_iterations):
        # Stratified sample
        sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=i)
        for train_idx, _ in sss.split(df, df['Gamified']):
            sample = df.iloc[train_idx]
            mean_gamified = sample[sample['Gamified']]['Adherence'].mean()
            mean_control = sample[~sample['Gamified']]['Adherence'].mean()
            effect = mean_gamified - mean_control
            effect_sizes.append(effect)
    
    return effect_sizes

def main():
    """CLI entry point."""
    log_pipeline_stage(logger, "START", "Robustness Validation")
    
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(root, "data", "processed", "merged_data.csv")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    df = pd.read_csv(input_path)
    
    effects = bootstrap_effect_size(df, n_iterations=50)
    
    mean_effect = np.mean(effects)
    std_effect = np.std(effects)
    ci_low = np.percentile(effects, 2.5)
    ci_high = np.percentile(effects, 97.5)
    
    logger.info(f"Bootstrap Results: Mean={mean_effect:.4f}, Std={std_effect:.4f}")
    logger.info(f"95% CI: [{ci_low:.4f}, {ci_high:.4f}]")
    
    if std_effect >= 0.01:
        logger.warning(f"Bootstrap variance ({std_effect:.4f}) exceeds threshold.")
    
    # Save results
    result = {
        "mean_effect": mean_effect,
        "std_effect": std_effect,
        "ci_95": [ci_low, ci_high],
        "iterations": 50
    }
    
    output_path = os.path.join(root, "data", "processed", "bootstrap_results.json")
    import json
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    log_pipeline_stage(logger, "END", "Robustness Validation")

if __name__ == "__main__":
    main()
