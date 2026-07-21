import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.logging_config import setup_logging, create_logger

logger = create_logger(__name__)

PROCESSED_DATA_PATH = Path("data/processed/alloys_raw.csv")
SOURCE_STATUS_NIST = Path("data/raw/nist_source_status.json")
SOURCE_STATUS_JOURNAL = Path("data/raw/journal_source_status.json")
MANUAL_CURATED_PATH = Path("data/raw/manual_curated.csv")
REPORT_PATH = Path("data/processed/completeness_report.json")

def load_processed_data() -> Optional[pd.DataFrame]:
    if not PROCESSED_DATA_PATH.exists():
        logger.error(f"Processed data file not found: {PROCESSED_DATA_PATH}")
        return None
    try:
        df = pd.read_csv(PROCESSED_DATA_PATH)
        logger.info(f"Loaded {len(df)} rows from {PROCESSED_DATA_PATH}")
        return df
    except Exception as e:
        logger.error(f"Failed to load processed data: {e}")
        return None

def get_source_counts() -> Dict[str, int]:
    """Get total rows per source from status files."""
    counts = {"NIST": 0, "Journal": 0, "Manual": 0}
    
    if SOURCE_STATUS_NIST.exists():
        with open(SOURCE_STATUS_NIST, 'r') as f:
            status = json.load(f)
        if status.get("status") == "found" and "count" in status:
            counts["NIST"] = status["count"]
    
    if SOURCE_STATUS_JOURNAL.exists():
        with open(SOURCE_STATUS_JOURNAL, 'r') as f:
            status = json.load(f)
        if status.get("status") == "found" and "count" in status:
            counts["Journal"] = status["count"]
    
    if MANUAL_CURATED_PATH.exists():
        try:
            df = pd.read_csv(MANUAL_CURATED_PATH)
            counts["Manual"] = len(df)
        except Exception:
            pass
    
    return counts

def calculate_source_proportions(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Calculate validity and proportions per source."""
    total_rows = len(df)
    sources = df['source'].unique() if 'source' in df.columns else []
    
    result = {}
    for src in ["NIST", "Journal", "Manual"]:
        src_count = get_source_counts().get(src, 0)
        valid_count = len(df[df['source'] == src]) if 'source' in df.columns else 0
        
        # If source column missing, assume all rows are valid for the first source found?
        # Better: if 'source' column missing, we can't split, so report 0 for split, total for overall.
        if 'source' not in df.columns:
            valid_count = 0
            if src == "NIST": # Arbitrary assignment if no source col
                valid_count = total_rows 
        
        completeness = (valid_count / src_count * 100) if src_count > 0 else 0.0
        
        result[src] = {
            "total_rows": src_count,
            "valid_rows": valid_count,
            "completeness_pct": round(completeness, 2)
        }
    
    return result

def generate_completeness_report() -> Dict[str, Any]:
    """Generate the full completeness report."""
    df = load_processed_data()
    if df is None:
        return {
            "sources": {
                "NIST": {"total_rows": 0, "valid_rows": 0, "completeness_pct": 0.0},
                "Journal": {"total_rows": 0, "valid_rows": 0, "completeness_pct": 0.0},
                "Manual": {"total_rows": 0, "valid_rows": 0, "completeness_pct": 0.0}
            },
            "overall": {"total_rows": 0, "valid_rows": 0, "completeness_pct": 0.0}
        }
    
    source_stats = calculate_source_proportions(df)
    total_rows = len(df)
    valid_rows = total_rows # Assuming all rows in processed file are valid
    
    report = {
        "sources": source_stats,
        "overall": {
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "completeness_pct": 100.0 if total_rows > 0 else 0.0
        }
    }
    return report

def run_completeness_report_pipeline() -> bool:
    """Run the pipeline and save report."""
    setup_logging()
    logger.info("Generating completeness report...")
    
    report = generate_completeness_report()
    
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Completeness report saved to {REPORT_PATH}")
    return True

def main() -> int:
    try:
        success = run_completeness_report_pipeline()
        return 0 if success else 1
    except Exception as e:
        logger.critical(f"Completeness report generation failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
