import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Ensure imports align with existing project structure
# We assume this file is run from the project root or code/ directory
# Adding code/ to path if running as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from models.entities import IsothermParameter
from models.evaluate import load_models, load_test_data, ensure_dirs as ensure_eval_dirs

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_dirs(output_dir: Optional[Path] = None) -> Path:
    """Create output directories for permutation analysis results."""
    if output_dir is None:
        output_dir = Path("data/validation")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def load_test_data() -> pd.DataFrame:
    """
    Load the preprocessed test data.
    Expects data/processed/adsorption_dataset.csv as per pipeline convention.
    """
    data_path = Path("data/processed/adsorption_dataset.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Test data not found at {data_path}. Run preprocessing first.")
    
    df = pd.read_csv(data_path)
    
    # Identify target columns based on schema
    target_cols = [col for col in df.columns if col in ['langmuir_capacity', 'henry_constant']]
    if not target_cols:
        raise ValueError("No valid target columns found in dataset.")
    
    # We focus on the primary target for permutation analysis if multiple exist
    # For this implementation, we'll use 'langmuir_capacity' if present, else the first available
    target = 'langmuir_capacity' if 'langmuir_capacity' in target_cols else target_cols[0]
    
    # Filter to only include rows with valid targets
    df = df.dropna(subset=[target])
    
    return df, target

def calculate_p_values(
    model_name: str,
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
    n_permutations: int = 1000,
    scoring: str = 'r2',
    random_state: int = 42,
    n_jobs: int = -1
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Calculate permutation-based p-values for feature importances.
    
    The p-value represents the probability that the observed importance 
    could have occurred by chance (i.e., importance of permuted feature >= original).
    
    Args:
        model_name: Name of the model being analyzed
        model: Trained sklearn-compatible model
        X: Feature matrix (test set)
        y: Target values (test set)
        n_permutations: Number of permutations per feature
        scoring: Scoring metric to use (e.g., 'r2', 'neg_mean_squared_error')
        random_state: Random seed for reproducibility
        n_jobs: Number of parallel jobs (-1 for all)
        
    Returns:
        Tuple of (results_df, p_values_dict)
    """
    logger.info(f"Starting permutation analysis for {model_name} with {n_permutations} permutations")
    
    # Calculate original score
    original_score = model.score(X, y)
    logger.info(f"Original {scoring} score: {original_score:.4f}")
    
    # Calculate permutation importance
    # sklearn's permutation_importance returns mean and std of score decrease
    perm_result = permutation_importance(
        model, X, y,
        n_permutations=n_permutations,
        scoring=scoring,
        random_state=random_state,
        n_jobs=n_jobs
    )
    
    feature_names = X.columns.tolist()
    mean_importance = perm_result.importances_mean
    std_importance = perm_result.importances_std
    
    # Calculate p-values
    # For each feature, we compare the distribution of permuted importances
    # against the observed importance.
    # A low p-value means the feature's importance is significantly better than random.
    
    p_values = {}
    importance_stats = []
    
    for i, feature in enumerate(feature_names):
        # The importance in sklearn is defined as: original_score - permuted_score
        # So higher positive values mean the feature is important.
        # We want to test if the observed importance is significantly greater than 0 (or random).
        
        # Get the distribution of importance values for this feature
        # perm_result.importances shape: (n_features, n_permutations)
        feature_importances = perm_result.importances[i]
        
        # Calculate the observed importance for this feature
        # Note: sklearn's mean_importance is the average decrease in score
        observed_importance = mean_importance[i]
        
        # P-value: proportion of permuted importances >= observed importance
        # This tests the null hypothesis that the feature is not important
        # If the observed importance is much larger than permuted ones, p-value is small
        p_value = np.mean(feature_importances >= observed_importance)
        
        # However, a more standard approach for feature importance p-values
        # is to test if the importance is significantly greater than 0
        # Let's use the distribution of permuted importances to create a null distribution
        # and see where the observed importance falls.
        
        # Actually, the standard permutation test for feature importance:
        # 1. Compute importance with original data
        # 2. Shuffle the feature values many times
        # 3. Compute importance for each shuffled version
        # 4. p-value = (number of shuffled importances >= original importance + 1) / (n_permutations + 1)
        
        # But sklearn's permutation_importance already does the shuffling internally
        # and returns the decrease in score. So we can use the distribution directly.
        
        # Let's recalculate to be precise:
        # We have the distribution of score decreases from shuffling
        # We want to know if the observed decrease is significantly larger than what we'd get by chance
        
        # The observed importance is mean_importance[i]
        # The null distribution is feature_importances (the decreases from shuffling)
        
        # If the feature is important, shuffling it should cause a large drop in performance
        # So the observed importance should be much larger than the permuted importances
        
        # P-value: probability that a random permutation gives an importance >= observed
        # This is the standard one-sided test
        p_val = (np.sum(feature_importances >= observed_importance) + 1) / (n_permutations + 1)
        
        p_values[feature] = p_val
        
        importance_stats.append({
            'feature': feature,
            'importance': observed_importance,
            'std': std_importance[i],
            'p_value': p_val
        })
    
    results_df = pd.DataFrame(importance_stats)
    results_df = results_df.sort_values('importance', ascending=False)
    
    logger.info(f"Permutation analysis complete. Top 3 features: {results_df.head(3)['feature'].tolist()}")
    
    return results_df, p_values

def run_permutation_analysis(
    model_names: Optional[List[str]] = None,
    n_permutations: int = 1000,
    scoring: str = 'r2',
    random_state: int = 42,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run permutation-based p-value calculation for all trained models.
    
    Args:
        model_names: List of model names to analyze. If None, uses all available models.
        n_permutations: Number of permutations per feature
        scoring: Scoring metric
        random_state: Random seed
        output_dir: Directory to save results
        
    Returns:
        Dictionary containing analysis results for all models
    """
    output_dir = ensure_dirs(output_dir)
    
    # Load data and models
    logger.info("Loading test data and models...")
    df, target = load_test_data()
    models = load_models()
    
    if not models:
        raise RuntimeError("No models found. Run training first.")
    
    # Filter models if specific names provided
    if model_names:
        models = {k: v for k, v in models.items() if k in model_names}
    
    results = {}
    
    for model_name, model in models.items():
        logger.info(f"Analyzing {model_name}...")
        
        # Prepare features
        # Exclude non-feature columns
        exclude_cols = ['material_id', 'adsorbate_smiles', 'adsorbent_id', 
                      'langmuir_capacity', 'henry_constant', 'surface_area']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        X = df[feature_cols]
        y = df[target]
        
        # Calculate p-values
        importance_df, p_values = calculate_p_values(
            model_name=model_name,
            model=model,
            X=X,
            y=y,
            n_permutations=n_permutations,
            scoring=scoring,
            random_state=random_state
        )
        
        # Save results for this model
        output_path = output_dir / f"permutation_pvalues_{model_name}.csv"
        importance_df.to_csv(output_path, index=False)
        logger.info(f"Saved results to {output_path}")
        
        results[model_name] = {
            'importance_df': importance_df,
            'p_values': p_values,
            'output_file': str(output_path)
        }
    
    # Save summary
    summary_path = output_dir / "permutation_analysis_summary.json"
    summary_data = {
        'models_analyzed': list(results.keys()),
        'n_permutations': n_permutations,
        'scoring_metric': scoring,
        'random_state': random_state,
        'results': {
            model_name: {
                'top_features': results[model_name]['importance_df'].head(5)[['feature', 'importance', 'p_value']].to_dict('records'),
                'significant_features': [
                    feat for feat, p in results[model_name]['p_values'].items() 
                    if p < 0.05
                ]
            }
            for model_name in results
        }
    }
    
    import json
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    logger.info(f"Summary saved to {summary_path}")
    return results

def main():
    """Main entry point for permutation p-value analysis."""
    logger.info("Starting permutation-based p-value calculation for feature importances")
    
    try:
        results = run_permutation_analysis(
            n_permutations=1000,
            scoring='r2',
            random_state=42
        )
        
        logger.info("Permutation analysis completed successfully")
        
        # Print summary
        for model_name, model_results in results.items():
            print(f"\n{model_name}:")
            print(model_results['importance_df'].to_string(index=False))
            
    except Exception as e:
        logger.error(f"Error during permutation analysis: {e}")
        raise

if __name__ == "__main__":
    main()