import sys
from pathlib import Path
from utils.checksums import verify_checksums, CHECKSUM_MANIFEST_FILE

def main():
    """
    Verify the integrity of the data directory structure against the stored manifest.
    Exits with code 0 if all checksums match, 1 otherwise.
    """
    print("Verifying data integrity...")
    success = verify_checksums(CHECKSUM_MANIFEST_FILE)
    
    if not success:
        print("Integrity check failed. Please investigate the mismatches above.")
        sys.exit(1)
    else:
        print("Integrity check passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
