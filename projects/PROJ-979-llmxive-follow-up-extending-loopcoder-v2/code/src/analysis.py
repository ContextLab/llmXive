import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import numpy as np
from scipy import stats

from src.utils import calculate_flops, get_model_param_count

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_entropy_results(filepath: str) -> List[Dict[str, Any]]:
    """Load entropy results from CSV."""
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'task_id': row['task_id'],
                'entropy': float(row['entropy']),
                'num_clusters': int(row['num_clusters'])
            })
    return results

def load_convergence_results(filepath: str) -> List[Dict[str, Any]]:
    """Load convergence results from CSV."""
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'task_id': row['task_id'],
                'convergence_step': int(row['convergence_step']),
                'is_converged': row['is_converged'] == 'True',
                'k_value': int(row['k_value'])
            })
    return results

def compute_spearman_correlation(entropy_data: List[Dict], convergence_data: List[Dict]) -> Tuple[float, float]:
    """Compute Spearman correlation between entropy and convergence step."""
    # Align data by task_id
    entropy_map = {d['task_id']: d['entropy'] for d in entropy_data}
    convergence_map = {d['task_id']: d['convergence_step'] for d in convergence_data}

    common_ids = set(entropy_map.keys()) & set(convergence_map.keys())
    if not common_ids:
        raise ValueError("No common task_ids between entropy and convergence results")

    entropies = [entropy_map[tid] for tid in common_ids]
    steps = [convergence_map[tid] for tid in common_ids]

    rho, p_value = stats.spearmanr(entropies, steps)
    return rho, p_value

def save_correlation_results(results: Dict[str, Any], output_path: str) -> None:
    """Save correlation results to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

def train_logistic_router(entropy_data: List[Dict], convergence_data: List[Dict]) -> Dict[str, Any]:
    """Train a logistic regression model to predict optimal k based on entropy."""
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        raise ImportError("scikit-learn is required for logistic regression training. Install via pip install scikit-learn")

    # Align data
    entropy_map = {d['task_id']: d['entropy'] for d in entropy_data}
    convergence_map = {d['task_id']: d['convergence_step'] for d in convergence_data}

    common_ids = list(set(entropy_map.keys()) & set(convergence_map.keys()))
    if not common_ids:
        raise ValueError("No common task_ids for training router")

    X = np.array([[entropy_map[tid]] for tid in common_ids])
    # Target: 1 if converged at k=1, 0 otherwise
    y = np.array([1 if convergence_map[tid] == 1 else 0 for tid in common_ids])

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_scaled, y)

    # Predict probabilities for all samples
    probs = model.predict_proba(X_scaled)[:, 1]
    predictions = model.predict(X_scaled)

    return {
        'model': model,
        'scaler': scaler,
        'predictions': predictions,
        'probabilities': probs,
        'task_ids': common_ids,
        'accuracy': model.score(X_scaled, y)
    }

def save_router_predictions(router_data: Dict[str, Any], output_path: str) -> None:
    """Save router predictions to CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['task_id', 'predicted_k', 'probability_converge_k1', 'actual_convergence_step'])
        
        # Load actual convergence data to include actual step
        convergence_map = {}
        if os.path.exists(output_path.replace('router_results.csv', 'convergence_results.csv')):
            with open(output_path.replace('router_results.csv', 'convergence_results.csv'), 'r') as cf:
                reader = csv.DictReader(cf)
                for row in reader:
                    convergence_map[row['task_id']] = int(row['convergence_step'])

        for i, tid in enumerate(router_data['task_ids']):
            # Predicted k: if probability > 0.5, predict k=1, else k=2 (dynamic)
            # For this simulation, we map probability to optimal k estimate
            # If prob_converge_k1 > 0.5, we predict k=1, otherwise we predict k=2
            pred_k = 1 if router_data['predictions'][i] == 1 else 2
            prob = router_data['probabilities'][i]
            actual = convergence_map.get(tid, -1)
            
            writer.writerow([tid, pred_k, f"{prob:.4f}", actual])

def load_router_predictions(filepath: str) -> List[Dict[str, Any]]:
    """Load router predictions from CSV."""
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'task_id': row['task_id'],
                'predicted_k': int(row['predicted_k']),
                'probability_converge_k1': float(row['probability_converge_k1']),
                'actual_convergence_step': int(row['actual_convergence_step'])
            })
    return results

def calculate_flops_savings(router_predictions: List[Dict], convergence_results: List[Dict], model_params: int = 1300000000) -> Dict[str, float]:
    """Calculate FLOPs savings of dynamic router vs static k=2 baseline."""
    # Align data
    convergence_map = {d['task_id']: d['convergence_step'] for d in convergence_results}
    
    total_flops_dynamic = 0
    total_flops_static = 0
    n_samples = len(router_predictions)
    
    for pred in router_predictions:
        tid = pred['task_id']
        actual_k = convergence_map.get(tid, 2)  # Default to 2 if missing
        pred_k = pred['predicted_k']
        
        # FLOPs = parameters * sequence_length * k
        # Assume sequence_length = 256 for estimation
        seq_len = 256
        
        flops_dynamic = model_params * seq_len * pred_k
        flops_static = model_params * seq_len * 2  # Static baseline k=2
        
        total_flops_dynamic += flops_dynamic
        total_flops_static += flops_static

    savings = total_flops_static - total_flops_dynamic
    savings_pct = (savings / total_flops_static) * 100 if total_flops_static > 0 else 0

    return {
        'total_flops_dynamic': total_flops_dynamic,
        'total_flops_static': total_flops_static,
        'flops_savings': savings,
        'savings_percentage': savings_pct,
        'n_samples': n_samples
    }

def run_flops_analysis(router_predictions_path: str, convergence_results_path: str, output_path: str, model_params: int = 1300000000) -> Dict[str, Any]:
    """Run full FLOPs analysis and save results."""
    router_preds = load_router_predictions(router_predictions_path)
    conv_results = load_convergence_results(convergence_results_path)
    
    flops_results = calculate_flops_savings(router_preds, conv_results, model_params)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(flops_results, f, indent=2)
    
    return flops_results

def generate_router_report(entropy_results_path: str, convergence_results_path: str, router_predictions_path: str, output_report_path: str) -> Dict[str, Any]:
    """Generate a comprehensive router simulation report."""
    # Load data
    entropy_data = load_entropy_results(entropy_results_path)
    convergence_data = load_convergence_results(convergence_results_path)
    router_preds = load_router_predictions(router_predictions_path)
    
    # Calculate metrics
    rho, p_value = compute_spearman_correlation(entropy_data, convergence_data)
    
    # Accuracy of router (does predicted_k match actual convergence step?)
    # For simplicity: accuracy = % of times router predicted k=1 and it actually converged at k=1
    correct_predictions = 0
    total = len(router_preds)
    for pred in router_preds:
        if pred['predicted_k'] == 1 and pred['actual_convergence_step'] == 1:
            correct_predictions += 1
        elif pred['predicted_k'] != 1 and pred['actual_convergence_step'] != 1:
            correct_predictions += 1
    
    router_accuracy = correct_predictions / total if total > 0 else 0.0
    
    # FLOPs savings
    flops_metrics = calculate_flops_savings(router_preds, convergence_data)
    
    report = {
        'entropy_convergence_correlation': {
            'rho': rho,
            'p_value': p_value
        },
        'router_accuracy': router_accuracy,
        'flops_analysis': flops_metrics,
        'sample_size': len(router_preds),
        'generated_at': str(Path(output_report_path).parent)
    }
    
    with open(output_report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    return report

def run_analysis(entropy_results_path: str, convergence_results_path: str, router_predictions_path: str, output_dir: str) -> None:
    """Run the full analysis pipeline for User Story 2."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 1. Load and verify data
    entropy_data = load_entropy_results(entropy_results_path)
    convergence_data = load_convergence_results(convergence_results_path)
    logger.info(f"Loaded {len(entropy_data)} entropy results and {len(convergence_data)} convergence results")
    
    # 2. Train router (if not already done, but we assume T019 did this)
    # Re-train here to ensure consistency for the report
    router_model_data = train_logistic_router(entropy_data, convergence_data)
    logger.info(f"Router trained with accuracy: {router_model_data['accuracy']:.4f}")
    
    # 3. Save router predictions (update if needed, or just ensure file exists)
    # If router_predictions_path doesn't exist, save it now
    if not os.path.exists(router_predictions_path):
        save_router_predictions(router_model_data, router_predictions_path)
        logger.info(f"Saved router predictions to {router_predictions_path}")
    
    # 4. Generate comprehensive report
    report_path = os.path.join(output_dir, 'router_simulation_report.json')
    report = generate_router_report(
        entropy_results_path, 
        convergence_results_path, 
        router_predictions_path, 
        report_path
    )
    
    logger.info(f"Router simulation report generated: {report_path}")
    logger.info(f"Correlation (rho): {report['entropy_convergence_correlation']['rho']:.4f}")
    logger.info(f"Router Accuracy: {report['router_accuracy']:.4f}")
    logger.info(f"FLOPs Savings: {report['flops_analysis']['savings_percentage']:.2f}%")

def main():
    """Main entry point for analysis script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run router simulation analysis')
    parser.add_argument('--entropy-file', type=str, default='data/processed/entropy_results.csv',
                      help='Path to entropy results CSV')
    parser.add_argument('--convergence-file', type=str, default='data/processed/convergence_results.csv',
                      help='Path to convergence results CSV')
    parser.add_argument('--router-file', type=str, default='data/processed/router_results.csv',
                      help='Path to router predictions CSV')
    parser.add_argument('--output-dir', type=str, default='data/processed',
                      help='Directory to save reports')
    
    args = parser.parse_args()
    
    run_analysis(args.entropy_file, args.convergence_file, args.router_file, args.output_dir)

if __name__ == '__main__':
    main()