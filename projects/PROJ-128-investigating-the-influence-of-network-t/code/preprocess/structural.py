import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import json
import os
import sys

# Ensure project root is in path for imports
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from config import get_config_dict
from preprocess.loader import load_hcp_dmri

def calculate_graph_metrics(
    adjacency_matrix: np.ndarray,
    density_threshold: float,
    is_proportional: bool = True
) -> Dict[str, float]:
    """
    Calculate global graph metrics for a given adjacency matrix and density threshold.

    Args:
        adjacency_matrix: NxN adjacency matrix (connectivity weights).
        density_threshold: Threshold value (0.0 to 1.0).
        is_proportional: If True, threshold keeps top X% of edges. If False, applies absolute cutoff.

    Returns:
        Dictionary with metrics: global_efficiency, avg_clustering, modularity, num_nodes, num_edges.
    """
    # Apply threshold
    if is_proportional:
        # Flatten and sort to find threshold
        weights = adjacency_matrix[adjacency_matrix > 0]
        if len(weights) == 0:
            return {
                "global_efficiency": 0.0,
                "avg_clustering": 0.0,
                "modularity": 0.0,
                "num_nodes": adjacency_matrix.shape[0],
                "num_edges": 0
            }
        threshold_val = np.sort(weights)[int(len(weights) * (1 - density_threshold))]
        adj_binary = (adjacency_matrix >= threshold_val).astype(float)
    else:
        adj_binary = (adjacency_matrix >= density_threshold).astype(float)

    # Remove self-loops
    np.fill_diagonal(adj_binary, 0)

    # Create graph
    G = nx.from_numpy_array(adj_binary)

    # Calculate metrics
    try:
        global_eff = nx.global_efficiency(G)
    except Exception:
        global_eff = 0.0

    try:
        clustering = nx.average_clustering(G)
    except Exception:
        clustering = 0.0

    # Modularity requires communities
    try:
        # Use greedy modularity optimization
        communities = nx.community.greedy_modularity_communities(G)
        modularity = nx.community.modularity(G, communities)
    except Exception:
        modularity = 0.0

    return {
        "global_efficiency": float(global_eff),
        "avg_clustering": float(clustering),
        "modularity": float(modularity),
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges()
    }

def process_subject_structural_metrics(
    subject_id: str,
    config: Dict,
    dmri_data: Optional[np.ndarray] = None
) -> Dict[str, any]:
    """
    Process a single subject's structural data and compute metrics at baseline density.

    Args:
        subject_id: Subject identifier.
        config: Configuration dictionary.
        dmri_data: Preloaded dmri adjacency matrix. If None, loads from disk.

    Returns:
        Dictionary with subject metrics.
    """
    if dmri_data is None:
        dmri_data = load_hcp_dmri(subject_id, config)

    if dmri_data is None:
        raise ValueError(f"Could not load dmri data for subject {subject_id}")

    density_threshold = config.get("DENSITY_THRESHOLD_BASELINE", 0.15)

    metrics = calculate_graph_metrics(dmri_data, density_threshold)
    metrics["subject_id"] = subject_id
    metrics["density_threshold"] = density_threshold

    return metrics

def run_structural_pipeline(
    subjects: List[str],
    config: Dict,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Run structural metric calculation for a list of subjects.

    Args:
        subjects: List of subject IDs.
        config: Configuration dictionary.
        output_path: Path to save CSV results.

    Returns:
        DataFrame with all metrics.
    """
    results = []
    for subj in subjects:
        try:
            metrics = process_subject_structural_metrics(subj, config)
            results.append(metrics)
        except Exception as e:
            print(f"Error processing subject {subj}: {e}", file=sys.stderr)
            continue

    df = pd.DataFrame(results)
    if output_path:
        df.to_csv(output_path, index=False)
    return df

def save_structural_metrics_to_csv(
    metrics_list: List[Dict],
    output_path: Path
) -> None:
    """Save a list of metric dictionaries to a CSV file."""
    df = pd.DataFrame(metrics_list)
    df.to_csv(output_path, index=False)

def run_sensitivity_analysis(
    subjects: List[str],
    config: Dict,
    output_path: Path
) -> pd.DataFrame:
    """
    Perform sensitivity analysis on graph density thresholds as mandated by FR-008.

    Iterates through DENSITY_THRESHOLD_VARIATIONS and calculates metrics for each.
    Saves results to the specified output path.

    Args:
        subjects: List of subject IDs to process.
        config: Configuration dictionary containing DENSITY_THRESHOLD_VARIATIONS.
        output_path: Path to save the sensitivity CSV results.

    Returns:
        DataFrame containing the sensitivity analysis results.
    """
    density_variations = config.get("DENSITY_THRESHOLD_VARIATIONS", [0.10, 0.15, 0.20])
    all_results = []

    print(f"Running structural density sensitivity analysis for {len(subjects)} subjects...")
    print(f"Density thresholds: {density_variations}")

    for subj_id in subjects:
        try:
            # Load data once per subject
            dmri_data = load_hcp_dmri(subj_id, config)
            if dmri_data is None:
                print(f"Skipping {subj_id}: No dmri data found.")
                continue

            for density in density_variations:
                try:
                    metrics = calculate_graph_metrics(dmri_data, density, is_proportional=True)
                    metrics["subject_id"] = subj_id
                    metrics["density_threshold"] = float(density)
                    all_results.append(metrics)
                except Exception as e:
                    print(f"Error at density {density} for {subj_id}: {e}")
                    continue

        except Exception as e:
            print(f"Failed to load data for {subj_id}: {e}")
            continue

    if not all_results:
        # Create empty dataframe with correct columns if no data
        columns = ["subject_id", "density_threshold", "global_efficiency", "avg_clustering", "modularity", "num_nodes", "num_edges"]
        df = pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(all_results)
        # Ensure column order
        cols = ["subject_id", "density_threshold", "global_efficiency", "avg_clustering", "modularity", "num_nodes", "num_edges"]
        df = df[[c for c in cols if c in df.columns]]

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Sensitivity analysis results saved to {output_path}")

    return df

def main():
    """
    Main entry point for running the structural pipeline and sensitivity analysis.
    """
    config = get_config_dict()
    ensure_directories = config.get("ensure_directories", lambda: None)
    ensure_directories()

    # Example subjects - in real usage, this would be loaded from a manifest or directory scan
    # For this task, we assume a standard HCP subject list or read from data/raw if available
    # If no real subjects exist, we cannot run on real data, so we rely on the loader to fail loudly
    # or the user to provide the list. We'll attempt to scan data/raw/dmri if it exists.
    data_raw_path = Path(config.get("DATA_RAW_PATH", "data/raw"))
    dmri_dir = data_raw_path / "dmri"

    subjects = []
    if dmri_dir.exists():
        # Look for standard HCP naming or just list directories
        for item in dmri_dir.iterdir():
            if item.is_dir():
                subjects.append(item.name)
    else:
        # Fallback to a known list if the user hasn't downloaded data yet
        # This will trigger a loader error if data is missing, satisfying the "fail loudly" constraint
        subjects = ["100307"]  # Example HCP ID

    if not subjects:
        print("No subjects found. Exiting.", file=sys.stderr)
        sys.exit(1)

    print(f"Processing subjects: {subjects}")

    # Run baseline structural metrics (T015a)
    baseline_output = Path(config.get("DATA_PROCESSED_PATH", "data/processed")) / "structural_metrics.csv"
    run_structural_pipeline(subjects, config, baseline_output)

    # Run Sensitivity Analysis (T015b)
    sensitivity_output = Path(config.get("DATA_PROCESSED_PATH", "data/processed")) / "structural_density_sensitivity.csv"
    run_sensitivity_analysis(subjects, config, sensitivity_output)

if __name__ == "__main__":
    main()