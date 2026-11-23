"""
Utility script to validate the configuration module.
Ensures all required quantization levels are present.
"""
import sys
import os

# Add the code directory to the path to allow imports
code_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from config import QUANTIZATION_LEVELS, validate_config

def main():
    print("Validating configuration...")
    
    # Check if the validate_config function returns True
    if not validate_config():
        print("ERROR: Configuration validation failed.")
        return 1

    # Check for specific required quantization levels
    required_levels = [4, 6, 8, 16]
    missing_levels = [lvl for lvl in required_levels if lvl not in QUANTIZATION_LEVELS]

    if missing_levels:
        print(f"ERROR: Missing required quantization levels: {missing_levels}")
        print(f"Current levels: {QUANTIZATION_LEVELS}")
        return 1

    print(f"SUCCESS: All required quantization levels {required_levels} are present.")
    print(f"Current quantization levels: {QUANTIZATION_LEVELS}")
    return 0

if __name__ == "__main__":
    sys.exit(main())