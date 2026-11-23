import math
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from statsmodels.stats.power import TTestIndPower

# Configure logging for the module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
ALPHA = 0.05
MIN_POWER = 0.0
MAX_POWER = 1.0

class PowerCalculationError(Exception):
    """Custom exception for power calculation errors."""
    pass

def calculate_sensitivity_power(
    actual_sample_size: int,
    assumed_effect_size: float,
    alpha: float = ALPHA
) -> float:
    """
    Calculate sensitivity power using actual sample size and assumed effect size.
    
    Args:
        actual_sample_size (int): The observed sample size (n per group or total depending on context, 
                                  assuming total n for TTestIndPower if not specified, but usually 
                                  statsmodels expects nobs1). We assume this is n per group or handle
                                  accordingly. Based on typical usage in this domain, we assume 
                                  actual_sample_size is the total N, so n per group = N/2.
        assumed_effect_size (float): The effect size assumption (Cohen's d).
        alpha (float): Significance level (default 0.05).
        
    Returns:
        float: Calculated power.
    """
    if actual_sample_size <= 0:
        raise PowerCalculationError(f"Actual sample size must be positive, got {actual_sample_size}")
    
    if not (0 < alpha < 1):
        raise PowerCalculationError(f"Alpha must be between 0 and 1, got {alpha}")

    # Assume equal group sizes for T-test. If actual_sample_size is total N:
    # statsmodels TTestIndPower expects nobs1 (n per group).
    n_per_group = actual_sample_size / 2.0
    
    if n_per_group < 2:
        raise PowerCalculationError(f"Sample size too small for power calculation (n_per_group={n_per_group})")

    power_analysis = TTestIndPower()
    
    try:
        power = power_analysis.solve_power(
            effect_size=assumed_effect_size,
            nobs1=n_per_group,
            alpha=alpha,
            power=None,
            ratio=1.0
        )
    except Exception as e:
        raise PowerCalculationError(f"Power calculation failed: {str(e)}")

    return float(power)

def calculate_power_gap(
    planned_power: float,
    sensitivity_power: float
) -> float:
    """
    Calculate the power gap: planned_power - sensitivity_power.
    
    Args:
        planned_power (float): The power planned in the pre-registration.
        sensitivity_power (float): The calculated sensitivity power.
        
    Returns:
        float: The power gap.
    """
    return float(planned_power - sensitivity_power)

def clamp_power(
    power: float,
    min_val: float = MIN_POWER,
    max_val: float = MAX_POWER
) -> float:
    """
    Clamp power value to the valid probability range [0, 1].
    Logs a warning if the value is outside the valid range.
    
    Args:
        power (float): The raw power value.
        min_val (float): Minimum allowed value (default 0.0).
        max_val (float): Maximum allowed value (default 1.0).
        
    Returns:
        float: The clamped power value.
    """
    if math.isnan(power) or math.isinf(power):
        logger.warning(f"Received non-finite power value: {power}. Clamping to {min_val}.")
        return min_val

    original = power
    clamped = max(min_val, min(max_val, power))

    if clamped != original:
        logger.warning(
            f"Sensitivity power value {original:.4f} is outside valid range [{min_val}, {max_val}]. "
            f"Clamped to {clamped:.4f}."
        )
    
    return clamped

def process_study_records(
    records: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Process a list of study records to calculate sensitivity power and power gap.
    Includes validation and clamping logic (T025).
    
    Args:
        records (List[Dict[str, Any]]): List of study records with keys:
            - 'planned_power'
            - 'effect_size_assumption'
            - 'actual_sample_size'
            
    Returns:
        List[Dict[str, Any]]: Processed records with added keys:
            - 'sensitivity_power' (clamped)
            - 'power_gap'
            - 'validation_status' ('valid', 'clamped', 'error')
    """
    processed_records = []
    
    for i, record in enumerate(records):
        try:
            planned_power = record.get('planned_power')
            assumed_effect_size = record.get('effect_size_assumption')
            actual_sample_size = record.get('actual_sample_size')
            
            if planned_power is None or assumed_effect_size is None or actual_sample_size is None:
                logger.warning(f"Record {i}: Missing required fields. Skipping power calculation.")
                processed_record = record.copy()
                processed_record['sensitivity_power'] = None
                processed_record['power_gap'] = None
                processed_record['validation_status'] = 'missing_data'
                processed_records.append(processed_record)
                continue

            # Calculate raw sensitivity power
            raw_power = calculate_sensitivity_power(
                actual_sample_size=int(actual_sample_size),
                assumed_effect_size=float(assumed_effect_size)
            )
            
            # T025: Clamp and log warnings
            clamped_power = clamp_power(raw_power)
            
            # Determine status
            if clamped_power != raw_power:
                status = 'clamped'
            else:
                status = 'valid'
                
            # Calculate power gap
            power_gap = calculate_power_gap(float(planned_power), clamped_power)
            
            processed_record = record.copy()
            processed_record['sensitivity_power'] = clamped_power
            processed_record['power_gap'] = power_gap
            processed_record['validation_status'] = status
            
        except PowerCalculationError as e:
            logger.error(f"Record {i}: Power calculation error - {str(e)}")
            processed_record = record.copy()
            processed_record['sensitivity_power'] = None
            processed_record['power_gap'] = None
            processed_record['validation_status'] = 'error'
            processed_record['calculation_error'] = str(e)
        except Exception as e:
            logger.error(f"Record {i}: Unexpected error - {str(e)}")
            processed_record = record.copy()
            processed_record['sensitivity_power'] = None
            processed_record['power_gap'] = None
            processed_record['validation_status'] = 'error'
            processed_record['calculation_error'] = str(e)
            
        processed_records.append(processed_record)
        
    return processed_records

def main():
    """
    Main entry point for power calculation pipeline.
    Reads from data/derived/study_records_raw.json, processes, and writes to data/derived/power_analysis.csv.
    """
    import json
    import csv
    from pathlib import Path

    input_path = Path("data/derived/study_records_raw.json")
    output_path = Path("data/derived/power_analysis.csv")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading study records from {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        records = json.load(f)

    if not isinstance(records, list):
        logger.error("Input JSON must be a list of records.")
        sys.exit(1)

    logger.info(f"Processing {len(records)} records...")
    processed_records = process_study_records(records)

    logger.info(f"Writing processed results to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if processed_records:
        fieldnames = list(processed_records[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(processed_records)
    
    logger.info("Power calculation complete.")

if __name__ == "__main__":
    main()