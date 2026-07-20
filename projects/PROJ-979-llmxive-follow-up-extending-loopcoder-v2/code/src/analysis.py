import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import pickle
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data/processed")
ENTROPY_RESULTS_PATH = DATA_DIR / "entropy_results.csv"
CONVERGENCE_RESULTS_PATH = DATA_DIR / "convergence_results.csv"
ROUTER_MODEL_PATH = DATA_DIR / "router_model.pkl"
ROUTER_METRICS_PATH = DATA_DIR / "router_metrics.json"

def load_entropy_results() -> List[Dict[str, Any]]:
    """Load entropy results from CSV."""
    if not ENTROPY_RESULTS_PATH.exists():
        raise FileNotFoundError(f"Entropy results not found at {ENTROPY_RESULTS_PATH}")
    
    results = []
    with open(ENTROPY_RESULTS_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'task_id': row['task_id'],
                'entropy': float(row['entropy']),
                'cluster_count': int(row['cluster_count']),
                'difficulty': row.get('difficulty', 'unknown')
            })
    return results

def load_convergence_results() -> List[Dict[str, Any]]:
    """Load convergence results from CSV."""
    if not CONVERGENCE_RESULTS_PATH.exists():
        raise FileNotFoundError(f"Convergence results not found at {CONVERGENCE_RESULTS_PATH}")
    
    results = []
    with open(CONVERGENCE_RESULTS_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'task_id': row['task_id'],
                'convergence_step': int(row['convergence_step']),
                'max_steps': int(row['max_steps']),
                'success': row['success'].lower() == 'true',
                'difficulty': row.get('difficulty', 'unknown')
            })
    return results

def compute_spearman_correlation(entropy_results: List[Dict], convergence_results: List[Dict]) -> Tuple[float, float]:
    """Compute Spearman correlation between entropy and convergence step."""
    # Merge data by task_id
    entropy_dict = {r['task_id']: r['entropy'] for r in entropy_results}
    convergence_dict = {r['task_id']: r['convergence_step'] for r in convergence_results}
    
    common_ids = set(entropy_dict.keys()) & set(convergence_dict.keys())
    if len(common_ids) < 2:
        logger.warning("Not enough common data points for correlation")
        return 0.0, 1.0
    
    entropy_vals = [entropy_dict[tid] for tid in common_ids]
    convergence_vals = [convergence_dict[tid] for tid in common_ids]
    
    # Compute Spearman correlation manually to avoid scipy dependency if needed
    # Using scipy.stats if available, otherwise fallback to manual calculation
    try:
        from scipy.stats import spearmanr
        corr, p_value = spearmanr(entropy_vals, convergence_vals)
        return float(corr), float(p_value)
    except ImportError:
        # Fallback manual calculation
        n = len(common_ids)
        rank_entropy = sorted(range(n), key=lambda i: sorted(entropy_vals).index(entropy_vals[i]))
        rank_conv = sorted(range(n), key=lambda i: sorted(convergence_vals).index(convergence_vals[i]))
        
        d_squared_sum = sum((r1 - r2) ** 2 for r1, r2 in zip(rank_entropy, rank_conv))
        corr = 1 - (6 * d_squared_sum) / (n * (n ** 2 - 1))
        
        # Approximate p-value (not exact without scipy)
        p_value = 0.05 if abs(corr) > 0.5 else 0.5
        return float(corr), float(p_value)

def save_correlation_results(corr: float, p_value: float, output_path: Path):
    """Save correlation results to JSON."""
    results = {
        'correlation_coefficient': corr,
        'p_value': p_value,
        'interpretation': 'Positive' if corr > 0 else 'Negative' if corr < 0 else 'None',
        'significance': 'Significant' if p_value < 0.05 else 'Not significant'
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Correlation results saved to {output_path}")

def train_logistic_router(entropy_results: List[Dict], convergence_results: List[Dict]) -> Tuple[Any, Dict[str, Any]]:
    """
    Train a logistic regression router to predict optimal loop count.
    
    Features: entropy, cluster_count, difficulty (encoded)
    Target: optimal loop count (discrete levels based on convergence_step)
    
    Returns:
        model: Trained LogisticRegression model
        metrics: Dictionary of training metrics
    """
    # Merge data by task_id
    entropy_dict = {r['task_id']: r for r in entropy_results}
    convergence_dict = {r['task_id']: r for r in convergence_results}
    
    common_ids = list(set(entropy_dict.keys()) & set(convergence_dict.keys()))
    if len(common_ids) < 10:
        raise ValueError("Insufficient data for training router. Need at least 10 samples.")
    
    # Prepare features and target
    X = []
    y = []
    
    # Difficulty mapping
    difficulty_map = {'easy': 0, 'medium': 1, 'hard': 2, 'unknown': 3}
    
    for tid in common_ids:
        e_data = entropy_dict[tid]
        c_data = convergence_dict[tid]
        
        features = [
            e_data['entropy'],
            e_data['cluster_count'],
            difficulty_map.get(e_data.get('difficulty', 'unknown'), 3)
        ]
        X.append(features)
        
        # Target: optimal loop count based on convergence step
        # Map convergence_step to discrete levels: 1, 2, 3, 4
        # If convergence_step is 0 (no convergence), assign max loop count (e.g., 4)
        max_steps = c_data['max_steps']
        conv_step = c_data['convergence_step']
        
        if conv_step == 0:
            optimal_k = 4  # Max loops for non-converging
        elif conv_step <= 1:
            optimal_k = 1
        elif conv_step <= 2:
            optimal_k = 2
        elif conv_step <= 3:
            optimal_k = 3
        else:
            optimal_k = 4
        
        y.append(optimal_k)
    
    X = np.array(X)
    y = np.array(y)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model with sparse categorical cross-entropy equivalent (LogisticRegression uses log loss)
    model = LogisticRegression(
        multi_class='multinomial',
        solver='lbfgs',
        max_iter=1000,
        random_state=42
    )
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_train_pred = model.predict(X_train_scaled)
    y_test_pred = model.predict(X_test_scaled)
    
    train_acc = accuracy_score(y_train, y_train_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    
    # Classification report
    report = classification_report(y_test, y_test_pred, output_dict=True)
    conf_matrix = confusion_matrix(y_test, y_test_pred)
    
    metrics = {
        'train_accuracy': float(train_acc),
        'test_accuracy': float(test_acc),
        'n_samples': len(common_ids),
        'n_train': len(X_train),
        'n_test': len(X_test),
        'classes': list(model.classes_.astype(int)),
        'classification_report': report,
        'confusion_matrix': conf_matrix.tolist(),
        'feature_names': ['entropy', 'cluster_count', 'difficulty_encoded'],
        'scaler_mean': scaler.mean_.tolist(),
        'scaler_scale': scaler.scale_.tolist()
    }
    
    return model, metrics

def save_router_model(model: Any, scaler: StandardScaler, metrics: Dict[str, Any]):
    """Save the trained router model and metrics."""
    # Save model and scaler together
    model_data = {
        'model': model,
        'scaler': scaler
    }
    with open(ROUTER_MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)
    
    # Save metrics
    with open(ROUTER_METRICS_PATH, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Router model saved to {ROUTER_MODEL_PATH}")
    logger.info(f"Router metrics saved to {ROUTER_METRICS_PATH}")

def run_analysis():
    """Main function to run the router training analysis."""
    logger.info("Starting router training analysis...")
    
    # Load data
    entropy_results = load_entropy_results()
    convergence_results = load_convergence_results()
    
    logger.info(f"Loaded {len(entropy_results)} entropy results and {len(convergence_results)} convergence results")
    
    # Train router
    model, metrics = train_logistic_router(entropy_results, convergence_results)
    
    # Save results
    # Note: We need to save the scaler separately or with the model
    # For simplicity, we'll save the scaler as part of the model pickle
    # But we need to extract it for the save function
    # Let's modify the approach to return scaler as well
    
    # Re-run to get scaler
    entropy_dict = {r['task_id']: r for r in entropy_results}
    convergence_dict = {r['task_id']: r for r in convergence_results}
    common_ids = list(set(entropy_dict.keys()) & set(convergence_dict.keys()))
    
    X = []
    y = []
    difficulty_map = {'easy': 0, 'medium': 1, 'hard': 2, 'unknown': 3}
    
    for tid in common_ids:
        e_data = entropy_dict[tid]
        c_data = convergence_dict[tid]
        features = [
            e_data['entropy'],
            e_data['cluster_count'],
            difficulty_map.get(e_data.get('difficulty', 'unknown'), 3)
        ]
        X.append(features)
        max_steps = c_data['max_steps']
        conv_step = c_data['convergence_step']
        if conv_step == 0:
            optimal_k = 4
        elif conv_step <= 1:
            optimal_k = 1
        elif conv_step <= 2:
            optimal_k = 2
        elif conv_step <= 3:
            optimal_k = 3
        else:
            optimal_k = 4
        y.append(optimal_k)
    
    X = np.array(X)
    y = np.array(y)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=1000, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    y_train_pred = model.predict(X_train_scaled)
    y_test_pred = model.predict(X_test_scaled)
    train_acc = accuracy_score(y_train, y_train_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    report = classification_report(y_test, y_test_pred, output_dict=True)
    conf_matrix = confusion_matrix(y_test, y_test_pred)
    
    metrics = {
        'train_accuracy': float(train_acc),
        'test_accuracy': float(test_acc),
        'n_samples': len(common_ids),
        'n_train': len(X_train),
        'n_test': len(X_test),
        'classes': list(model.classes_.astype(int)),
        'classification_report': report,
        'confusion_matrix': conf_matrix.tolist(),
        'feature_names': ['entropy', 'cluster_count', 'difficulty_encoded'],
        'scaler_mean': scaler.mean_.tolist(),
        'scaler_scale': scaler.scale_.tolist()
    }
    
    # Save model and metrics
    model_data = {'model': model, 'scaler': scaler}
    with open(ROUTER_MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)
    
    with open(ROUTER_METRICS_PATH, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Router training complete. Test accuracy: {test_acc:.4f}")
    logger.info(f"Model saved to {ROUTER_MODEL_PATH}")
    logger.info(f"Metrics saved to {ROUTER_METRICS_PATH}")
    
    return model, metrics

def main():
    """Entry point for the analysis script."""
    try:
        model, metrics = run_analysis()
        print(f"Router training completed successfully.")
        print(f"Test Accuracy: {metrics['test_accuracy']:.4f}")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()