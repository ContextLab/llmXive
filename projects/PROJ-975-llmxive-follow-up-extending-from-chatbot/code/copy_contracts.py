"""
Copy contract schema files verbatim from the read‑only specs folder into the
project‑owned ``contracts/`` directory and record SHA‑256 hashes.

The mapping of source and destination hashes is written to a JSON file
``contract_hashes.json`` at the repository root (i.e. ``paths.root``). This
location matches the task specification that requires the file to live at
the repository root rather than under ``data/raw/``.
"""
import os
import shutil
import hashlib
import json

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def compute_sha256(file_path: str) -> str:
    """Compute the SHA‑256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def copy_and_hash_contracts():
    """
    Copy all contract schema files verbatim from the read‑only specs folder
    to the project‑owned ``contracts`` directory and record SHA‑256 hashes.

    The hash mapping is written to ``contract_hashes.json`` at the repository
    root (``paths.root``). Files that are missing in the source directory are
    silently skipped so that the script does not fail when optional contract
    schemas have not yet been added.
    """
    # Resolve source (read‑only) and destination (project‑owned) directories.
    spec_contracts_dir = os.path.join(
        paths.root,
        "specs",
        "001-llmxive-follow-up-extending-from-chatbot",
        "contracts",
    )
    dest_contracts_dir = os.path.join(paths.root, "contracts")

    if not os.path.isdir(spec_contracts_dir):
        raise FileNotFoundError(
            f"Source contracts directory not found: {spec_contracts_dir}"
        )

    os.makedirs(dest_contracts_dir, exist_ok=True)

    # Dynamically discover all files in the source contracts folder.
    source_files = [
        f for f in os.listdir(spec_contracts_dir)
        if os.path.isfile(os.path.join(spec_contracts_dir, f))
    ]

    if not source_files:
        log.warning("No contract files found in source directory; nothing to copy.")
        return

    hash_mapping = {}

    for filename in source_files:
        src_path = os.path.join(spec_contracts_dir, filename)
        dst_path = os.path.join(dest_contracts_dir, filename)

        # Copy file verbatim (preserve metadata).
        shutil.copy2(src_path, dst_path)

        # Compute hashes for verification.
        src_hash = compute_sha256(src_path)
        dst_hash = compute_sha256(dst_path)

        hash_mapping[filename] = {"src_hash": src_hash, "dst_hash": dst_hash}
        log.info(
            f"Copied {filename}: src_hash={src_hash}, dst_hash={dst_hash}"
        )

    # Write mapping to the repository root.
    output_path = os.path.join(paths.root, "contract_hashes.json")
    with open(output_path, "w", encoding="utf-8") as out_f:
        json.dump(hash_mapping, out_f, indent=2, sort_keys=True)

    log.info(f"Contract hash mapping written to {output_path}")

def main():
    """Entry point for the script."""
    copy_and_hash_contracts()

if __name__ == "__main__":
    main()
