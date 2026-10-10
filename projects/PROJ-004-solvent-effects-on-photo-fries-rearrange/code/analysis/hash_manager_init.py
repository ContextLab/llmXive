"""
Initialization script to run hash_manager.initialize_solvents_hash() at startup.
This ensures state/artifact_hashes.yaml is populated before any dependent tasks run.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from analysis.hash_manager import initialize_solvents_hash, HashVerificationError

if __name__ == "__main__":
    try:
        result = initialize_solvents_hash()
        print("Hash initialization successful")
        print(f"Solvents hash: {result['hash']}")
        print(f"Stored in: {result['stored_in']}")
        sys.exit(0)
    except HashVerificationError as e:
        print(f"Hash initialization failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)