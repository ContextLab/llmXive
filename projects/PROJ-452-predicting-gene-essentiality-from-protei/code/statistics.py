import logging
import os
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from scipy import stats
from pathlib import Path
import dendropy
from statsmodels.regression.linear_model import WLS
from statsmodels.tools import add_constant
from statsmodels.genmod.generalized_linear_model import GLS
import pandas as pd

class StatisticsError(Exception):
    """Custom exception for statistics-related errors."""
    pass

def calculate_spearman_correlation(x: List[float], y: List[float]) -> Dict[str, float]:
    """
    Calculate Spearman's rank correlation coefficient.
    
    Args:
        x: First variable (e.g., centrality scores)
        y: Second variable (e.g., essentiality labels)
        
    Returns:
        Dictionary with 'rho' (correlation coefficient) and 'p_value'
    """
    if len(x) != len(y) or len(x) == 0:
        raise StatisticsError("Input lists must be of equal non-zero length.")
    
    rho, p_value = stats.spearmanr(x, y)
    return {
        "rho": float(rho),
        "p_value": float(p_value)
    }

def fisher_z_transform(r: float) -> float:
    """
    Apply Fisher's z-transformation to a correlation coefficient.
    z = 0.5 * ln((1 + r) / (1 - r))
    """
    if not -1 < r < 1:
        raise StatisticsError(f"Correlation coefficient r={r} must be strictly between -1 and 1.")
    return 0.5 * np.log((1 + r) / (1 - r))

def fisher_z_to_r(z: float) -> float:
    """
    Inverse Fisher's z-transformation.
    r = (exp(2z) - 1) / (exp(2z) + 1)
    """
    return (np.exp(2 * z) - 1) / (np.exp(2 * z) + 1)

def generate_null_distribution_permutation(
    centrality: List[float], 
    essentiality: List[int], 
    n_permutations: int = 1000, 
    seed: Optional[int] = None
) -> List[float]:
    """
    Generate null distribution of Spearman correlations by permuting labels.
    
    Args:
        centrality: Observed centrality scores
        essentiality: Observed essentiality labels (binary)
        n_permutations: Number of permutations to run
        seed: Random seed for reproducibility
        
    Returns:
        List of correlation coefficients from permuted data
    """
    if seed is not None:
        np.random.seed(seed)
        
    if len(centrality) != len(essentiality):
        raise StatisticsError("Centrality and essentiality lists must be of equal length.")
        
    null_dists = []
    centrality_arr = np.array(centrality)
    essentiality_arr = np.array(essentiality)
    
    for _ in range(n_permutations):
        permuted_labels = np.random.permutation(essentiality_arr)
        try:
            rho, _ = stats.spearmanr(centrality_arr, permuted_labels)
            if not np.isnan(rho):
                null_dists.append(float(rho))
        except Exception:
            continue
            
    return null_dists

def calculate_empirical_p_value(observed_rho: float, null_dists: List[float]) -> float:
    """
    Calculate empirical p-value by comparing observed correlation to null distribution.
    Two-tailed test: proportion of null values with |value| >= |observed|
    """
    if not null_dists:
        raise StatisticsError("Null distribution is empty; cannot calculate p-value.")
        
    abs_observed = abs(observed_rho)
    count_extreme = sum(1 for val in null_dists if abs(val) >= abs_observed)
    return count_extreme / len(null_dists)

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg correction for multiple testing.
    
    Args:
        p_values: List of raw p-values
        
    Returns:
        List of adjusted p-values (FDR)
    """
    if not p_values:
        return []
        
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])
    
    # Calculate adjusted p-values
    adjusted = np.zeros(n)
    for i in range(n):
        rank = i + 1
        adjusted[i] = sorted_p[i] * n / rank
        
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i + 1])
        
    # Cap at 1.0
    adjusted = np.minimum(adjusted, 1.0)
    
    # Restore original order
    final_adjusted = np.zeros(n)
    final_adjusted[sorted_indices] = adjusted
    
    return [float(x) for x in final_adjusted]

def run_label_permutation_analysis(
    centrality: List[float], 
    essentiality: List[int], 
    output_path: str, 
    n_permutations: int = 1000,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run full label permutation analysis and save results to CSV.
    
    Args:
        centrality: Centrality scores
        essentiality: Essentiality labels
        output_path: Path to save results CSV
        n_permutations: Number of permutations
        seed: Random seed
        
    Returns:
        Dictionary with 'observed_rho', 'empirical_p_value', 'null_stats'
    """
    observed_result = calculate_spearman_correlation(centrality, essentiality)
    observed_rho = observed_result['rho']
    
    null_dists = generate_null_distribution_permutation(
        centrality, essentiality, n_permutations, seed
    )
    
    empirical_p = calculate_empirical_p_value(observed_rho, null_dists)
    
    # Save to CSV
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({'correlation': null_dists})
    df.to_csv(output_path, index=False)
    
    return {
        "observed_rho": observed_rho,
        "empirical_p_value": empirical_p,
        "null_distribution_summary": {
            "mean": float(np.mean(null_dists)),
            "std": float(np.std(null_dists)),
            "count": len(null_dists)
        }
    }

def calculate_rewired_correlations(
    rewired_graphs: List[Any], 
    essentiality_map: Dict[str, int],
    id_mapping: Dict[str, str]
) -> List[float]:
    """
    Calculate correlations between rewired graph centralities and original essentiality.
    
    Args:
        rewired_graphs: List of rewired networkx graphs
        essentiality_map: Map of gene ID to essentiality (binary)
        id_mapping: Map of original ID to mapped ID
        
    Returns:
        List of correlation coefficients
    """
    import networkx as nx
    
    correlations = []
    for graph in rewired_graphs:
        # Compute degree centrality for rewired graph
        centrality = nx.degree_centrality(graph)
        
        # Filter to genes with essentiality labels
        x_vals = []
        y_vals = []
        for node, cent_val in centrality.items():
            # Try to find essentiality for this node
            if node in essentiality_map:
                x_vals.append(cent_val)
                y_vals.append(essentiality_map[node])
        
        if len(x_vals) > 2:
            try:
                rho, _ = stats.spearmanr(x_vals, y_vals)
                if not np.isnan(rho):
                    correlations.append(float(rho))
            except Exception:
                continue
                
    return correlations

def validate_graph_rewiring_model(
    original_graph: Any, 
    rewired_graph: Any,
    tolerance: float = 0.01
) -> bool:
    """
    Validate that a rewired graph preserves degree distribution within tolerance.
    
    Args:
        original_graph: Original networkx graph
        rewired_graph: Rewired networkx graph
        tolerance: Maximum allowed difference in mean degree
        
    Returns:
        True if validation passes
    """
    import networkx as nx
    
    orig_degrees = [d for n, d in original_graph.degree()]
    rew_degrees = [d for n, d in rewired_graph.degree()]
    
    if not orig_degrees or not rew_degrees:
        return False
        
    mean_orig = np.mean(orig_degrees)
    mean_rew = np.mean(rew_degrees)
    
    if mean_orig == 0:
        return abs(mean_rew) < tolerance
        
    return abs(mean_orig - mean_rew) / mean_orig < tolerance

def run_pgls_analysis(
    correlation_data: Dict[str, float],
    phylogeny_path: str,
    organism_tax_ids: Dict[str, int]
) -> Dict[str, Any]:
    """
    Run Phylogenetic Generalized Least Squares (PGLS) analysis to test 
    for differences in correlation strength across organisms.
    
    This function:
    1. Loads the phylogenetic tree
    2. Prepares data (correlation coefficients as response, organism traits as predictors)
    3. Fits a PGLS model using statsmodels
    4. Returns model statistics
    
    Args:
        correlation_data: Dict mapping organism_id -> correlation_coefficient (rho)
        phylogeny_path: Path to Newick tree file
        organism_tax_ids: Dict mapping organism_id -> taxonomic ID
        
    Returns:
        Dictionary with PGLS results including statistic, p-value, and parameters
    """
    if not correlation_data:
        raise StatisticsError("No correlation data provided for PGLS analysis.")
        
    # Load phylogenetic tree
    try:
        tree = dendropy.Tree.get(
            path=phylogeny_path, 
            schema="newick", 
            rooting="force-rooted"
        )
    except Exception as e:
        raise StatisticsError(f"Failed to load phylogenetic tree: {e}")
        
    # Prepare data
    # We use the correlation coefficient (rho) as the response variable.
    # For a basic PGLS test of "differences", we might test against a constant
    # or against a specific trait if available. Here we test if the mean correlation
    # differs from zero, accounting for phylogeny.
    # A more complex model would include organism-specific predictors.
    # For this implementation, we perform a test of the intercept (mean rho).
    
    # Map organism IDs to tree tip labels
    # We assume the tree tips are labeled with taxonomic IDs or can be matched
    # via the provided organism_tax_ids mapping.
    
    # Filter data to organisms present in the tree
    valid_data = {}
    for org_id, rho in correlation_data.items():
        tax_id = organism_tax_ids.get(org_id)
        if tax_id:
            # Check if this tax_id is in the tree
            # Dendropy labels are usually strings
            label_str = str(tax_id)
            # Try to find the node
            found = False
            for node in tree:
                if node.taxon and node.taxon.label == label_str:
                    valid_data[org_id] = rho
                    found = True
                    break
            if not found:
                # Try matching by organism name if tax_id didn't work
                # (Simplistic fallback: check if org_id itself is in tree)
                for node in tree:
                    if node.taxon and node.taxon.label == org_id:
                        valid_data[org_id] = rho
                        found = True
                        break
    
    if len(valid_data) < 2:
        raise StatisticsError(
            f"Insufficient data for PGLS: need at least 2 organisms with tree presence. "
            f"Found {len(valid_data)}."
        )
        
    # Build the phylogenetic variance-covariance matrix (V)
    # Dendropy can calculate patristic distances
    tree.phylogenetic_distance_matrix()
    pdm = tree.phylogenetic_distance_matrix()
    
    # Get list of taxa in our valid data
    taxa_list = list(valid_data.keys())
    n = len(taxa_list)
    
    # Construct V matrix (covariance proportional to shared branch length)
    # For a Brownian motion model, Cov(Y_i, Y_j) = sigma^2 * t_ij
    # We normalize by the total tree height or max distance if needed, 
    # but statsmodels GLS handles the scaling.
    V = np.zeros((n, n))
    for i, org_i in enumerate(taxa_list):
        for j, org_j in enumerate(taxa_list):
            # Get path distance between taxa
            tax_i = tree.find_taxa_by_label(str(organism_tax_ids.get(org_i, org_i)))[0] if any(str(organism_tax_ids.get(org_i, org_i)) == t.label for t in tree.taxon_namespace) else None
            # Fallback: try direct label match if tax_id lookup failed
            if tax_i is None:
                try:
                    tax_i = tree.find_taxa_by_label(org_i)[0]
                except IndexError:
                    tax_i = None
                    
            tax_j = tree.find_taxa_by_label(str(organism_tax_ids.get(org_j, org_j)))[0] if any(str(organism_tax_ids.get(org_j, org_j)) == t.label for t in tree.taxon_namespace) else None
            if tax_j is None:
                try:
                    tax_j = tree.find_taxa_by_label(org_j)[0]
                except IndexError:
                    tax_j = None
            
            if tax_i and tax_j:
                try:
                    dist = pdm.patristic_distance(tax_i, tax_j)
                    V[i, j] = dist
                except Exception:
                    V[i, j] = 0.0 # Should not happen for valid tree
            else:
                V[i, j] = 0.0
    
    # Ensure V is positive definite (add small jitter if needed)
    try:
        np.linalg.cholesky(V)
    except np.linalg.LinAlgError:
        # Add small value to diagonal
        V += np.eye(n) * 1e-6
        
    # Prepare response vector (Y)
    Y = np.array([valid_data[org] for org in taxa_list])
    
    # Design matrix (X): intercept only for testing mean != 0
    X = np.ones((n, 1))
    
    # Fit GLS model
    try:
        model = GLS(Y, X, sigma=V)
        results = model.fit()
        
        # Extract statistics
        # The coefficient for the intercept is the estimated mean correlation
        # The t-statistic and p-value test if this mean is significantly different from 0
        coef = results.params[0]
        t_stat = results.tvalues[0]
        p_val = results.pvalues[0]
        
        # Also calculate the Fisher Z-transformed mean for reporting
        # Note: PGLS operates on the raw scale here. If we want to test Z-transformed means,
        # we should transform Y first. However, standard PGLS on rho is common.
        # Let's report both.
        z_mean = fisher_z_transform(coef) if -1 < coef < 1 else None
        
        return {
            "statistic": float(t_stat),
            "p_value": float(p_val),
            "estimated_mean_rho": float(coef),
            "estimated_mean_z": float(z_mean) if z_mean else None,
            "sample_size": n,
            "organisms_included": taxa_list,
            "model_type": "PGLS (Intercept-only)",
            "phylogeny_file": phylogeny_path
        }
        
    except Exception as e:
        raise StatisticsError(f"PGLS model fitting failed: {e}")

def main():
    """
    Main entry point for statistics module.
    Currently used for testing or running specific statistical analyses.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Statistics module loaded.")

if __name__ == "__main__":
    main()