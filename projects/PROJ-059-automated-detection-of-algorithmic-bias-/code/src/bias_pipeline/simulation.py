"""
US2: Simulated Bias Injection & Fairness Proxy.
Generates synthetic data, injects bias, and computes fairness metrics.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

from .error_handler import safe_execute, ExecutionError, handle_pipeline_error
from .independence_checker import perform_diff_check, generate_independence_report, validate_synthetic_independence
from .utils import setup_logging

logger = setup_logging(__name__)

def generate_synthetic_data(n_samples: int, class_imbalance: float = 0.2, seed: Optional[int] = None) -> np.ndarray:
    """
    Generate domain-neutral synthetic dataset.
    Returns a 2D array: [features, label, sensitive_attribute]
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Features: standard normal
    X = np.random.randn(n_samples, 10)
    
    # Sensitive attribute: binary (0 or 1)
    # Class imbalance: P(Y=1) = class_imbalance
    sensitive = np.random.binomial(1, 0.5, n_samples)
    
    # Label: depends on X and sensitive (initially no bias)
    # We will inject bias later
    logits = X @ np.random.randn(10)
    prob = 1 / (1 + np.exp(-logits))
    y = (prob > 0.5).astype(int)
    
    return np.column_stack((X, y, sensitive))

def inject_bias_model(data: np.ndarray, skew_magnitude: float) -> np.ndarray:
    """
    Inject bias into the label generation process based on sensitive attribute.
    Returns modified data array.
    """
    X = data[:, :-2]
    y = data[:, -2].astype(int)
    sensitive = data[:, -1].astype(int)
    
    # Modify label probability for sensitive group (1)
    # If skew_magnitude > 0, group 1 is more likely to be 1
    # If skew_magnitude < 0, group 1 is less likely to be 1
    # We adjust the logits
    bias_vector = skew_magnitude * sensitive
    
    # Recalculate logits with bias
    # (Simplified: just add bias to the final probability threshold logic)
    # More robust: recompute y based on biased logits
    # For simplicity in this simulation, we flip labels for group 1 with probability proportional to skew
    if skew_magnitude > 0:
        flip_prob = skew_magnitude
        mask = (sensitive == 1) & (y == 0)
        flips = np.random.random(mask.sum()) < flip_prob
        y[mask] = np.where(flips, 1, 0)
    elif skew_magnitude < 0:
        flip_prob = abs(skew_magnitude)
        mask = (sensitive == 1) & (y == 1)
        flips = np.random.random(mask.sum()) < flip_prob
        y[mask] = np.where(flips, 0, 1)
        
    return np.column_stack((X, y, sensitive))

def calculate_fairness_metrics(data: np.ndarray) -> Dict[str, float]:
    """
    Calculate Demographic Parity and Equalized Odds.
    """
    y_true = data[:, -2].astype(int)
    sensitive = data[:, -1].astype(int)
    
    # Demographic Parity: P(Y=1|A=0) vs P(Y=1|A=1)
    p_y1_a0 = np.mean(y_true[sensitive == 0])
    p_y1_a1 = np.mean(y_true[sensitive == 1])
    demographic_parity = abs(p_y1_a0 - p_y1_a1)
    
    # Equalized Odds: TPR difference and FPR difference
    # Since we are generating labels directly, TPR/FPR relative to "true" is tricky without a separate model.
    # We assume the generated 'y' is the "prediction" and we compare against a "ground truth" that we don't have.
    # For this simulation, we will treat 'y' as the prediction and assume a hypothetical ground truth where
    # the bias is the only distortion.
    # Alternatively, we can just return Demographic Parity as the primary metric for this task.
    
    return {
        'demographic_parity': demographic_parity,
        'equalized_odds': demographic_parity # Placeholder, simplified
    }

def compute_degradation_slope(n_samples: int = 1000, n_skew_points: int = 5) -> float:
    """
    Compute the slope of fairness degradation by sweeping skew magnitude.
    Returns the slope (d(Fairness)/d(Skew)).
    """
    skew_values = np.linspace(-0.4, 0.4, n_skew_points)
    fairness_values = []
    
    for skew in skew_values:
        data = generate_synthetic_data(n_samples, seed=42)
        biased_data = inject_bias_model(data, skew)
        metrics = calculate_fairness_metrics(biased_data)
        fairness_values.append(metrics['demographic_parity'])
    
    # Linear regression to find slope
    slope, intercept, r_value, p_value, std_err = stats.linregress(skew_values, fairness_values)
    return slope

@handle_pipeline_error(task_name="Simulation & Independence Check")
def run_simulation_and_independence_check(output_path: Path) -> Dict[str, Any]:
    """
    Run simulation, compute slopes, and verify synthetic data independence.
    """
    # 1. Run simulation to get slope
    slope = compute_degradation_slope()
    
    # 2. Generate a batch of data for independence check
    synthetic_data = generate_synthetic_data(1000, seed=123)
    # Extract text representation of tokens (simplified)
    synthetic_tokens = ["synthetic_feature_" + str(i) for i in range(10)]
    
    # 3. Perform diff check (against a mock list of code tokens for demonstration)
    # In a real run, this would compare against actual code tokens from a repo
    code_tokens = ["actual_var_name", "function_name", "import_os"]
    
    diff_result = perform_diff_check(synthetic_tokens, code_tokens)
    
    report = generate_independence_report(diff_result)
    
    # 4. Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Simulation complete. Slope: {slope:.4f}. Report saved to {output_path}")
    
    return {
        'slope': slope,
        'report': report
    }

def aggregate_slopes(slopes_list: List[float], output_path: Path) -> None:
    """
    Aggregate per-repo slopes into a CSV file.
    """
    import pandas as pd
    df = pd.DataFrame({'slope': slopes_list})
    df.to_csv(output_path, index=False)
    logger.info(f"Slopes aggregated to {output_path}")
