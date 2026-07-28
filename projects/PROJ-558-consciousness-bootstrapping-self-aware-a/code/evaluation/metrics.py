import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.preprocessing import label_binarize
from scipy.stats import entropy
from utils.logging import get_logger
import json
import os

logger = get_logger(__name__)

def calculate_self_consistency(predictions: List[List[str]], ground_truth: List[str]) -> float:
    """
    Calculate self-consistency score based on majority vote.
    
    Args:
        predictions: List of lists, where each inner list contains multiple reasoning paths for a question
        ground_truth: List of correct answers for each question
    
    Returns:
        Self-consistency score (fraction of questions where majority vote matches ground truth)
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Number of prediction sets must match number of ground truth items")
    
    correct_count = 0
    total = len(predictions)
    
    for paths, truth in zip(predictions, ground_truth):
        if not paths:
            continue
        # Count occurrences of each answer
        vote_counts = {}
        for path in paths:
            # Extract answer from path (simplified: assume last line or specific format)
            # In practice, this would parse the actual answer format
            answer = path.strip().split('\n')[-1]
            vote_counts[answer] = vote_counts.get(answer, 0) + 1
        
        # Get majority vote
        majority_answer = max(vote_counts, key=vote_counts.get)
        if majority_answer == truth.strip():
            correct_count += 1
    
    return correct_count / total if total > 0 else 0.0

def calculate_roc_auc(true_labels: List[int], predicted_scores: List[float]) -> float:
    """
    Calculate ROC-AUC score for binary classification.
    
    Args:
        true_labels: List of binary labels (0 or 1)
        predicted_scores: List of predicted confidence scores (0.0 to 1.0)
    
    Returns:
        ROC-AUC score
    """
    if len(true_labels) != len(predicted_scores):
        raise ValueError("True labels and predicted scores must have same length")
    
    if len(set(true_labels)) < 2:
        logger.warning("Only one class present in true labels, returning 0.5 for ROC-AUC")
        return 0.5
    
    return roc_auc_score(true_labels, predicted_scores)

def calculate_brier_score(true_labels: List[int], predicted_probabilities: List[float]) -> float:
    """
    Calculate Brier score for probability predictions.
    
    Args:
        true_labels: List of binary labels (0 or 1)
        predicted_probabilities: List of predicted probabilities (0.0 to 1.0)
    
    Returns:
        Brier score (lower is better)
    """
    if len(true_labels) != len(predicted_probabilities):
        raise ValueError("True labels and predicted probabilities must have same length")
    
    return brier_score_loss(true_labels, predicted_probabilities)

def calculate_ece(true_labels: List[int], predicted_probabilities: List[float], n_bins: int = 10) -> float:
    """
    Calculate Expected Calibration Error (ECE).
    
    Args:
        true_labels: List of binary labels (0 or 1)
        predicted_probabilities: List of predicted probabilities (0.0 to 1.0)
        n_bins: Number of bins for calibration (default: 10)
    
    Returns:
        Expected Calibration Error
    """
    if len(true_labels) != len(predicted_probabilities):
        raise ValueError("True labels and predicted probabilities must have same length")
    
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total_samples = len(true_labels)
    
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        # Find samples in this bin
        in_bin = (predicted_probabilities >= bin_lower) & (predicted_probabilities < bin_upper)
        if i == n_bins - 1:  # Include upper bound for last bin
            in_bin = (predicted_probabilities >= bin_lower) & (predicted_probabilities <= bin_upper)
        
        bin_size = np.sum(in_bin)
        
        if bin_size > 0:
            bin_accuracy = np.mean(np.array(true_labels)[in_bin])
            bin_confidence = np.mean(np.array(predicted_probabilities)[in_bin])
            ece += (bin_size / total_samples) * np.abs(bin_accuracy - bin_confidence)
    
    return ece

def calculate_calibration_curve(true_labels: List[int], predicted_probabilities: List[float], n_bins: int = 10) -> Dict[str, Any]:
    """
    Calculate calibration curve data for error detection.
    
    Args:
        true_labels: List of binary labels (0 = correct, 1 = error)
        predicted_probabilities: List of predicted error probabilities (0.0 to 1.0)
        n_bins: Number of bins (default: 10)
    
    Returns:
        Dictionary with bin_edges, bin_counts, and observed_accuracies
    """
    if len(true_labels) != len(predicted_probabilities):
        raise ValueError("True labels and predicted probabilities must have same length")
    
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_counts = []
    observed_accuracies = []
    
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        # Find samples in this bin
        in_bin = (predicted_probabilities >= bin_lower) & (predicted_probabilities < bin_upper)
        if i == n_bins - 1:  # Include upper bound for last bin
            in_bin = (predicted_probabilities >= bin_lower) & (predicted_probabilities <= bin_upper)
        
        bin_size = np.sum(in_bin)
        bin_counts.append(int(bin_size))
        
        if bin_size > 0:
            # Accuracy within bin (fraction of correct answers)
            # true_labels: 0 = correct, 1 = error, so accuracy = 1 - mean(error_rate)
            bin_error_rate = np.mean(np.array(true_labels)[in_bin])
            bin_accuracy = 1.0 - bin_error_rate
            observed_accuracies.append(float(bin_accuracy))
        else:
            observed_accuracies.append(0.0)
    
    return {
        "bin_edges": bin_boundaries.tolist(),
        "bin_counts": bin_counts,
        "observed_accuracies": observed_accuracies
    }

def calculate_entropy(probabilities: List[float]) -> float:
    """
    Calculate entropy of a probability distribution.
    
    Args:
        probabilities: List of probabilities (must sum to 1)
    
    Returns:
        Entropy value
    """
    if not probabilities:
        return 0.0
    
    # Filter out zeros to avoid log(0)
    p = np.array([p for p in probabilities if p > 0])
    if len(p) == 0:
        return 0.0
    
    return float(entropy(p))

def aggregate_metrics(
    self_consistency: float,
    roc_auc: float,
    brier_score: float,
    ece: float,
    calibration_curve: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate all metrics into a single dictionary.
    
    Args:
        self_consistency: Self-consistency score
        roc_auc: ROC-AUC score
        brier_score: Brier score
        ece: Expected Calibration Error
        calibration_curve: Calibration curve data
    
    Returns:
        Dictionary containing all metrics
    """
    return {
        "self_consistency": self_consistency,
        "roc_auc": roc_auc,
        "brier_score": brier_score,
        "ece": ece,
        "calibration_curve": calibration_curve
    }

def calculate_error_detection_calibration(
    error_flags: List[int],
    confidence_scores: List[float],
    n_bins: int = 10
) -> Dict[str, Any]:
    """
    Calculate error detection calibration by correlating predicted error probability
    with actual correctness.
    
    Args:
        error_flags: List of binary flags (0 = correct, 1 = error) from model's classification head
        confidence_scores: List of confidence scores (predicted error probabilities) from model
        n_bins: Number of bins for calibration (default: 10)
    
    Returns:
        Dictionary with bin_edges, bin_counts, predicted_error_rates, and observed_error_rates
    """
    if len(error_flags) != len(confidence_scores):
        raise ValueError("Error flags and confidence scores must have same length")
    
    if len(error_flags) == 0:
        logger.warning("No data provided for error detection calibration")
        return {
            "bin_edges": [i/10 for i in range(11)],
            "bin_counts": [0] * 11,
            "predicted_error_rates": [0.0] * 11,
            "observed_error_rates": [0.0] * 11
        }
    
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_counts = []
    predicted_error_rates = []
    observed_error_rates = []
    
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        # Find samples in this bin
        in_bin = (np.array(confidence_scores) >= bin_lower) & (np.array(confidence_scores) < bin_upper)
        if i == n_bins - 1:  # Include upper bound for last bin
            in_bin = (np.array(confidence_scores) >= bin_lower) & (np.array(confidence_scores) <= bin_upper)
        
        bin_size = int(np.sum(in_bin))
        bin_counts.append(bin_size)
        
        if bin_size > 0:
            # Predicted error rate: average of confidence scores in this bin
            avg_predicted_error = np.mean(np.array(confidence_scores)[in_bin])
            predicted_error_rates.append(float(avg_predicted_error))
            
            # Observed error rate: fraction of actual errors in this bin
            avg_observed_error = np.mean(np.array(error_flags)[in_bin])
            observed_error_rates.append(float(avg_observed_error))
        else:
            predicted_error_rates.append(0.0)
            observed_error_rates.append(0.0)
    
    return {
        "bin_edges": bin_boundaries.tolist(),
        "bin_counts": bin_counts,
        "predicted_error_rates": predicted_error_rates,
        "observed_error_rates": observed_error_rates
    }

def save_calibration_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save calibration results to a JSON file.
    
    Args:
        results: Dictionary containing calibration results
        output_path: Path to save the JSON file
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Calibration results saved to {output_path}")

def main():
    """
    Main function to demonstrate error detection calibration.
    This would typically be called by run_benchmarks.py after evaluation.
    """
    logger.info("Error Detection Calibration Module Loaded")
    logger.info("Use calculate_error_detection_calibration() to compute calibration metrics")
    logger.info("Use save_calibration_results() to save results to JSON")

if __name__ == "__main__":
    main()
