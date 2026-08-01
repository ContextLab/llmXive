"""
Standardization & Stratification Module (T020)

Implements:
1. Read data/gate_status.json. If FAIL, generate empty artifacts and exit.
2. If PASS, convert rates, standardize units, stratify for "Standard" conditions.
3. Gate Check: If N < 30, trigger T020b logic (write stat_gate_status.json FAIL).
4. If N >= 30, save standard_subset and data_characteristics.csv, write stat_gate_status.json PASS.
"""
from __future__ import annotations

import csv
import json
import logging
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_config
from logging_config import get_logger, log_operation

logger = get_logger(__name__)

def get_data_path() -> Path:
    return PROJECT_ROOT / "data"

def load_gate_status() -> Optional[Dict[str, Any]]:
    """Load data/gate_status.json."""
    path = get_data_path() / "gate_status.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_stat_gate_status(status: Dict[str, Any]) -> None:
    """Save data/stat_gate_status.json."""
    path = get_data_path() / "stat_gate_status.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

def convert_k_to_half_life(k: float) -> Optional[float]:
    """Convert rate constant k (1/h) to half-life t1/2 (h)."""
    if k <= 0:
        return None
    return math.log(2) / k

def normalize_time_unit_to_hours(value: float, unit: str) -> float:
    """Normalize time value to hours."""
    unit = unit.lower()
    if unit in ["h", "hour", "hours"]:
        return value
    elif unit in ["d", "day", "days"]:
        return value * 24
    elif unit in ["min", "minute", "minutes"]:
        return value / 60
    elif unit in ["s", "sec", "second", "seconds"]:
        return value / 3600
    else:
        # Assume hours if unknown
        return value

def check_data_coverage(df: List[Dict]) -> Tuple[int, int]:
    """Count total records and records with degradation data."""
    total = len(df)
    with_data = sum(1 for row in df if row.get("half_life") or row.get("degradation_rate") or row.get("t12"))
    return total, with_data

def standardize_dataset(df: List[Dict]) -> List[Dict]:
    """
    Standardize degradation units and convert to half-life.
    Assumes input has 'degradation_rate' or 'half_life'.
    """
    standardized = []
    for row in df:
        new_row = row.copy()
        
        # Handle rate constant to half-life
        if new_row.get("degradation_rate") is not None:
            k = float(new_row["degradation_rate"])
            t12 = convert_k_to_half_life(k)
            if t12 is not None:
                new_row["half_life"] = t12
                new_row["time_unit"] = "hours"
        
        # Normalize existing half-life if unit is specified
        if new_row.get("half_life") is not None and new_row.get("time_unit"):
            val = float(new_row["half_life"])
            unit = str(new_row["time_unit"])
            new_row["half_life"] = normalize_time_unit_to_hours(val, unit)
            new_row["time_unit"] = "hours"
        
        standardized.append(new_row)
    return standardized

def generate_data_characteristics_table(df: List[Dict]) -> None:
    """Generate data/processed/data_characteristics.csv."""
    path = get_data_path() / "processed" / "data_characteristics.csv"
    
    if not df:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "value"])
            writer.writerow(["status", "No Data"])
        return

    metrics = {
        "total_records": len(df),
        "mean_half_life": sum(r.get("half_life", 0) or 0 for r in df) / len(df) if df else 0,
        "min_half_life": min(r.get("half_life", 0) or 0 for r in df) if df else 0,
        "max_half_life": max(r.get("half_life", 0) or 0 for r in df) if df else 0,
    }
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for k, v in metrics.items():
            writer.writerow([k, f"{v:.4f}" if isinstance(v, float) else v])

def log_arrhenius_exclusion() -> None:
    """Log Arrhenius exclusion if needed (placeholder for T021d logic if called separately)."""
    # This is handled in T020b if gate fails, but we log here if we are proceeding
    pass

def merge_audit_trail() -> None:
    """Merge audit trail (placeholder)."""
    pass

def standardize_and_stratify(df: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Filter for Standard conditions:
    Temperature: 25.0 OR "25°C"
    pH: 7.4 OR "7.4"
    """
    standard = []
    excluded = []
    
    for row in df:
        temp = str(row.get("temperature_c", "")).strip()
        ph = str(row.get("ph_value", "")).strip()
        
        # Normalize temperature
        temp_val = None
        if temp:
            try:
                temp_val = float(temp)
            except ValueError:
                if "25" in temp:
                    temp_val = 25.0
        
        # Normalize pH
        ph_val = None
        if ph:
            try:
                ph_val = float(ph)
            except ValueError:
                if "7.4" in ph:
                    ph_val = 7.4
        
        # Check conditions
        is_temp_standard = temp_val == 25.0
        is_ph_standard = ph_val == 7.4
        
        if is_temp_standard and is_ph_standard:
            standard.append(row)
        else:
            excluded.append(row)
    
    return standard, excluded

def main() -> None:
    """
    Main entry point for T020.
    """
    log_operation("start_standardization_and_stratification")
    
    # 1. Read gate_status.json
    gate_status = load_gate_status()
    
    if gate_status is None or gate_status.get("status") == "FAIL":
        # Generate empty artifacts for FAIL case
        logger.info("Data Gate Failed. Generating empty artifacts.")
        
        # Create empty standard_subset.csv
        standard_path = get_data_path() / "processed" / "standard_subset.csv"
        with open(standard_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["canonical_smiles", "half_life", "temperature_c", "ph_value"])
        
        # Create data_characteristics.csv with "No Data"
        generate_data_characteristics_table([])
        
        # Write stat_gate_status.json FAIL
        save_stat_gate_status({
            "status": "FAIL",
            "reason": "Data Gate Failed",
            "N": 0
        })
        
        # Trigger T020b logic via insufficiency.py if needed, 
        # but T020b is a separate task. We just set the status and exit.
        # The T020b task will read this status and generate the detailed report.
        log_operation("standardization_complete_gate_fail")
        return

    # 2. If PASS, load merged_drugs.csv
    merged_path = get_data_path() / "processed" / "merged_drugs.csv"
    if not merged_path.exists():
        logger.error("merged_drugs.csv not found despite Gate PASS.")
        save_stat_gate_status({
            "status": "FAIL",
            "reason": "Missing merged_drugs.csv",
            "N": 0
        })
        return

    # Load data
    df = []
    with open(merged_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            df.append(row)

    if not df:
        save_stat_gate_status({
            "status": "FAIL",
            "reason": "Empty merged dataset",
            "N": 0
        })
        return

    # 3. Standardize
    df_std = standardize_dataset(df)

    # 4. Stratify
    standard_subset, excluded = standardize_and_stratify(df_std)

    N = len(standard_subset)

    # 5. Gate Check
    if N < 30:
        logger.warning(f"Statistical Insufficiency: N={N} < 30.")
        save_stat_gate_status({
            "status": "FAIL",
            "reason": "Insufficient standard condition records",
            "N": N
        })
        # Note: T020b will handle the detailed report generation based on this status.
        log_operation("standardization_complete_stat_gate_fail", N=N)
        return

    # 6. Save standard_subset
    standard_path = get_data_path() / "processed" / "standard_subset.csv"
    if standard_subset:
        with open(standard_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=standard_subset[0].keys())
            writer.writeheader()
            writer.writerows(standard_subset)
    
    # 7. Generate characteristics
    generate_data_characteristics_table(standard_subset)

    # 8. Write stat_gate_status.json PASS
    save_stat_gate_status({
        "status": "PASS",
        "N": N
    })

    log_operation("standardization_complete_gate_pass", N=N)

if __name__ == "__main__":
    main()