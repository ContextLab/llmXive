import logging
import os
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from scipy import stats
from pathlib import Path

class StatisticsError(Exception):
    """Custom exception for statistics-related errors."""
    pass

def calculate_spearman_correlation(
    centrality_values: List[float], 
    essentiality_labels: List[int]
) -> Tuple[float, float]:
    """
    Calculate Spearman's rank correlation between centrality and essentiality.
    
    Args:
        centrality_values: List of centrality metric values.
        essentiality_labels: List of binary essentiality labels (0 or 1).
        
    Returns:
        Tuple of (correlation_coefficient, p_value).
        
    Raises:
        StatisticsError: If input lists are empty or invalid.
    """
    if not centrality_values or not essentiality_labels:
        raise StatisticsError("Input lists cannot be empty.")
    if len(centrality_values) != len(essentiality_labels):
        raise StatisticsError("Input lists must have the same length.")
        
    # Filter out NaN or Inf values which can occur in centrality calculations
    valid_indices = [
        i for i in range(len(centrality_values)) 
        if np.isfinite(centrality_values[i]) and essentiality_labels[i] in [0, 1]
    ]
    
    if len(valid_indices) < 2:
        raise StatisticsError("Insufficient valid data points for correlation calculation.")
        
    clean_centralities = [centrality_values[i] for i in valid_indices]
    clean_labels = [essentiality_labels[i] for i in valid_indices]
    
    rho, p_value = stats.spearmanr(clean_centralities, clean_labels)
    return float(rho), float(p_value)

def fisher_z_transform(r: float) -> float:
    """
    Apply Fisher's z-transformation to a correlation coefficient.
    
    This transformation normalizes the sampling distribution of the correlation
    coefficient, making it approximately normal. This is essential for comparing
    correlation coefficients across different organisms or conditions.
    
    Formula: z = 0.5 * ln((1 + r) / (1 - r))
    
    Args:
        r: Pearson or Spearman correlation coefficient (-1 < r < 1).
        
    Returns:
        Fisher's z-transformed value.
        
    Raises:
        StatisticsError: If r is outside the valid range (-1, 1).
    """
    if not isinstance(r, (int, float)):
        raise StatisticsError("Input 'r' must be a numeric value.")
    if r <= -1.0 or r >= 1.0:
        # Clamp to valid range with a small epsilon to avoid log(0)
        epsilon = 1e-7
        if r <= -1.0:
            r = -1.0 + epsilon
        elif r >= 1.0:
            r = 1.0 - epsilon
        
    try:
        z = 0.5 * np.log((1 + r) / (1 - r))
        return float(z)
    except (ValueError, ZeroDivisionError) as e:
        raise StatisticsError(f"Error in Fisher's z-transform: {e}")

def fisher_z_to_r(z: float) -> float:
    """
    Inverse Fisher's z-transformation to recover correlation coefficient.
    
    Formula: r = (exp(2z) - 1) / (exp(2z) + 1)
    
    Args:
        z: Fisher's z-transformed value.
        
    Returns:
        Correlation coefficient r.
    """
    if not isinstance(z, (int, float)):
        raise StatisticsError("Input 'z' must be a numeric value.")
        
    try:
        exp_2z = np.exp(2 * z)
        r = (exp_2z - 1) / (exp_2z + 1)
        return float(r)
    except (ValueError, OverflowError) as e:
        # Handle extreme values that cause overflow
        if z > 20:
            return 0.9999999
        elif z < -20:
            return -0.9999999
        raise StatisticsError(f"Error in inverse Fisher's z-transform: {e}")

def generate_null_distribution_permutation(
    centrality_values: List[float],
    essentiality_labels: List[int],
    n_permutations: int = 1000,
    random_seed: Optional[int] = None
) -> List[float]:
    """
    Generate null distribution of correlation coefficients via label permutation.
    
    Args:
        centrality_values: List of centrality metric values.
        essentiality_labels: List of binary essentiality labels.
        n_permutations: Number of permutations to perform.
        random_seed: Random seed for reproducibility.
        
    Returns:
        List of correlation coefficients from permuted data.
    """
    if random_seed is not None:
        np.random.seed(random_seed)
        
    null_dists = []
    n = len(essentiality_labels)
    
    for _ in range(n_permutations):
        # Shuffle labels while keeping centralities fixed
        permuted_labels = np.random.permutation(essentiality_labels).tolist()
        try:
            rho, _ = calculate_spearman_correlation(centrality_values, permuted_labels)
            null_dists.append(rho)
        except StatisticsError:
            # Skip if permutation results in invalid data (rare)
            continue
            
    return null_dists

def calculate_empirical_p_value(
    observed_stat: float,
    null_distribution: List[float],
    alternative: str = "two-sided"
) -> float:
    """
    Calculate empirical p-value from a null distribution.
    
    Args:
        observed_stat: The observed test statistic.
        null_distribution: List of statistics from the null distribution.
        alternative: Type of test ("two-sided", "greater", "less").
        
    Returns:
        Empirical p-value.
    """
    if not null_distribution:
        raise StatisticsError("Null distribution cannot be empty.")
        
    null_arr = np.array(null_distribution)
    
    if alternative == "two-sided":
        # Two-sided: count how many null stats are as extreme as observed
        count = np.sum(np.abs(null_arr) >= np.abs(observed_stat))
    elif alternative == "greater":
        count = np.sum(null_arr >= observed_stat)
    elif alternative == "less":
        count = np.sum(null_arr <= observed_stat)
    else:
        raise StatisticsError(f"Unknown alternative: {alternative}")
        
    # Add 1 to numerator and denominator for conservative estimate
    p_value = (count + 1) / (len(null_distribution) + 1)
    return float(p_value)

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg procedure for false discovery rate control.
    
    Args:
        p_values: List of raw p-values.
        
    Returns:
        List of adjusted p-values.
    """
    if not p_values:
        return []
        
    m = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    adjusted = np.zeros(m)
    for i in range(m - 1, -1, -1):
        rank = i + 1
        adjusted[i] = min(
            (m / rank) * sorted_p_values[i],
            1.0
        )
        if i < m - 1:
            adjusted[i] = min(adjusted[i], adjusted[i + 1])
            
    # Reorder to original sequence
    final_adjusted = [0.0] * m
    for idx, adj_val in zip(sorted_indices, adjusted):
        final_adjusted[idx] = float(adj_val)
        
    return final_adjusted

def run_label_permutation_analysis(
    centrality_values: List[float],
    essentiality_labels: List[int],
    observed_rho: float,
    n_permutations: int = 1000,
    output_path: Optional[Path] = None,
    random_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run full label permutation analysis including null distribution generation
    and empirical p-value calculation.
    
    Args:
        centrality_values: List of centrality values.
        essentiality_labels: List of essentiality labels.
        observed_rho: Observed correlation coefficient.
        n_permutations: Number of permutations.
        output_path: Path to save null distribution CSV (optional).
        random_seed: Random seed.
        
    Returns:
        Dictionary with null distribution summary and empirical p-value.
    """
    null_dist = generate_null_distribution_permutation(
        centrality_values, essentiality_labels, n_permutations, random_seed
    )
    
    empirical_p = calculate_empirical_p_value(observed_rho, null_dist)
    
    result = {
        "n_permutations": len(null_dist),
        "observed_rho": observed_rho,
        "empirical_p_value": empirical_p,
        "null_distribution_summary": {
            "mean": float(np.mean(null_dist)),
            "std": float(np.std(null_dist)),
            "min": float(np.min(null_dist)),
            "max": float(np.max(null_dist)),
            "median": float(np.median(null_dist))
        }
    }
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write("rho_value\n")
            for val in null_dist:
                f.write(f"{val}\n")
                
    return result

def calculate_rewired_correlations(
    rewired_graphs: List[Any],
    essentiality_labels: List[int],
    centrality_metric: str = "degree"
) -> List[float]:
    """
    Calculate correlations between rewired graph centralities and original labels.
    
    Args:
        rewired_graphs: List of NetworkX graph objects.
        essentiality_labels: Original essentiality labels.
        centrality_metric: Type of centrality to compute.
        
    Returns:
        List of correlation coefficients.
    """
    import networkx as nx
    
    correlations = []
    for graph in rewired_graphs:
        try:
            if centrality_metric == "degree":
                centrality = nx.degree_centrality(graph)
            elif centrality_metric == "betweenness":
                centrality = nx.betweenness_centrality(graph)
            elif centrality_metric == "eigenvector":
                centrality = nx.eigenvector_centrality(graph, max_iter=1000)
            else:
                raise StatisticsError(f"Unknown centrality metric: {centrality_metric}")
                
            values = [centrality.get(node, 0.0) for node in range(len(essentiality_labels))]
            rho, _ = calculate_spearman_correlation(values, essentiality_labels)
            correlations.append(rho)
        except Exception as e:
            logging.warning(f"Failed to calculate correlation for rewired graph: {e}")
            continue
            
    return correlations

def validate_graph_rewiring_model(
    original_graph: Any,
    rewired_graphs: List[Any],
    essentiality_labels: List[int],
    observed_rho: float,
    n_permutations: int = 1000
) -> Dict[str, Any]:
    """
    Validate the graph rewiring null model.
    
    Args:
        original_graph: Original NetworkX graph.
        rewired_graphs: List of rewired graphs.
        essentiality_labels: Essentiality labels.
        observed_rho: Observed correlation.
        n_permutations: Number of permutations for label shuffling.
        
    Returns:
        Validation report dictionary.
    """
    import networkx as nx
    
    # Check degree preservation
    original_degrees = sorted([d for _, d in original_graph.degree()])
    degree_preserved = True
    for rewired in rewired_graphs:
        rewired_degrees = sorted([d for _, d in rewired.degree()])
        if original_degrees != rewired_degrees:
            degree_preserved = False
            break
            
    # Calculate rewired correlations
    rewired_corrs = calculate_rewired_correlations(
        rewired_graphs, essentiality_labels, "degree"
    )
    
    if rewired_corrs:
        mean_rewired_rho = np.mean(rewired_corrs)
        std_rewired_rho = np.std(rewired_corrs)
        
        # Empirical p-value from rewiring null
        p_value_rewiring = calculate_empirical_p_value(
            observed_rho, rewired_corrs, alternative="two-sided"
        )
    else:
        mean_rewired_rho = None
        std_rewired_rho = None
        p_value_rewiring = None
        
    return {
        "degree_preserved": degree_preserved,
        "n_rewired_graphs": len(rewired_graphs),
        "rewired_correlations_mean": mean_rewired_rho,
        "rewired_correlations_std": std_rewired_rho,
        "observed_rho": observed_rho,
        "rewiring_p_value": p_value_rewiring
    }

def main():
    """Entry point for statistics module (for testing/debugging)."""
    logging.basicConfig(level=logging.INFO)
    logging.info("Statistics module loaded successfully.")
    logging.info("Available functions: calculate_spearman_correlation, fisher_z_transform, fisher_z_to_r, generate_null_distribution_permutation, calculate_empirical_p_value, benjamini_hochberg, run_label_permutation_analysis, calculate_rewired_correlations, validate_graph_rewiring_model")

if __name__ == "__main__":
    main()