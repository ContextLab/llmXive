import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_file_hash(file_path: str) -> str:
    return calculate_sha256(file_path)

def verify_file_hash(file_path: str, expected_hash: str) -> bool:
    actual = calculate_sha256(file_path)
    return actual == expected_hash

def generate_checksum_manifest(files: List[str], output_path: str):
    manifest = {}
    for f in files:
        if os.path.exists(f):
            manifest[os.path.basename(f)] = calculate_sha256(f)
        else:
            manifest[os.path.basename(f)] = "MISSING"
    
    with open(output_path, 'w') as out:
        json.dump({"files": manifest, "created": datetime.now().isoformat()}, out, indent=2)

def load_checksum_manifest(manifest_path: str) -> Dict:
    with open(manifest_path, 'r') as f:
        return json.load(f)

def verify_manifest(manifest_path: str) -> bool:
    manifest = load_checksum_manifest(manifest_path)
    for fname, expected in manifest.get("files", {}).items():
        fpath = Path(manifest_path).parent / fname
        if not fpath.exists():
            return False
        if expected != "MISSING":
            if calculate_sha256(str(fpath)) != expected:
                return False
    return True

def get_checksum_report(files: List[str]) -> List[Tuple[str, str]]:
    return [(f, calculate_sha256(f)) for f in files if os.path.exists(f)]

def main():
    pass

if __name__ == "__main__":
    main()
