import csv
import json
import logging
import os
import pickle
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_entropy_results(path: str) -> List[Dict[str, Any]]:
    """Load entropy results from CSV."""
    results = []
    if not os.path.exists(path):
        logger.error(f"Entropy results file not found: {path}")
        return results
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'task_id': row['task_id'],
                'entropy': float(row['entropy']),
                'cluster_count': int(row['cluster_count'])
            })
    return results

def load_convergence_results(path: str) -> List[Dict[str, Any]]:
    """Load convergence results from CSV."""
    results = []
    if not os.path.exists(path):
        logger.error(f"Convergence results file not found: {path}")
        return results
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            k_val = row['k_correct']
            k_correct = int(k_val) if k_val != 'None' and k_val != '' else None
            results.append({
                'task_id': row['task_id'],
                'k_correct': k_correct,
                'trajectory_status': row['trajectory_status']
            })
    return results

def compute_spearman_correlation(entropy_df: List[Dict], conv_df: List[Dict]) -> Tuple[Optional[float], Optional[float]]:
    """Compute Spearman correlation between entropy and convergence step."""
    # Align data by task_id
    entropy_map = {item['task_id']: item['entropy'] for item in entropy_df}
    conv_map = {item['task_id']: item['k_correct'] for item in conv_df if item['k_correct'] is not None}

    common_ids = list(set(entropy_map.keys()) & set(conv_map.keys()))
    if len(common_ids) < 2:
        logger.warning("Not enough common data points to compute correlation.")
        return None, None

    entropies = [entropy_map[tid] for tid in common_ids]
    convergences = [conv_map[tid] for tid in common_ids]

    try:
        rho, p_value = spearmanr(entropies, convergences)
        return rho, p_value
    except Exception as e:
        logger.error(f"Error computing correlation: {e}")
        return None, None

def save_correlation_results(rho: float, p_value: float, path: str):
    """Save correlation results to JSON."""
    data = {
        'spearman_rho': rho,
        'p_value': p_value,
        'is_significant': generate_significance_flag(p_value)
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Correlation results saved to {path}")

def generate_significance_flag(p_value: Optional[float]) -> bool:
    """
    Generate a significance flag based on p-value.
    Returns True if p < 0.05, else False.
    If p_value is None, returns False.
    """
    if p_value is None:
        return False
    return p_value < 0.05

def train_logistic_router(entropy_df: List[Dict], conv_df: List[Dict]) -> Any:
    """
    Train a logistic regression router to predict optimal loop count.
    
    Target: optimal loop count (minimum k where solution is correct).
    Features: entropy, cluster_count.
    
    Returns:
        trained_model: The fitted LogisticRegression model.
        metrics: Dictionary containing accuracy and other metrics.
    """
    # Merge data by task_id
    entropy_map = {item['task_id']: item for item in entropy_df}
    conv_map = {item['task_id']: item for item in conv_df if item['k_correct'] is not None}

    common_ids = list(set(entropy_map.keys()) & set(conv_map.keys()))
    if len(common_ids) < 10:
        logger.error("Insufficient data to train router (need at least 10 samples).")
        return None, {}

    # Prepare features and labels
    X = []
    y = []
    valid_ids = []
    
    for tid in common_ids:
        ent_data = entropy_map[tid]
        conv_data = conv_map[tid]
        
        # Features: entropy and cluster_count
        features = [ent_data['entropy'], ent_data['cluster_count']]
        label = conv_data['k_correct']
        
        X.append(features)
        y.append(label)
        valid_ids.append(tid)

    if len(set(y)) < 2:
        logger.error("Insufficient class diversity in labels for multi-class classification.")
        return None, {}

    # Split data for training and validation
    try:
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    except Exception as e:
        logger.warning(f"Stratified split failed, using random split: {e}")
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

    # Train Logistic Regression with multinomial loss
    # multi_class='multinomial' uses cross-entropy loss by default for multinomial
    model = LogisticRegression(
        multi_class='multinomial',
        solver='lbfgs',
        max_iter=1000,
        random_state=42
    )
    
    try:
        model.fit(X_train, y_train)
    except Exception as e:
        logger.error(f"Failed to train logistic regression model: {e}")
        return None, {}

    # Evaluate on validation set
    y_pred = model.predict(X_val)
    accuracy = accuracy_score(y_val, y_pred)
    
    metrics = {
        'train_size': len(X_train),
        'val_size': len(X_val),
        'accuracy': accuracy,
        'unique_classes': sorted(list(set(y))),
        'feature_names': ['entropy', 'cluster_count']
    }

    logger.info(f"Router trained. Validation Accuracy: {accuracy:.4f}")
    logger.info(f"Classification report:\n{classification_report(y_val, y_pred)}")

    return model, metrics

def save_router_model(model, metrics: Dict, path_model: str, path_metrics: str):
    """Save the trained router model and metrics to disk."""
    # Save model
    with open(path_model, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Router model saved to {path_model}")

    # Save metrics
    with open(path_metrics, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Router metrics saved to {path_metrics}")

def run_analysis(entropy_path: str, conv_path: str, output_path: str):
    """Run full analysis pipeline."""
    entropy_df = load_entropy_results(entropy_path)
    conv_df = load_convergence_results(conv_path)

    if not entropy_df or not conv_df:
        logger.error("Failed to load data for analysis.")
        return

    rho, p_value = compute_spearman_correlation(entropy_df, conv_df)

    if rho is not None:
        save_correlation_results(rho, p_value, output_path)
        logger.info(f"Analysis complete. Spearman rho: {rho}, p-value: {p_value}")
    else:
        logger.error("Correlation computation failed.")

def main():
    """Main entry point for analysis script."""
    base_dir = Path(__file__).parent.parent.parent
    entropy_path = base_dir / "data" / "processed" / "entropy_results.csv"
    conv_path = base_dir / "data" / "processed" / "convergence_results.csv"
    output_path = base_dir / "data" / "processed" / "analysis_summary.json"

    run_analysis(str(entropy_path), str(conv_path), str(output_path))

if __name__ == "__main__":
    main()