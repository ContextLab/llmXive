import sys
import os
from code.utils.checksum_recorder import record_all_datasets

def main() -> None:
    """Entry point for the record checksums pipeline."""
    print("Starting checksum recording pipeline...")
    try:
        checksums = record_all_datasets()
        print("Checksum recording completed successfully.")
        for name, checksum in checksums.items():
            print(f"  {name}: {checksum}")
    except Exception as e:
        print(f"Error during checksum recording: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
