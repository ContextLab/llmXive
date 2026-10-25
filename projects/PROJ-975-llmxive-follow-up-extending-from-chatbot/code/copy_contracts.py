import os
import shutil
import hashlib
import json
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# List of contract filenames to copy
CONTRACT_FILES = [
    "task.schema.yaml",
    "skill.schema.yaml",
    "experiment_log.schema.yaml",
    "execution_log.schema.yaml",
    "metrics.schema.yaml",
]

def compute_sha256(file_path: str) -> str:
    """Compute the SHA‑256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def copy_and_hash_contracts():
    """Copy contract schema files verbatim from the read‑only specs folder
    to the project‑owned contracts directory and record SHA‑256 hashes."""
    # Resolve source and destination directories
    spec_contracts_dir = os.path.join(
        paths.root,
        "specs",
        "001-llmxive-follow-up-extending-from-chatbot",
        "contracts",
    )
    dest_contracts_dir = os.path.join(paths.root, "contracts")

    if not os.path.isdir(spec_contracts_dir):
        raise FileNotFoundError(f"Source contracts directory not found: {spec_contracts_dir}")

    os.makedirs(dest_contracts_dir, exist_ok=True)

    hash_mapping = {}

    for filename in CONTRACT_FILES:
        src_path = os.path.join(spec_contracts_dir, filename)
        dst_path = os.path.join(dest_contracts_dir, filename)

        if not os.path.isfile(src_path):
            raise FileNotFoundError(f"Source contract file missing: {src_path}")

        # Copy file verbatim
        shutil.copy2(src_path, dst_path)

        # Compute hashes
        src_hash = compute_sha256(src_path)
        dst_hash = compute_sha256(dst_path)

        hash_mapping[filename] = {"src_hash": src_hash, "dst_hash": dst_hash}
        log.info(f"Copied {filename}: src_hash={src_hash}, dst_hash={dst_hash}")

    # Write mapping to data/raw/contract_hashes.json
    output_path = paths.data("raw", "contract_hashes.json")
    with open(output_path, "w", encoding="utf-8") as out_f:
        json.dump(hash_mapping, out_f, indent=2, sort_keys=True)

    log.info(f"Contract hash mapping written to {output_path}")

def main():
    """Entry point for the script."""
    copy_and_hash_contracts()

if __name__ == "__main__":
    main()
