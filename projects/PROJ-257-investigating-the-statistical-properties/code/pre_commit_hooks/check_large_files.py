"""
Pre-commit hook to check for large file uploads.
Rejects files larger than 10MB (10 * 1024 * 1024 bytes).
"""
import os
import sys
from pathlib import Path

MAX_SIZE_MB = 10
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

# Common large data extensions to check
LARGE_FILE_EXTS = {'.h5', '.hdf5', '.csv', '.parquet', '.feather', '.pkl', '.pickle', '.npy', '.npz', '.tar', '.gz', '.zip'}

def check_large_files(filenames):
    """
    Check if any of the provided files exceed the size limit.
    Returns 0 if all files are OK, 1 if any are too large.
    """
    violations = []
    for filename in filenames:
        path = Path(filename)
        if not path.exists():
            continue
        
        size_bytes = path.stat().st_size
        if size_bytes > MAX_SIZE_BYTES:
            size_mb = size_bytes / (1024 * 1024)
            violations.append(f"{filename} ({size_mb:.2f} MB)")

    if violations:
        print(f"Error: The following files exceed the {MAX_SIZE_MB}MB limit:")
        for v in violations:
            print(f"  - {v}")
        print("Please remove these files from git tracking or use git-lfs.")
        return 1
    return 0

def main():
    if len(sys.argv) < 2:
        print("No files to check.")
        return 0
    return check_large_files(sys.argv[1:])

if __name__ == "__main__":
    sys.exit(main())