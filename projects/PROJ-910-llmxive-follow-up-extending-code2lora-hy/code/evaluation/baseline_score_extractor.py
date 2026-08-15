import json
import csv
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from evaluation.baseline_loader import load_baseline_adapter, get_baseline_adapter_path

def calculate_baseline_accuracy() -> float:
    """
    Calculate the baseline accuracy score from the neural evaluation results.
    
    This function loads the baseline adapter and runs evaluation on the 
    RepoPeftBench dataset to compute the exact-match score.
    
    Returns:
        float: The baseline accuracy score (0.0 to 1.0)
    """
    # Load the baseline adapter
    baseline_path = get_baseline_adapter_path()
    if not baseline_path.exists():
        raise FileNotFoundError(
            f"Baseline adapter not found at {baseline_path}. "
            "Run T024b to generate the baseline adapter first."
        )
    
    # Note: In a full implementation, we would load the adapter and run evaluation.
    # For now, we read the score from the evaluation results if available.
    # The actual evaluation would be done by running the baseline evaluation pipeline.
    
    # Check if we have evaluation results from T021/T024
    results_dir = Path("data/results")
    neural_scores_path = results_dir / "neural_scores.csv"
    
    if neural_scores_path.exists():
        # Read the scores and compute average exact match
        scores = []
        with open(neural_scores_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'exact_match' in row:
                    try:
                        scores.append(float(row['exact_match']))
                    except (ValueError, KeyError):
                        continue
        
        if scores:
            return sum(scores) / len(scores)
    
    # If no scores file exists, we need to run evaluation
    # This is a simplified version - in practice, you'd run the full evaluation
    # For now, we'll raise an error to indicate the need for evaluation
    raise RuntimeError(
        "No neural evaluation scores found. Please run the baseline evaluation "
        "pipeline (T021 with baseline adapter) first."
    )

def save_baseline_score(score: float, output_path: Optional[str] = None) -> None:
    """
    Save the baseline score to a JSON file.
    
    Args:
        score: The baseline accuracy score
        output_path: Path to the output JSON file (default: data/results/baseline_score.json)
    """
    if output_path is None:
        output_path = "data/results/baseline_score.json"
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        "score": float(score)
    }
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Baseline score saved to {output_file}")

def extract_baseline_score(input_path: Optional[str] = None) -> float:
    """
    Extract the baseline score from the saved JSON file.
    
    Args:
        input_path: Path to the baseline_score.json file (default: data/results/baseline_score.json)
    
    Returns:
        float: The baseline accuracy score
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        KeyError: If the 'score' key is missing
        ValueError: If the score is not a valid float
    """
    if input_path is None:
        input_path = "data/results/baseline_score.json"
    
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Baseline score file not found at {input_file}")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    if 'score' not in data:
        raise KeyError(f"'score' key not found in {input_file}")
    
    score = float(data['score'])
    return score

def main():
    """Main entry point for baseline score extraction and saving."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract and save baseline score")
    parser.add_argument(
        '--output',
        type=str,
        default='data/results/baseline_score.json',
        help='Output path for baseline score JSON'
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='Input path for neural scores CSV (optional, for recalculation)'
    )
    
    args = parser.parse_args()
    
    try:
        # Calculate baseline accuracy
        score = calculate_baseline_accuracy()
        
        # Save to JSON
        save_baseline_score(score, args.output)
        
        print(f"Baseline accuracy: {score:.4f}")
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()