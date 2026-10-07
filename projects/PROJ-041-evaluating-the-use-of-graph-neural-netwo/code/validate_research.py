"""
validate_research.py

Task: T007d - Validate research.md and configure target_auc.

Logic:
1. Check existence of research.md (produced by T007e_gen).
2. Verify code/config.yaml (produced by T007e_cfg) contains 'target_auc'.
3. If either is missing, raise a blocking error.
4. Output: Verified code/config.yaml.

This task is a prerequisite for the entire project; failure here stops execution.
"""

import os
import sys
import re
import logging
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH_MD_PATH = os.path.join(PROJECT_ROOT, "research.md")
CONFIG_YAML_PATH = os.path.join(PROJECT_ROOT, "code", "config.yaml")


def check_research_md_exists():
    """
    Check if research.md exists.
    Returns True if exists, raises FileNotFoundError if not.
    """
    if not os.path.exists(RESEARCH_MD_PATH):
        raise FileNotFoundError(
            f"CRITICAL: research.md not found at {RESEARCH_MD_PATH}. "
            "Task T007e_gen must complete first."
        )
    logger.info(f"research.md found at {RESEARCH_MD_PATH}")
    return True


def extract_target_auc_from_research():
    """
    Extract target_auc value from research.md.
    Returns the float value or raises ValueError if not found.
    """
    try:
        with open(RESEARCH_MD_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for patterns like "target_auc: 0.75" or "Target AUC: 0.75"
        # Case insensitive search
        pattern = r'target[_\s]?auc[:\s]+([0-9.]+)'
        match = re.search(pattern, content, re.IGNORECASE)

        if match:
            value_str = match.group(1)
            try:
                value = float(value_str)
                logger.info(f"Extracted target_auc = {value} from research.md")
                return value
            except ValueError:
                raise ValueError(f"Invalid target_auc value found in research.md: {value_str}")
        else:
            raise ValueError(
                "CRITICAL: 'target_auc' not found in research.md. "
                "Please ensure T007e_gen wrote the value correctly."
            )
    except FileNotFoundError:
        raise FileNotFoundError(f"research.md not found at {RESEARCH_MD_PATH}")


def update_config_yaml(target_auc_value):
    """
    Ensure code/config.yaml exists and contains the correct target_auc.
    If it exists but lacks target_auc, add it. If it has a different value, update it.
    """
    if not os.path.exists(CONFIG_YAML_PATH):
        logger.warning(f"config.yaml not found at {CONFIG_YAML_PATH}. Creating new one.")
        config_data = {
            'target_auc': target_auc_value,
            'temporal_split_ratio': 0.8,
            'seed': 42,
            'memory_limit_mb': 7000
        }
    else:
        logger.info(f"Loading existing config.yaml from {CONFIG_YAML_PATH}")
        with open(CONFIG_YAML_PATH, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}

        if 'target_auc' not in config_data:
            logger.info(f"Adding target_auc = {target_auc_value} to config.yaml")
            config_data['target_auc'] = target_auc_value
        elif config_data['target_auc'] != target_auc_value:
            logger.warning(
                f"Updating target_auc from {config_data['target_auc']} to {target_auc_value} "
                "in config.yaml to match research.md."
            )
            config_data['target_auc'] = target_auc_value
        else:
            logger.info(f"config.yaml already has correct target_auc = {target_auc_value}")

    # Write back to file
    with open(CONFIG_YAML_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Updated config.yaml at {CONFIG_YAML_PATH}")
    return config_data


def validate_config():
    """
    Final validation: Ensure config.yaml exists and has target_auc.
    Returns True if valid, raises error otherwise.
    """
    if not os.path.exists(CONFIG_YAML_PATH):
        raise FileNotFoundError(f"config.yaml not found at {CONFIG_YAML_PATH}")

    with open(CONFIG_YAML_PATH, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)

    if 'target_auc' not in config_data:
        raise ValueError(
            f"CRITICAL: 'target_auc' missing in {CONFIG_YAML_PATH}. "
            "Task T007e_cfg must complete first."
        )

    logger.info(f"Validation successful: config.yaml contains target_auc = {config_data['target_auc']}")
    return True


def main():
    """
    Main execution for T007d.
    """
    logger.info("Starting T007d: Validate research.md and configure target_auc")

    try:
        # Step 1: Check existence of research.md
        logger.info("Step 1: Checking existence of research.md...")
        check_research_md_exists()

        # Step 2: Extract target_auc from research.md
        logger.info("Step 2: Extracting target_auc from research.md...")
        target_auc_value = extract_target_auc_from_research()

        # Step 3: Update/verify config.yaml
        logger.info("Step 3: Updating/verifying code/config.yaml...")
        update_config_yaml(target_auc_value)

        # Step 4: Final validation
        logger.info("Step 4: Final validation of config.yaml...")
        validate_config()

        logger.info("T007d completed successfully. research.md validated and config.yaml updated.")
        return 0

    except (FileNotFoundError, ValueError) as e:
        logger.error(f"CRITICAL ERROR in T007d: {e}")
        logger.error("Execution halted. Please resolve the missing artifacts or configuration.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error in T007d: {e}")
        logger.error("Execution halted.")
        return 1


if __name__ == "__main__":
    sys.exit(main())