import yaml
from datetime import datetime
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main():
    """
    Initialize the project state file (state.yaml).
    This file is used to track artifact checksums, configuration, and 
    the last update timestamp to ensure reproducibility and data hygiene.
    """
    state_path = paths.root / "state.yaml"
    
    # Structure defined to be compatible with verify_artifacts.py 
    # which expects a 'files' dictionary for checksums.
    initial_state = {
        "updated_at": datetime.utcnow().isoformat(),
        "config": {
            "project_id": "PROJ-200-the-impact-of-incidental-music-on-autobi",
            "version": "1.0.0",
            "status": "initialized"
        },
        "files": {} # Maps relative paths to checksum metadata
    }
    
    try:
        with open(state_path, "w") as f:
            yaml.dump(initial_state, f, default_flow_style=False)
        log.info(f"Successfully initialized state file at {state_path}")
    except Exception as e:
        log.error(f"Failed to initialize state file: {e}")
        raise

if __name__ == "__main__":
    main()