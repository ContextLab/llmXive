"""
Utility script to validate YAML syntax and structure of data source configurations.
Used by T001 to verify sources.yaml.
"""
import sys
import os
import yaml

def validate_yaml_file(file_path: str) -> bool:
    """
    Validate that a file is syntactically correct YAML.
    
    Args:
        file_path: Path to the YAML file.
        
    Returns:
        True if valid, False otherwise.
    """
    try:
        with open(file_path, 'r') as f:
            yaml.safe_load(f)
        return True
    except yaml.YAMLError as e:
        print(f"YAML Syntax Error: {e}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"File not found: {file_path}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_yaml.py <path_to_yaml_file>")
        sys.exit(1)
    
    target_file = sys.argv[1]
    if validate_yaml_file(target_file):
        print(f"SUCCESS: {target_file} is valid YAML.")
        sys.exit(0)
    else:
        print(f"FAILED: {target_file} has invalid YAML syntax.")
        sys.exit(1)