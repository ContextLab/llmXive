"""
Configuration Migration Utility for PROJ-024

Merges derived statistics from the main config.yaml into the project state file,
ensuring config.yaml remains under the 2KB limit (FR-009).
"""
import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
# The project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"
CONFIG_SIZE_LIMIT = 2048  # 2KB

# Keys to migrate (derived statistics)
KEYS_TO_MIGRATE = [
    "dataset_stats",
    "inference_results",
    "simulation_metrics"
]

def load_yaml(path: Path) -> dict:
    """Load a YAML file, returning empty dict if not found or empty."""
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        return data if data else {}

def save_yaml(data: dict, path: Path) -> None:
    """Save data to a YAML file, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        # Use sort_keys=False to preserve insertion order for readability
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def migrate_config() -> bool:
    """
    Main migration logic.
    Returns True if successful, False otherwise.
    """
    logger.info(f"Starting config migration for project PROJ-024")
    logger.info(f"Config path: {CONFIG_PATH}")
    logger.info(f"State file path: {STATE_FILE}")

    # 1. Load current config
    if not CONFIG_PATH.exists():
        logger.error(f"Config file not found at {CONFIG_PATH}")
        return False

    config = load_yaml(CONFIG_PATH)
    logger.info(f"Loaded config with {len(config)} top-level keys: {list(config.keys())}")

    # 2. Load or initialize state file
    state = load_yaml(STATE_FILE)
    if "projects" not in state:
        state["projects"] = {}
    
    proj_key = "PROJ-024-bayesian-nonparametrics-for-anomaly-dete"
    if proj_key not in state["projects"]:
        state["projects"][proj_key] = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            "artifacts": {},
            "derived_statistics": {}
        }

    project_state = state["projects"][proj_key]
    # Ensure derived_statistics exists even if the key was missing in loaded state
    if "derived_statistics" not in project_state:
        project_state["derived_statistics"] = {}
    
    derived_stats = project_state["derived_statistics"]

    migrated_count = 0
    missing_keys = []

    # 3. Migrate keys
    for key in KEYS_TO_MIGRATE:
        if key in config:
            logger.info(f"Migrating key: '{key}'")
            # Deep copy to avoid modifying config before pop() if needed later, 
            # but pop is fine here as we save config after.
            derived_stats[key] = config.pop(key)
            migrated_count += 1
        else:
            logger.info(f"Key '{key}' not found in config (skipping)")
            missing_keys.append(key)

    # 4. Update state file metadata and save
    project_state["derived_statistics"] = derived_stats
    project_state["metadata"]["updated_at"] = datetime.now().isoformat()
    
    save_yaml(state, STATE_FILE)
    logger.info(f"Updated state file at {STATE_FILE}")

    # 5. Save reduced config
    save_yaml(config, CONFIG_PATH)
    logger.info(f"Saved reduced config to {CONFIG_PATH}")

    # 6. Verify size
    current_size = os.path.getsize(CONFIG_PATH)
    logger.info(f"Config file size: {current_size} bytes (limit: {CONFIG_SIZE_LIMIT})")

    if current_size > CONFIG_SIZE_LIMIT:
        logger.error(f"Config file size ({current_size}) exceeds limit ({CONFIG_SIZE_LIMIT})")
        return False

    if migrated_count == 0:
        logger.warning("No keys were migrated. Config might already be clean or keys missing.")

    logger.info(f"Migration successful. Migrated {migrated_count} keys.")
    return True

def main():
    """Entry point for script execution."""
    try:
        success = migrate_config()
        if success:
            print("SUCCESS: Configuration migration completed.")
            sys.exit(0)
        else:
            print("FAILURE: Configuration migration failed.")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during migration: {e}")
        print(f"FAILURE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()