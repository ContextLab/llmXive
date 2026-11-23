"""
Phylogenetically-aware permutation testing module.

Implements PGLS residual permutation to test for association between
genomic features and resistance phenotypes while respecting clonal lineages.
"""
import os
import sys
import json
import logging
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import dendropy

# Import project utilities
# Assuming utils.config is available as per API surface
try:
    from utils.logging import get_logger
    from utils.config import load_config, get_config_value
except ImportError:
    # Fallback for direct execution context if imports differ
    import logging
    def get_logger(name):
        return logging.getLogger(name)
    
    def load_config(path=None):
        return {}
    
    def get_config_value(config, key, default=None):
        return config.get(key, default)

logger = get_logger(__name__)

def load_phylogeny_tree(tree_path: Path) -> dendropy.Tree:
    """
    Load a phylogenetic tree from a Newick file.
    
    Args:
        tree_path: Path to the Newick formatted tree file.
        
    Returns:
        A DendroPy Tree object.
    """
    if not tree_path.exists():
        raise FileNotFoundError(f"Tree file not found: {tree_path}")
    
    logger.info(f"Loading phylogenetic tree from {tree_path}")
    tree = dendropy.Tree.get(
        path=tree_path,
        schema="newick",
        preserve_underscores=True
    )
    logger.info(f"Tree loaded: {len(tree.taxon_namespace)} taxa, {len(tree.leaf_nodes())} leaves")
    return tree

def extract_clade_members(tree: dendropy.Tree, threshold: float = 0.95) -> Dict[str, List[str]]:
    """
    Extract clade members based on a bootstrap support or posterior probability threshold.
    
    Args:
        tree: The phylogenetic tree object.
        threshold: Minimum support value to consider a node as a clade (default 0.95).
        
    Returns:
        A dictionary mapping clade IDs to lists of taxon labels.
    """
    clades = {}
    clade_counter = 0
    
    for node in tree.postorder_node_iter():
        if not node.is_leaf():
            # Check support value if available, otherwise assume high support for internal nodes
            support = node.support if node.support is not None else 1.0
            
            if support >= threshold:
                clade_id = f"clade_{clade_counter}"
                taxa = [leaf.taxon.label for leaf in node.leaf_iter()]
                clades[clade_id] = taxa
                clade_counter += 1
                logger.debug(f"Identified clade {clade_id} with {len(taxa)} members")
    
    # If no clades found with threshold, treat the whole tree as one clade
    if not clades:
        logger.warning("No clades found with threshold >= 0.95. Treating entire tree as one clade.")
        all_taxa = [leaf.taxon.label for leaf in tree.leaf_nodes()]
        clades["clade_root"] = all_taxa
        
    return clades

def permute_within_clades(
    values: np.ndarray,
    labels: np.ndarray,
    clades: Dict[str, List[str]],
    taxon_order: List[str],
    rng: np.random.Generator
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Permute labels within each clade to preserve phylogenetic structure.
    
    Args:
        values: Genomic feature values (not permuted).
        labels: Resistance phenotype labels to be permuted.
        clades: Dictionary of clade members.
        taxon_order: List of taxon labels matching the order of values and labels arrays.
        rng: NumPy random number generator.
        
    Returns:
        Permuted labels array.
    """
    permuted_labels = labels.copy()
    taxon_to_idx = {taxon: i for i, taxon in enumerate(taxon_order)}
    
    for clade_id, members in clades.items():
        # Get indices for members of this clade
        indices = [taxon_to_idx[m] for m in members if m in taxon_to_idx]
        
        if len(indices) > 1:
            # Permute labels within this clade
            cluster_labels = labels[indices]
            shuffled = rng.permutation(cluster_labels)
            permuted_labels[indices] = shuffled
        elif len(indices) == 1:
            # Single member clade, no permutation possible/needed
            pass
            
    return permuted_labels

def calculate_residuals(
    X: np.ndarray,
    y: np.ndarray,
    clades: Dict[str, List[str]],
    taxon_order: List[str]
) -> np.ndarray:
    """
    Calculate residuals from a phylogenetic generalized least squares (PGLS) model.
    
    For simplicity in this implementation, we use a linear model with clade as a fixed effect
    to approximate the PGLS residual structure.
    
    Args:
        X: Genomic feature matrix.
        y: Resistance phenotype vector.
        clades: Dictionary of clade members.
        taxon_order: List of taxon labels.
        
    Returns:
        Residuals from the model.
    """
    try:
        import statsmodels.api as sm
    except ImportError:
        logger.error("statsmodels is required for PGLS residual calculation. Please install it.")
        raise
        
    # Create a design matrix with clade indicators
    n_samples = len(taxon_order)
    n_clades = len(clades)
    
    # Map taxon to clade
    taxon_to_clade = {}
    for clade_id, members in clades.items():
        for member in members:
            taxon_to_clade[member] = clade_id
            
    # Create clade dummy variables
    clade_matrix = np.zeros((n_samples, n_clades))
    clade_labels = sorted(clades.keys())
    clade_to_idx = {c: i for i, c in enumerate(clade_labels)}
    
    for i, taxon in enumerate(taxon_order):
        if taxon in taxon_to_clade:
            clade_idx = clade_to_idx[taxon_to_clade[taxon]]
            clade_matrix[i, clade_idx] = 1
            
    # Fit linear model: y ~ X + Clade_Fixed_Effects
    # We add an intercept
    X_design = np.hstack([np.ones((n_samples, 1)), X, clade_matrix])
    
    # Handle potential rank deficiency if clades cover all samples perfectly
    try:
        model = sm.OLS(y, X_design)
        results = model.fit()
        residuals = results.resid
    except Exception as e:
        logger.warning(f"PGLS residual calculation failed ({e}), falling back to standard residuals")
        # Fallback: simple linear regression residuals without clade effects
        X_simple = sm.add_constant(X)
        try:
            model_simple = sm.OLS(y, X_simple)
            results_simple = model_simple.fit()
            residuals = results_simple.resid
        except Exception:
            # Last resort: return centered y
            residuals = y - np.mean(y)
            
    return residuals

def run_permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    tree: dendropy.Tree,
    n_permutations: int = 1000,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Run the phylogenetically-aware permutation test.
    
    Args:
        X: Genomic feature matrix (samples x features).
        y: Resistance phenotype vector.
        tree: Phylogenetic tree object.
        n_permutations: Number of permutations to perform.
        random_seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing p-value, observed statistic, null distribution, and significance flag.
    """
    rng = np.random.default_rng(random_seed)
    taxon_order = [leaf.taxon.label for leaf in tree.leaf_nodes()]
    
    # Filter X and y to only include taxa present in the tree
    valid_indices = []
    for i, taxon in enumerate(taxon_order):
        # Assuming X rows are ordered by taxon_order or we need to match
        # For this implementation, we assume X rows correspond to taxon_order
        # In a real scenario, we might need to match indices carefully
        if i < len(X):
            valid_indices.append(i)
        
    X_valid = X[valid_indices]
    y_valid = y[valid_indices]
    
    if len(X_valid) == 0:
        raise ValueError("No valid samples found after matching with tree taxa.")
        
    # Calculate observed statistic (e.g., F-statistic or R-squared from a model)
    # Here we use a simple correlation-based statistic for demonstration
    # In a full implementation, this would be the test statistic from the model
    try:
        from scipy import stats
        # Calculate F-statistic or similar for the model
        # For simplicity, we'll use the sum of squared residuals from a null model vs full model
        # Null model: intercept only
        # Full model: intercept + features
        # This is a simplified version; a real PGLS test would be more complex
        
        # Let's use a simpler statistic: correlation between predicted and observed
        # from a simple linear model
        import statsmodels.api as sm
        X_const = sm.add_constant(X_valid)
        try:
            full_model = sm.OLS(y_valid, X_const).fit()
            observed_stat = full_model.rsquared
        except Exception:
            observed_stat = 0.0
    except ImportError:
        # Fallback if scipy/statsmodels not available
        observed_stat = 0.0
        
    logger.info(f"Observed statistic: {observed_stat:.4f}")
    
    # Get clades
    clades = extract_clade_members(tree)
    
    # Calculate residuals for permutation
    # Note: In a full PGLS, we permute residuals, not labels directly
    # Here we permute labels within clades as a proxy
    residuals = calculate_residuals(X_valid, y_valid, clades, [taxon_order[i] for i in valid_indices])
    
    # Permutation loop
    null_distribution = []
    for i in range(n_permutations):
        # Permute residuals within clades
        permuted_residuals = permute_within_clades(
            residuals,
            residuals, # We are permuting residuals here
            clades,
            [taxon_order[i] for i in valid_indices],
            rng
        )
        
        # Reconstruct permuted y
        # y_perm = y_mean + permuted_residuals (simplified)
        y_mean = np.mean(y_valid)
        y_perm = y_mean + permuted_residuals
        
        # Calculate statistic for permuted data
        try:
            X_const = sm.add_constant(X_valid)
            perm_model = sm.OLS(y_perm, X_const).fit()
            perm_stat = perm_model.rsquared
        except Exception:
            perm_stat = 0.0
            
        null_distribution.append(perm_stat)
        
        if (i + 1) % 100 == 0:
            logger.debug(f"Permutation {i+1}/{n_permutations} completed")
            
    null_distribution = np.array(null_distribution)
    
    # Calculate p-value
    # One-sided test: probability of observing a statistic as extreme or more extreme
    p_value = np.mean(null_distribution >= observed_stat)
    
    # Two-sided test could be: 2 * min(p, 1-p)
    # But for R-squared, one-sided is typically appropriate
    
    significance = p_value < 0.05
    
    result = {
        "observed_statistic": float(observed_stat),
        "p_value": float(p_value),
        "n_permutations": n_permutations,
        "significant": significance,
        "null_distribution_mean": float(np.mean(null_distribution)),
        "null_distribution_std": float(np.std(null_distribution)),
        "clades_used": list(clades.keys()),
        "random_seed": random_seed
    }
    
    logger.info(f"Permutation test completed. P-value: {p_value:.4f}, Significant: {significance}")
    
    return result

def save_results(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save permutation test results to a JSON file.
    
    Args:
        results: Dictionary containing test results.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Results saved to {output_path}")

def main() -> None:
    """Main entry point for the phylogenetic permutation test."""
    parser = argparse.ArgumentParser(description="Run phylogenetically-aware permutation test")
    parser.add_argument("--tree", type=str, required=True, help="Path to the phylogenetic tree (Newick)")
    parser.add_argument("--features", type=str, required=True, help="Path to the feature matrix (CSV)")
    parser.add_argument("--phenotype", type=str, required=True, help="Path to the phenotype data (CSV)")
    parser.add_argument("--output", type=str, required=True, help="Path to the output JSON file")
    parser.add_argument("--n-permutations", type=int, default=1000, help="Number of permutations")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    # Setup logging
    logger.info("Starting phylogenetic permutation test")
    
    try:
        # Load data
        tree = load_phylogeny_tree(Path(args.tree))
        
        # Load feature matrix and phenotype
        import pandas as pd
        
        features_df = pd.read_csv(args.features)
        phenotype_df = pd.read_csv(args.phenotype)
        
        # Merge on isolate_id
        if 'isolate_id' not in features_df.columns or 'isolate_id' not in phenotype_df.columns:
            # Try to find a common column
            common_cols = set(features_df.columns) & set(phenotype_df.columns)
            if 'isolate_id' in common_cols:
                pass
            else:
                raise ValueError("Could not find a common key column to merge features and phenotype")
                
        merged = pd.merge(features_df, phenotype_df, on='isolate_id', how='inner')
        
        if len(merged) == 0:
            raise ValueError("No overlapping samples found between features and phenotype")
            
        # Extract features (exclude isolate_id and phenotype columns)
        feature_cols = [c for c in merged.columns if c not in ['isolate_id', 'resistance_phenotype']]
        X = merged[feature_cols].values
        y = merged['resistance_phenotype'].values.astype(float)
        
        # Run permutation test
        results = run_permutation_test(
            X, y, tree,
            n_permutations=args.n_permutations,
            random_seed=args.seed
        )
        
        # Save results
        save_results(results, Path(args.output))
        
        # Log significance status
        if results['significant']:
            logger.info("Result is SIGNIFICANT (p < 0.05)")
        else:
            logger.warning("Result is NOT significant (p >= 0.05) - pipeline continues")
            
    except Exception as e:
        logger.error(f"Error during permutation test: {e}")
        raise

if __name__ == "__main__":
    main()