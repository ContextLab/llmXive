import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

from utils.config import get_results_dir, get_code_dir, set_seed, get_seed
from eval.metrics import calculate_r2, load_predictions_from_csv

# Configure logging
def setup_evaluator_logging() -> logging.Logger:
    logger = logging.getLogger("evaluator")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
        ))
        logger.addHandler(handler)
    return logger

def write_null_hypothesis_report(
    r2_value: float,
    threshold: float,
    status: str,
    output_path: Path
) -> None:
    """
    Writes the null hypothesis report to a JSON file.
    
    Args:
        r2_value: The calculated R² value.
        threshold: The threshold used for comparison.
        status: The status string (e.g., "rejected", "failed").
        output_path: Path to the output JSON file.
    """
    report = {
        "status": status,
        "r2_value": float(r2_value),
        "threshold": float(threshold)
    }
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logging.info(f"Null hypothesis report written to {output_path}")

def evaluate_and_check_null_hypothesis(
    predictions_path: Path,
    threshold: float = 0.2,
    output_dir: Optional[Path] = None
) -> bool:
    """
    Evaluates the model performance and checks the null hypothesis protocol.
    
    If R² < threshold, writes a report and raises SystemExit(1).
    Returns True if the null hypothesis is rejected (R² >= threshold).
    
    Args:
        predictions_path: Path to the CSV file containing predictions and true values.
        threshold: The R² threshold for the null hypothesis check.
        output_dir: Directory to write the null hypothesis report. Defaults to results/.
        
    Returns:
        bool: True if R² >= threshold, False otherwise.
        
    Raises:
        SystemExit: If R² < threshold.
    """
    logger = setup_evaluator_logging()
    logger.info(f"Loading predictions from {predictions_path}")
    
    if not predictions_path.exists():
        logger.error(f"Predictions file not found: {predictions_path}")
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")
    
    # Load predictions and calculate R²
    predictions_df = load_predictions_from_csv(predictions_path)
    
    if predictions_df.empty:
        logger.error("Predictions dataframe is empty.")
        raise ValueError("Predictions dataframe is empty.")
    
    true_values = predictions_df['true_value'].values
    pred_values = predictions_df['predicted_value'].values
    
    r2 = calculate_r2(true_values, pred_values)
    logger.info(f"Calculated R²: {r2:.4f} (Threshold: {threshold})")
    
    # Determine status
    if r2 >= threshold:
        status = "rejected"  # Null hypothesis rejected (performance is good)
        logger.info(f"Null hypothesis REJECTED: R² ({r2:.4f}) >= Threshold ({threshold})")
        return True
    else:
        status = "failed"    # Null hypothesis not rejected (performance is poor)
        logger.warning(f"Null hypothesis NOT REJECTED: R² ({r2:.4f}) < Threshold ({threshold})")
        
        # Write report
        if output_dir is None:
            output_dir = get_results_dir()
        
        report_path = output_dir / "null_hypothesis_report.json"
        write_null_hypothesis_report(r2, threshold, status, report_path)
        
        # Raise SystemExit to halt the pipeline
        raise SystemExit(1)

def main() -> None:
    """
    Main entry point for the evaluator script.
    Parses arguments, runs evaluation, and checks the null hypothesis.
    """
    parser = argparse.ArgumentParser(
        description="Evaluate model performance and check null hypothesis protocol."
    )
    parser.add_argument(
        "--predictions",
        type=str,
        required=True,
        help="Path to the predictions CSV file."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.2,
        help="R² threshold for the null hypothesis check (default: 0.2)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    
    args = parser.parse_args()
    set_seed(args.seed)
    
    predictions_path = Path(args.predictions)
    
    try:
        evaluate_and_check_null_hypothesis(
            predictions_path=predictions_path,
            threshold=args.threshold
        )
        logging.info("Evaluation completed successfully.")
    except SystemExit as e:
        # Re-raise SystemExit to ensure the pipeline fails as intended
        raise
    except Exception as e:
        logging.error(f"Evaluation failed with error: {e}")
        raise

if __name__ == "__main__":
    main()