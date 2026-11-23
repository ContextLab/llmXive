import json
import os
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime

class DataIngestionError(Exception):
    """Custom exception for data ingestion failures."""
    pass

def load_real_participant_data(input_path: str) -> List[Dict[str, Any]]:
    """
    Load real participant data from a JSON file.
    
    Expected schema:
    {
        "responses": [
            {
                "participant_id": str,
                "age": int,
                "gender": str,
                "condition": str,
                "raw_responses": {
                    "CAMI_1": int, ... "CAMI_20": int,
                    "help_seeking": int,
                    "attention_check": str
                }
            }
        ]
    }
    
    Args:
        input_path: Path to the JSON file containing survey responses.
        
    Returns:
        List of dictionaries containing participant data.
        
    Raises:
        DataIngestionError: If the file does not exist, is not valid JSON,
                            or does not match the expected schema.
    """
    if not os.path.exists(input_path):
        raise DataIngestionError(f"Input file not found: {input_path}")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DataIngestionError(f"Invalid JSON in {input_path}: {e}")
    
    if "responses" not in data:
        raise DataIngestionError(f"Missing 'responses' key in {input_path}")
    
    responses = data["responses"]
    if not isinstance(responses, list):
        raise DataIngestionError(f"'responses' must be a list in {input_path}")
    
    if len(responses) == 0:
        raise DataIngestionError(f"No responses found in {input_path}")
    
    # Validate schema for each response
    required_keys = {"participant_id", "age", "gender", "condition", "raw_responses"}
    for i, resp in enumerate(responses):
        if not isinstance(resp, dict):
            raise DataIngestionError(f"Response at index {i} is not a dictionary")
        
        missing_keys = required_keys - set(resp.keys())
        if missing_keys:
            raise DataIngestionError(
                f"Response at index {i} missing required keys: {missing_keys}"
            )
        
        if not isinstance(resp["raw_responses"], dict):
            raise DataIngestionError(
                f"'raw_responses' at index {i} must be a dictionary"
            )
        
        # Check for CAMI items and help seeking
        raw = resp["raw_responses"]
        if "help_seeking" not in raw:
            raise DataIngestionError(
                f"Missing 'help_seeking' in raw_responses for participant {resp['participant_id']}"
            )
        
        cami_keys = [f"CAMI_{i}" for i in range(1, 21)]
        missing_cami = set(cami_keys) - set(raw.keys())
        if missing_cami:
            raise DataIngestionError(
                f"Missing CAMI items {missing_cami} for participant {resp['participant_id']}"
            )
    
    return responses

def load_assignments(assignment_path: str) -> List[Dict[str, Any]]:
    """
    Load experimental assignments from a CSV file.
    
    Args:
        assignment_path: Path to the CSV file.
        
    Returns:
        List of dictionaries containing assignment data.
    """
    if not os.path.exists(assignment_path):
        raise DataIngestionError(f"Assignment file not found: {assignment_path}")
    
    assignments = []
    with open(assignment_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            assignments.append(row)
    
    return assignments

def main():
    """Main entry point for data ingestion script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load real participant data")
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/survey_responses.json",
        help="Path to the input JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/validated_responses.json",
        help="Path to the output validated JSON file"
    )
    
    args = parser.parse_args()
    
    try:
        responses = load_real_participant_data(args.input)
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Write validated data
        output_data = {
            "validated_at": datetime.now().isoformat(),
            "source": args.input,
            "response_count": len(responses),
            "responses": responses
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Successfully loaded and validated {len(responses)} responses")
        print(f"Output written to: {args.output}")
        
    except DataIngestionError as e:
        print(f"Data ingestion error: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    main()