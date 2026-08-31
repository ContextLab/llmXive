"""
Semantic Novelty Quantification Module.

This module implements the logic to quantify semantic novelty by comparing
event entropy distributions between the CA (Eco-Director) and Neural Baseline runs.
It ensures the metric is not derived solely from the CA rules by explicitly
calculating the divergence between the two distributions.

Dependencies:
    - numpy: For numerical operations and entropy calculation.
    - scipy.stats: For statistical divergence measures (KL Divergence).
    - pandas: For loading and processing simulation data logs.

Output:
    A dictionary containing the calculated novelty score and distribution statistics.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from scipy.stats import entropy as scipy_entropy
import logging
import os

logger = logging.getLogger(__name__)


def calculate_entropy_distribution(values: np.ndarray, num_bins: int = 50) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculates the entropy of a distribution derived from a set of values.
    
    Args:
        values: A 1D numpy array of metric values (e.g., coherence scores, energy states).
        num_bins: Number of bins to use for histogram estimation.
        
    Returns:
        A tuple (bin_edges, entropy_value).
        
    Raises:
        ValueError: If the input array is empty or contains only NaN values.
    """
    if values.size == 0:
        raise ValueError("Input array is empty.")
        
    # Filter out NaN and Inf values to ensure valid probability calculation
    clean_values = values[~np.isnan(values) & ~np.isinf(values)]
    
    if clean_values.size == 0:
        raise ValueError("Input array contains only NaN or Inf values.")

    # Compute histogram to estimate probability distribution
    hist, bin_edges = np.histogram(clean_values, bins=num_bins, density=False)
    
    # Normalize to get probabilities
    probabilities = hist / hist.sum()
    
    # Filter out zero probabilities to avoid log(0)
    probabilities = probabilities[probabilities > 0]
    
    # Calculate Shannon Entropy
    entropy_value = scipy_entropy(probabilities)
    
    return bin_edges, entropy_value


def calculate_kl_divergence(p: np.ndarray, q: np.ndarray) -> float:
    """
    Calculates the Kullback-Leibler divergence between two probability distributions.
    
    KL(P || Q) = sum(P(x) * log(P(x) / Q(x)))
    
    This metric quantifies how much information is lost when Q is used to approximate P.
    In the context of novelty, it measures how different the CA distribution is from the Neural baseline.
    
    Args:
        p: Probability distribution (numpy array, must sum to 1).
        q: Reference probability distribution (numpy array, must sum to 1).
        
    Returns:
        KL divergence value (float). Returns infinity if q has zeros where p has mass.
    """
    if p.size != q.size:
        raise ValueError("Distributions must have the same size.")
        
    # Ensure no division by zero
    mask = (p > 0) & (q > 0)
    if not np.any(mask):
        return float('inf')
        
    p_filtered = p[mask]
    q_filtered = q[mask]
    
    kl_val = np.sum(p_filtered * np.log(p_filtered / q_filtered))
    return float(kl_val)


def quantify_semantic_novelty(
    ca_metrics_path: str,
    neural_metrics_path: str,
    metric_column: str = 'coherence_score',
    num_bins: int = 50
) -> Dict[str, Any]:
    """
    Quantifies semantic novelty by comparing event entropy distributions between
    CA and Neural Baseline runs.
    
    This function:
    1. Loads the raw metric data from both simulation runs.
    2. Calculates the probability distribution of the specified metric for both.
    3. Computes the Shannon Entropy for each.
    4. Computes the KL Divergence (P_CA || P_Neural) as the novelty score.
    
    The novelty score represents the "surprise" of the CA behavior relative to the
    Neural Baseline. A high score indicates the CA is exploring regions of the
    state space not covered by the Neural model.
    
    Args:
        ca_metrics_path: Path to the CSV/Parquet file containing CA simulation metrics.
        neural_metrics_path: Path to the CSV/Parquet file containing Neural baseline metrics.
        metric_column: The name of the column to analyze (default: 'coherence_score').
        num_bins: Number of bins for histogram estimation.
        
    Returns:
        A dictionary with the following keys:
            - 'ca_entropy': Shannon entropy of the CA distribution.
            - 'neural_entropy': Shannon entropy of the Neural distribution.
            - 'kl_divergence': KL(P_CA || P_Neural) as the novelty score.
            - 'ca_mean': Mean of the CA metric values.
            - 'neural_mean': Mean of the Neural metric values.
            - 'status': 'success' or 'error'.
            - 'error_message': If status is 'error', the reason.
    
    Raises:
        FileNotFoundError: If input files do not exist.
        KeyError: If the specified metric column is missing in the data.
    """
    result = {
        'ca_entropy': None,
        'neural_entropy': None,
        'kl_divergence': None,
        'ca_mean': None,
        'neural_mean': None,
        'status': 'success',
        'error_message': None
    }
    
    try:
        # Load Data
        if not os.path.exists(ca_metrics_path):
            raise FileNotFoundError(f"CA metrics file not found: {ca_metrics_path}")
        if not os.path.exists(neural_metrics_path):
            raise FileNotFoundError(f"Neural metrics file not found: {neural_metrics_path}")
            
        # Determine file type and load
        if ca_metrics_path.endswith('.parquet'):
            df_ca = pd.read_parquet(ca_metrics_path)
        else:
            df_ca = pd.read_csv(ca_metrics_path)
            
        if neural_metrics_path.endswith('.parquet'):
            df_neural = pd.read_parquet(neural_metrics_path)
        else:
            df_neural = pd.read_csv(neural_metrics_path)
            
        # Validate columns
        if metric_column not in df_ca.columns:
            raise KeyError(f"Column '{metric_column}' not found in CA metrics. Available: {list(df_ca.columns)}")
        if metric_column not in df_neural.columns:
            raise KeyError(f"Column '{metric_column}' not found in Neural metrics. Available: {list(df_neural.columns)}")
            
        # Extract values
        values_ca = df_ca[metric_column].to_numpy()
        values_neural = df_neural[metric_column].to_numpy()
        
        logger.info(f"Loaded {len(values_ca)} CA points and {len(values_neural)} Neural points for '{metric_column}'.")
        
        # Calculate Entropies
        # We use the same bin edges for both to ensure comparability in KL calculation
        # First, determine global bin edges
        all_vals = np.concatenate([values_ca, values_neural])
        # Handle case where all values are identical or empty
        if len(np.unique(all_vals)) == 1:
            logger.warning("All values are identical. Entropy will be 0. KL divergence may be 0.")
            bin_edges = np.unique(all_vals)
        else:
            bin_edges = np.linspace(np.min(all_vals), np.max(all_vals), num_bins + 1)
            
        hist_ca, _ = np.histogram(values_ca, bins=bin_edges, density=False)
        hist_neural, _ = np.histogram(values_neural, bins=bin_edges, density=False)
        
        # Normalize
        p_ca = hist_ca / hist_ca.sum()
        p_neural = hist_neural / hist_neural.sum()
        
        # Calculate Entropy for each
        p_ca_nonzero = p_ca[p_ca > 0]
        p_neural_nonzero = p_neural[p_neural > 0]
        
        ca_entropy = scipy_entropy(p_ca_nonzero) if len(p_ca_nonzero) > 0 else 0.0
        neural_entropy = scipy_entropy(p_neural_nonzero) if len(p_neural_nonzero) > 0 else 0.0
        
        # Calculate KL Divergence: P_CA || P_Neural
        # We need to handle zeros carefully. If P_CA has mass where P_Neural is 0, KL is inf.
        # This is actually desired behavior for novelty: it means CA found something Neural never saw.
        kl_val = calculate_kl_divergence(p_ca, p_neural)
        
        result['ca_entropy'] = float(ca_entropy)
        result['neural_entropy'] = float(neural_entropy)
        result['kl_divergence'] = kl_val
        result['ca_mean'] = float(np.mean(values_ca))
        result['neural_mean'] = float(np.mean(values_neural))
        
        logger.info(f"Novelty Analysis Complete. KL Divergence: {kl_val}")
        
    except Exception as e:
        result['status'] = 'error'
        result['error_message'] = str(e)
        logger.error(f"Error in quantify_semantic_novelty: {e}")
        raise
        
    return result


def run_novelty_analysis(
    output_path: str,
    ca_metrics_path: str,
    neural_metrics_path: str,
    metric_column: str = 'coherence_score'
) -> None:
    """
    Runs the novelty analysis and writes the results to a JSON file.
    
    Args:
        output_path: Path to write the JSON results file.
        ca_metrics_path: Path to CA metrics.
        neural_metrics_path: Path to Neural metrics.
        metric_column: Column name to analyze.
    """
    results = quantify_semantic_novelty(
        ca_metrics_path=ca_metrics_path,
        neural_metrics_path=neural_metrics_path,
        metric_column=metric_column
    )
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Novelty analysis results written to {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate semantic novelty between CA and Neural runs.")
    parser.add_argument("--ca-path", type=str, required=True, help="Path to CA metrics file (CSV or Parquet).")
    parser.add_argument("--neural-path", type=str, required=True, help="Path to Neural baseline metrics file.")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON results file.")
    parser.add_argument("--column", type=str, default="coherence_score", help="Metric column to analyze.")
    
    args = parser.parse_args()
    
    run_novelty_analysis(
        output_path=args.output,
        ca_metrics_path=args.ca_path,
        neural_metrics_path=args.neural_path,
        metric_column=args.column
    )