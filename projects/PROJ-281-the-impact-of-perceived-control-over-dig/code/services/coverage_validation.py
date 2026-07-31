"""
Coverage Validation Service for User Story 1.

Implements logic to verify >=95% scoring coverage by comparing row counts
of preprocessed_text.csv and scoring_results.csv, generating a coverage report.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from code.config import CONFIG

logger = logging.getLogger(__name__)

def validate_coverage(
    preprocessed_path: Path,
    scoring_results_path: Path,
    threshold: float = 0.95
) -> Dict[str, Any]:
    """
    Validate that the number of scored rows is at least `threshold` * preprocessed rows.
    
    Args:
        preprocessed_path: Path to preprocessed_text.csv
        scoring_results_path: Path to scoring_results.csv
        threshold: Minimum required coverage ratio (default 0.95)
        
    Returns:
        Dictionary containing coverage statistics and pass/fail status.
    """
    logger.info(f"Validating coverage between {preprocessed_path} and {scoring_results_path}")
    
    if not preprocessed_path.exists():
        raise FileNotFoundError(f"Preprocessed file not found: {preprocessed_path}")
    if not scoring_results_path.exists():
        raise FileNotFoundError(f"Scoring results file not found: {scoring_results_path}")
        
    df_preprocessed = pd.read_csv(preprocessed_path)
    df_scoring = pd.read_csv(scoring_results_path)
    
    preprocessed_count = len(df_preprocessed)
    scoring_count = len(df_scoring)
    
    if preprocessed_count == 0:
        logger.warning("Preprocessed file is empty. Coverage cannot be calculated.")
        coverage_ratio = 0.0
    else:
        coverage_ratio = scoring_count / preprocessed_count
        
    is_valid = coverage_ratio >= threshold
    
    report = {
        "preprocessed_count": preprocessed_count,
        "scoring_count": scoring_count,
        "coverage_ratio": round(coverage_ratio, 4),
        "threshold": threshold,
        "is_valid": is_valid,
        "message": (
            f"Coverage validation {'PASSED' if is_valid else 'FAILED'}. "
            f"{scoring_count}/{preprocessed_count} rows scored ({coverage_ratio:.2%}). "
            f"Required: >= {threshold:.2%}"
        )
    }
    
    logger.info(f"Coverage validation result: {report['message']}")
    return report

def run_coverage_validation() -> Path:
    """
    Main entry point for the coverage validation pipeline.
    
    Reads paths from CONFIG, performs validation, and saves the report to
    data/processed/coverage_report.json.
    
    Returns:
        Path to the generated coverage report.
    """
    preprocessed_path = CONFIG.DATA_PROCESSED_DIR / "preprocessed_text.csv"
    scoring_results_path = CONFIG.DATA_PROCESSED_DIR / "scoring_results.csv"
    output_path = CONFIG.DATA_PROCESSED_DIR / "coverage_report.json"
    
    try:
        report = validate_coverage(
            preprocessed_path,
            scoring_results_path,
            threshold=0.95
        )
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Coverage report saved to {output_path}")
        return output_path
        
    except FileNotFoundError as e:
        logger.error(f"Validation failed due to missing file: {e}")
        raise
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {e}")
        raise
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_coverage_validation()
