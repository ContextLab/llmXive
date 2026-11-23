import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.logging_config import setup_logging, create_logger
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = create_logger(__name__)
INPUT_FILE = project_root / "data" / "processed" / "alloys_raw.csv"
OUTPUT_FILE = project_root / "data" / "processed" / "completeness_report.json"

def load_processed_data() -> Optional[pd.DataFrame]:
    if not INPUT_FILE.exists():
        logger.error(f"Processed data file not found: {INPUT_FILE}")
        return None
    try:
        return pd.read_csv(INPUT_FILE)
    except Exception as e:
        logger.error(f"Error loading processed data: {e}")
        return None

def get_source_counts(df: pd.DataFrame) -> Dict[str, int]:
    if df.empty:
        return {}
    return df['source_type'].value_counts().to_dict()

def calculate_source_proportions(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    if df.empty:
        return {}
    
    sources = df['source_type'].unique()
    result = {}
    total_rows = len(df)
    
    for source in sources:
        source_df = df[df['source_type'] == source]
        total = len(source_df)
        # Assume valid_rows = total for now, or count non-null critical fields
        valid = source_df[['coercivity_oe', 'saturation_magnetization_emu_g']].notna().all(axis=1).sum()
        pct = (valid / total * 100) if total > 0 else 0.0
        
        result[source] = {
            "total_rows": total,
            "valid_rows": int(valid),
            "completeness_pct": round(pct, 2)
        }
    
    return result

def generate_completeness_report(df: pd.DataFrame) -> Dict[str, Any]:
    sources_data = calculate_source_proportions(df)
    total_rows = len(df)
    valid_rows = df[['coercivity_oe', 'saturation_magnetization_emu_g']].notna().all(axis=1).sum()
    
    report = {
        "sources": sources_data,
        "overall": {
            "total_rows": total_rows,
            "valid_rows": int(valid_rows),
            "completeness_pct": round((valid_rows / total_rows * 100) if total_rows > 0 else 0.0, 2)
        }
    }
    return report

def run_completeness_report_pipeline() -> Dict[str, Any]:
    logger.info("Running Completeness Report Pipeline (T028)...")
    df = load_processed_data()
    if df is None:
        logger.error("Cannot generate report: no processed data.")
        return {"error": "No processed data"}
    
    report = generate_completeness_report(df)
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Completeness report saved to {OUTPUT_FILE}")
    return report

def main():
    setup_logging()
    logger.info("Completeness Reporter Main Entry")
    try:
        run_completeness_report_pipeline()
        return 0
    except Exception as e:
        logger.critical(f"Completeness report failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())