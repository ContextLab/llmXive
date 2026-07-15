"""
Metric extraction module for trace compressibility analysis.

Implements FR-002: Compute sequence entropy, tool-repetition frequency,
and argument semantic variance for generated synthetic traces.
"""
import json
import math
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

from config import Config
from utils.loaders import TraceLoader
from utils.metrics_extract import (
    calculate_sequence_entropy,
    calculate_tool_repetition_frequency,
    calculate_argument_variance,
)

# Singleton for the embedding model to avoid reloading on every call
_EMBEDDING_MODEL = None
_MODEL_NAME = "all-MiniLM-L6-v2"

def _get_embedding_model() -> SentenceTransformer:
    """
    Lazy load the sentence-transformers model.
    Returns a cached instance to ensure CPU-only usage and efficiency.
    """
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        # Explicitly force CPU as per task constraints
        _EMBEDDING_MODEL = SentenceTransformer(_MODEL_NAME, device="cpu")
    return _EMBEDDING_MODEL

def _compute_semantic_variance(arguments: List[str]) -> float:
    """
    Compute the semantic variance of a list of argument strings.
    
    Definition: Variance = mean pairwise cosine distance of all argument embeddings.
    
    Args:
        arguments: List of argument strings from the trace.
        
    Returns:
        Mean pairwise cosine distance. Returns 0.0 if fewer than 2 arguments.
    """
    if len(arguments) < 2:
        return 0.0
    
    model = _get_embedding_model()
    embeddings = model.encode(arguments, show_progress_bar=False)
    
    n = len(embeddings)
    total_distance = 0.0
    count = 0
    
    # Calculate mean pairwise cosine distance
    # Cosine distance = 1 - cosine_similarity
    for i in range(n):
        for j in range(i + 1, n):
            # Normalize vectors for cosine similarity calculation
            vec_i = embeddings[i]
            vec_j = embeddings[j]
            
            dot_product = np.dot(vec_i, vec_j)
            norm_i = np.linalg.norm(vec_i)
            norm_j = np.linalg.norm(vec_j)
            
            if norm_i == 0 or norm_j == 0:
                # If a vector is zero, distance is 1 (max dissimilarity)
                cosine_similarity = 0.0
            else:
                cosine_similarity = dot_product / (norm_i * norm_j)
            
            cosine_distance = 1.0 - cosine_similarity
            total_distance += cosine_distance
            count += 1
    
    if count == 0:
        return 0.0
        
    return total_distance / count

def extract_metrics_for_trace(trace_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute structural metrics for a single trace.
    
    Args:
        trace_data: Dictionary containing trace data with 'exact_tool_sequence' 
                    and optionally 'arguments' keys.
    
    Returns:
        Dictionary containing computed metrics:
        - sequence_entropy: Shannon entropy of the tool sequence
        - tool_repetition_frequency: Frequency of tool repetitions
        - argument_variance: Semantic variance of arguments (if available)
        - trace_length: Number of tools in the sequence
    """
    tool_sequence = trace_data.get("exact_tool_sequence", [])
    trace_length = len(tool_sequence)
    
    if trace_length == 0:
        return {
            "sequence_entropy": 0.0,
            "tool_repetition_frequency": 0.0,
            "argument_variance": 0.0,
            "trace_length": 0,
        }
    
    # Calculate sequence entropy
    sequence_entropy = calculate_sequence_entropy(tool_sequence)
    
    # Calculate tool repetition frequency
    tool_repetition_frequency = calculate_tool_repetition_frequency(tool_sequence)
    
    # Calculate argument variance if arguments are available
    arguments = trace_data.get("arguments", [])
    if arguments:
        argument_variance = _compute_semantic_variance(arguments)
    else:
        # Default to 0.0 if no arguments (imputed default as per T016)
        argument_variance = 0.0
    
    return {
        "sequence_entropy": float(sequence_entropy),
        "tool_repetition_frequency": float(tool_repetition_frequency),
        "argument_variance": float(argument_variance),
        "trace_length": trace_length,
    }

def extract_metrics_from_trace_file(trace_file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract metrics from a single trace file.
    
    Args:
        trace_file_path: Path to the trace JSON file.
    
    Returns:
        Dictionary containing trace_id and computed metrics, or None if file is invalid.
    """
    try:
        with open(trace_file_path, "r", encoding="utf-8") as f:
            trace_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading trace file {trace_file_path}: {e}")
        return None
    
    trace_id = trace_data.get("trace_id", trace_file_path.stem)
    metrics = extract_metrics_for_trace(trace_data)
    
    return {
        "trace_id": trace_id,
        **metrics,
    }

def process_all_traces(data_dir: Path, output_path: Path) -> List[Dict[str, Any]]:
    """
    Process all trace files in a directory and write metrics to CSV.
    
    Args:
        data_dir: Directory containing trace JSON files.
        output_path: Path to write the output CSV file.
    
    Returns:
        List of dictionaries containing trace metrics.
    """
    config = Config()
    loader = TraceLoader(config)
    
    # Use the loader to get all trace files
    trace_files = loader.get_all_traces(data_dir)
    
    if not trace_files:
        print(f"No trace files found in {data_dir}")
        return []
    
    all_metrics = []
    for trace_file in trace_files:
        metrics_data = extract_metrics_from_trace_file(trace_file)
        if metrics_data:
            all_metrics.append(metrics_data)
    
    # Write metrics to CSV
    if all_metrics:
        _write_metrics_to_csv(all_metrics, output_path)
    
    return all_metrics

def _write_metrics_to_csv(metrics_list: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write metrics list to a CSV file.
    
    Args:
        metrics_list: List of dictionaries containing metrics.
        output_path: Path to write the CSV file.
    """
    if not metrics_list:
        return
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define CSV columns
    columns = [
        "trace_id",
        "sequence_entropy",
        "tool_repetition_frequency",
        "argument_variance",
        "trace_length",
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        for metrics in metrics_list:
            # Ensure all columns are present
            row = {col: metrics.get(col, "") for col in columns}
            writer.writerow(row)

def main() -> None:
    """
    Main entry point for metric extraction.
    
    Reads all traces from data/raw/, computes structural metrics,
    and writes results to data/processed/feature_matrix.csv.
    """
    config = Config()
    
    input_dir = config.raw_data_path
    output_path = config.processed_data_path / "feature_matrix.csv"
    
    print(f"Processing traces from: {input_dir}")
    print(f"Output metrics to: {output_path}")
    
    metrics = process_all_traces(input_dir, output_path)
    
    print(f"Successfully processed {len(metrics)} traces.")
    print(f"Metrics written to: {output_path}")


if __name__ == "__main__":
    main()
