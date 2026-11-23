"""
Coverage validation service for User Story 1.

Verifies that the anxiety scoring pipeline achieved >= 95% coverage
of valid (preprocessed) rows.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from code.config import CONFIG

logger = logging.getLogger(__name__)

class CoverageError(Exception):
    """Raised when coverage requirements are not met."""
    pass

def validate_coverage(preprocessed_path: Path, scored_path: Path) -> Dict[str, Any]:
    """
    Validate that >= 95% of preprocessed rows have corresponding anxiety scores.
    
    Args:
        preprocessed_path: Path to preprocessed_text.csv
        scored_path: Path to scoring_results.csv
        
    Returns:
        Dictionary with coverage metrics and status
        
    Raises:
        FileNotFoundError: If input files don't exist
        CoverageError: If coverage is below 95%
    """
    if not preprocessed_path.exists():
        raise FileNotFoundError(f"Preprocessed file not found: {preprocessed_path}")
    if not scored_path.exists():
        raise FileNotFoundError(f"Scored file not found: {scored_path}")
    
    # Load datasets
    df_preprocessed = pd.read_csv(preprocessed_path)
    df_scored = pd.read_csv(scored_path)
    
    # Count rows
    total_valid_rows = len(df_preprocessed)
    scored_rows = len(df_scored)
    
    if total_valid_rows == 0:
        logger.warning("No valid rows in preprocessed data")
        coverage = 0.0
    else:
        coverage = (scored_rows / total_valid_rows) * 100
    
    # Build report
    report = {
        "preprocessed_count": total_valid_rows,
        "scored_count": scored_rows,
        "coverage_percentage": round(coverage, 2),
        "threshold_percentage": 95.0,
        "status": "PASS" if coverage >= 95.0 else "FAIL",
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    logger.info(f"Coverage validation: {scored_rows}/{total_valid_rows} = {coverage:.2f}%")
    
    # Raise error if coverage insufficient
    if coverage < 95.0:
        error_msg = (
            f"Coverage {coverage:.2f}% is below required threshold of 95.0%. "
            f"Scored {scored_rows} of {total_valid_rows} valid rows."
        )
        raise CoverageError(error_msg)
    
    return report

def run_coverage_validation(
    preprocessed_path: Optional[Path] = None,
    scored_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run coverage validation with default paths from config.
    
    Args:
        preprocessed_path: Path to preprocessed_text.csv (default from CONFIG)
        scored_path: Path to scoring_results.csv (default from CONFIG)
        output_path: Path to save coverage_report.json (default from CONFIG)
        
    Returns:
        Coverage report dictionary
    """
    if preprocessed_path is None:
        preprocessed_path = CONFIG.PROCESSED_DIR / "preprocessed_text.csv"
    if scored_path is None:
        scored_path = CONFIG.PROCESSED_DIR / "scoring_results.csv"
    if output_path is None:
        output_path = CONFIG.PROCESSED_DIR / "coverage_report.json"
    
    logger.info(f"Validating coverage between {preprocessed_path} and {scored_path}")
    
    report = validate_coverage(preprocessed_path, scored_path)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Coverage report saved to {output_path}")
    
    return report

def main():
    """CLI entry point for coverage validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate anxiety scoring coverage")
    parser.add_argument(
        "--preprocessed",
        type=Path,
        default=None,
        help="Path to preprocessed_text.csv"
    )
    parser.add_argument(
        "--scored",
        type=Path,
        default=None,
        help="Path to scoring_results.csv"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to save coverage_report.json"
    )
    
    args = parser.parse_args()
    
    try:
        report = run_coverage_validation(
            preprocessed_path=args.preprocessed,
            scored_path=args.scored,
            output_path=args.output
        )
        print(json.dumps(report, indent=2))
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except CoverageError as e:
        logger.error(str(e))
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
