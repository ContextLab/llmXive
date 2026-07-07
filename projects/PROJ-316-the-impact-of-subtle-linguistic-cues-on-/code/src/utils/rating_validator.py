import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import krippendorff

from src.config import get_seed

logger = logging.getLogger(__name__)

TARGET_ALPHA = 0.7

def load_ratings_for_validator(ratings_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the ratings DataFrame from the standard location if not provided.
    Expects a CSV with columns: conversation_id, authenticity_score, rater_id.
    """
    if ratings_path is None:
        ratings_path = Path("data/processed/ratings.csv")
    
    if not ratings_path.exists():
        raise FileNotFoundError(f"Ratings file not found at {ratings_path}. "
                                "Ensure T001c has been completed successfully.")
    
    df = pd.read_csv(ratings_path)
    required_cols = {"conversation_id", "authenticity_score", "rater_id"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Ratings file missing required columns: {missing}")
    
    return df

def calculate_krippendorff_alpha(df: pd.DataFrame) -> float:
    """
    Calculate Krippendorff's alpha for inter-rater reliability.
    
    The input DataFrame must be in long format with columns:
    - conversation_id: unique item identifier
    - rater_id: unique rater identifier
    - authenticity_score: the rating given (numeric)
    
    Returns the alpha coefficient.
    """
    # Pivot to wide format: rows=items, columns=raters, values=scores
    # This creates a matrix where missing ratings become NaN
    rating_matrix = df.pivot_table(
        index="conversation_id",
        columns="rater_id",
        values="authenticity_score",
        aggfunc="first"
    )
    
    # Convert to numpy array (NaNs are handled by krippendorff)
    alpha_matrix = rating_matrix.to_numpy()
    
    # Calculate alpha (metric level for continuous/interval data)
    alpha = krippendorff.alpha(
        reliability_data=alpha_matrix,
        level_of_measurement='interval'
    )
    
    return float(alpha)

def write_reliability_metrics(
    alpha_value: float,
    df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> None:
    """
    Write the reliability metrics to a JSON file.
    
    Args:
        alpha_value: The calculated Krippendorff's alpha.
        df: The original ratings DataFrame (to count items/raters).
        output_path: Path for the output JSON file. Defaults to data/derived/reliability_metrics.json.
    """
    if output_path is None:
        output_path = Path("data/derived/reliability_metrics.json")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    num_items = df["conversation_id"].nunique()
    num_raters = df["rater_id"].nunique()
    status = "PASS" if alpha_value >= TARGET_ALPHA else "FAIL"
    
    metrics = {
        "krippendorff_alpha": round(alpha_value, 4),
        "target_alpha": TARGET_ALPHA,
        "num_items": int(num_items),
        "num_raters": int(num_raters),
        "status": status
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Reliability metrics written to {output_path}")
    logger.info(f"Alpha: {alpha_value:.4f} (Target: {TARGET_ALPHA}) - Status: {status}")

def validate_ratings(reliability_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main entry point to validate ratings and calculate reliability.
    
    Args:
        reliability_path: Optional path to the reliability metrics JSON to overwrite.
    
    Returns:
        Dictionary containing the validation results.
    """
    logger.info("Starting rating validation...")
    
    # Load data
    df = load_ratings_for_validator()
    logger.info(f"Loaded {len(df)} ratings for {df['conversation_id'].nunique()} items "
                f"from {df['rater_id'].nunique()} raters.")
    
    # Calculate alpha
    alpha = calculate_krippendorff_alpha(df)
    logger.info(f"Calculated Krippendorff's Alpha: {alpha:.4f}")
    
    # Write metrics
    write_reliability_metrics(alpha, df, reliability_path)
    
    return {
        "alpha": alpha,
        "target": TARGET_ALPHA,
        "passed": alpha >= TARGET_ALPHA,
        "num_items": df["conversation_id"].nunique(),
        "num_raters": df["rater_id"].nunique()
    }

def main():
    """CLI entry point for rating validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate inter-rater reliability using Krippendorff's Alpha.")
    parser.add_argument(
        "--ratings-path",
        type=str,
        default="data/processed/ratings.csv",
        help="Path to the ratings CSV file."
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/derived/reliability_metrics.json",
        help="Path for the output reliability metrics JSON."
    )
    
    args = parser.parse_args()
    
    # Set seed for reproducibility if needed
    set_seed(get_seed())
    
    result = validate_ratings(
        reliability_path=Path(args.output_path)
    )
    
    if result["passed"]:
        print(f"Validation PASSED. Alpha: {result['alpha']:.4f} >= {result['target']}")
    else:
        print(f"Validation FAILED. Alpha: {result['alpha']:.4f} < {result['target']}")
    
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    exit(main())
