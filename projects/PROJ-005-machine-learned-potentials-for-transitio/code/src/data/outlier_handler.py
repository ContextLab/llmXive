import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from src.data.graph_construction import load_processed_graphs_intermediate, get_project_root
from src.utils.logging import get_logger, log_metric

logger = get_logger(__name__)

def load_graphs_with_metadata(graphs_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the intermediate graphs parquet file.
    Returns a DataFrame where each row represents a graph with its metadata.
    """
    if graphs_path is None:
        project_root = get_project_root()
        graphs_path = project_root / "data" / "processed" / "graphs_intermediate.parquet"

    if not graphs_path.exists():
        raise FileNotFoundError(f"Graphs file not found at {graphs_path}. Run graph_construction first.")

    logger.info(f"Loading graphs from {graphs_path}")
    df = pd.read_parquet(graphs_path)
    return df

def compute_coordination_numbers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the maximum coordination number for each graph in the DataFrame.
    Assumes the DataFrame has an 'adjacency_matrix' column or similar structural data.
    If adjacency is stored as a list of lists or a 2D array, we sum rows.
    """
    logger.info("Computing coordination numbers from adjacency matrices...")

    # Handle case where adjacency might be stored as a list of arrays or a single column
    if 'adjacency_matrix' not in df.columns:
        # Fallback: try to infer from edge list if available, otherwise raise
        if 'edge_index' in df.columns:
            # This is a simplified assumption; real implementation depends on storage format
            logger.warning("Using edge_index to estimate coordination. Ensure format matches.")
            # This path requires complex logic to reconstruct max degree per graph ID.
            # For this task, we assume the 'adjacency_matrix' column exists as per T016a.
            raise ValueError("Expected 'adjacency_matrix' column in graphs parquet.")
        else:
            raise ValueError("No adjacency or edge data found in graph DataFrame.")

    def get_max_degree(adj):
        if adj is None:
            return 0
        # Handle numpy arrays or lists
        if isinstance(adj, np.ndarray):
            # Sum rows to get degree
            degrees = np.sum(adj, axis=1)
            return float(np.max(degrees)) if degrees.size > 0 else 0.0
        elif isinstance(adj, list):
            if not adj:
                return 0.0
            # Assume list of lists representing rows
            degrees = [sum(row) for row in adj]
            return float(max(degrees)) if degrees else 0.0
        else:
            return 0.0

    df['max_coordination'] = df['adjacency_matrix'].apply(get_max_degree)
    return df

def flag_outliers(df: pd.DataFrame, threshold: int = 6) -> pd.DataFrame:
    """
    Flag samples with coordination number > threshold.
    Logic:
    - If max_coordination > threshold:
      - Set 'exclude_from_training' = True
      - Set 'retain_in_test' = True (as per task requirement: "exclusion from training but retention in test")
    - Else:
      - Set 'exclude_from_training' = False
      - Set 'retain_in_test' = True (standard samples are in test if they are in the split)

    Note: This function adds flags to the DataFrame. The actual splitting logic (LLSO)
    happens in splits.py. This function prepares the flags for the split generation
    or for a final metadata file.
    """
    logger.info(f"Flagging outliers with coordination threshold > {threshold}...")

    df['is_outlier'] = df['max_coordination'] > threshold
    df['exclude_from_training'] = df['is_outlier']
    # Requirement: "retention in test".
    # We mark them as 'retain_in_test' = True. The split logic in T011b must be aware
    # that outliers might be forced into test or excluded from train.
    # For now, we just flag them. The downstream task (T020) will use these flags.
    df['retain_in_test'] = True

    outlier_count = df['is_outlier'].sum()
    total_count = len(df)
    logger.info(f"Found {outlier_count} outliers (coordination > {threshold}) out of {total_count} samples.")

    return df

def save_outlier_summary(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save a summary of outliers to a JSON file.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "outlier_summary.json"

    summary = {
        "total_samples": len(df),
        "outlier_count": int(df['is_outlier'].sum()),
        "outlier_threshold": 6,
        "outlier_indices": df[df['is_outlier']]['graph_id'].tolist() if 'graph_id' in df.columns else [],
        "coordination_stats": {
            "mean": float(df['max_coordination'].mean()),
            "max": float(df['max_coordination'].max()),
            "min": float(df['max_coordination'].min())
        }
    }

    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Outlier summary saved to {output_path}")
    return output_path

def save_flagged_graphs(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save the DataFrame with outlier flags to a new parquet file.
    This file is used as input for the split generation (T020) or final artifact generation.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "graphs_flagged.parquet"

    df.to_parquet(output_path, index=False)
    logger.info(f"Flagged graphs saved to {output_path}")
    return output_path

def run_outlier_handling(input_path: Optional[Path] = None, output_dir: Optional[Path] = None) -> Tuple[Path, Path]:
    """
    Main entry point for outlier handling.
    1. Load graphs.
    2. Compute coordination numbers.
    3. Flag outliers.
    4. Save summary and flagged graphs.
    """
    if input_path is None:
        project_root = get_project_root()
        input_path = project_root / "data" / "processed" / "graphs_intermediate.parquet"

    if output_dir is None:
        project_root = get_project_root()
        output_dir = project_root / "data" / "processed"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load
    df = load_graphs_with_metadata(input_path)

    # Compute
    df = compute_coordination_numbers(df)

    # Flag
    df = flag_outliers(df, threshold=6)

    # Save
    summary_path = output_dir / "outlier_summary.json"
    flagged_path = output_dir / "graphs_flagged.parquet"

    save_outlier_summary(df, summary_path)
    save_flagged_graphs(df, flagged_path)

    log_metric("outlier_count", int(df['is_outlier'].sum()))
    log_metric("total_samples", len(df))

    return summary_path, flagged_path

def main():
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    try:
        summary_path, flagged_path = run_outlier_handling()
        print(f"Outlier handling complete.")
        print(f"Summary: {summary_path}")
        print(f"Flagged Graphs: {flagged_path}")
    except Exception as e:
        logger.error(f"Outlier handling failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
