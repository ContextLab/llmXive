import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

def load_json_file(file_path: str) -> Any:
    """Load a JSON file and return its contents."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_raw_schema(data: Any) -> bool:
    """
    Validate the raw perturbation candidates schema.
    Expected format: List of dictionaries with task_id, perturbation_type, raw_score, is_valid.
    """
    if not isinstance(data, list):
        print("ERROR: Raw data must be a list.")
        return False
    
    required_fields = ['task_id', 'perturbation_type', 'raw_score', 'is_valid']
    
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            print(f"ERROR: Item {i} is not a dictionary.")
            return False
        
        for field in required_fields:
            if field not in item:
                print(f"ERROR: Item {i} missing required field: {field}")
                return False
        
        # Validate types
        if not isinstance(item['task_id'], str):
            print(f"ERROR: Item {i} task_id must be a string.")
            return False
        
        if not isinstance(item['perturbation_type'], str):
            print(f"ERROR: Item {i} perturbation_type must be a string.")
            return False
        
        if not isinstance(item['raw_score'], (int, float)):
            print(f"ERROR: Item {i} raw_score must be a number.")
            return False
        
        if not isinstance(item['is_valid'], bool):
            print(f"ERROR: Item {i} is_valid must be a boolean.")
            return False
    
    print(f"Raw schema validation passed for {len(data)} items.")
    return True

def validate_filtered_schema(data: Any) -> bool:
    """
    Validate the filtered perturbation candidates schema.
    Expected format: List of dictionaries with task_id, perturbation_type, raw_score.
    All items should have raw_score > 0.95.
    """
    if not isinstance(data, list):
        print("ERROR: Filtered data must be a list.")
        return False
    
    if len(data) == 0:
        print("WARNING: Filtered data is empty.")
        return True
    
    required_fields = ['task_id', 'perturbation_type', 'raw_score']
    
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            print(f"ERROR: Item {i} is not a dictionary.")
            return False
        
        for field in required_fields:
            if field not in item:
                print(f"ERROR: Item {i} missing required field: {field}")
                return False
        
        # Validate types
        if not isinstance(item['task_id'], str):
            print(f"ERROR: Item {i} task_id must be a string.")
            return False
        
        if not isinstance(item['perturbation_type'], str):
            print(f"ERROR: Item {i} perturbation_type must be a string.")
            return False
        
        if not isinstance(item['raw_score'], (int, float)):
            print(f"ERROR: Item {i} raw_score must be a number.")
            return False
        
        # Validate score threshold
        if item['raw_score'] <= 0.95:
            print(f"ERROR: Item {i} raw_score ({item['raw_score']}) must be > 0.95.")
            return False
    
    print(f"Filtered schema validation passed for {len(data)} items.")
    return True

def validate_error_classification_schema(data: Any) -> bool:
    """
    Validate the error classification report schema.
    Expected format: List of dictionaries with task_id, perturbation_type, classification.
    """
    if not isinstance(data, list):
        print("ERROR: Error classification data must be a list.")
        return False
    
    if len(data) == 0:
        print("WARNING: Error classification data is empty.")
        return True
    
    required_fields = ['task_id', 'perturbation_type', 'classification']
    
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            print(f"ERROR: Item {i} is not a dictionary.")
            return False
        
        for field in required_fields:
            if field not in item:
                print(f"ERROR: Item {i} missing required field: {field}")
                return False
        
        # Validate types
        if not isinstance(item['task_id'], str):
            print(f"ERROR: Item {i} task_id must be a string.")
            return False
        
        if not isinstance(item['perturbation_type'], str):
            print(f"ERROR: Item {i} perturbation_type must be a string.")
            return False
        
        if not isinstance(item['classification'], str):
            print(f"ERROR: Item {i} classification must be a string.")
            return False
        
        if item['classification'] not in ['syntax', 'logic', 'unknown']:
            print(f"ERROR: Item {i} classification must be 'syntax', 'logic', or 'unknown'.")
            return False
    
    # Check max size constraint (<= 50)
    if len(data) > 50:
        print(f"ERROR: Error classification report must have <= 50 items, found {len(data)}.")
        return False
    
    print(f"Error classification schema validation passed for {len(data)} items.")
    return True

def main():
    """Main entry point for schema validation."""
    parser = argparse.ArgumentParser(description='Validate JSON schema for perturbation and error classification outputs.')
    parser.add_argument('--input', type=str, required=True, help='Path to the input JSON file.')
    parser.add_argument('--type', type=str, choices=['raw', 'filtered', 'error_classification'], 
                      default='filtered', help='Type of schema to validate.')
    
    args = parser.parse_args()
    
    try:
        data = load_json_file(args.input)
    except Exception as e:
        print(f"ERROR: Failed to load JSON file: {e}")
        sys.exit(1)
    
    if args.type == 'raw':
        success = validate_raw_schema(data)
    elif args.type == 'filtered':
        success = validate_filtered_schema(data)
    elif args.type == 'error_classification':
        success = validate_error_classification_schema(data)
    else:
        print(f"ERROR: Unknown schema type: {args.type}")
        sys.exit(1)
    
    if success:
        print("Validation successful.")
        sys.exit(0)
    else:
        print("Validation failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()