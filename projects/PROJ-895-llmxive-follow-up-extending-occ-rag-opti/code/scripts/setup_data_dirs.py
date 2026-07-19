import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

def ensure_dir(path: str) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def init_checksums(checksum_file: str) -> Dict[str, Any]:
    """Initialize or load the checksums.json file."""
    if os.path.exists(checksum_file):
        with open(checksum_file, "r") as f:
            return json.load(f)
    return {
        "version": "1.0",
        "artifacts": {}
    }

def register_artifact(
    checksums: Dict[str, Any],
    artifact_name: str,
    path: str,
    source: str,
    checksum: Optional[str] = None
) -> Dict[str, Any]:
    """Register an artifact in the checksums dictionary."""
    checksums["artifacts"][artifact_name] = {
        "path": path,
        "source": source,
        "status": "verified" if checksum else "pending",
        "checksum": checksum,
        "timestamp": None
    }
    return checksums

def main():
    """Main entry point to setup data directories and initialize checksums."""
    # Ensure required directories exist
    ensure_dir("data/raw")
    ensure_dir("data/processed")
    
    # Initialize or update checksums file
    checksums_file = "data/checksums.json"
    checksums = init_checksums(checksums_file)
    
    # Register expected artifacts (placeholders for now)
    # These will be populated by T004 and T004.1 when datasets are fetched
    if "occ_rag_corpus" not in checksums["artifacts"]:
        checksums = register_artifact(
            checksums,
            "occ_rag_corpus",
            "data/raw/occ_rag_corpus.jsonl",
            "nlp4research/occ-rag-synthetic-corpus"
        )
    
    if "occ_rag_model_weights" not in checksums["artifacts"]:
        checksums = register_artifact(
            checksums,
            "occ_rag_model_weights",
            "data/raw/occ-rag-1.7b-frozen",
            "nlp4research/occ-rag-1.7b-frozen"
        )
    
    # Save updated checksums
    with open(checksums_file, "w") as f:
        json.dump(checksums, f, indent=2)
    
    print(f"Data directories setup complete. Checksums file: {checksums_file}")

if __name__ == "__main__":
    main()