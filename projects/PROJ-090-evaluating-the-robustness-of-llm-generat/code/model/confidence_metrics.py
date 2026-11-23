import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from utils.logging import get_inference_logger
from config import ensure_directories

logger = get_inference_logger()

def compute_confidence_from_logits(
    logits: np.ndarray,
    mask: Optional[np.ndarray] = None
) -> float:
    """
    Compute a scalar confidence score (0.0 to 1.0) from model logits.
    
    Strategy: Calculate the average probability of the generated tokens.
    This serves as the model's self-reported confidence in its generation.
    
    Args:
        logits: Logits from the model (shape: [seq_len, vocab_size] or [batch, seq_len, vocab_size])
        mask: Optional boolean mask for valid tokens (True = valid)
        
    Returns:
        float: Average token probability in range [0.0, 1.0]
    """
    # Handle batch dimension if present
    if logits.ndim == 3:
        # Assume batch size 1 for single generation
        logits = logits[0]
    
    # Apply softmax to get probabilities
    # Subtract max for numerical stability
    logits_shifted = logits - np.max(logits, axis=-1, keepdims=True)
    exp_logits = np.exp(logits_shifted)
    probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)
    
    # Get the probability of the selected token at each position
    # We need to know which token was actually generated.
    # Since we don't have the generated token IDs here, we approximate
    # confidence by the maximum probability at each step (max token probability).
    # This is a standard proxy for generation confidence when token IDs aren't passed.
    max_probs = np.max(probs, axis=-1)
    
    if mask is not None:
        # Only consider valid tokens
        valid_probs = max_probs[mask]
        if len(valid_probs) == 0:
            return 0.0
        confidence = float(np.mean(valid_probs))
    else:
        confidence = float(np.mean(max_probs))
        
    # Ensure bounds [0.0, 1.0]
    return max(0.0, min(1.0, confidence))

def extract_confidence_from_inference_log(
    inference_log: Dict[str, Any]
) -> float:
    """
    Extract or compute confidence score from an inference log entry.
    
    If the log already contains a 'confidence_score', use it.
    Otherwise, compute it from 'logits' if available.
    If neither is available, return 0.5 as a neutral default.
    
    Args:
        inference_log: A single entry from inference_logs.json
        
    Returns:
        float: Confidence score in [0.0, 1.0]
    """
    if 'confidence_score' in inference_log:
        return float(inference_log['confidence_score'])
    
    if 'logits' in inference_log:
        try:
            # Convert string representation back to numpy array if needed
            logits_str = inference_log['logits']
            if isinstance(logits_str, str):
                # Simple parsing for stringified array or base64
                # For this implementation, we assume logits are stored as a list of lists
                # or a string representation that can be eval'd safely (or we skip)
                # Given the constraint of not using eval on untrusted data, 
                # we'll assume the inference engine stored it as a list.
                import ast
                logits_list = ast.literal_eval(logits_str)
                logits = np.array(logits_list, dtype=np.float32)
                return compute_confidence_from_logits(logits)
            elif isinstance(logits_str, list):
                logits = np.array(logits_str, dtype=np.float32)
                return compute_confidence_from_logits(logits)
        except Exception as e:
            logger.warning(f"Failed to parse logits for confidence: {e}")
            return 0.5
    
    # Default if no data available
    return 0.5

def compute_expected_calibration_error(
    predictions: List[Dict[str, Any]],
    n_bins: int = 10
) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Compute Expected Calibration Error (ECE) for a list of predictions.
    
    ECE measures the gap between model confidence and actual accuracy.
    Bins predictions by confidence, calculates average confidence and accuracy per bin,
    then computes weighted average absolute difference.
    
    Args:
        predictions: List of dicts with 'confidence_score' and 'status' (pass/fail)
        n_bins: Number of bins for calibration curve
        
    Returns:
        Tuple of (ECE score, list of bin statistics)
    """
    if not predictions:
        return 0.0, []
    
    # Extract confidence and accuracy
    confidences = [p['confidence_score'] for p in predictions]
    accuracies = [1.0 if p['status'] == 'pass' else 0.0 for p in predictions]
    
    # Create bins
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_stats = []
    ece = 0.0
    total_samples = len(predictions)
    
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        # Find samples in this bin
        in_bin = [
            (conf, acc) 
            for conf, acc in zip(confidences, accuracies)
            if bin_lower <= conf < bin_upper
        ]
        
        if not in_bin:
            continue
        
        bin_confidences = [c for c, _ in in_bin]
        bin_accuracies = [a for _, a in in_bin]
        
        avg_confidence = np.mean(bin_confidences)
        avg_accuracy = np.mean(bin_accuracies)
        bin_size = len(in_bin)
        
        # Calculate ECE contribution
        ece += (bin_size / total_samples) * abs(avg_confidence - avg_accuracy)
        
        bin_stats.append({
            "bin": i,
            "lower_bound": bin_lower,
            "upper_bound": bin_upper,
            "avg_confidence": round(avg_confidence, 4),
            "avg_accuracy": round(avg_accuracy, 4),
            "sample_count": bin_size,
            "gap": round(abs(avg_confidence - avg_accuracy), 4)
        })
    
    return round(ece, 4), bin_stats

def compute_ece_by_perturbation_type(
    predictions: List[Dict[str, Any]],
    perturbation_field: str = 'perturbation_type'
) -> Dict[str, Any]:
    """
    Compute ECE separately for each perturbation type.
    
    Args:
        predictions: List of predictions with perturbation_type field
        perturbation_field: Field name containing perturbation type
        
    Returns:
        Dict with ECE scores per type and overall
    """
    # Group by perturbation type
    by_type = {}
    for pred in predictions:
        ptype = pred.get(perturbation_field, 'original')
        if ptype not in by_type:
            by_type[ptype] = []
        by_type[ptype].append(pred)
    
    results = {}
    total_ece = 0.0
    total_samples = 0
    
    for ptype, preds in by_type.items():
        ece, bins = compute_expected_calibration_error(preds)
        results[ptype] = {
            "ece": ece,
            "sample_count": len(preds),
            "bins": bins
        }
        total_ece += ece * len(preds)
        total_samples += len(preds)
    
    # Overall ECE
    overall_ece = total_ece / total_samples if total_samples > 0 else 0.0
    
    return {
        "ece_by_type": {k: v["ece"] for k, v in results.items()},
        "overall_ece": round(overall_ece, 4),
        "by_type_details": results
    }

def save_calibration_report(
    predictions: List[Dict[str, Any]],
    output_path: Path,
    perturbation_field: str = 'perturbation_type'
) -> None:
    """Save calibration report to JSON file."""
    report = compute_ece_by_perturbation_type(predictions, perturbation_field)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved calibration report to {output_path}")
    logger.info(f"Overall ECE: {report['overall_ece']}")

def update_inference_logs_with_confidence(
    input_path: Path,
    output_path: Path
) -> None:
    """
    Load inference logs, ensure confidence_score is present for every entry,
    and write the updated logs back.
    
    This function implements the core requirement of T026: appending
    confidence_score and ece_bin to the inference logs.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    updated_logs = []
    for log_entry in logs:
        updated_entry = log_entry.copy()
        
        # Ensure confidence_score exists
        if 'confidence_score' not in updated_entry:
            updated_entry['confidence_score'] = extract_confidence_from_inference_log(updated_entry)
        
        # Determine ECE bin (0-9) based on confidence
        conf = updated_entry['confidence_score']
        # Bin width is 0.1, so bin index is floor(conf * 10)
        # Clamp to 0-9
        ece_bin = min(9, max(0, int(conf * 10)))
        updated_entry['ece_bin'] = ece_bin
        
        updated_logs.append(updated_entry)
    
    # Ensure output directory exists
    ensure_directories([output_path.parent])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(updated_logs, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Updated {len(updated_logs)} entries with confidence and ece_bin")
    logger.info(f"Saved to {output_path}")

def main():
    """Main entry point for confidence metrics extraction and ECE analysis."""
    input_path = Path("data/processed/inference_logs.json")
    output_path = Path("data/processed/inference_logs.json") # Overwrite as per task requirement
    report_path = Path("data/processed/calibration_report.json")
    
    ensure_directories([input_path.parent])
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Cannot proceed with confidence extraction. Ensure T021 has run.")
        return
    
    logger.info(f"Loading inference logs from {input_path}")
    
    # Update logs with confidence and ece_bin
    update_inference_logs_with_confidence(input_path, output_path)
    
    # Load updated logs for report generation
    with open(output_path, 'r', encoding='utf-8') as f:
        predictions = json.load(f)
    
    logger.info(f"Loaded {len(predictions)} predictions for calibration analysis")
    
    # Compute and save calibration report
    save_calibration_report(predictions, report_path)

if __name__ == "__main__":
    main()
