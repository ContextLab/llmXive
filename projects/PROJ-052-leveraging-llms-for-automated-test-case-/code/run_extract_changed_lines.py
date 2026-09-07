"""
Script to run the extract_changed_lines function and generate the output artifact.
This script is designed to be run as a standalone command to produce data/changed_lines.json.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import extract_changed_lines, ensure_data_loaded_and_integrity_recorded

def main():
    """Main entry point for extracting changed lines."""
    print("Starting changed lines extraction...")
    
    try:
        # Ensure data is loaded and integrity is recorded
        ensure_data_loaded_and_integrity_recorded()
        
        # Extract changed lines and write to output file
        result = extract_changed_lines()
        
        print(f"Successfully extracted changed lines for {len(result)} projects")
        print("Output written to data/changed_lines.json")
        
        return 0
    except Exception as e:
        print(f"Error extracting changed lines: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
