"""
Control Set Configuration Generator.

Implements the "Control Set" requirement from Plan.md "Complexity Tracking"
to support FR-003 (Binary AUC), overriding FR-002's strict "subtle only" constraint.
"""
import os
import json
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any

# Import config utilities to ensure paths are correct
# We assume config.py has been loaded or will be loaded by the main entry point
# For this utility, we rely on standard project paths
from config import PathConfig

logger = logging.getLogger(__name__)

# Hardcoded mapping of class names to dataset IDs (ESC-50 / AudioSet compatible)
# These represent "Control Set" classes: low-frequency, sustained amplitude.
# This list overrides FR-002's "subtle only" constraint as per Plan.md authorization.
CONTROL_CLASS_MAPPING: Dict[str, int] = {
    "engine hum": 0,
    "wind": 1,
    "rain": 2,
    "babbling": 3,
    "chainsaw": 4,
    "drilling": 5,
    "gunshot": 6,
    "jackhammer": 7,
    "siren": 8,
    "street music": 9
}

def get_control_classes() -> List[int]:
    """
    Returns the list of class IDs that constitute the Control Set.

    Returns:
        List[int]: List of integer class IDs corresponding to non-subtle classes.
    """
    return list(CONTROL_CLASS_MAPPING.values())

def generate_control_config(output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Generates the control set configuration and writes it to a YAML file.

    This function implements the "Control Set" requirement from Plan.md
    "Complexity Tracking" to support FR-003 (Binary AUC).

    Args:
        output_path: Optional path to write the YAML file. If None, uses
                     data/processed/class_config_control.yaml.

    Returns:
        Dict[str, Any]: The generated configuration dictionary.

    Raises:
        IOError: If the file cannot be written.
    """
    # Determine output path
    if output_path is None:
        # Use PathConfig to get the processed data directory
        try:
            # Attempt to get config; if it fails, fallback to relative path
            path_config = PathConfig()
            base_dir = path_config.project_root if hasattr(path_config, 'project_root') else Path.cwd()
            output_dir = base_dir / "data" / "processed"
        except Exception:
            output_dir = Path("data") / "processed"

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / "class_config_control.yaml")

    # Prepare configuration content
    config_content = {
        "criteria": {
            "description": "Low-frequency, sustained amplitude classes (non-subtle)",
            "source": "Plan.md Complexity Tracking (Override FR-002)",
            "definition": "Classes with dominant frequency < 8kHz AND amplitude > -40dBFS"
        },
        "control_classes": get_control_classes(),
        "class_names": list(CONTROL_CLASS_MAPPING.keys()),
        "mapping": CONTROL_CLASS_MAPPING
    }

    # Atomic write to ensure consistency
    temp_path = str(output_path) + ".tmp"
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_content, f, default_flow_style=False, sort_keys=False)
        
        # Atomic rename
        os.replace(temp_path, output_path)
        logger.info(f"Control set config written to {output_path}")
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error(f"Failed to write control set config: {e}")
        raise

    return config_content

def main() -> int:
    """
    Main entry point for executing the control set definition.

    Returns:
        int: 0 on success, 1 on failure.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        logger.info("Generating control set configuration...")
        config = generate_control_config()
        logger.info(f"Control classes identified: {config['control_classes']}")
        return 0
    except Exception as e:
        logger.exception(f"Error generating control set config: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
