import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional
import numpy as np

# Import from existing utils
from utils.semantic_matcher import encode_texts, cosine_similarity
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_pilot_traces(path: Path) -> List[Dict[str, Any]]:
    """Load pilot traces from JSONL file."""
    traces = []
    if not path.exists():
        raise FileNotFoundError(f"Pilot traces file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
              traces.append(json.loads(line))
    
    if not traces:
        raise ValueError(f"No traces found in {path}")
    
    return traces

def load_pilot_labels(path: Path) -> List[Dict[str, Any]]:
    """Load pilot ground truth labels from JSONL file."""
    labels = []
    if not path.exists():
        raise FileNotFoundError(f"Pilot labels file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
              labels.append(json.loads(line))
    
    if not labels:
        raise ValueError(f"No labels found in {path}")
    
    return labels

def align_traces_and_labels(traces: List[Dict], labels: List[Dict]) -> List[Tuple[Dict, Dict]]:
    """Align traces with their corresponding ground truth labels by task_id."""
    label_map = {l['task_id']: l for l in labels}
    aligned = []
    
    for trace in traces:
        task_id = trace.get('task_id')
        if task_id and task_id in label_map:
            aligned.append((trace, label_map[task_id]))
        else:
            logger.warning(f"Skipping trace without matching label: {task_id}")
    
    if not aligned:
        raise ValueError("No aligned trace-label pairs found. Check task_id consistency.")
    
    return aligned

def compute_agreement(automated_matches: List[bool], ground_truth_labels: List[bool]) -> float:
    """Compute agreement rate between automated matches and ground truth."""
    if len(automated_matches) != len(ground_truth_labels):
        raise ValueError("Mismatch in lengths of automated matches and ground truth labels")
    
    if len(automated_matches) == 0:
        return 0.0
    
    agreements = sum(1 for a, g in zip(automated_matches, ground_truth_labels) if a == g)
    return agreements / len(automated_matches)

def tune_threshold(
    aligned_pairs: List[Tuple[Dict, Dict]],
    threshold_range: Tuple[float, float] = (0.0, 1.0),
    num_steps: int = 100
) -> Tuple[float, float, List[Tuple[float, float]]]:
    """
    Iterate cosine similarity thresholds to maximize agreement with ground truth.
    
    Args:
        aligned_pairs: List of (trace, label) tuples aligned by task_id
        threshold_range: (min, max) threshold values to search
        num_steps: Number of steps in the search grid
    
    Returns:
        Tuple of (optimal_threshold, max_agreement, history)
    """
    min_thresh, max_thresh = threshold_range
    thresholds = np.linspace(min_thresh, max_thresh, num_steps)
    
    history = []
    best_threshold = 0.5
    best_agreement = -1.0
    
    # Extract constraint mentions from labels (ground truth)
    # Assuming label format: {'task_id': ..., 'constraint_mention': True/False}
    ground_truth_mentions = [pair[1].get('constraint_mention', False) for pair in aligned_pairs]
    
    # Extract traces for encoding
    trace_texts = [pair[0].get('cot_trace', '') for pair in aligned_pairs]
    
    if not any(trace_texts):
        raise ValueError("No valid trace text found in pilot traces")
    
    logger.info(f"Encoding {len(trace_texts)} traces for semantic matching...")
    
    # Encode all traces once (efficient)
    try:
        embeddings = encode_texts(trace_texts, model_name="all-MiniLM-L6-v2")
    except Exception as e:
        logger.error(f"Failed to encode traces: {e}")
        raise
    
    # Define a reference constraint phrase to match against
    # We use the constraint from the first task as a reference, or a generic one
    # Better approach: use the constraint from the task record if available
    # For now, we assume the trace itself contains the constraint mention if labeled True
    # We need to compare each trace against a reference constraint string
    
    # Strategy: For each trace, we check if it is semantically similar to a known constraint phrase
    # Since we don't have the original constraint strings in the trace object directly here,
    # we will use the label's constraint_mention as the target and find the threshold that
    # best separates traces labeled True vs False based on their similarity to a reference.
    
    # However, the task asks to tune threshold for "automated semantic match".
    # The automated match typically compares the trace's constraint mention (if extracted)
    # against the original task constraint.
    
    # Since we are tuning threshold, we simulate the automated match:
    # We assume the "automated match" returns True if the trace is semantically similar
    # to a reference constraint string (e.g., "Find the object that is red").
    # We need the original constraint strings. Let's assume they are in the trace metadata
    # or we use a generic reference if not present.
    
    # Alternative interpretation: The pilot labels tell us if the constraint was mentioned.
    # We want to find a threshold T such that:
    #   If similarity(trace, reference_constraint) > T => Predicted Mention = True
    #   Else => Predicted Mention = False
    # And this prediction matches the ground truth (label) best.
    
    # We need the reference constraint string. Let's assume it's in the trace data or task data.
    # If not available, we cannot compute semantic similarity against a specific constraint.
    # Let's assume the trace object contains 'original_constraint' or similar.
    
    reference_constraints = []
    for pair in aligned_pairs:
        trace = pair[0]
        # Try to find constraint in trace or nested task data
        constraint = trace.get('original_constraint') or trace.get('task', {}).get('constraint')
        if constraint:
            reference_constraints.append(constraint)
        else:
            # Fallback: If no constraint string is available, we cannot compute semantic similarity.
            # This implies the pilot data structure might be missing the constraint string.
            # In a real scenario, we would fail or request the data.
            # For this implementation, we assume the constraint is present.
            raise ValueError(f"Missing 'original_constraint' in trace for task {trace.get('task_id')}")
    
    # Encode reference constraints
    ref_embeddings = encode_texts(reference_constraints, model_name="all-MiniLM-L6-v2")
    
    # Compute similarities
    # embeddings: (N, D), ref_embeddings: (N, D)
    # We want similarity between trace_i and ref_i
    similarities = cosine_similarity(embeddings, ref_embeddings)
    
    logger.info(f"Computed {len(similarities)} similarity scores. Range: [{min(similarities):.3f}, {max(similarities):.3f}]")
    
    for thresh in thresholds:
        # Automated prediction: True if similarity > thresh
        predicted_mentions = [s > thresh for s in similarities]
        
        agreement = compute_agreement(predicted_mentions, ground_truth_mentions)
        history.append((thresh, agreement))
        
        if agreement > best_agreement:
            best_agreement = agreement
            best_threshold = thresh
    
    logger.info(f"Optimal threshold: {best_threshold:.4f} with agreement: {best_agreement:.4f}")
    
    return best_threshold, best_agreement, history

def save_results(
    optimal_threshold: float,
    agreement: float,
    history: List[Tuple[float, float]],
    output_path: Path
):
    """Save tuned threshold and metrics to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        "optimal_threshold": float(optimal_threshold),
        "agreement_rate": float(agreement),
        "history": [{"threshold": float(t), "agreement": float(a)} for t, a in history],
        "num_samples": len(history),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Tune semantic matching threshold for pilot study")
    parser.add_argument(
        "--traces",
        type=str,
        default="data/pilot/pilot_traces.jsonl",
        help="Path to pilot traces JSONL"
    )
    parser.add_argument(
        "--labels",
        type=str,
        default="data/pilot/pilot_ground_truth_labels.jsonl",
        help="Path to pilot ground truth labels JSONL"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/pilot/tuned_threshold.json",
        help="Path to output threshold JSON"
    )
    parser.add_argument(
        "--threshold-min",
        type=float,
        default=0.0,
        help="Minimum threshold to search"
    )
    parser.add_argument(
        "--threshold-max",
        type=float,
        default=1.0,
        help="Maximum threshold to search"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=100,
        help="Number of steps in threshold search"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Loading pilot traces from {args.traces}")
    traces = load_pilot_traces(Path(args.traces))
    
    logger.info(f"Loading pilot labels from {args.labels}")
    labels = load_pilot_labels(Path(args.labels))
    
    logger.info("Aligning traces and labels...")
    aligned = align_traces_and_labels(traces, labels)
    logger.info(f"Aligned {len(aligned)} pairs")
    
    logger.info(f"Tuning threshold in range [{args.threshold_min}, {args.threshold_max}]...")
    optimal_thresh, best_agreement, history = tune_threshold(
        aligned,
        threshold_range=(args.threshold_min, args.threshold_max),
        num_steps=args.steps
    )
    
    logger.info(f"Saving results to {args.output}")
    save_results(optimal_thresh, best_agreement, history, Path(args.output))
    
    logger.info(f"Done. Optimal threshold: {optimal_thresh:.4f}, Agreement: {best_agreement:.4f}")

if __name__ == "__main__":
    main()
