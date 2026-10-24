import json
import hashlib
import logging
from llmxive_toolkit import paths

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def get_sha256(file_path):
    """Computes the SHA-256 hash of a file in chunks to be memory efficient."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    # Define input paths
    tasks_path = paths.data("raw", "tasks.json")
    skills_path = paths.data("raw", "skills.json")
    checksums_path = paths.data("raw", "checksums.json")

    # Ensure source files exist before attempting to hash
    if not tasks_path.exists():
        log.error(f"Source file not found: {tasks_path}")
        raise FileNotFoundError(f"Missing {tasks_path}")
    if not skills_path.exists():
        log.error(f"Source file not found: {skills_path}")
        raise FileNotFoundError(f"Missing {skills_path}")

    log.info(f"Computing checksums for {tasks_path} and {skills_path}...")
    
    # Compute hashes using the keys required by T003
    checksums = {
        "tasks_json_sha256": get_sha256(tasks_path),
        "skills_json_sha256": get_sha256(skills_path),
    }

    # Write to project-owned checksums file (data/raw/checksums.json)
    # This avoids using platform-owned state/ directories.
    with open(checksums_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)

    log.info(f"Successfully wrote checksums to {checksums_path}")
    print(json.dumps(checksums, indent=2))

if __name__ == "__main__":
    main()
