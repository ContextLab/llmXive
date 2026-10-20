import json
import yaml
import hashlib
from datetime import datetime
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def get_file_sha256(file_path):
    """Computes the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    checksums_path = paths.data("raw", "checksums.json")
    # Re-scoped from state/projects/... to a project-owned path to avoid shadowing platform state
    state_path = paths.data("raw", "project_state.yaml")

    if not checksums_path.exists():
        log.error(f"Checksums file not found at {checksums_path}")
        raise FileNotFoundError(f"Missing {checksums_path}")

    # Read existing checksums for tasks and skills
    with open(checksums_path, 'r') as f:
        checksums_data = json.load(f)

    # Calculate the hash of the checksums file itself
    checksums_sha = get_file_sha256(checksums_path)

    # Construct state mapping
    state = {
        "tasks_json_sha256": checksums_data.get("tasks.json"),
        "skills_json_sha256": checksums_data.get("skills.json"),
        "checksums_json_sha256": checksums_sha,
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }

    # Write to project-owned directory
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

    log.info(f"Project state updated at {state_path}")

if __name__ == "__main__":
    main()
