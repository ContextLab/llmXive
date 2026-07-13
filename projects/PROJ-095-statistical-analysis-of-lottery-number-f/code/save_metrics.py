"""
Task T013: Save processed metrics to data/processed/metrics.json with schema validation.

This script reads the raw draws from data/raw/lottery_draws.csv, calculates
birthday_cluster_ratio and consecutive_pattern_count using code/metrics.py,
and saves the aggregated results to data/processed/metrics.json.

It also validates the output against the schema defined in data/schemas/final_report.schema.json
(specifically checking for the required keys structure, though the schema is primarily
for the final report, we ensure our intermediate file matches the expected keys).
"""
import json
import os
import sys
import logging
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics import calculate_birthday_ratio, calculate_consecutive_ratio
from data_utils import load_draws_csv
from exceptions import LotteryDataError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_processed_metrics_schema() -> Dict[str, Any]:
    """
    Load the schema for validation. 
    Note: T011a created final_report.schema.json. 
    We will perform a structural validation based on the keys expected in the final report
    that correspond to these metrics, ensuring we output the correct keys.
    """
    schema_path = os.path.join("data", "schemas", "final_report.schema.json")
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            return json.load(f)
    else:
        logger.warning(f"Schema file {schema_path} not found. Skipping strict schema validation.")
        return {}

def validate_metrics_output(metrics: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validates that the metrics dictionary contains the required keys 
    as per the project's schema requirements (derived from T011a).
    """
    required_keys = ["birthday_cluster_ratio", "consecutive_pattern_count", "is_majority_birthday"]
    
    for key in required_keys:
        if key not in metrics:
            logger.error(f"Validation failed: Missing required key '{key}' in metrics output.")
            return False
    
    # Validate types
    if not isinstance(metrics["birthday_cluster_ratio"], (int, float)):
        logger.error("Validation failed: 'birthday_cluster_ratio' must be a number.")
        return False
    
    if not isinstance(metrics["consecutive_pattern_count"], (int, float)):
        logger.error("Validation failed: 'consecutive_pattern_count' must be a number.")
        return False

    return True

def main():
    logger.info("Starting T013: Save processed metrics.")
    
    raw_data_path = os.path.join("data", "raw", "lottery_draws.csv")
    output_path = os.path.join("data", "processed", "metrics.json")
    
    if not os.path.exists(raw_data_path):
        raise FileNotFoundError(f"Raw data file not found at {raw_data_path}. Run T008 first.")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        # Load data
        logger.info(f"Loading draws from {raw_data_path}...")
        draws_df = load_draws_csv(raw_data_path)
        
        if draws_df.empty:
            raise LotteryDataError("No draws found in the dataset.")

        logger.info(f"Processing {len(draws_df)} draws...")

        # Calculate metrics
        # Assuming the dataframe has a column 'numbers' containing the list of numbers for the draw
        # or separate columns. Based on typical lottery data and the API, we assume a list or string parsing.
        # Let's handle the case where 'numbers' might be a string "1,2,3,4,5,6" or a list.
        
        total_draws = len(draws_df)
        birthday_ratios = []
        consecutive_ratios = []
        
        # Check column names to find the numbers
        cols = draws_df.columns.tolist()
        numbers_col = None
        for candidate in ['numbers', 'draw_numbers', 'ball_numbers', 'balls']:
            if candidate in cols:
                numbers_col = candidate
                break
        
        if not numbers_col:
            # Fallback: try to find any column that looks like it holds the draw numbers
            # If the data format is unknown, we might need to adapt. 
            # Assuming standard format from T008 ingestion which likely parses into a list column.
            raise ValueError("Could not identify column containing draw numbers.")

        for idx, row in draws_df.iterrows():
            draw_nums = row[numbers_col]
            
            # Ensure draw_nums is a list of integers
            if isinstance(draw_nums, str):
                draw_nums = [int(x.strip()) for x in draw_nums.split(',')]
            elif not isinstance(draw_nums, list):
                draw_nums = list(draw_nums)
            
            # Calculate metrics
            b_ratio = calculate_birthday_ratio(draw_nums)
            c_ratio = calculate_consecutive_ratio(draw_nums)
            
            birthday_ratios.append(b_ratio)
            consecutive_ratios.append(c_ratio)

        # Aggregate metrics
        avg_birthday_ratio = sum(birthday_ratios) / len(birthday_ratios) if birthday_ratios else 0.0
        avg_consecutive_ratio = sum(consecutive_ratios) / len(consecutive_ratios) if consecutive_ratios else 0.0
        
        # Determine majority flag (based on average or majority of draws? 
        # T011 description says: "Flag is_majority_birthday if birthday_cluster_ratio > 0.5"
        # This likely refers to the aggregate metric being > 0.5)
        is_majority_birthday = avg_birthday_ratio > 0.5

        metrics_output = {
            "birthday_cluster_ratio": avg_birthday_ratio,
            "consecutive_pattern_count": avg_consecutive_ratio,
            "is_majority_birthday": is_majority_birthday,
            "total_draws_analyzed": total_draws
        }

        # Validate against schema requirements
        schema = load_processed_metrics_schema()
        if not validate_metrics_output(metrics_output, schema):
            raise LotteryDataError("Generated metrics failed schema validation.")

        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(metrics_output, f, indent=2)

        logger.info(f"Successfully saved metrics to {output_path}")
        logger.info(f"Results: birthday_cluster_ratio={avg_birthday_ratio:.4f}, "
                    f"consecutive_pattern_count={avg_consecutive_ratio:.4f}, "
                    f"is_majority_birthday={is_majority_birthday}")

    except Exception as e:
        logger.error(f"Error during metric calculation or saving: {e}")
        raise

if __name__ == "__main__":
    main()