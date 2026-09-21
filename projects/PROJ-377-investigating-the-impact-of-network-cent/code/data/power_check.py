import os
import json
import logging
from pathlib import Path
import pandas as pd
from utils.logging import setup_logger
from utils.config import get_config, get_power_threshold_n

def load_retention_metrics() -> dict:
    """
    Load retention metrics from the JSON file generated in T003.
    
    Returns:
        dict: Dictionary containing retention rate, total subjects, retained subjects, etc.
    
    Raises:
        FileNotFoundError: If the retention metrics file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    config = get_config()
    retention_metrics_path = config.output_paths.retention_metrics_path
    
    if not os.path.exists(retention_metrics_path):
        raise FileNotFoundError(f"Retention metrics file not found at {retention_metrics_path}. "
                                "Ensure T003 has been completed successfully.")
    
    with open(retention_metrics_path, 'r') as f:
        metrics = json.load(f)
    
    return metrics

def check_power(retention_metrics: dict) -> dict:
    """
    Check if the study is adequately powered based on the number of retained subjects.
    
    Args:
        retention_metrics (dict): Dictionary containing retention metrics, specifically 'retained_subjects'.
    
    Returns:
        dict: Dictionary containing the power check result, including 'is_underpowered', 'warning_message',
              and 'flag_for_report'.
    """
    config = get_config()
    power_threshold_n = get_power_threshold_n()
    
    retained_subjects = retention_metrics.get('retained_subjects', 0)
    is_underpowered = retained_subjects < power_threshold_n
    
    result = {
        'retained_subjects': retained_subjects,
        'power_threshold_n': power_threshold_n,
        'is_underpowered': is_underpowered,
        'flag_for_report': is_underpowered,
        'warning_message': None
    }
    
    if is_underpowered:
        warning_msg = f"Underpowered for small effects (r=0.3). N={retained_subjects} < threshold={power_threshold_n}."
        result['warning_message'] = warning_msg
        logging.warning(warning_msg)
    else:
        logging.info(f"Study is adequately powered. N={retained_subjects} >= threshold={power_threshold_n}.")
    
    return result

def save_power_check_results(power_check_result: dict) -> Path:
    """
    Save the power check results to a JSON file.
    
    Args:
        power_check_result (dict): Dictionary containing the power check results.
    
    Returns:
        Path: Path to the saved JSON file.
    """
    config = get_config()
    output_dir = config.output_paths.power_check_results_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = config.output_paths.power_check_results_path
    
    with open(output_path, 'w') as f:
        json.dump(power_check_result, f, indent=4)
    
    logging.info(f"Power check results saved to {output_path}")
    return output_path

def main():
    """
    Main function to run the power check.
    """
    # Setup logger
    logger = setup_logger("power_check")
    logger.info("Starting power check (T004)...")
    
    try:
        # Load retention metrics
        logger.info("Loading retention metrics...")
        retention_metrics = load_retention_metrics()
        
        # Check power
        logger.info("Checking power...")
        power_check_result = check_power(retention_metrics)
        
        # Save results
        logger.info("Saving power check results...")
        output_path = save_power_check_results(power_check_result)
        
        logger.info(f"Power check completed successfully. Results saved to {output_path}")
        
        # If underpowered, the warning has already been logged.
        # The 'flag_for_report' field is set to True if underpowered,
        # which can be picked up by the final report generation (T040).
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Error: Invalid JSON in retention metrics file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during power check: {e}")
        return 1

if __name__ == "__main__":
    exit(main())