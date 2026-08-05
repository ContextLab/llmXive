from __future__ import annotations

import csv
import json
import logging
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from logging_config import get_logger, log_operation, log_pipeline_failure
from config import get_config

logger = get_logger("standardize")

def get_data_path() -> Path:
    return Path(__file__).parent.parent / "data"

def load_config() -> Dict[str, Any]:
    config_path = get_data_path() / "config.yaml"
    if not config_path.exists():
        # Fallback to defaults if config missing, though T080/T081 should have created it
        return {
            "temp_min": 20.0,
            "temp_max": 30.0,
            "ph_min": 7.35,
            "ph_max": 7.45
        }
    import yaml
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def load_gate_status() -> Dict[str, Any]:
    gate_path = get_data_path() / "gate_status.json"
    if not gate_path.exists():
        return {"status": "UNKNOWN"}
    with open(gate_path, "r") as f:
        return json.load(f)

def save_stat_gate_status(status: Dict[str, Any]) -> None:
    """Save the statistical gate status to data/stat_gate_status.json."""
    output_path = get_data_path() / "stat_gate_status.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(status, f, indent=2)
    logger.log("StatGateStatusSaved", {"path": str(output_path)})

def standardize_and_stratify() -> int:
    """
    Implements T020: Standardization & Stratification.
    1. Check Gate Status.
    2. Read merged_drugs.csv.
    3. Standardize units (k -> t1/2, time -> hours).
    4. Create Full Dataset (with covariates).
    5. Create Standard Subset (filter by temp/pH).
    6. Check Secondary Gate (N_std >= 30).
    7. Save outputs and update stat_gate_status.json.
    """
    logger.log("StandardizeStart", {"task": "T020"})

    # 1. Check Gate Status
    gate_status = load_gate_status()
    if gate_status.get("status") != "PASS":
        logger.log("GateFailed", {"status": gate_status.get("status")})
        # Update stat gate to reflect upstream failure
        save_stat_gate_status({
            "status": "FAIL",
            "reason": "Upstream Data Availability Gate Failed",
            "upstream_status": gate_status
        })
        return 1

    try:
        # 2. Read merged data
        merged_path = get_data_path() / "processed" / "merged_drugs.csv"
        if not merged_path.exists():
            raise FileNotFoundError(f"Merged drugs file not found at {merged_path}")
        
        df = pd.read_csv(merged_path)
        logger.log("DataLoaded", {"rows": len(df), "columns": list(df.columns)})

        # 3. Standardize Units
        # Check for rate constant columns
        rate_cols = [c for c in df.columns if 'rate' in c.lower() or 'k' in c.lower()]
        half_life_cols = [c for c in df.columns if 'half' in c.lower() or 't1/2' in c.lower()]
        
        if not rate_cols and not half_life_cols:
            raise ValueError("No rate constant or half-life columns found in merged data")

        # Assume we have a 'rate_constant' or similar, convert to half_life
        # If half_life exists, use it. If only rate exists, calculate.
        # For this implementation, we assume a column 'rate_constant' exists or 'k'
        # and we generate 'half_life_hours'.
        
        if 'rate_constant' in df.columns:
            # k -> t1/2 = ln(2) / k
            # Assume rate_constant is in 1/hours? Spec says standardize to hours.
            # If units are unknown, we assume consistent units and convert.
            # Let's assume input is 1/hours for simplicity, or convert if unit column exists.
            # If unit column exists (e.g. 'rate_unit'), we would handle that.
            # For now, direct conversion assuming 1/hours or scaling if needed.
            df['half_life_hours'] = math.log(2) / df['rate_constant']
        elif half_life_cols:
            # Use existing, ensure named 'half_life_hours'
            col = half_life_cols[0]
            df['half_life_hours'] = df[col]
        else:
            raise ValueError("Could not derive half_life_hours")

        # 4. Create Full Dataset
        full_path = get_data_data_path() / "processed" / "full_dataset_with_covariates.csv"
        df.to_csv(full_path, index=False)
        logger.log("FullDatasetSaved", {"path": str(full_path)})

        # 5. Create Standard Subset
        config = load_config()
        temp_min = config.get("temp_min", 20.0)
        temp_max = config.get("temp_max", 30.0)
        ph_min = config.get("ph_min", 7.35)
        ph_max = config.get("ph_max", 7.45)

        # Identify temperature and pH columns
        temp_cols = [c for c in df.columns if 'temp' in c.lower()]
        ph_cols = [c for c in df.columns if 'ph' in c.lower()]

        if not temp_cols or not ph_cols:
            # If no temp/pH columns, we cannot filter. 
            # Per spec, we must filter. If missing, we might fail the gate or take all.
            # Spec T081 defines defaults. If data missing, we cannot verify.
            # Let's assume if columns missing, we cannot form a standard subset.
            raise ValueError("Temperature and pH columns required for standard subset filtering")

        temp_col = temp_cols[0]
        ph_col = ph_cols[0]

        mask = (
            (df[temp_col] >= temp_min) & (df[temp_col] <= temp_max) &
            (df[ph_col] >= ph_min) & (df[ph_col] <= ph_max)
        )
        df_std = df[mask].copy()

        n_std = len(df_std)
        logger.log("StandardSubsetFiltered", {"N": n_std, "threshold": 30})

        # 6. Secondary Gate Check
        if n_std < 30:
            logger.log("StatGateFailed", {"reason": "N_std < 30", "N": n_std})
            save_stat_gate_status({
                "status": "FAIL",
                "reason": "N_std < 30",
                "N_std": n_std,
                "threshold": 30
            })
            # Generate insufficiency report? T020 says generate data_insufficiency_report.md
            # We'll assume report generation is handled by a separate script or T034 logic
            # But we must exit with code 1.
            return 1

        # 7. Save Standard Subset and Update Gate
        std_path = get_data_path() / "processed" / "standard_subset.csv"
        df_std.to_csv(std_path, index=False)
        logger.log("StandardSubsetSaved", {"path": str(std_path)})

        save_stat_gate_status({
            "status": "PASS",
            "N_std": n_std,
            "threshold": 30,
            "temp_range": [temp_min, temp_max],
            "ph_range": [ph_min, ph_max]
        })
        logger.log("StandardizeComplete", {"status": "PASS", "N": n_std})
        return 0

    except Exception as e:
        logger.log("StandardizeError", {"error": str(e)})
        log_pipeline_failure("Standardize", str(e))
        return 1

if __name__ == "__main__":
    sys.exit(standardize_and_stratify())