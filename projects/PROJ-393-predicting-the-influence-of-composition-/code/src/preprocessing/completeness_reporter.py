import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.logging_config import setup_logging

logger = setup_logging("completeness_reporter", logging.INFO)

# SC-004: Data Completeness Report
# Reports data proportions per source (NIST, Journal, Manual)

def load_processed_data(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the preprocessed alloys dataset.
    Expected path: data/processed/alloys_raw.csv
    """
    if data_path is None:
        data_path = Path("data/processed/alloys_raw.csv")
    
    if not data_path.exists():
        raise FileNotFoundError(
            f"Processed data file not found at {data_path}. "
            "Run the preprocessing pipeline (T027) first."
        )
    
    logger.info(f"Loading processed data from {data_path}")
    df = pd.read_csv(data_path)
    return df

def calculate_source_proportions(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Calculate total rows, valid rows, and completeness percentage per source.
    
    A row is considered 'valid' if it has non-null values for key hysteresis parameters:
    - coercivity_oe
    - saturation_magnetization_emu_g
    
    Returns a dictionary structure matching SC-004 requirements.
    """
    sources = ["NIST", "Journal", "Manual"]
    results = {}
    
    # Define key columns for validity check
    # Based on the schema in T010, these are the critical hysteresis fields
    validity_columns = ["coercivity_oe", "saturation_magnetization_emu_g"]
    
    for source in sources:
        # Filter rows for this source
        # The 'source_type' column is expected to contain the source name
        source_df = df[df['source_type'].str.lower() == source.lower()]
        
        total_rows = len(source_df)
        
        # Check validity: all key columns must be non-null
        if total_rows > 0:
            # Ensure columns exist before checking
            valid_mask = pd.Series([True] * total_rows, index=source_df.index)
            for col in validity_columns:
                if col in source_df.columns:
                    valid_mask &= source_df[col].notna()
                else:
                    logger.warning(f"Column {col} not found in dataframe for source {source}")
            
            valid_rows = valid_mask.sum()
        else:
            valid_rows = 0
        
        completeness_pct = (valid_rows / total_rows * 100) if total_rows > 0 else 0.0
        
        results[source] = {
            "total_rows": int(total_rows),
            "valid_rows": int(valid_rows),
            "completeness_pct": round(completeness_pct, 2)
        }
        
        logger.info(f"Source {source}: {total_rows} total, {valid_rows} valid, {completeness_pct:.2f}% complete")
    
    return results

def generate_completeness_report(
    source_stats: Dict[str, Dict[str, Any]],
    df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Generate the final completeness report structure per SC-004.
    """
    total_rows = len(df)
    
    # Calculate overall validity
    validity_columns = ["coercivity_oe", "saturation_magnetization_emu_g"]
    valid_mask = pd.Series([True] * total_rows, index=df.index)
    for col in validity_columns:
        if col in df.columns:
            valid_mask &= df[col].notna()
    
    overall_valid_rows = valid_mask.sum()
    overall_completeness = (overall_valid_rows / total_rows * 100) if total_rows > 0 else 0.0
    
    report = {
        "sources": source_stats,
        "overall": {
            "total_rows": int(total_rows),
            "valid_rows": int(overall_valid_rows),
            "completeness_pct": round(overall_completeness, 2)
        }
    }
    
    return report

def run_completeness_report_pipeline(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the full pipeline to generate the completeness report.
    """
    if input_path is None:
        input_path = Path("data/processed/alloys_raw.csv")
    
    if output_path is None:
        output_path = Path("data/processed/completeness_report.json")
    
    logger.info("Starting completeness report generation (SC-004)")
    
    # 1. Load data
    df = load_processed_data(input_path)
    
    # 2. Calculate proportions
    source_stats = calculate_source_proportions(df)
    
    # 3. Generate report
    report = generate_completeness_report(source_stats, df)
    
    # 4. Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Completeness report saved to {output_path}")
    return report

def main():
    """
    Entry point for the script.
    """
    try:
        report = run_completeness_report_pipeline()
        print(json.dumps(report, indent=2))
    except Exception as e:
        logger.error(f"Failed to generate completeness report: {e}")
        raise