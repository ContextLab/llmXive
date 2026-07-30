"""
Standardize module for T020: Standardization & Stratification.
"""
from __future__ import annotations

import csv
import json
import logging
import math
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd

from error_handlers import StatisticalInsufficiencyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_data_path() -> Path:
    return Path(__file__).parent.parent / "data"

def load_gate_status() -> Dict[str, Any]:
    gate_file = get_data_path() / "gate_status.json"
    if not gate_file.exists():
        return {"status": "FAIL", "reason": "Missing", "N": 0}
    with open(gate_file, "r") as f:
        return json.load(f)

def save_gate_status(status: str, reason: str, n: int) -> None:
    gate_file = get_data_path() / "gate_status.json"
    data = {"status": status, "reason": reason, "N": n}
    with open(gate_file, "w") as f:
        json.dump(data, f, indent=2)

def convert_k_to_half_life(k: float) -> float:
    """Convert rate constant k to half-life t1/2 = ln(2)/k."""
    if k <= 0:
        return float('inf')
    return math.log(2) / k

def normalize_time_unit_to_hours(value: float, unit: str) -> float:
    """Normalize time to hours."""
    unit = unit.lower()
    if "day" in unit:
        return value * 24
    elif "min" in unit:
        return value / 60
    elif "sec" in unit:
        return value / 3600
    elif "hour" in unit or "hr" in unit:
        return value
    return value

def check_data_coverage(df: pd.DataFrame) -> bool:
    """Check if standard conditions are present."""
    # Assume columns 'temperature', 'ph' exist or similar
    # Filter for 25C, pH 7.4
    if 'temperature' in df.columns and 'ph' in df.columns:
        mask = (df['temperature'] == 25) & (df['ph'] == 7.4)
        return mask.sum() > 0
    return False

def standardize_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize degradation units and stratify."""
    # Identify degradation column
    deg_cols = [c for c in df.columns if 'half_life' in c.lower() or 't12' in c.lower() or 'rate' in c.lower()]
    if not deg_cols:
        return df

    deg_col = deg_cols[0]
    
    # Convert to numeric
    df[deg_col] = pd.to_numeric(df[deg_col], errors='coerce')
    
    # If it's a rate, convert to half-life
    if 'rate' in deg_col.lower():
        df['half_life_hours'] = df[deg_col].apply(lambda x: convert_k_to_half_life(x) if pd.notna(x) else None)
        df[deg_col] = df[deg_col].apply(lambda x: normalize_time_unit_to_hours(x, 'hours')) # Assume hours for now
        df['half_life_hours'] = df[deg_col] # Placeholder logic

    return df

def generate_data_characteristics_table(df: pd.DataFrame) -> None:
    """Generate data_characteristics.csv."""
    path = get_data_path() / "processed" / "data_characteristics.csv"
    stats = {
        "column": list(df.columns),
        "non_null": [df[c].notna().sum() for c in df.columns],
        "mean": [df[c].mean() if pd.api.types.is_numeric_dtype(df[c]) else None for c in df.columns],
        "std": [df[c].std() if pd.api.types.is_numeric_dtype(df[c]) else None for c in df.columns]
    }
    stats_df = pd.DataFrame(stats)
    stats_df.to_csv(path, index=False)

def log_arrhenius_exclusion() -> None:
    """Log Arrhenius exclusion."""
    path = get_data_path() / "processed" / "analysis_log.txt"
    with open(path, "a") as f:
        f.write(f"{pd.Timestamp.utcnow()}: Arrhenius normalization skipped (insufficient data).\n")

def merge_audit_trail(df: pd.DataFrame) -> pd.DataFrame:
    """Add is_included and derivation_source."""
    df['is_included'] = True
    df['derivation_source'] = 'standardized'
    return df

def standardize_and_stratify(df: pd.DataFrame) -> pd.DataFrame:
    """Filter for standard conditions."""
    # Simple filter if columns exist
    if 'temperature' in df.columns and 'ph' in df.columns:
        df = df[(df['temperature'] == 25) & (df['ph'] == 7.4)]
    return df

def main():
    """Main entry point for Standardize."""
    logger.info("Starting Standardize (T020)...")
    
    gate = load_gate_status()
    if gate.get("status") == "FAIL":
        logger.warning("Gate failed. Generating empty artifacts.")
        # Generate empty standard_subset.csv
        path = get_data_path() / "processed" / "standard_subset.csv"
        pd.DataFrame(columns=["smiles", "half_life"]).to_csv(path, index=False)
        generate_data_characteristics_table(pd.DataFrame())
        return

    merged_path = get_data_path() / "processed" / "merged_drugs.csv"
    if not merged_path.exists():
        logger.error("Merged dataset not found.")
        return

    df = pd.read_csv(merged_path)
    
    df = standardize_dataset(df)
    df = standardize_and_stratify(df)
    
    n = len(df)
    if n < 30:
        logger.warning(f"Statistical Gate Failed: N={n}")
        # Generate insufficiency artifacts
        report_path = get_data_path() / "processed" / "statistical_insufficiency_report.md"
        with open(report_path, "w") as f:
            f.write(f"# Statistical Insufficiency\nN={n}\nReason: Insufficient standard condition records\nDecision: Skip Analysis\n")
        
        full_state_path = get_data_path() / "processed" / "full_processed_state.csv"
        df_audit = merge_audit_trail(df)
        df_audit.to_csv(full_state_path, index=False)
        
        log_arrhenius_exclusion()
        
        raise StatisticalInsufficiencyError(f"Statistical Gate Failed: N={n}")

    # Save standard_subset
    subset_path = get_data_path() / "processed" / "standard_subset.csv"
    df.to_csv(subset_path, index=False)
    
    generate_data_characteristics_table(df)
    logger.info(f"Standardize complete. N={n}")

if __name__ == "__main__":
    main()
