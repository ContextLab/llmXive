"""
Aggregation logic for User Story 2: Dynamic Connectivity Metric Computation.

Implements the collapse of edge-wise metrics into a single subject-level
Variability_Metric (mean edge SD) and Shannon entropy.

This module fulfills T023 and supports T026 (saving metrics).
"""
import os
import logging
from typing import Dict, List, Optional, Union, Any
import numpy as np
import pandas as pd

from code.config import get_config
from code.data.paths import get_processed_path, ensure_dir
from code.utils.logging import log_error, log_warning, init_logging

# Configure logging
logger = logging.getLogger(__name__)

def aggregate_subject_metrics(
    subject_id: str,
    edge_sd: np.ndarray,
    edge_entropy: np.ndarray
) -> Dict[str, Union[str, float]]:
    """
    Aggregate edge-wise metrics into a single subject-level metric.
    
    According to T023 specification:
    - Variability_Metric: Mean of edge-wise standard deviations.
    - Entropy: Mean of edge-wise Shannon entropy (or total, depending on spec interpretation;
      here we use mean to keep scale comparable to SD).
    
    Args:
        subject_id: Unique identifier for the subject.
        edge_sd: 1D numpy array of standard deviations for each edge.
        edge_entropy: 1D numpy array of Shannon entropy for each edge.
    
    Returns:
        Dictionary containing Subject_ID, Variability_Metric, and Entropy.
    
    Raises:
        ValueError: If input arrays are empty or have mismatched shapes.
    """
    if edge_sd.size == 0:
        raise ValueError(f"Edge SD array is empty for subject {subject_id}.")
    if edge_entropy.size == 0:
        raise ValueError(f"Edge Entropy array is empty for subject {subject_id}.")
    
    if edge_sd.shape != edge_entropy.shape:
        raise ValueError(
            f"Shape mismatch for subject {subject_id}: "
            f"edge_sd {edge_sd.shape} vs edge_entropy {edge_entropy.shape}."
        )
    
    # Calculate mean edge SD as the primary Variability_Metric
    variability_metric = float(np.mean(edge_sd))
    
    # Calculate mean edge entropy
    entropy_value = float(np.mean(edge_entropy))
    
    return {
        "Subject_ID": subject_id,
        "Variability_Metric": variability_metric,
        "Entropy": entropy_value
    }

def save_metrics_to_csv(
    metrics_list: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> str:
    """
    Save a list of subject metrics to a CSV file.
    
    Args:
        metrics_list: List of dictionaries returned by aggregate_subject_metrics.
        output_path: Optional path to write the CSV. If None, uses default path
                     from config (data/processed/metrics.csv).
    
    Returns:
        The path to the written CSV file.
    
    Raises:
        RuntimeError: If the list is empty or if writing fails.
    """
    if not metrics_list:
        raise RuntimeError("No metrics to save. The input list is empty.")
    
    if output_path is None:
        output_path = os.path.join(get_processed_path(), "metrics.csv")
    
    ensure_dir(output_path)
    
    try:
        df = pd.DataFrame(metrics_list)
        # Ensure column order matches spec for T026
        expected_cols = ["Subject_ID", "Variability_Metric", "Entropy"]
        if not all(col in df.columns for col in expected_cols):
            missing = set(expected_cols) - set(df.columns)
            raise RuntimeError(f"Missing columns in metrics DataFrame: {missing}")
        
        df = df[expected_cols]
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(metrics_list)} subject metrics to {output_path}")
        return output_path
    except Exception as e:
        log_error(f"Failed to save metrics to {output_path}: {str(e)}")
        raise

def run_aggregation_pipeline(
    input_metrics_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Run the full aggregation pipeline:
    1. Load edge metrics from intermediate connectivity output (if provided).
       Note: In this specific task flow, T022 produces edge metrics per subject.
       We assume T022's output is passed in or read from a known intermediate location.
       However, T023 specifically asks to "Implement aggregation logic".
       The function signature here assumes we are aggregating data that has
       already been computed by T022.
       
       Since T022 (compute_edge_metrics) likely outputs a structure like:
       { subject_id: { 'edge_sd': array, 'edge_entropy': array } }
       We need to access that.
       
       To make this pipeline runnable as a standalone script (T023 requirement),
       we assume the input is a pre-computed JSON or CSV of edge stats, OR
       we rely on the fact that T026 calls this function.
       
       For the purpose of this task implementation, we define the function
       to accept a list of pre-aggregated edge stats or a path to a file
       containing raw edge metrics per subject.
       
       Given the task description "Implement aggregation logic to collapse edge metrics",
       the core logic is in aggregate_subject_metrics. This pipeline function
       orchestrates the saving.
       
       Assumption: The caller (e.g., main.py or a batch processor) has collected
       the edge_sd and edge_entropy arrays for each subject.
       
       To satisfy the "runnable" constraint without circular dependencies on T022's
       internal state, we will assume this function is called with the results
       of T022's processing.
       
       If input_metrics_path is provided, we assume it's a CSV/JSON with columns:
       Subject_ID, Edge_SD_List, Edge_Entropy_List (serialized) OR
       we expect the caller to pass the data directly.
       
       However, looking at T026: "Save subject-level metrics to data/processed/metrics.csv".
       This implies T023's output IS the metrics.csv.
       
       Let's define the input to this pipeline as a list of dictionaries
       containing the raw edge arrays, or a path to a file where these are stored.
       
       For robustness, we will implement a version that reads from a temporary
       intermediate file if path is given, or processes a list if given.
       
       But to keep it simple and aligned with the "one task" constraint:
       We will assume the input is a list of dicts with 'subject_id', 'edge_sd', 'edge_entropy'.
       
       If the caller passes a path, we try to load it as a CSV where lists are stored
       as comma-separated strings or similar.
       
       Actually, the most robust way for T023 is to define the function that
       takes the raw data (edge_sd, edge_entropy) and returns the aggregated dict.
       The pipeline function will just handle the I/O if needed.
       
       Let's assume the pipeline is triggered by a script that has the data in memory.
       We will implement the logic to aggregate and save.
    """
    # If input_metrics_path is provided, we attempt to load it.
    # Expected format: CSV with Subject_ID, Edge_SD (string of comma-separated values), Edge_Entropy (string)
    # OR we assume the data is passed via a global state (not recommended).
    # For this implementation, we assume the function is called with the data in memory
    # or we simulate the loading from a known intermediate file if the path is provided.
    
    # Since T022 is the producer of edge metrics, and T023 consumes them,
    # the standard flow is:
    # 1. T022 processes all subjects, storing edge_sd/entropy in a temporary structure/file.
    # 2. T023 reads that structure/file, aggregates, and saves metrics.csv.
    
    # To make this task self-contained and runnable, we will assume the input
    # is a path to a CSV file generated by T022 (or a mock of it for testing).
    # If no path is provided, we raise an error or expect the caller to provide data.
    
    # However, the task description says "Implement aggregation logic".
    # The logic is in aggregate_subject_metrics.
    # The pipeline function is a wrapper.
    
    # Let's assume the input is a list of dicts with 'Subject_ID', 'edge_sd', 'edge_entropy'
    # and the function aggregates them.
    
    # If input_metrics_path is provided, we try to load it.
    # If not, we expect the caller to have passed the data.
    # But the function signature here takes a path.
    # Let's assume the path points to a file with columns: Subject_ID, Edge_SD, Edge_Entropy
    # where Edge_SD and Edge_Entropy are comma-separated strings of floats.
    
    if input_metrics_path and os.path.exists(input_metrics_path):
        logger.info(f"Loading edge metrics from {input_metrics_path}")
        df_raw = pd.read_csv(input_metrics_path)
        
        metrics_list = []
        for _, row in df_raw.iterrows():
            sub_id = str(row['Subject_ID'])
            try:
                # Parse comma-separated strings to numpy arrays
                sd_vals = np.array([float(x) for x in str(row['Edge_SD']).split(',') if x.strip()])
                ent_vals = np.array([float(x) for x in str(row['Edge_Entropy']).split(',') if x.strip()])
                
                agg = aggregate_subject_metrics(sub_id, sd_vals, ent_vals)
                metrics_list.append(agg)
            except Exception as e:
                log_warning(f"Skipping subject {sub_id} due to error: {e}")
                continue
        
        if not metrics_list:
            raise RuntimeError("No valid metrics could be aggregated from the input file.")
        
        output_path = save_metrics_to_csv(metrics_list, output_path)
        return output_path
    
    else:
        # If no input path, we assume the data is passed in a way not covered by this signature
        # or we are in a testing environment where we expect the caller to handle it.
        # For the purpose of this task, we raise a clear error if no input is provided.
        raise ValueError(
            "No input metrics path provided or file not found. "
            "T023 requires an input source of edge metrics (e.g., from T022)."
        )

def main():
    """
    Entry point for the aggregation pipeline when run as a script.
    Expects environment variables or arguments to specify input/output paths.
    """
    init_logging()
    config = get_config()
    
    # Default paths
    # Assuming T022 writes to data/processed/edge_metrics_raw.csv
    input_path = os.path.join(get_processed_path(), "edge_metrics_raw.csv")
    output_path = os.path.join(get_processed_path(), "metrics.csv")
    
    # Check if input exists
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Ensure T022 has run and produced edge_metrics_raw.csv")
        sys.exit(1)
    
    try:
        result_path = run_aggregation_pipeline(input_path, output_path)
        logger.info(f"Aggregation complete. Output: {result_path}")
    except Exception as e:
        log_error(f"Aggregation pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()