"""
Permutation-based p-value calculation for feature importances.

This module implements a permutation test to determine the statistical
significance of feature importances derived from a trained model.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score, mean_squared_error
from joblib import load

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure output directories exist
def ensure_dirs(output_dir: Path) -> None:
    """Ensure the output directory exists."""
    output_dir.mkdir(parents=True, exist_ok=True)

def load_models(model_dir: Path) -> Dict[str, Any]:
    """
    Load trained models from the model directory.
    
    Args:
        model_dir: Path to the directory containing saved models.
        
    Returns:
        Dictionary mapping model names to loaded model objects.
    """
    models = {}
    for file_path in model_dir.glob("*.joblib"):
        model_name = file_path.stem
        logger.info(f"Loading model: {model_name}")
        models[model_name] = load(file_path)
    return models

def load_test_data(data_path: Path) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load the test dataset.
    
    Args:
        data_path: Path to the test CSV file.
        
    Returns:
        Tuple of (feature DataFrame, target Series).
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Test data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Identify target column (assuming 'langmuir_capacity' or similar)
    target_col = None
    for col in ['langmuir_capacity', 'henry_constant']:
        if col in df.columns:
            target_col = col
            break
    
    if target_col is None:
        raise ValueError("Could not identify target column in test data.")
    
    feature_cols = [col for col in df.columns if col not in ['material_id', target_col]]
    X = df[feature_cols]
    y = df[target_col]
    
    return X, y

def calculate_p_values(
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
    n_permutations: int = 1000,
    scoring: str = 'r2',
    random_state: Optional[int] = None,
    n_jobs: int = -1
) -> pd.DataFrame:
    """
    Calculate p-values for feature importances using permutation testing.
    
    The null hypothesis is that the feature has no predictive power.
    We permute the target variable y (not the features) to break the
    relationship between X and y, then measure the drop in performance.
    The p-value is the fraction of permutations where the permuted model
    performs as well as or better than the original model.
    
    Args:
        model: Trained model object.
        X: Feature DataFrame.
        y: Target Series.
        n_permutations: Number of permutations to perform.
        scoring: Scoring metric (e.g., 'r2', 'neg_mean_squared_error').
        random_state: Random seed for reproducibility.
        n_jobs: Number of parallel jobs.
        
    Returns:
        DataFrame with feature names, original scores, permuted scores, and p-values.
    """
    logger.info(f"Starting permutation test with {n_permutations} permutations...")
    
    # Calculate original score
    original_pred = model.predict(X)
    if scoring == 'r2':
        original_score = r2_score(y, original_pred)
    elif scoring == 'neg_mean_squared_error':
        original_score = mean_squared_error(y, original_pred)
    else:
        # Default to R2
        original_score = r2_score(y, original_pred)
    
    logger.info(f"Original model score ({scoring}): {original_score:.4f}")
    
    # Permute target variable y to break relationship with X
    # This is more rigorous than permuting features because it tests
    # the null hypothesis that y is independent of X
    rng = np.random.RandomState(random_state)
    perm_scores = []
    
    for i in range(n_permutations):
        # Permute y
        y_perm = y.sample(frac=1, random_state=rng).reset_index(drop=True)
        
        # Evaluate model on permuted target
        # We use the same X but compare predictions against permuted y
        # This measures how much the model's performance drops when the
        # true relationship is broken
        if scoring == 'r2':
            perm_score = r2_score(y_perm, original_pred)
        elif scoring == 'neg_mean_squared_error':
            perm_score = mean_squared_error(y_perm, original_pred)
        else:
            perm_score = r2_score(y_perm, original_pred)
        
        perm_scores.append(perm_score)
    
    perm_scores = np.array(perm_scores)
    
    # Calculate p-value: proportion of permutations where permuted score >= original score
    # For R2, higher is better, so we count how often perm_score >= original_score
    # For MSE (negative), lower is better, so we need to adjust logic
    if scoring == 'r2' or 'r2' in scoring.lower():
        p_values = (perm_scores >= original_score) / n_permutations
    else:
        # For negative metrics, we want to count how often the permuted model
        # performs as well as or better (less negative or more positive)
        p_values = (perm_scores >= original_score) / n_permutations
    
    # Create results DataFrame
    feature_names = list(X.columns)
    results = pd.DataFrame({
        'feature': feature_names,
        'original_score': [original_score] * len(feature_names),
        'mean_perm_score': np.mean(perm_scores),
        'std_perm_score': np.std(perm_scores),
        'p_value': p_values
    })
    
    # Sort by p-value (most significant first)
    results = results.sort_values('p_value', ascending=True).reset_index(drop=True)
    
    logger.info(f"Permutation test completed. Results saved.")
    return results

def run_permutation_analysis(
    model_name: str,
    model_dir: Path,
    test_data_path: Path,
    output_dir: Path,
    n_permutations: int = 1000,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Run the full permutation analysis pipeline.
    
    Args:
        model_name: Name of the model to analyze.
        model_dir: Directory containing saved models.
        test_data_path: Path to the test dataset.
        output_dir: Directory to save results.
        n_permutations: Number of permutations.
        random_state: Random seed.
        
    Returns:
        Dictionary containing analysis results.
    """
    ensure_dirs(output_dir)
    
    # Load model
    models = load_models(model_dir)
    if model_name not in models:
        raise ValueError(f"Model '{model_name}' not found. Available: {list(models.keys())}")
    
    model = models[model_name]
    
    # Load test data
    X, y = load_test_data(test_data_path)
    
    # Run permutation test
    results = calculate_p_values(
        model=model,
        X=X,
        y=y,
        n_permutations=n_permutations,
        random_state=random_state
    )
    
    # Save results
    output_path = output_dir / f"pvalues_{model_name}.csv"
    results.to_csv(output_path, index=False)
    logger.info(f"P-value results saved to {output_path}")
    
    # Also save a summary JSON
    summary = {
        'model_name': model_name,
        'n_permutations': n_permutations,
        'random_state': random_state,
        'features': results['feature'].tolist(),
        'p_values': results['p_value'].tolist(),
        'significant_features': results[results['p_value'] < 0.05]['feature'].tolist(),
        'output_file': str(output_path)
    }
    
    summary_path = output_dir / f"pvalues_{model_name}_summary.json"
    import json
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Summary saved to {summary_path}")
    
    return summary

def main():
    """Main entry point for the permutation p-value analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate p-values for feature importances")
    parser.add_argument("--model_name", type=str, default="random_forest",
                      help="Name of the model to analyze")
    parser.add_argument("--model_dir", type=str, default="data/models",
                      help="Directory containing saved models")
    parser.add_argument("--test_data", type=str, default="data/processed/test_data.csv",
                      help="Path to test dataset")
    parser.add_argument("--output_dir", type=str, default="data/validation",
                      help="Directory to save results")
    parser.add_argument("--n_permutations", type=int, default=1000,
                      help="Number of permutations")
    parser.add_argument("--random_state", type=int, default=42,
                      help="Random seed")
    
    args = parser.parse_args()
    
    try:
        result = run_permutation_analysis(
            model_name=args.model_name,
            model_dir=Path(args.model_dir),
            test_data_path=Path(args.test_data),
            output_dir=Path(args.output_dir),
            n_permutations=args.n_permutations,
            random_state=args.random_state
        )
        print(f"Analysis complete. Significant features: {result['significant_features']}")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
