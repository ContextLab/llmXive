import yaml
from datetime import datetime
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main():
    """
    Initialize the project state file (state.yaml).
    This file is used to track artifact checksums, configuration, and
    the last update timestamp to ensure reproducibility and data hygiene.

    Required structure (per task T000):
      - artifact_hashes: mapping of relative artifact paths to SHA-256 checksums
      - updated_at: ISO timestamp of the last update
      - config: project-level configuration
    """
    state_path = paths.root / "state.yaml"

    initial_state = {
        "updated_at": datetime.utcnow().isoformat(),
        "config": {
            "project_id": "PROJ-200-the-impact-of-incidental-music-on-autobi",
            "version": "1.0.0",
            "status": "initialized"
        },
        # Maps relative artifact paths to SHA-256 checksum metadata.
        # Required key name per task T000: artifact_hashes.
        "artifact_hashes": {}
    }

    try:
        with open(state_path, "w") as f:
            yaml.dump(initial_state, f, default_flow_style=False)
        log.info(f"Successfully initialized state file at {state_path}")
    except Exception as e:
        log.error(f"Failed to initialize state file: {e}")
        raise

    # Verify the written structure contains all required keys.
    with open(state_path, "r") as f:
        loaded = yaml.safe_load(f)
    for key in ("artifact_hashes", "updated_at", "config"):
        if key not in loaded:
            raise RuntimeError(
                f"state.yaml is missing required key '{key}' after initialization"
            )
    log.info("state.yaml structure verified: artifact_hashes, updated_at, config present.")

if __name__ == "__main__":
    main()