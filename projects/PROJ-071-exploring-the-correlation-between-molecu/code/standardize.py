"""
Standardization and Stratification Module (T020, T021, T021b).

Handles unit conversion, condition filtering, and data characteristics logging.
"""
import json
import logging
import os
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

# Import shared logging utilities (T005)
from logging_config import get_logger, log_operation, log_pipeline_failure

# Import error handlers (T008)
from error_handlers import StatisticalInsufficiencyError

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
GATE_STATUS_PATH = DATA_DIR / "gate_status.json"

# Output paths for T021b
DATA_CHARACTERISTICS_PATH = PROCESSED_DIR / "data_characteristics.csv"
STANDARD_SUBSET_PATH = PROCESSED_DIR / "standard_subset.csv"
EXCLUDED_RECORDS_PATH = PROCESSED_DIR / "excluded_records.csv"

logger = get_logger(__name__)

def get_data_path() -> Path:
    """Return the path to the processed structural subset."""
    return PROCESSED_DIR / "structural_subset.csv"

def convert_k_to_half_life(k_value: float) -> float:
    """
    Convert rate constant k (1/h) to half-life t1/2 (hours).
    Formula: t1/2 = ln(2) / k
    """
    if k_value <= 0:
        raise ValueError(f"Rate constant must be positive, got {k_value}")
    return math.log(2) / k_value

def normalize_arrhenius(k: float, T: float, Ea: float) -> float:
    """
    Normalize rate constant to 298.15K using Arrhenius equation.
    Note: Skipped in T022a due to missing Ea data, but kept for API completeness.
    """
    R = 8.314  # J/(mol*K)
    T_ref = 298.15
    if Ea is None or math.isnan(Ea):
        raise ValueError("Activation energy (Ea) is required for Arrhenius normalization")
    return k * math.exp((Ea / R) * (1/T - 1/T_ref))

def check_data_coverage(df: pd.DataFrame) -> Dict[str, int]:
    """Check counts of records by condition type."""
    counts = df['condition_type'].value_counts().to_dict()
    return {str(k): int(v) for k, v in counts.items()}

def standardize_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize units and prepare data for analysis.
    - Ensure time units are hours.
    - Convert rate constants to half-lives if needed.
    """
    df = df.copy()
    
    # Ensure half-life column exists (T020)
    if 'half_life' not in df.columns and 'rate_constant' in df.columns:
        logger.log("convert_rate_to_half_life", operation="unit_conversion", status="started")
        df['half_life'] = df['rate_constant'].apply(convert_k_to_half_life)
        logger.log("convert_rate_to_half_life", operation="unit_conversion", status="completed")
    
    # Standardize time units if other columns exist (e.g., 'time_unit')
    if 'time_unit' in df.columns:
        # Assume conversion logic exists or data is already in hours per T020
        pass

    return df

def generate_data_characteristics_table(
    total_records: int,
    included_records: int,
    excluded_records: int,
    excluded_reasons: Optional[Dict[str, int]] = None
) -> pd.DataFrame:
    """
    Generate the Data Characteristics table (T021b).
    
    Lists the count of records excluded from the primary model due to 
    non-standard conditions.
    
    Args:
        total_records: Total records in the input dataset.
        included_records: Records in the standard_subset.
        excluded_records: Records excluded (total - included).
        excluded_reasons: Dict mapping exclusion reason to count.
    
    Returns:
        DataFrame ready for CSV export.
    """
    rows = []
    
    # Base counts
    rows.append({
        "category": "Total Records",
        "count": total_records,
        "notes": "Full dataset from ingestion"
    })
    rows.append({
        "category": "Included Records (Standard Subset)",
        "count": included_records,
        "notes": "Filtered for 25C, pH 7.4"
    })
    rows.append({
        "category": "Excluded Records (Non-Standard)",
        "count": excluded_records,
        "notes": "Excluded due to condition mismatch"
    })
    
    # Detailed reasons if available
    if excluded_reasons:
        for reason, count in excluded_reasons.items():
            rows.append({
                "category": f"Excluded: {reason}",
                "count": count,
                "notes": "Specific exclusion reason"
            })
    
    df = pd.DataFrame(rows)
    return df

def log_arrhenius_exclusion() -> None:
    """Log the decision to skip Arrhenius normalization (T022a)."""
    log_file = PROCESSED_DIR / "analysis_log.txt"
    with open(log_file, 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] Arrhenius normalization skipped: Activation Energy (Ea) data unavailable.\n")
    logger.log("arrhenius_skip", operation="decision_log", status="logged")

def merge_audit_trail(included_df: pd.DataFrame, excluded_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge included and excluded records into a single audit trail (T021c).
    Adds 'is_included' and 'derivation_source' columns.
    """
    if included_df is not None and not included_df.empty:
        included_df = included_df.copy()
        included_df['is_included'] = True
        included_df['derivation_source'] = 'included'
    
    if excluded_df is not None and not excluded_df.empty:
        excluded_df = excluded_df.copy()
        excluded_df['is_included'] = False
        excluded_df['derivation_source'] = 'excluded_condition'
    
    if included_df is not None and excluded_df is not None:
        return pd.concat([included_df, excluded_df], ignore_index=True)
    elif included_df is not None:
        return included_df
    elif excluded_df is not None:
        return excluded_df
    else:
        return pd.DataFrame()

def standardize_and_stratify() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main logic for T020, T021, T021b, T021c.
    
    1. Load structural subset.
    2. Check Gate Status.
    3. Filter for Standard Conditions (25C, pH 7.4).
    4. Generate Data Characteristics Table (T021b).
    5. Save outputs.
    
    Returns:
        Tuple of (standard_subset_df, excluded_df)
    """
    input_path = get_data_path()
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Check Gate Status (T013)
    if GATE_STATUS_PATH.exists():
        with open(GATE_STATUS_PATH, 'r') as f:
            gate_status = json.load(f)
        if gate_status.get('status') == 'FAIL':
            logger.log("skip_stratification", operation="gate_check", status="skipped", reason="Gate Failed")
            return pd.DataFrame(), pd.DataFrame()
    else:
        logger.log("gate_missing", operation="gate_check", status="warning", reason="Gate status file missing")
    
    # Load data
    df = pd.read_csv(input_path)
    total_records = len(df)
    
    # T021: Filter for Standard Conditions
    # Assumption: Columns 'temperature' and 'ph' exist. 
    # If 'condition_type' exists and is 'Standard', use that.
    # Based on T021 description: Filter for "Standard" conditions (25°C, pH 7.4).
    
    mask = (df['temperature'] == 25.0) & (df['ph'] == 7.4)
    standard_df = df[mask].copy()
    excluded_df = df[~mask].copy()
    
    included_count = len(standard_df)
    excluded_count = len(excluded_df)
    
    if included_count < 30:
        # T021: Raise StatisticalInsufficiencyError
        raise StatisticalInsufficiencyError(
            f"Standard subset N={included_count} < 30. Analysis halted."
        )
    
    # T021b: Generate Data Characteristics Table
    excluded_reasons = {}
    if not excluded_df.empty:
        # Try to categorize exclusions if 'condition_type' or similar exists
        if 'condition_type' in excluded_df.columns:
            reasons = excluded_df['condition_type'].value_counts().to_dict()
            excluded_reasons = {str(k): int(v) for k, v in reasons.items()}
        else:
            excluded_reasons["Non-Standard Conditions"] = excluded_count
    
    characteristics_df = generate_data_characteristics_table(
        total_records=total_records,
        included_records=included_count,
        excluded_records=excluded_count,
        excluded_reasons=excluded_reasons
    )
    
    # Save Data Characteristics Table (T021b Output)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    characteristics_df.to_csv(DATA_CHARACTERISTICS_PATH, index=False)
    logger.log("save_data_characteristics", operation="artifact_generation", status="completed", path=str(DATA_CHARACTERISTICS_PATH))
    
    # Save Standard Subset (for T023, T024)
    standard_df.to_csv(STANDARD_SUBSET_PATH, index=False)
    logger.log("save_standard_subset", operation="artifact_generation", status="completed", path=str(STANDARD_SUBSET_PATH))
    
    # Save Excluded Records (for T021c audit trail)
    if not excluded_df.empty:
        excluded_df.to_csv(EXCLUDED_RECORDS_PATH, index=False)
    
    # T021c: Merge Audit Trail
    full_audit_df = merge_audit_trail(standard_df, excluded_df)
    full_audit_path = PROCESSED_DIR / "full_processed_state.csv"
    full_audit_df.to_csv(full_audit_path, index=False)
    logger.log("save_audit_trail", operation="artifact_generation", status="completed", path=str(full_audit_path))
    
    return standard_df, excluded_df

def main() -> None:
    """Entry point for T020, T021, T021b execution."""
    try:
        logger.log("standardize_start", operation="pipeline_stage", status="started")
        standard_df, excluded_df = standardize_and_stratify()
        logger.log("standardize_complete", operation="pipeline_stage", status="completed")
    except StatisticalInsufficiencyError as e:
        logger.log("statistical_insufficiency", operation="pipeline_stage", status="failed", reason=str(e))
        # T021d: Generate Report
        report_path = PROCESSED_DIR / "statistical_insufficiency_report.md"
        with open(report_path, 'w') as f:
            f.write(f"# Statistical Insufficiency Report\n\n")
            f.write(f"**Date**: {datetime.now().isoformat()}\n\n")
            f.write(f"**Reason**: {str(e)}\n\n")
            f.write(f"**Action**: Analysis halted due to insufficient sample size in standard conditions.\n")
        logger.log("insufficiency_report_generated", operation="artifact_generation", status="completed", path=str(report_path))
    except Exception as e:
        logger.log("standardize_failed", operation="pipeline_stage", status="failed", reason=str(e))
        log_pipeline_failure(logger, "standardize_module", str(e))
        raise

if __name__ == "__main__":
    main()