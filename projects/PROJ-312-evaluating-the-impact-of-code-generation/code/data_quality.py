import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from utils import validate_json_schema

logger = logging.getLogger(__name__)

class DataQualityError(Exception):
    pass

def calculate_success_rate(processed_count: int, total_count: int) -> float:
    if total_count == 0:
        return 0.0
    return processed_count / total_count

def validate_and_check_quality(data: list, schema_path: str, threshold: float = 0.95) -> bool:
    valid_count = 0
    for item in data:
        if validate_json_schema(item, schema_path):
            valid_count += 1
    
    rate = calculate_success_rate(valid_count, len(data))
    if rate < threshold:
        raise DataQualityError(f"Data quality threshold not met: {rate:.1%}")
    
    logger.info(f"Data quality check passed: {rate:.1%}")
    return True

def main():
    """Run data quality checks."""
    schema_path = "contracts/pull_request.schema.yaml"
    data_path = "data/processed/pr_data.json"
    
    if not os.path.exists(data_path):
        logger.error("Processed data not found. Run fetch_data.py first.")
        return
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    try:
        validate_and_check_quality(data, schema_path)
    except DataQualityError as e:
        logger.error(str(e))

if __name__ == "__main__":
    main()
