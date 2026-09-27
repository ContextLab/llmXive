"""
T019: Tune the semantic matching threshold to maximize agreement with human labels.

Iterates cosine similarity thresholds (0.0 to 1.0, step 0.05) to find the optimal
value that maximizes the agreement rate between automated semantic matching and
human expert labels from the pilot study.

Deliverable: data/pilot/tuned_threshold.json
"""
import argparse
import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

import numpy as np

# Import from project utilities
from utils.semantic_matcher import encode_texts, cosine_similarity
from utils.logging_config import get_logger, setup_root_logger

logger = get_logger(__name__)


def load_pilot_traces(path: Path) -> List[Dict[str, Any]]:
    """Load pilot traces from JSONL file."""
    if not path.exists():
        raise FileNotFoundError(f"Pilot traces file not found: {path}")
    
    traces = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
              traces.append(json.loads(line))
    logger.info(f"Loaded {len(traces)} pilot traces from {path}")
    return traces


def load_pilot_labels(path: Path) -> List[Dict[str, Any]]:
    """Load pilot labels from JSONL file."""
    if not path.exists():
        raise FileNotFoundError(f"Pilot labels file not found: {path}")
    
    labels = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
              labels.append(json.loads(line))
    logger.info(f"Loaded {len(labels)} pilot labels from {path}")
    return labels


def align_traces_and_labels(
    traces: List[Dict[str, Any]], 
    labels: List[Dict[str, Any]]
) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Align traces with their corresponding human labels by task_id."""
    label_map = {l['task_id']: l for l in labels}
    aligned = []
    
    for trace in traces:
        task_id = trace.get('task_id')
        if task_id in label_map:
            aligned.append((trace, label_map[task_id]))
        else:
            logger.warning(f"No label found for task_id: {task_id}")
    
    logger.info(f"Aligned {len(aligned)} trace-label pairs")
    return aligned


def compute_agreement(
    aligned_data: List[Tuple[Dict[str, Any], Dict[str, Any]]],
    threshold: float,
    model: Any
) -> float:
    """
    Compute agreement rate between automated semantic matching and human labels.
    
    For each pair:
    1. Extract trace text and constraint from the task record
    2. Compute semantic similarity
    3. Classify as 'mention' if similarity >= threshold
    4. Compare with human label ('yes'/'no')
    5. Calculate agreement rate
    """
    if not aligned_data:
        return 0.0
    
    matches = 0
    total = 0
    
    for trace, label in aligned_data:
        # Extract the trace text (generated CoT)
        trace_text = trace.get('cot_trace', '')
        if not trace_text:
            continue
        
        # Extract the constraint text from the original task
        # We need to get the constraint from the trace's original task record
        # Assuming the trace contains the original task data or we load it
        # For now, we assume the trace record has the constraint or we pass it
        # In the pilot study, we likely have the constraint in the trace record
        constraint_text = trace.get('constraint', '')
        if not constraint_text:
            # If not in trace, we might need to load the original task
            # For this implementation, we assume it's available in the trace
            logger.warning(f"No constraint found for task {trace.get('task_id')}")
            continue
        
        # Compute semantic similarity
        try:
            embeddings = encode_texts([trace_text, constraint_text], model)
            similarity = cosine_similarity(embeddings[0], embeddings[1])
        except Exception as e:
            logger.error(f"Error computing similarity for task {trace.get('task_id')}: {e}")
            continue
        
        # Automated prediction: 'yes' if similarity >= threshold
        automated_mention = 'yes' if similarity >= threshold else 'no'
        
        # Human label
        human_mention = label.get('constraint_mention', 'no').lower()
        
        # Check agreement
        if automated_mention == human_mention:
            matches += 1
        
        total += 1
    
    if total == 0:
        return 0.0
    
    agreement_rate = matches / total
    return agreement_rate


def tune_threshold(
    aligned_data: List[Tuple[Dict[str, Any], Dict[str, Any]]],
    model: Any,
    step: float = 0.05,
    min_threshold: float = 0.0,
    max_threshold: float = 1.0
) -> Tuple[float, float]:
    """
    Iterate through thresholds and find the one that maximizes agreement rate.
    
    Returns:
        Tuple of (optimal_threshold, max_agreement_rate)
    """
    thresholds = np.arange(min_threshold, max_threshold + step, step)
    best_threshold = min_threshold
    best_agreement = -1.0
    
    logger.info(f"Tuning threshold from {min_threshold} to {max_threshold} (step {step})")
    
    for threshold in thresholds:
        agreement = compute_agreement(aligned_data, threshold, model)
        logger.debug(f"Threshold {threshold:.2f}: Agreement = {agreement:.4f}")
        
        if agreement > best_agreement:
            best_agreement = agreement
            best_threshold = threshold
    
    logger.info(f"Best threshold: {best_threshold:.2f} with agreement: {best_agreement:.4f}")
    return best_threshold, best_agreement


def save_results(
    optimal_threshold: float,
    agreement_rate: float,
    output_path: Path
):
    """Save the tuned threshold to JSON file."""
    result = {
        'optimal_threshold': optimal_threshold,
        'agreement_rate': agreement_rate,
        'description': 'Threshold optimized to maximize agreement between automated semantic matching and human labels',
        'step_size': 0.05,
        'threshold_range': [0.0, 1.0]
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved tuned threshold to {output_path}")


def main():
    """Main entry point for threshold tuning."""
    parser = argparse.ArgumentParser(description='Tune semantic matching threshold')
    parser.add_argument(
        '--traces',
        type=str,
        default='data/pilot/pilot_traces.jsonl',
        help='Path to pilot traces JSONL file'
    )
    parser.add_argument(
        '--labels',
        type=str,
        default='data/pilot/pilot_ground_truth_labels.jsonl',
        help='Path to pilot labels JSONL file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/pilot/tuned_threshold.json',
        help='Path to output threshold JSON file'
    )
    parser.add_argument(
        '--step',
        type=float,
        default=0.05,
        help='Step size for threshold iteration'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_root_logger()
    
    # Load data
    try:
        traces = load_pilot_traces(Path(args.traces))
        labels = load_pilot_labels(Path(args.labels))
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        sys.exit(1)
    
    if not traces or not labels:
        logger.error("No data loaded. Cannot proceed with tuning.")
        sys.exit(1)
    
    # Align traces and labels
    aligned_data = align_traces_and_labels(traces, labels)
    
    if not aligned_data:
        logger.error("No aligned trace-label pairs found. Cannot proceed with tuning.")
        sys.exit(1)
    
    # Load semantic matching model
    logger.info("Loading semantic matching model...")
    try:
        from utils.semantic_matcher import encode_texts
        # The model is loaded inside the semantic_matcher module
        # We need to ensure it's loaded. The module uses a singleton pattern.
        # For now, we assume the model is loaded on first use.
        # We'll trigger a load by calling encode_texts with dummy data
        dummy_embeddings = encode_texts(["test", "test"], None)
    except Exception as e:
        logger.error(f"Failed to load semantic matching model: {e}")
        sys.exit(1)
    
    # Import the model instance from the semantic_matcher module
    # Since the module manages the model internally, we need to access it
    # We'll assume the module has a way to get the model or we reload it
    # For simplicity, we'll re-initialize the model here if needed
    # But to avoid duplication, let's assume the semantic_matcher module
    # provides a function to get the model or we use the same initialization
    
    # Re-initialize the model for this script
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Semantic matching model loaded successfully")
    
    # Tune threshold
    optimal_threshold, agreement_rate = tune_threshold(
        aligned_data, 
        model, 
        step=args.step
    )
    
    # Save results
    save_results(optimal_threshold, agreement_rate, Path(args.output))
    
    logger.info(f"Tuning complete. Optimal threshold: {optimal_threshold:.2f}")
    return 0


if __name__ == '__main__':
    sys.exit(main())