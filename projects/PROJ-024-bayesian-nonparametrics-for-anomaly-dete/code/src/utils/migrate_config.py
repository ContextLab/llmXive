"""
Migrate derived statistics from config.yaml to the state file.

This script moves keys 'dataset_stats', 'inference_results', and 'simulation_metrics'
from projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/config.yaml 
to state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml,
then verifies the config file size is under 2048 bytes.

If the keys do not exist in config.yaml, it ensures the state file structure exists
with empty placeholders to satisfy the migration requirement and ensures the config 
remains minimal.
"""
import os
import sys
import yaml
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
# The script is at code/src/utils/migrate_config.py
# Project root is 4 levels up: code/src/utils/ -> code/src/ -> code/ -> projects/.../
# Note: The project structure is projects/PROJ-024-.../code/...
# We assume the script is run from the project root or we calculate relative to this file
# The task description says: "from `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/config.yaml`"
# So we need to locate the project root dynamically.

# Assuming this file is at: projects/PROJ-024-.../code/src/utils/migrate_config.py
# Then PROJECT_ROOT = parent of parent of parent of parent of this file
# But wait, the provided path in the prompt shows:
# code/config.yaml (at repo root relative to project?)
# The task says: "from `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/config.yaml`"
# Let's assume the script is run from the repo root, or we calculate based on __file__

# Let's try to find the project root by looking for 'code/config.yaml' and 'state/projects'
# Or simply assume the structure is:
# <repo_root>/projects/PROJ-024-.../code/config.yaml
# <repo_root>/state/projects/PROJ-024-...yaml

# If this file is at code/src/utils/migrate_config.py, then:
# PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
# But the prompt says the project is PROJ-024-... inside projects/

# Let's assume the script is executed from the repo root, and we use relative paths
# OR we calculate based on the known structure.

# Given the task description:
# "from `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/config.yaml`"
# "to `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`"

# Let's assume the script is run from the repo root.
# If not, we can try to find the project root.

# For robustness, let's try to locate the project root by searching for the config file
# starting from the script's location.

def find_project_root(start_path: Path) -> Path:
    """Find the project root by looking for 'code/config.yaml'."""
    current = start_path
    while current != current.parent:
        if (current / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete" / "code" / "config.yaml").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root")

PROJECT_ROOT = find_project_root(Path(__file__).resolve())
CONFIG_PATH = PROJECT_ROOT / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete" / "code" / "config.yaml"
STATE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"
MAX_CONFIG_SIZE = 2048  # 2KB

KEYS_TO_MIGRATE = ['dataset_stats', 'inference_results', 'simulation_metrics']

def load_yaml(path: Path) -> dict:
    """Load a YAML file."""
    if not path.exists():
        logger.warning(f"File not found: {path}. Returning empty dict.")
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        if not content.strip():
            return {}
        return yaml.safe_load(content) or {}

def save_yaml(path: Path, data: dict) -> None:
    """Save data to a YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def migrate_config() -> bool:
    """
    Migrate derived statistics from config to state file.
    
    Returns:
        True if migration was successful and config size is compliant, False otherwise.
    """
    logger.info(f"Project root found at: {PROJECT_ROOT}")
    logger.info(f"Config path: {CONFIG_PATH}")
    logger.info(f"State path: {STATE_PATH}")
    
    if not CONFIG_PATH.exists():
        logger.error(f"Config file not found at {CONFIG_PATH}")
        return False
        
    config = load_yaml(CONFIG_PATH)
    logger.info(f"Loaded config with keys: {list(config.keys())}")
    
    if not STATE_PATH.exists():
        logger.info(f"State file not found at {STATE_PATH}. Creating new state file.")
        state = {}
    else:
        state = load_yaml(STATE_PATH)
        logger.info(f"Loaded existing state file.")
    
    # Ensure state has the required nested structure
    if 'projects' not in state:
        state['projects'] = {}
    proj_key = "PROJ-024-bayesian-nonparametrics-for-anomaly-dete"
    if proj_key not in state['projects']:
        state['projects'][proj_key] = {}
    
    project_state = state['projects'][proj_key]
    if 'derived_statistics' not in project_state:
        project_state['derived_statistics'] = {}
    
    derived_stats = project_state['derived_statistics']
    migrated_count = 0
    keys_found = 0
    
    for key in KEYS_TO_MIGRATE:
        if key in config:
            logger.info(f"Migrating key '{key}' from config to state")
            derived_stats[key] = config.pop(key)
            keys_found += 1
            migrated_count += 1
        else:
            logger.info(f"Key '{key}' not found in config. Initializing in state if missing.")
            # Initialize in state if missing to ensure structure exists
            if key not in derived_stats:
                derived_stats[key] = {}
    
    # Save state to ensure structure is updated (even if just initializing empty dicts)
    logger.info(f"Saving updated state to {STATE_PATH}")
    save_yaml(STATE_PATH, state)
    
    # Only save config if we actually removed keys
    if migrated_count > 0:
        logger.info(f"Saving updated config to {CONFIG_PATH}")
        save_yaml(CONFIG_PATH, config)
    else:
        logger.info("No keys to migrate from config. Config remains unchanged.")
    
    # Verify config size
    if not CONFIG_PATH.exists():
        logger.error("Config file missing after migration!")
        return False
        
    size_bytes = os.path.getsize(CONFIG_PATH)
    logger.info(f"Config file size: {size_bytes} bytes (limit: {MAX_CONFIG_SIZE} bytes)")
    
    if size_bytes > MAX_CONFIG_SIZE:
        logger.error(f"Config file size ({size_bytes}) exceeds limit ({MAX_CONFIG_SIZE})")
        return False
        
    logger.info("Config migration and size verification successful.")
    return True

def main():
    """Entry point for the migration script."""
    try:
        success = migrate_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception(f"Migration failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
