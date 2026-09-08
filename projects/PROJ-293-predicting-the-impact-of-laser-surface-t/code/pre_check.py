import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime

# Import hygiene utilities to update artifact hashes
from hygiene import calculate_md5, load_artifact_hashes, save_artifact_hashes, update_artifact_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
THRESHOLD_NORMALIZED = 300
REPORT_PATH = Path("reports/pre_check.json")
PROCESSED_DATA_PATH = Path("data/processed/aggregated_clean.csv")
NORMALIZATION_COL = "normalization_method"

def load_aggregated_data(path: Path) -> pd.DataFrame:
    """Load the aggregated clean CSV file."""
    if not path.exists():
        raise FileNotFoundError(f"Required data file not found: {path}. "
                                "Ensure T015 has been completed successfully.")
    logger.info(f"Loading aggregated data from {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} records")
    return df

def calculate_counts(df: pd.DataFrame) -> Dict[str, int]:
    """Calculate counts for total, normalized, and raw records."""
    total_count = len(df)
    
    # Count normalized records (where normalization_method is not 'raw')
    # Assuming 'normalized' or other valid methods are not 'raw'
    normalized_mask = df[NORMALIZATION_COL] != 'raw'
    normalized_count = normalized_mask.sum()
    
    # Count raw records
    raw_count = (~normalized_mask).sum()
    
    counts = {
        "total_count": int(total_count),
        "normalized_count": int(normalized_count),
        "raw_count": int(raw_count)
    }
    
    logger.info(f"Counts - Total: {total_count}, Normalized: {normalized_count}, Raw: {raw_count}")
    return counts

def evaluate_threshold(counts: Dict[str, int]) -> Dict[str, Any]:
    """Evaluate counts against the threshold and generate status/warnings."""
    normalized_count = counts["normalized_count"]
    is_sufficient = normalized_count >= THRESHOLD_NORMALIZED
    
    status = "PASS" if is_sufficient else "FAIL"
    warnings = []
    
    if not is_sufficient:
        warning_msg = (
            f"Power limitation warning: Normalized record count ({normalized_count}) "
            f"is below the required threshold ({THRESHOLD_NORMALIZED}). "
            f"Model training may suffer from low statistical power or overfitting."
        )
        warnings.append(warning_msg)
        logger.warning(warning_msg)
    else:
        logger.info(f"Threshold check passed: {normalized_count} >= {THRESHOLD_NORMALIZED}")
    
    return {
        "status": status,
        "threshold": THRESHOLD_NORMALIZED,
        "normalized_count": normalized_count,
        "is_sufficient": is_sufficient,
        "warnings": warnings
    }

def generate_report(df: pd.DataFrame, counts: Dict[str, int], evaluation: Dict[str, Any]) -> Dict[str, Any]:
    """Generate the full pre-check report."""
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source_file": str(PROCESSED_DATA_PATH),
        "record_counts": counts,
        "threshold_evaluation": evaluation,
        "data_quality_summary": {
            "total_records": counts["total_count"],
            "normalized_records": counts["normalized_count"],
            "raw_records": counts["raw_count"],
            "missing_predictor_count": int(df.isnull().any(axis=1).sum()),
            "columns": list(df.columns)
        }
    }
    return report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the report to a JSON file and update artifact hashes."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Pre-check report saved to {output_path}")
    
    # Update artifact hash for the report
    artifact_hash = calculate_md5(output_path)
    hashes = load_artifact_hashes()
    update_artifact_hash(hashes, str(output_path), artifact_hash)
    save_artifact_hashes(hashes)
    logger.info(f"Updated artifact hash for {output_path}: {artifact_hash}")

def main() -> int:
    """Main entry point for the pre-check task."""
    try:
        # Ensure logs directory exists
        Path("logs").mkdir(parents=True, exist_ok=True)
        
        # 1. Load data (T015 output)
        df = load_aggregated_data(PROCESSED_DATA_PATH)
        
        # 2. Calculate counts
        counts = calculate_counts(df)
        
        # 3. Evaluate threshold
        evaluation = evaluate_threshold(counts)
        
        # 4. Generate report
        report = generate_report(df, counts, evaluation)
        
        # 5. Save report
        save_report(report, REPORT_PATH)
        
        # Return non-zero exit code if threshold not met (optional, depending on pipeline strictness)
        if not evaluation["is_sufficient"]:
            logger.error("Pre-check failed: Insufficient normalized data.")
            return 1
        
        logger.info("Pre-check completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        return 1
    except Exception as e:
        logger.error(f"Pre-check failed with unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
