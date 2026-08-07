"""
Module: code/metrics/extract.py
Purpose: Compute structural metrics (entropy, repetition, semantic variance) for traces.
"""
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import csv
import warnings

# Sentence Transformers for semantic variance
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    raise ImportError(
        "Missing required dependency: sentence-transformers. "
        "Please install it via: pip install sentence-transformers"
    )

# Project imports
from config import get_config
from utils.loaders import TraceLoader
from utils.validators import MetricsValidator

class MetricExtractionError(Exception):
    """Custom exception for metric extraction failures."""
    pass


def calculate_sequence_entropy(tool_sequence: List[str]) -> float:
    """
    Calculate Shannon entropy of the tool call sequence.
    Higher entropy implies more diverse/unpredictable tool usage.
    """
    if not tool_sequence:
        return 0.0
    
    counts = Counter(tool_sequence)
    total = len(tool_sequence)
    entropy = 0.0
    
    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    
    return entropy


def calculate_tool_repetition_frequency(tool_sequence: List[str]) -> float:
    """
    Calculate the frequency of tool repetitions.
    Defined as 1 - (unique_tools / total_tools).
    0.0 = all unique, 1.0 = all same.
    """
    if not tool_sequence:
        return 0.0
    
    unique_count = len(set(tool_sequence))
    total_count = len(tool_sequence)
    
    if unique_count == 0:
        return 0.0
        
    return 1.0 - (unique_count / total_count)


def calculate_argument_variance(arguments: List[str]) -> float:
    """
    Calculate argument semantic variance using sentence embeddings.
    Definition: Mean pairwise cosine distance of all argument embeddings.
    If variance is undefined (0 or 1 argument), returns 0.0.
    """
    if len(arguments) <= 1:
        return 0.0
    
    # Load model (CPU-only, cached)
    # Using a global variable to avoid reloading for every trace in a large batch
    # is risky in a script context without a persistent server, so we load here.
    # For large scale, consider caching the model instance in a singleton if refactored.
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    try:
        embeddings = model.encode(arguments, show_progress_bar=False, convert_to_numpy=True)
    except Exception as e:
        raise MetricExtractionError(f"Failed to encode arguments: {e}")
    
    n = len(embeddings)
    if n <= 1:
        return 0.0
    
    # Calculate mean pairwise cosine distance
    # Cosine distance = 1 - cosine_similarity
    total_dist = 0.0
    count = 0
    
    # Optimization: Vectorize if possible, but for typical trace lengths (N < 1000),
    # a double loop is acceptable and avoids complex numpy broadcasting errors.
    # However, to be safe with large N, we use numpy broadcasting for the matrix.
    # embeddings shape: (N, D)
    # Dot product: (N, N)
    # Norms: (N, 1)
    
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    # Avoid division by zero
    norms = np.where(norms == 0, 1e-10, norms)
    normalized = embeddings / norms
    
    # Cosine similarity matrix
    sim_matrix = np.dot(normalized, normalized.T)
    
    # Clip to [-1, 1] to avoid numerical errors in acos if used, 
    # but here we just need distance = 1 - sim
    sim_matrix = np.clip(sim_matrix, -1.0, 1.0)
    
    # Upper triangle (excluding diagonal) for unique pairs
    upper_tri_indices = np.triu_indices(n, k=1)
    pairwise_sims = sim_matrix[upper_tri_indices]
    
    mean_sim = np.mean(pairwise_sims)
    mean_dist = 1.0 - mean_sim
    
    return float(mean_dist)


def extract_metrics_for_trace(trace_data: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
    """
    Extract all structural metrics for a single trace.
    """
    tool_sequence = trace_data.get('exact_tool_sequence', [])
    arguments = trace_data.get('raw_arg_variance', [])
    
    # If arguments is a list of dicts/objects, extract string content
    # Assuming raw_arg_variance contains strings or objects with 'content'/'text'
    if arguments and isinstance(arguments[0], dict):
        arguments = [
            arg.get('text', arg.get('content', str(arg))) 
            for arg in arguments
        ]
    elif not arguments:
        arguments = []

    try:
        entropy = calculate_sequence_entropy(tool_sequence)
        repetition = calculate_tool_repetition_frequency(tool_sequence)
        variance = calculate_argument_variance(arguments)
    except Exception as e:
        raise MetricExtractionError(f"Error extracting metrics for trace {trace_id}: {e}")
    
    return {
        "trace_id": trace_id,
        "sequence_entropy": entropy,
        "tool_repetition_frequency": repetition,
        "argument_semantic_variance": variance,
        "sequence_length": len(tool_sequence),
        "argument_count": len(arguments)
    }


def extract_metrics_from_trace_file(file_path: Path) -> Dict[str, Any]:
    """
    Load a trace JSON file and extract metrics.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise MetricExtractionError(f"Invalid JSON in {file_path}: {e}")
    except Exception as e:
        raise MetricExtractionError(f"Failed to load {file_path}: {e}")
    
    # Handle cases where the file is a list of traces or a single trace object
    if isinstance(data, list):
        if len(data) == 0:
            raise MetricExtractionError(f"Empty trace list in {file_path}")
        # Assuming each file is one session, but if it's a list of sessions, we process the first or all?
        # Based on T012, files are named session_{uuid}.json containing ONE session.
        # If the generator accidentally wrote a list, we take the first element if it looks like a session.
        # However, T012 says "Output files named session_{uuid}.json containing ...", implying one object per file.
        # We'll assume the root is the trace object. If it's a list, we might need to handle it.
        # Let's assume the file content is the trace object itself.
        # If the file structure is [trace1, trace2], we should probably error or handle.
        # Given T012 description: "session_{uuid}.json containing exact_tool_sequence...", 
        # it implies the JSON root is the object.
        # If it's a list, we'll take the first item as a fallback, but log a warning.
        if isinstance(data[0], dict) and 'exact_tool_sequence' in data[0]:
            trace_data = data[0]
            warnings.warn(f"File {file_path} contains a list. Taking first element.")
        else:
            raise MetricExtractionError(f"Unexpected list structure in {file_path}")
    else:
        trace_data = data

    # Extract ID from filename if not in data
    trace_id = trace_data.get('trace_id') or trace_data.get('session_id') or file_path.stem
    
    return extract_metrics_for_trace(trace_data, trace_id)


def process_all_traces(input_dirs: List[Path], output_path: Path) -> None:
    """
    Process all traces in the given directories and write the feature matrix CSV.
    """
    all_metrics = []
    loader = TraceLoader()
    
    # Validate input directories exist
    for dir_path in input_dirs:
        if not dir_path.exists():
            raise MetricExtractionError(f"Input directory does not exist: {dir_path}")
    
    # Collect all JSON files
    json_files = []
    for dir_path in input_dirs:
        json_files.extend(list(dir_path.glob("*.json")))
    
    if not json_files:
        raise MetricExtractionError("No JSON trace files found in input directories.")
    
    print(f"Processing {len(json_files)} trace files...")
    
    for file_path in json_files:
        try:
            metrics = extract_metrics_from_trace_file(file_path)
            all_metrics.append(metrics)
        except MetricExtractionError as e:
            print(f"Warning: Skipping {file_path} due to error: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Unexpected error processing {file_path}: {e}", file=sys.stderr)
    
    if not all_metrics:
        raise MetricExtractionError("Failed to extract metrics from any trace file.")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    fieldnames = [
        "trace_id", 
        "sequence_entropy", 
        "tool_repetition_frequency", 
        "argument_semantic_variance",
        "sequence_length",
        "argument_count"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_metrics:
            writer.writerow(row)
    
    print(f"Feature matrix written to {output_path}")
    print(f"Total traces processed: {len(all_metrics)}")


def main():
    """
    Entry point for the script.
    """
    config = get_config()
    
    # Define paths
    training_dir = Path(config.DATA_PATHS['training'])
    held_out_dir = Path(config.DATA_PATHS['held_out'])
    output_file = Path(config.DATA_PATHS['processed']) / "feature_matrix.csv"
    
    # Validate input data exists (T046)
    if not training_dir.exists() or not list(training_dir.glob("*.json")):
        print(f"Error: Training directory is missing or empty: {training_dir}", file=sys.stderr)
        sys.exit(1)
    
    if not held_out_dir.exists() or not list(held_out_dir.glob("*.json")):
        print(f"Error: Held-out directory is missing or empty: {held_out_dir}", file=sys.stderr)
        sys.exit(1)
    
    try:
        process_all_traces([training_dir, held_out_dir], output_file)
        
        # Validate output (T046)
        if not output_file.exists():
            raise MetricExtractionError("Output file was not created.")
        
        # Quick sanity check on content
        with open(output_file, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2: # Header + at least 1 row
                raise MetricExtractionError("Output file is empty or has no data rows.")
                
        print("Metric extraction completed successfully.")
        
    except MetricExtractionError as e:
        print(f"Metric Extraction Failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()