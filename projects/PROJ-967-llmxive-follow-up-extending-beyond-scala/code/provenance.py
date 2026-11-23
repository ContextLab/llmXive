import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

def setup_logging(log_file: str = "data/raw/provenance_verification.log"):
    """Configure logging for the provenance verification process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode="w"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)

def load_dataset(filepath: str, logger: logging.Logger) -> pd.DataFrame:
    """Load the dataset from the specified path."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found: {filepath}")
    
    logger.info(f"Loading dataset from {filepath}")
    try:
        df = pd.read_parquet(filepath)
        logger.info(f"Loaded {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def verify_provenance_independence(df: pd.DataFrame, logger: logging.Logger) -> dict:
    """
    Verify that human_annotations are generated independently of teacher_scores.
    
    This function checks if human_annotations can be predicted from teacher_scores.
    If they are independent, the correlation should be near zero and a simple
    linear regression should yield very poor R^2 scores.
    
    Returns a dict with verification results.
    """
    logger.info("Starting provenance independence verification")
    
    # Ensure required columns exist
    required_cols = ["teacher_scores", "student_scalar", "human_annotations"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Expand list columns into separate columns for analysis
    # teacher_scores: list of 4 floats
    # human_annotations: list of 4 floats
    teacher_cols = [f"teacher_{i}" for i in range(4)]
    human_cols = [f"human_{i}" for i in range(4)]
    
    teacher_matrix = np.array(df["teacher_scores"].tolist())
    human_matrix = np.array(df["human_annotations"].tolist())
    
    # Flatten for correlation analysis
    teacher_flat = teacher_matrix.flatten()
    human_flat = human_matrix.flatten()
    
    # Calculate correlation matrix
    logger.info("Calculating correlation between teacher scores and human annotations")
    correlations = []
    for i in range(4):
        for j in range(4):
            corr = np.corrcoef(teacher_flat, human_flat)[0, 1]
            correlations.append({
                "teacher_dimension": i,
                "human_dimension": j,
                "correlation": float(corr)
            })
    
    # Perform linear regression test
    # If human_annotations depend on teacher_scores, R^2 should be significant
    logger.info("Performing linear regression test for dependency")
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score
    
    # Test 1: Can teacher_scores predict human_annotations?
    X = teacher_matrix.reshape(teacher_matrix.shape[0], -1)  # Flatten to (n_samples, 4)
    y = human_matrix.flatten()
    
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    
    # Test 2: Check if student_scalar predicts human_annotations (should be independent)
    X_student = df["student_scalar"].values.reshape(-1, 1)
    model_student = LinearRegression()
    model_student.fit(X_student, y)
    y_pred_student = model_student.predict(X_student)
    r2_student = r2_score(y, y_pred_student)
    
    # Verification result
    is_independent = r2 < 0.01 and r2_student < 0.01
    
    result = {
        "verification_passed": is_independent,
        "teacher_human_correlations": correlations,
        "linear_regression_r2_from_teacher": float(r2),
        "linear_regression_r2_from_student_scalar": float(r2_student),
        "sample_count": len(df),
        "message": "Human annotations are independent of teacher scores" if is_independent 
                  else "WARNING: Human annotations show dependency on teacher scores"
    }
    
    logger.info(f"Verification result: {result['message']}")
    logger.info(f"R² from teacher scores: {r2:.6f}")
    logger.info(f"R² from student scalar: {r2_student:.6f}")
    
    return result

def save_verification_report(result: dict, output_path: str, logger: logging.Logger):
    """Save the verification report to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    logger.info(f"Verification report saved to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Verify data provenance independence")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/raw/oxford_pets_simulated.parquet",
        help="Path to the input dataset"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/provenance_verification_report.json",
        help="Path to save the verification report"
    )
    parser.add_argument(
        "--log",
        type=str,
        default="data/raw/provenance_verification.log",
        help="Path to the log file"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging(args.log)
    
    try:
        # Load dataset
        df = load_dataset(args.input, logger)
        
        # Verify provenance independence
        result = verify_provenance_independence(df, logger)
        
        # Save report
        save_verification_report(result, args.output, logger)
        
        # Exit with appropriate code
        if result["verification_passed"]:
            logger.info("Provenance verification PASSED")
            sys.exit(0)
        else:
            logger.error("Provenance verification FAILED")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Provenance verification failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
