import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import sys

# Ensure project root is in path for imports
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from config import get_config_dict


def load_processed_metrics() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the aggregated structural and dynamic metrics CSVs.
    Returns:
        Tuple of (structural_df, dynamic_df)
    """
    config = get_config_dict()
    data_dir = Path(config["paths"]["data_dir"])
    
    structural_path = data_dir / "processed" / "structural_metrics.csv"
    dynamic_path = data_dir / "processed" / "dynamic_metrics.csv"
    
    if not structural_path.exists():
        raise FileNotFoundError(f"Structural metrics file not found at {structural_path}")
    if not dynamic_path.exists():
        raise FileNotFoundError(f"Dynamic metrics file not found at {dynamic_path}")
        
    structural_df = pd.read_csv(structural_path)
    dynamic_df = pd.read_csv(dynamic_path)
    
    return structural_df, dynamic_df


def recompute_graph_metrics_for_density(
    subject_dmri_path: Path, 
    density: float
) -> Dict[str, float]:
    """
    Re-compute graph metrics for a specific density threshold.
    
    Args:
        subject_dmri_path: Path to the subject's structural connectivity matrix (CSV/NPY).
        density: Target density (0.0 to 1.0).
        
    Returns:
        Dictionary with keys: 'global_efficiency', 'clustering_coefficient', 'modularity'
    """
    import networkx as nx
    
    # Load connectivity matrix
    # Assuming the file format is a square matrix (CSV or NPY)
    if subject_dmri_path.suffix == '.csv':
        adj_matrix = pd.read_csv(subject_dmri_path, header=None).values
    elif subject_dmri_path.suffix == '.npy':
        adj_matrix = np.load(subject_dmri_path)
    else:
        # Fallback: try loading as CSV without header
        try:
            adj_matrix = pd.read_csv(subject_dmri_path, header=None).values
        except:
            raise ValueError(f"Unsupported file format for {subject_dmri_path}")

    # Threshold the matrix to achieve target density
    # Flatten, sort, and find the threshold value corresponding to the top 'density' fraction
    flat_weights = adj_matrix[adj_matrix > 0]
    if len(flat_weights) == 0:
        return {
            'global_efficiency': 0.0,
            'clustering_coefficient': 0.0,
            'modularity': 0.0
        }
        
    threshold = np.percentile(flat_weights, (1 - density) * 100)
    binary_adj = (adj_matrix >= threshold).astype(float)
    
    # Ensure diagonal is zero
    np.fill_diagonal(binary_adj, 0)
    
    # Create graph
    G = nx.from_numpy_array(binary_adj)
    
    # Calculate metrics
    try:
        global_eff = nx.global_efficiency(G)
    except:
        global_eff = 0.0
        
    try:
        clustering = nx.average_clustering(G)
    except:
        clustering = 0.0
        
    try:
        # Modularity requires a partition. 
        # If we don't have a pre-computed partition, we can use Louvain to find one
        # for this specific density.
        from community import community_louvain
        partition = community_louvain.best_partition(G)
        modularity = community_louvain.modularity(partition, G)
    except ImportError:
        # Fallback if python-louvain not installed
        modularity = 0.0
    except Exception:
        modularity = 0.0
        
    return {
        'global_efficiency': global_eff,
        'clustering_coefficient': clustering,
        'modularity': modularity
    }


def calculate_sensitivity_metrics(
    structural_df: pd.DataFrame, 
    dynamic_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate sensitivity metrics for structural threshold density variations (±5%).
    
    This function:
    1. Loads the original structural connectivity matrices for each subject.
    2. Re-computes graph metrics at density = baseline + 0.05 and baseline - 0.05.
    3. Calculates the absolute difference and percentage change from the baseline.
    
    Args:
        structural_df: DataFrame with original structural metrics and subject paths.
        dynamic_df: DataFrame with dynamic metrics (used for subject ID matching).
        
    Returns:
        DataFrame containing sensitivity analysis results.
    """
    config = get_config_dict()
    base_density = config.get("structural", {}).get("density_threshold", 0.15)
    sensitivity_delta = 0.05
    
    results = []
    
    # We need to iterate through subjects. 
    # Assuming 'structural_df' has a column 'subject_id' and 'dmri_path'
    # If 'dmri_path' is not present, we must construct it or fail.
    if 'dmri_path' not in structural_df.columns:
        # Try to infer path from subject_id if a standard pattern exists
        # For now, we assume the path is stored or we can't proceed without it.
        # Let's assume the column exists as per T015 implementation expectations.
        raise ValueError("structural_df must contain 'dmri_path' column for sensitivity analysis.")
        
    for _, row in structural_df.iterrows():
        subject_id = row['subject_id']
        dmri_path = Path(row['dmri_path'])
        
        if not dmri_path.exists():
            print(f"Warning: DMRI path not found for {subject_id}: {dmri_path}")
            continue
            
        baseline_metrics = {
            'global_efficiency': row.get('global_efficiency', 0.0),
            'clustering_coefficient': row.get('clustering_coefficient', 0.0),
            'modularity': row.get('modularity', 0.0)
        }
        
        # Compute for +5%
        density_high = min(base_density + sensitivity_delta, 1.0)
        metrics_high = recompute_graph_metrics_for_density(dmri_path, density_high)
        
        # Compute for -5%
        density_low = max(base_density - sensitivity_delta, 0.0)
        metrics_low = recompute_graph_metrics_for_density(dmri_path, density_low)
        
        # Calculate differences
        diff_eff_high = metrics_high['global_efficiency'] - baseline_metrics['global_efficiency']
        diff_eff_low = metrics_low['global_efficiency'] - baseline_metrics['global_efficiency']
        
        diff_clust_high = metrics_high['clustering_coefficient'] - baseline_metrics['clustering_coefficient']
        diff_clust_low = metrics_low['clustering_coefficient'] - baseline_metrics['clustering_coefficient']
        
        diff_mod_high = metrics_high['modularity'] - baseline_metrics['modularity']
        diff_mod_low = metrics_low['modularity'] - baseline_metrics['modularity']
        
        results.append({
            'subject_id': subject_id,
            'baseline_density': base_density,
            'high_density': density_high,
            'low_density': density_low,
            'eff_diff_high': diff_eff_high,
            'eff_diff_low': diff_eff_low,
            'clust_diff_high': diff_clust_high,
            'clust_diff_low': diff_clust_low,
            'mod_diff_high': diff_mod_high,
            'mod_diff_low': diff_mod_low,
            'eff_abs_diff_high': abs(diff_eff_high),
            'eff_abs_diff_low': abs(diff_eff_low),
            'clust_abs_diff_high': abs(diff_clust_high),
            'clust_abs_diff_low': abs(diff_clust_low),
            'mod_abs_diff_high': abs(diff_mod_high),
            'mod_abs_diff_low': abs(diff_mod_low)
        })
        
    return pd.DataFrame(results)


def run_sensitivity_analysis() -> pd.DataFrame:
    """
    Main entry point to run the density sensitivity analysis.
    """
    print("Loading processed metrics...")
    structural_df, dynamic_df = load_processed_metrics()
    
    print("Calculating sensitivity metrics for density variation (±5%)...")
    sensitivity_df = calculate_sensitivity_metrics(structural_df, dynamic_df)
    
    return sensitivity_df


def save_sensitivity_results(sensitivity_df: pd.DataFrame, output_path: Optional[str] = None):
    """
    Save the sensitivity analysis results to a CSV file.
    """
    config = get_config_dict()
    data_dir = Path(config["paths"]["data_dir"])
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    if output_path is None:
        output_path = processed_dir / "density_sensitivity_results.csv"
    else:
        output_path = Path(output_path)
        
    sensitivity_df.to_csv(output_path, index=False)
    print(f"Sensitivity results saved to {output_path}")
    return output_path


def main():
    """
    Execute the sensitivity analysis for structural threshold density.
    """
    try:
        sensitivity_df = run_sensitivity_analysis()
        output_path = save_sensitivity_results(sensitivity_df)
        
        # Summary statistics
        print("\n--- Sensitivity Analysis Summary ---")
        print(f"Subjects analyzed: {len(sensitivity_df)}")
        print(f"Mean absolute change in Global Efficiency (High): {sensitivity_df['eff_abs_diff_high'].mean():.6f}")
        print(f"Mean absolute change in Global Efficiency (Low): {sensitivity_df['eff_abs_diff_low'].mean():.6f}")
        print(f"Mean absolute change in Clustering (High): {sensitivity_df['clust_abs_diff_high'].mean():.6f}")
        print(f"Mean absolute change in Clustering (Low): {sensitivity_df['clust_abs_diff_low'].mean():.6f}")
        
    except Exception as e:
        print(f"Error running sensitivity analysis: {e}")
        raise


if __name__ == "__main__":
    main()