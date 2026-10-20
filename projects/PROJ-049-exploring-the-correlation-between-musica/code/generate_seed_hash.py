import seed
"""Generate the SHA‑256 hash of seed.py and write it to seed_hash.txt.

This script is executed as part of the task to ensure that `code/seed_hash.txt`
contains the correct hash for verification.
"""
import hashlib
from pathlib import Path

# Resolve paths relative to this script's directory
seed_path = Path(__file__).parent / "seed.py"
hash_path = Path(__file__).parent / "seed_hash.txt"

# Read the seed.py file and compute its SHA‑256 hash
content = seed_path.read_bytes()
sha256 = hashlib.sha256(content).hexdigest()

# Write the hash to seed_hash.txt
hash_path.write_text(sha256)