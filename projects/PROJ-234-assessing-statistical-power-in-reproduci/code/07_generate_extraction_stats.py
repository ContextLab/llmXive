"""
T027: Generate extraction statistics from parsed publication data.

Reads data/processed/extracted_params.json and generates
data/processed/extraction_stats.json containing success_rate and
failure_reasons counts.
"""
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List

# Import logging config from existing utility
from utils.logging_config import setup_logging

def load_extracted_params(input_path: str) -> List[Dict[str, Any]]:
    """Load the extracted parameters JSON file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of records in {input_path}, got {type(data)}")
    
    return data

def generate_extraction_stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate extraction statistics from the parsed records.
    
    Returns a dictionary with:
    - success_rate: float (0.0 to 1.0)
    - failure_reasons: dict with counts for "paywalled", "unparseable", "insufficient data"
    """
    if not records:
        return {
            "success_rate": 0.0,
            "failure_reasons": {
                "paywalled": 0,
                "unparseable": 0,
                "insufficient data": 0
            }
        }
    
    total = len(records)
    success_count = 0
    failure_reasons = {
        "paywalled": 0,
        "unparseable": 0,
        "insufficient data": 0
    }
    
    for record in records:
        status = record.get("status", "unknown")
        
        if status == "success":
            success_count += 1
        elif status in failure_reasons:
            failure_reasons[status] += 1
        else:
            # Any other status is treated as a failure but not categorized
            # We could add it to a generic "other" bucket if needed, 
            # but for now we just don't count it in success.
            pass
    
    success_rate = success_count / total if total > 0 else 0.0
    
    return {
        "success_rate": success_rate,
        "failure_reasons": failure_reasons
    }

def main():
    """Main entry point for generating extraction statistics."""
    # Setup logging
    logger = setup_logging()
    
    input_file = "data/processed/extracted_params.json"
    output_file = "data/processed/extraction_stats.json"
    
    logger.info(f"Starting extraction stats generation from {input_file}")
    
    try:
        records = load_extracted_params(input_file)
        logger.info(f"Loaded {len(records)} records")
        
        stats = generate_extraction_stats(records)
        
        # Ensure output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Successfully wrote extraction stats to {output_file}")
        logger.info(f"Success rate: {stats['success_rate']:.2%}")
        logger.info(f"Failure reasons: {stats['failure_reasons']}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
