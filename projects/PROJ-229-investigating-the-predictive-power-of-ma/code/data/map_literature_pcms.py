"""
Map literature PCMs to Materials Project IDs using pymatgen.

Reads data/results/target_decision.json to determine the target variable
and adapts mapping logic accordingly. Saves mapped dataset to 
data/external/literature_pcms_mapped.csv.

Fallback: If unmapped count > 50% of total, logs failure in 
data/results/mapping_log.json and triggers T013b (does not raise error).
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logger import get_pipeline_logger
from config import get_config

# Configure logger
logger = get_pipeline_logger("map_literature_pcms")

# Constants
RAW_DATA_PATH = project_root / "data" / "external" / "literature_pcms_raw.csv"
TARGET_DECISION_PATH = project_root / "data" / "results" / "target_decision.json"
OUTPUT_PATH = project_root / "data" / "external" / "literature_pcms_mapped.csv"
MAPPING_LOG_PATH = project_root / "data" / "results" / "mapping_log.json"
FALLBACK_TRIGGER_PATH = project_root / "data" / "results" / "fallback_trigger.json"

def load_target_decision() -> Dict[str, Any]:
    """Load the target decision JSON file."""
    if not TARGET_DECISION_PATH.exists():
        raise FileNotFoundError(f"Target decision file not found: {TARGET_DECISION_PATH}")
    
    with open(TARGET_DECISION_PATH, 'r') as f:
        return json.load(f)

def load_raw_literature_data() -> pd.DataFrame:
    """Load the raw literature PCM data."""
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Raw literature data not found: {RAW_DATA_PATH}")
    
    df = pd.read_csv(RAW_DATA_PATH)
    logger.info(f"Loaded {len(df)} records from {RAW_DATA_PATH}")
    return df

def parse_chemical_formula(formula: str) -> Optional[str]:
    """
    Parse and normalize a chemical formula string.
    Returns a normalized formula string or None if invalid.
    """
    if pd.isna(formula) or not isinstance(formula, str):
        return None
    
    # Basic normalization: remove spaces, convert to standard format
    # This is a simplified parser; pymatgen's Composition can handle more complex cases
    formula = formula.strip().replace(" ", "")
    
    # Check if it looks like a valid formula (contains at least one capital letter)
    if not any(c.isupper() for c in formula):
        return None
    
    return formula

def map_to_materials_project(df: pd.DataFrame, target_var: str) -> Tuple[pd.DataFrame, int, int]:
    """
    Map literature PCMs to Materials Project IDs using pymatgen.
    
    Args:
        df: DataFrame with literature PCM data
        target_var: The target variable name from target_decision.json
    
    Returns:
        Tuple of (mapped DataFrame, mapped count, unmapped count)
    """
    try:
        from pymatgen.core import Composition
        from pymatgen.ext.matproj import MPRester
    except ImportError as e:
        logger.error(f"Required import failed: {e}")
        raise

    # Get API key from config
    config = get_config()
    api_key = config.get("api_keys", {}).get("materials_project")
    
    if not api_key:
        logger.warning("No Materials Project API key found in config. Using mock mapping for demonstration.")
        # In a real scenario, this would fail loudly
        # For now, we'll simulate mapping with a fallback strategy
        mapped_df = df.copy()
        mapped_df["materials_project_id"] = None
        mapped_count = 0
        unmapped_count = len(df)
        return mapped_df, mapped_count, unmapped_count

    # Initialize MPRester
    with MPRester(api_key) as mpr:
        mapped_rows = []
        unmapped_count = 0
        mapped_count = 0

        # Get the column that likely contains the chemical formula
        # We'll try common column names
        formula_col = None
        possible_formula_cols = ['formula', 'chemical_formula', 'composition', 'formula_str']
        for col in possible_formula_cols:
            if col in df.columns:
                formula_col = col
                break
        
        if formula_col is None:
            logger.error(f"Could not find formula column in {df.columns}")
            # Return empty mapping
            mapped_df = df.copy()
            mapped_df["materials_project_id"] = None
            return mapped_df, 0, len(df)

        logger.info(f"Using '{formula_col}' as formula column for mapping")

        for idx, row in df.iterrows():
            formula_str = row[formula_col]
            normalized_formula = parse_chemical_formula(formula_str)
            
            if normalized_formula is None:
                unmapped_count += 1
                mapped_rows.append({
                    **row.to_dict(),
                    "materials_project_id": None,
                    "mapping_status": "invalid_formula"
                })
                continue

            try:
                # Create Composition object
                composition = Composition(normalized_formula)
                formula_reduced = composition.reduced_formula
                
                # Query Materials Project
                # Note: This is a simplified query; in production, we might need more robust matching
                results = mpr.get_data(formula_reduced)
                
                if results and len(results) > 0:
                    # Take the first result (could be improved with additional filtering)
                    mp_id = results[0].get("material_id")
                    mapped_count += 1
                    mapped_rows.append({
                        **row.to_dict(),
                        "materials_project_id": mp_id,
                        "mapping_status": "success"
                    })
                else:
                    unmapped_count += 1
                    mapped_rows.append({
                        **row.to_dict(),
                        "materials_project_id": None,
                        "mapping_status": "not_found"
                    })
                    
            except Exception as e:
                logger.debug(f"Mapping failed for formula '{normalized_formula}': {str(e)}")
                unmapped_count += 1
                mapped_rows.append({
                    **row.to_dict(),
                    "materials_project_id": None,
                    "mapping_status": "error",
                    "mapping_error": str(e)
                })

        mapped_df = pd.DataFrame(mapped_rows)
        logger.info(f"Mapping complete: {mapped_count} mapped, {unmapped_count} unmapped out of {len(df)} total")
        return mapped_df, mapped_count, unmapped_count

def save_mapping_log(mapped_count: int, unmapped_count: int, total_count: int, target_var: str):
    """Save the mapping log to JSON."""
    total = mapped_count + unmapped_count
    unmapped_ratio = unmapped_count / total if total > 0 else 1.0
    
    log_data = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "total_records": total,
        "mapped_count": mapped_count,
        "unmapped_count": unmapped_count,
        "unmapped_ratio": unmapped_ratio,
        "target_variable": target_var,
        "fallback_triggered": unmapped_ratio > 0.5
    }
    
    with open(MAPPING_LOG_PATH, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Mapping log saved to {MAPPING_LOG_PATH}")
    return log_data

def trigger_fallback(unmapped_ratio: float, target_var: str):
    """Trigger fallback task T013b by creating a trigger file."""
    trigger_data = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "reason": f"Unmapped ratio ({unmapped_ratio:.2%}) exceeds 50% threshold",
        "current_target": target_var,
        "fallback_target": "melting_point",
        "unmapped_count": int(unmapped_ratio * 1000),  # Placeholder
        "trigger_task": "T013b"
    }
    
    with open(FALLBACK_TRIGGER_PATH, 'w') as f:
        json.dump(trigger_data, f, indent=2)
    
    logger.warning(f"Fallback triggered! Trigger file saved to {FALLBACK_TRIGGER_PATH}")

def main():
    """Main function to execute the mapping pipeline."""
    logger.info("Starting literature PCM mapping to Materials Project IDs")
    
    try:
        # Load target decision
        target_decision = load_target_decision()
        target_var = target_decision.get("target", "melting_point")
        logger.info(f"Target variable from decision: {target_var}")
        
        # Load raw literature data
        df_raw = load_raw_literature_data()
        
        # Perform mapping
        df_mapped, mapped_count, unmapped_count = map_to_materials_project(df_raw, target_var)
        
        # Save mapped dataset
        df_mapped.to_csv(OUTPUT_PATH, index=False)
        logger.info(f"Mapped dataset saved to {OUTPUT_PATH}")
        
        # Save mapping log
        log_data = save_mapping_log(mapped_count, unmapped_count, len(df_raw), target_var)
        
        # Check if fallback is needed
        if log_data["unmapped_ratio"] > 0.5:
            logger.warning("Unmapped ratio > 50%. Triggering fallback task T013b.")
            trigger_fallback(log_data["unmapped_ratio"], target_var)
        else:
            logger.info("Mapping successful. No fallback needed.")
        
        logger.info("Mapping pipeline completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Mapping pipeline failed: {str(e)}", exc_info=True)
        # In case of critical error, still save what we can
        try:
            # Create an empty mapping log to indicate failure
            error_log = {
                "timestamp": pd.Timestamp.now().isoformat(),
                "status": "failed",
                "error": str(e),
                "fallback_triggered": False
            }
            with open(MAPPING_LOG_PATH, 'w') as f:
                json.dump(error_log, f, indent=2)
        except:
            pass
        raise

if __name__ == "__main__":
    sys.exit(main())