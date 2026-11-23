import sys
from pathlib import Path
from data_loader import extract_changed_lines, ensure_data_loaded_and_integrity_recorded

def main():
    """Main entry point for extracting changed lines."""
    try:
        dataset = ensure_data_loaded_and_integrity_recorded()
        result = extract_changed_lines(dataset)
        print(f"Successfully extracted changed lines for {len(result)} projects.")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
