import json
import math
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

# Ensure project root is in path for imports
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_config
from utils.validators import MetricsValidator

# Constants
MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_VARIANCE = 0.0  # Imputation default for undefined variance

class MetricExtractionError(Exception):
    """Raised when metric extraction fails."""
    pass

def calculate_sequence_entropy(tool_sequence: List[str]) -> float:
    """
    Calculate Shannon entropy of the tool sequence.
    H = - sum(p(x) * log2(p(x)))
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
    Calculate the frequency of repeated tools.
    Defined as: (Total Length - Number of Unique Tools) / Total Length
    Range: [0, 1], where 1 means all tools are the same, 0 means all unique.
    """
    if not tool_sequence:
        return 0.0
    
    unique_count = len(set(tool_sequence))
    total_count = len(tool_sequence)
    
    if unique_count == 0:
        return 0.0
        
    return (total_count - unique_count) / total_count

def calculate_argument_variance(arguments: List[str]) -> float:
    """
    Calculate argument semantic variance using sentence embeddings.
    Variance = Mean pairwise cosine distance of all argument embeddings.
    
    If arguments list is empty or has only one element, variance is 0.0.
    """
    if not arguments or len(arguments) < 2:
        return DEFAULT_VARIANCE
    
    try:
        # Load model (cached on first call)
        model = SentenceTransformer(MODEL_NAME)
        embeddings = model.encode(arguments, show_progress_bar=False)
        
        n = len(embeddings)
        if n < 2:
            return DEFAULT_VARIANCE
        
        # Calculate mean pairwise cosine distance
        # Cosine distance = 1 - cosine_similarity
        total_distance = 0.0
        count = 0
        
        for i in range(n):
            for j in range(i + 1, n):
                # Normalize vectors for cosine similarity
                vec_i = embeddings[i]
                vec_j = embeddings[j]
                
                norm_i = np.linalg.norm(vec_i)
                norm_j = np.linalg.norm(vec_j)
                
                if norm_i == 0 or norm_j == 0:
                    continue
                
                cosine_sim = np.dot(vec_i, vec_j) / (norm_i * norm_j)
                cosine_dist = 1.0 - cosine_sim
                total_distance += cosine_dist
                count += 1
        
        if count == 0:
            return DEFAULT_VARIANCE
            
        return total_distance / count
        
    except Exception as e:
        raise MetricExtractionError(f"Failed to calculate argument variance: {e}")

def extract_metrics_for_trace(trace_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all structural metrics for a single trace.
    
    Args:
        trace_data: Dictionary containing 'exact_tool_sequence' and 'raw_arg_variance' (or raw args)
        
    Returns:
        Dictionary with computed metrics
    """
    tool_sequence = trace_data.get("exact_tool_sequence", [])
    arguments = trace_data.get("arguments", [])
    
    # If arguments are not provided as a list, try to extract from raw_arg_variance if it's a string representation
    if not arguments and "raw_arg_variance" in trace_data:
        # Fallback: if raw_arg_variance is a list of strings
        if isinstance(trace_data["raw_arg_variance"], list):
            arguments = [str(arg) for arg in trace_data["raw_arg_variance"]]
    
    sequence_entropy = calculate_sequence_entropy(tool_sequence)
    repetition_freq = calculate_tool_repetition_frequency(tool_sequence)
    arg_variance = calculate_argument_variance(arguments)
    
    return {
        "sequence_entropy": sequence_entropy,
        "tool_repetition_frequency": repetition_freq,
        "argument_semantic_variance": arg_variance,
        "trace_length": len(tool_sequence)
    }

def extract_metrics_from_trace_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a trace file and extract metrics.
    
    Args:
        file_path: Path to the JSON trace file
        
    Returns:
        Dictionary with trace_id and metrics, or None if file is invalid
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            trace_data = json.load(f)
        
        # Extract trace ID from filename or data
        trace_id = trace_data.get("trace_id", file_path.stem)
        
        metrics = extract_metrics_for_trace(trace_data)
        metrics["trace_id"] = trace_id
        
        return metrics
        
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {file_path}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return None

def process_all_traces(input_dirs: List[Path], output_path: Path) -> None:
    """
    Process all trace files in the given directories and write metrics to CSV.
    
    Args:
        input_dirs: List of directories containing trace JSON files
        output_path: Path to write the feature_matrix.csv
    """
    config = get_config()
    validator = MetricsValidator(config)
    
    all_metrics = []
    processed_count = 0
    failed_count = 0
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    for dir_path in input_dirs:
        if not dir_path.exists():
            raise FileNotFoundError(f"Input directory not found: {dir_path}")
        
        # Find all JSON files
        trace_files = list(dir_path.glob("*.json"))
        
        for trace_file in trace_files:
            result = extract_metrics_from_trace_file(trace_file)
            if result:
                # Validate against schema
                if validator.validate_metrics(result):
                    all_metrics.append(result)
                    processed_count += 1
                else:
                    print(f"Validation failed for {trace_file}", file=sys.stderr)
                    failed_count += 1
            else:
                failed_count += 1
    
    if processed_count == 0:
        raise MetricExtractionError("No valid traces were processed. Check input directories.")
    
    # Write to CSV
    fieldnames = ["trace_id", "sequence_entropy", "tool_repetition_frequency", 
                 "argument_semantic_variance", "trace_length"]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for metrics in all_metrics:
            # Ensure all fields are present
            row = {field: metrics.get(field, 0.0) for field in fieldnames}
            writer.writerow(row)
    
    print(f"Processed {processed_count} traces, {failed_count} failed.")
    print(f"Feature matrix written to {output_path}")

def main():
    """Main entry point for the metrics extraction script."""
    config = get_config()
    
    # Define input directories based on config
    training_dir = Path(config.data_training_path)
    held_out_dir = Path(config.data_held_out_path)
    
    input_dirs = [d for d in [training_dir, held_out_dir] if d.exists()]
    
    if not input_dirs:
        raise FileNotFoundError("No valid input directories found for trace data.")
    
    output_path = Path(config.data_processed_path) / "feature_matrix.csv"
    
    try:
        process_all_traces(input_dirs, output_path)
    except Exception as e:
        print(f"Fatal error in metrics extraction: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
