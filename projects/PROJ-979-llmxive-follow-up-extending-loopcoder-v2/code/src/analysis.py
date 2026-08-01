import csv
import json
import logging
import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_entropy_results(entropy_path: str) -> pd.DataFrame:
    """Load entropy results from CSV."""
    path = Path(entropy_path)
    if not path.exists():
        raise FileNotFoundError(f"Entropy results not found at {entropy_path}")
    df = pd.read_csv(path)
    required_cols = ['task_id', 'entropy']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in entropy results")
    return df

def load_convergence_results(convergence_path: str) -> pd.DataFrame:
    """Load convergence results from CSV."""
    path = Path(convergence_path)
    if not path.exists():
        raise FileNotFoundError(f"Convergence results not found at {convergence_path}")
    df = pd.read_csv(path)
    required_cols = ['task_id', 'k', 'is_correct', 'converged']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in convergence results")
    return df

def load_exclusion_log(exclusion_path: str) -> List[Dict[str, Any]]:
    """Load exclusion log from JSON."""
    path = Path(exclusion_path)
    if not path.exists():
        logger.warning(f"Exclusion log not found at {exclusion_path}, returning empty list")
        return []
    with open(path, 'r') as f:
        return json.load(f)

def load_strata_log(strata_path: str) -> Dict[str, Any]:
    """Load strata log from JSON."""
    path = Path(strata_path)
    if not path.exists():
        raise FileNotFoundError(f"Strata log not found at {strata_path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_filtered_splits(splits_path: str) -> List[Dict[str, Any]]:
    """Load filtered splits from JSON."""
    path = Path(splits_path)
    if not path.exists():
        raise FileNotFoundError(f"Filtered splits not found at {splits_path}")
    with open(path, 'r') as f:
        return json.load(f)

def compute_spearman_correlation(entropy_df: pd.DataFrame, convergence_df: pd.DataFrame) -> Tuple[float, float]:
    """Compute Spearman correlation between entropy and convergence metrics."""
    # Merge on task_id
    merged = pd.merge(entropy_df, convergence_df, on='task_id', how='inner')
    if merged.empty:
        logger.warning("No overlapping task_ids between entropy and convergence results")
        return 0.0, 1.0
    
    # Use 'converged' as binary target, or 'first_correct_step' if available
    if 'first_correct_step' in merged.columns:
        y = merged['first_correct_step'].fillna(-1)
    else:
        y = merged['converged'].astype(int)
    
    x = merged['entropy']
    
    # Compute Spearman correlation
    corr, p_val = spearmanr(x, y)
    return float(corr), float(p_val)

def train_logistic_router(entropy_df: pd.DataFrame, convergence_df: pd.DataFrame) -> Tuple[Any, Dict[str, Any]]:
    """Train logistic regression router to predict optimal loop count."""
    # Prepare features: entropy
    X = entropy_df[['entropy']].values
    
    # Prepare target: optimal k (derived from convergence data)
    # For each task_id, find the smallest k where converged=True, else max k
    merged = pd.merge(entropy_df, convergence_df, on='task_id', how='inner')
    
    def get_optimal_k(group):
        converged_rows = group[group['converged'] == True]
        if not converged_rows.empty:
            return converged_rows['k'].min()
        else:
            return group['k'].max()
    
    optimal_k = merged.groupby('task_id').apply(get_optimal_k).reset_index()
    optimal_k.columns = ['task_id', 'optimal_k']
    
    # Merge back
    data = pd.merge(entropy_df, optimal_k, on='task_id', how='inner')
    
    if data.empty:
        raise ValueError("No valid data for router training")
    
    X = data['entropy'].values.reshape(-1, 1)
    y = data['optimal_k'].values
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train logistic regression (multi-class)
    model = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=1000)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    cm = confusion_matrix(y_test, y_pred).tolist()
    
    metrics = {
        'accuracy': float(acc),
        'f1': float(f1),
        'confusion_matrix': cm
    }
    
    return model, metrics

def save_correlation_results(entropy_df: pd.DataFrame, convergence_df: pd.DataFrame, output_path: str):
    """Save correlation analysis results."""
    rho, p_val = compute_spearman_correlation(entropy_df, convergence_df)
    
    results = {
        'spearman_rho': rho,
        'p_value': p_val,
        'n_samples': len(entropy_df)
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Correlation results saved to {output_path}")

def save_router_model(model: Any, model_path: str):
    """Save trained router model."""
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Router model saved to {model_path}")

def run_analysis(entropy_path: str, convergence_path: str) -> Tuple[float, float]:
    """Run full analysis pipeline."""
    entropy_df = load_entropy_results(entropy_path)
    convergence_df = load_convergence_results(convergence_path)
    
    rho, p_val = compute_spearman_correlation(entropy_df, convergence_df)
    logger.info(f"Spearman correlation: {rho:.4f}, p-value: {p_val:.4f}")
    
    return rho, p_val

def generate_significance_flag(p_value: float, alpha: float = 0.05) -> bool:
    """Generate significance flag based on p-value."""
    return p_value < alpha

def integrate_router_results(
    entropy_path: str,
    convergence_path: str,
    router_model_path: str,
    flops_savings_path: str,
    output_path: str
) -> pd.DataFrame:
    """
    Integrate router simulation results into a final results CSV.
    
    Schema: {task_id, predicted_k, actual_k, accuracy, flops_saved}
    """
    # Load inputs
    entropy_df = load_entropy_results(entropy_path)
    convergence_df = load_convergence_results(convergence_path)
    
    # Load router model
    if not os.path.exists(router_model_path):
        raise FileNotFoundError(f"Router model not found at {router_model_path}")
    with open(router_model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Load FLOPs savings data if available
    flops_data = {}
    if os.path.exists(flops_savings_path):
        with open(flops_savings_path, 'r') as f:
            flops_data = json.load(f)
    
    # Prepare predictions
    X = entropy_df[['entropy']].values
    predicted_k = model.predict(X)
    
    # Determine actual optimal k from convergence data
    merged = pd.merge(entropy_df, convergence_df, on='task_id', how='inner')
    
    def get_actual_k(group):
        converged_rows = group[group['converged'] == True]
        if not converged_rows.empty:
            return converged_rows['k'].min()
        else:
            return group['k'].max()
    
    actual_k = merged.groupby('task_id').apply(get_actual_k).reset_index()
    actual_k.columns = ['task_id', 'actual_k']
    
    # Merge with predictions
    results = pd.merge(entropy_df, actual_k, on='task_id', how='inner')
    results['predicted_k'] = predicted_k
    
    # Calculate accuracy (match between predicted and actual)
    results['accuracy'] = (results['predicted_k'] == results['actual_k']).astype(int)
    
    # Calculate FLOPs saved
    # Baseline: static k=2. Dynamic: predicted_k.
    # FLOPs saved = (baseline_k - predicted_k) * constant (normalized)
    # We'll use a simple metric: if predicted_k < 2, saved = 2 - predicted_k; else 0
    results['flops_saved'] = np.maximum(0, 2 - results['predicted_k'])
    
    # Select and order columns
    final_cols = ['task_id', 'predicted_k', 'actual_k', 'accuracy', 'flops_saved']
    results = results[final_cols]
    
    # Save to CSV
    results.to_csv(output_path, index=False)
    logger.info(f"Router results integrated and saved to {output_path}")
    
    return results

def main():
    """Main entry point for analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run analysis pipeline")
    parser.add_argument('--entropy', type=str, required=True, help="Path to entropy results CSV")
    parser.add_argument('--convergence', type=str, required=True, help="Path to convergence results CSV")
    parser.add_argument('--output', type=str, required=True, help="Path to output results JSON")
    parser.add_argument('--router-model', type=str, default=None, help="Path to router model (optional)")
    parser.add_argument('--flops-savings', type=str, default=None, help="Path to FLOPs savings JSON (optional)")
    parser.add_argument('--router-output', type=str, default=None, help="Path to router results CSV (optional)")
    
    args = parser.parse_args()
    
    # Run basic analysis
    rho, p_val = run_analysis(args.entropy, args.convergence)
    
    # Save correlation results
    correlation_results = {
        'spearman_rho': rho,
        'p_value': p_val
    }
    with open(args.output, 'w') as f:
        json.dump(correlation_results, f, indent=2)
    
    # If router model and FLOPs data provided, integrate results
    if args.router_model and args.flops_savings and args.router_output:
        integrate_router_results(
            args.entropy,
            args.convergence,
            args.router_model,
            args.flops_savings,
            args.router_output
        )
    
    logger.info("Analysis completed successfully")

if __name__ == '__main__':
    main()
