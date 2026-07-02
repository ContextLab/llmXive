"""
Script to execute T025: Extract changed lines from Defects4J data.
This script parses the cached parquet file and outputs data/changed_lines.json.
"""
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import extract_changed_lines

def main():
    print("Starting extraction of changed lines from Defects4J data...")
    try:
        changed_lines = extract_changed_lines()
        print(f"Successfully extracted changed lines for {len(changed_lines)} projects.")
        print("Output written to data/changed_lines.json")
    except Exception as e:
        print(f"Error during extraction: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
