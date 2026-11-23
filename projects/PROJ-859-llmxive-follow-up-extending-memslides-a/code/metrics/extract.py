import json
import math
import os
import sys
import hashlib
import logging
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MetricExtractionError(Exception):
    """Raised when metric extraction fails."""
    pass

def calculate_sequence_entropy(tool_sequence: List[str]) -> float:
    if not tool_sequence:
        return 0.0
    counts = {}
    for tool in tool_sequence:
        counts[tool] = counts.get(tool, 0) + 1
    total = len(tool_sequence)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy

def calculate_tool_repetition_frequency(tool_sequence: List[str]) -> float:
    if len(tool_sequence) < 2:
        return 0.0
    repeats = 0
    for i in range(1, len(tool_sequence)):
        if tool_sequence[i] == tool_sequence[i-1]:
            repeats += 1
    return repeats / (len(tool_sequence) - 1)

def calculate_argument_variance(args_list: List[str]) -> float:
    """
    Placeholder for semantic variance. 
    In a full implementation, this would use sentence-transformers.
    For this task, we calculate a simple variance based on string uniqueness.
    """
    if not args_list:
        return 0.0
    unique = len(set(args_list))
    return unique / len(args_list) if len(args_list) > 0 else 0.0

def load_model():
    """
    Placeholder for loading sentence-transformers.
    If the library is not available, we fall back to the simple variance above.
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model
    except ImportError:
        logger.warning("sentence-transformers not found. Using simple variance calculation.")
        return None

def extract_metrics_from_trace_file(file_path: Path, model=None) -> Dict[str, Any]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            trace = json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load trace {file_path}: {e}")
        # Impute 0.0 as per T020 requirements
        return {
            'trace_id': file_path.stem,
            'sequence_entropy': 0.0,
            'tool_repetition_freq': 0.0,
            'arg_semantic_variance': 0.0
        }

    tool_sequence = trace.get('exact_tool_sequence', [])
    args_list = trace.get('raw_arg_sequence', []) # Assuming this field exists or similar

    seq_entropy = calculate_sequence_entropy(tool_sequence)
    tool_freq = calculate_tool_repetition_frequency(tool_sequence)
    
    # If model is available, use it for semantic variance
    if model is not None and args_list:
        try:
            embeddings = model.encode(args_list)
            # Calculate variance of embeddings (simplified: mean distance)
            # This is a placeholder for a real semantic variance metric
            import numpy as np
            if len(embeddings) > 1:
                mean_emb = np.mean(embeddings, axis=0)
                variance = np.mean(np.sum((embeddings - mean_emb) ** 2, axis=1))
                arg_var = float(variance)
            else:
                arg_var = 0.0
        except Exception as e:
            logger.warning(f"Failed to compute semantic variance for {file_path}: {e}. Using 0.0.")
            arg_var = 0.0
    else:
        arg_var = calculate_argument_variance(args_list)

    return {
        'trace_id': file_path.stem,
        'sequence_entropy': seq_entropy,
        'tool_repetition_freq': tool_freq,
        'arg_semantic_variance': arg_var
    }

def process_all_traces(traces_dir: Path, model=None) -> List[Dict[str, Any]]:
    metrics = []
    if not traces_dir.exists():
        raise MetricExtractionError(f"Traces directory not found: {traces_dir}")
    
    for file in traces_dir.glob("*.json"):
        m = extract_metrics_from_trace_file(file, model)
        metrics.append(m)
    return metrics

def save_feature_matrix(metrics: List[Dict[str, Any]], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['trace_id', 'sequence_entropy', 'tool_repetition_freq', 'arg_semantic_variance']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics)

def update_state_file(state_path: Path, feature_matrix_path: Path):
    if not state_path.exists():
        state = {}
    else:
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
    
    with open(feature_matrix_path, 'rb') as f:
        sha256_hash = hashlib.sha256(f.read()).hexdigest()
    
    state['derived_artifacts'] = state.get('derived_artifacts', {})
    state['derived_artifacts']['feature_matrix'] = {
        'path': str(feature_matrix_path),
        'sha256': sha256_hash,
        'timestamp': str(os.path.getmtime(feature_matrix_path))
    }
    
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)

def main():
    """
    Main entry point for T020.
    Computes structural metrics for traces and saves feature matrix.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    data_root = project_root / "data"
    
    training_dir = data_root / "training"
    held_out_dir = data_root / "held_out"
    output_path = data_root / "processed" / "feature_matrix.csv"
    state_path = data_root / "state.json"

    # Load model if available
    model = load_model()

    # Process training set
    logger.info(f"Processing training traces in {training_dir}...")
    training_metrics = process_all_traces(training_dir, model)
    
    # Process held-out set
    logger.info(f"Processing held-out traces in {held_out_dir}...")
    held_out_metrics = process_all_traces(held_out_dir, model)
    
    # Combine
    all_metrics = training_metrics + held_out_metrics
    
    if not all_metrics:
        raise MetricExtractionError("No metrics extracted. Check input directories.")

    save_feature_matrix(all_metrics, output_path)
    update_state_file(state_path, output_path)
    
    logger.info(f"Feature matrix saved to {output_path}")
    logger.info(f"SHA256 recorded in {state_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
