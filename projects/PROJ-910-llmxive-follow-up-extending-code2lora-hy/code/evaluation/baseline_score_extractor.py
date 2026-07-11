"""
Extracts the baseline accuracy score from neural evaluation results.

This module implements T031a: Extract baseline accuracy score from the neural
evaluation results (T021/T024) and save to data/results/baseline_score.json.

The baseline score is derived from the neural adapter evaluation results generated
by the baseline loader (T024) and evaluation runner (T021).
"""
import json
import csv
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from evaluation.baseline_loader import load_baseline_adapter, get_baseline_adapter_path
from evaluation.runner import run_evaluation, load_repopeftbench_data, load_ast_adapter
from evaluation.comparison_report import load_scores_from_csv
from utils.config import load_config
import logging

# Set up logging
logger = logging.getLogger(__name__)

def calculate_baseline_accuracy(neural_scores_path: Path) -> float:
    """
    Calculate the baseline accuracy score from neural evaluation results.
    
    Args:
        neural_scores_path: Path to the neural scores CSV file (data/results/neural_scores.csv)
        
    Returns:
        The average exact-match score as a float (0.0 to 1.0)
        
    Raises:
        FileNotFoundError: If the neural scores file does not exist
        ValueError: If the scores file is empty or has invalid format
    """
    if not neural_scores_path.exists():
        raise FileNotFoundError(f"Neural scores file not found: {neural_scores_path}")
    
    scores = load_scores_from_csv(neural_scores_path)
    
    if not scores:
        raise ValueError(f"Neural scores file is empty: {neural_scores_path}")
    
    # Calculate average exact-match score
    total_score = sum(score for score in scores)
    accuracy = total_score / len(scores)
    
    logger.info(f"Calculated baseline accuracy from {len(scores)} tasks: {accuracy:.4f}")
    return accuracy

def save_baseline_score(accuracy: float, output_path: Path) -> None:
    """
    Save the baseline accuracy score to a JSON file.
    
    Args:
        accuracy: The baseline accuracy score (float)
        output_path: Path to save the JSON file (data/results/baseline_score.json)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    baseline_data = {
        "accuracy": accuracy,
        "source": "neural_evaluation",
        "description": "Baseline accuracy score from neural adapter evaluation",
        "metric": "exact_match"
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(baseline_data, f, indent=2)
    
    logger.info(f"Saved baseline score to {output_path}")

def extract_baseline_score(
    neural_scores_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main function to extract and save baseline accuracy score.
    
    Args:
        neural_scores_path: Path to neural scores CSV. Defaults to data/results/neural_scores.csv
        output_path: Path to output JSON. Defaults to data/results/baseline_score.json
        
    Returns:
        Dictionary containing the baseline score and metadata
    """
    config = load_config()
    
    # Set default paths if not provided
    if neural_scores_path is None:
        neural_scores_path = Path(config.data_dir) / "results" / "neural_scores.csv"
    
    if output_path is None:
        output_path = Path(config.data_dir) / "results" / "baseline_score.json"
    
    # Extract baseline accuracy
    accuracy = calculate_baseline_accuracy(neural_scores_path)
    
    # Save to JSON
    save_baseline_score(accuracy, output_path)
    
    return {
        "accuracy": accuracy,
        "output_path": str(output_path),
        "source_path": str(neural_scores_path)
    }

def main():
    """CLI entry point for baseline score extraction."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract baseline accuracy score from neural evaluation results"
    )
    parser.add_argument(
        "--neural-scores",
        type=Path,
        default=None,
        help="Path to neural scores CSV file (default: data/results/neural_scores.csv)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to output JSON file (default: data/results/baseline_score.json)"
    )
    
    args = parser.parse_args()
    
    try:
        result = extract_baseline_score(
            neural_scores_path=args.neural_scores,
            output_path=args.output
        )
        print(f"Baseline accuracy: {result['accuracy']:.4f}")
        print(f"Saved to: {result['output_path']}")
    except Exception as e:
        logger.error(f"Failed to extract baseline score: {e}")
        raise

if __name__ == "__main__":
    main()
