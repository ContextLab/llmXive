"""
Script to validate research.md and configure target_auc in code/config.yaml.

This task (T007d) ensures that:
1. research.md exists (produced by T007e)
2. target_auc is extracted from research.md
3. code/config.yaml is updated with the target_auc value
4. If research.md is missing or malformed, a blocking error is raised

Output: code/config.yaml with target_auc
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

RESEARCH_MD_PATH = "research.md"
CONFIG_YAML_PATH = "code/config.yaml"

def check_research_md_exists():
    """Check if research.md exists."""
    if not os.path.exists(RESEARCH_MD_PATH):
        raise FileNotFoundError(
            f"CRITICAL: {RESEARCH_MD_PATH} not found. "
            "Task T007e (Generate Research Plan) must complete first."
        )
    logger.info(f"Found {RESEARCH_MD_PATH}")

def extract_target_auc_from_research():
    """
    Extract target_auc value from research.md.
    
    Looks for patterns like:
    - "target_auc: 0.75"
    - "Target AUC: 0.75"
    - "target_auc = 0.75"
    """
    with open(RESEARCH_MD_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern 1: YAML-style key-value
    pattern1 = r'target_auc\s*[:=]\s*([\d.]+)'
    match = re.search(pattern1, content, re.IGNORECASE)
    
    if match:
        target_auc = float(match.group(1))
        logger.info(f"Extracted target_auc from research.md: {target_auc}")
        return target_auc

    # Pattern 2: Natural language "Target AUC is X"
    pattern2 = r'target auc\s+(?:is|of|at)\s+([\d.]+)'
    match = re.search(pattern2, content, re.IGNORECASE)
    
    if match:
        target_auc = float(match.group(1))
        logger.info(f"Extracted target_auc from research.md (natural language): {target_auc}")
        return target_auc

    raise ValueError(
        f"CRITICAL: Could not find 'target_auc' value in {RESEARCH_MD_PATH}. "
        "Please ensure T007e properly defines the target AUC threshold."
    )

def update_config_yaml(target_auc):
    """
    Update code/config.yaml with the target_auc value.
    
    If the file exists, we update the target_auc key.
    If it doesn't exist, we create it with the target_auc and other defaults.
    """
    if os.path.exists(CONFIG_YAML_PATH):
        with open(CONFIG_YAML_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Updating {CONFIG_YAML_PATH} with target_auc = {target_auc}")
        config['target_auc'] = target_auc
        
        with open(CONFIG_YAML_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    else:
        # Create new config file with essential fields
        config = {
            'target_auc': target_auc,
            'temporal_split_ratio': 0.8,
            'seed': 42,
            'memory_limit_mb': 7000,
            'research_plan_version': '1.0',
            'research_plan_date': '2023-10-27',
            'research_plan_author': 'llmXive Automated Science Pipeline'
        }
        
        logger.info(f"Creating {CONFIG_YAML_PATH} with target_auc = {target_auc}")
        os.makedirs(os.path.dirname(CONFIG_YAML_PATH), exist_ok=True)
        
        with open(CONFIG_YAML_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

def validate_config():
    """Validate that config.yaml now contains target_auc."""
    if not os.path.exists(CONFIG_YAML_PATH):
        raise RuntimeError(f"CRITICAL: {CONFIG_YAML_PATH} was not created.")
    
    with open(CONFIG_YAML_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if 'target_auc' not in config:
        raise RuntimeError(
            f"CRITICAL: target_auc not found in {CONFIG_YAML_PATH} after update."
        )
    
    logger.info(f"Validation successful: {CONFIG_YAML_PATH} contains target_auc = {config['target_auc']}")
    return config['target_auc']

def main():
    """Main entry point for T007d."""
    logger.info("Starting T007d: Validate research.md and configure target_auc")
    
    try:
        # Step 1: Check existence of research.md
        check_research_md_exists()
        
        # Step 2: Extract target_auc from research.md
        target_auc = extract_target_auc_from_research()
        
        # Step 3: Write to code/config.yaml
        update_config_yaml(target_auc)
        
        # Step 4: Validate the update
        final_auc = validate_config()
        
        logger.info(f"T007d completed successfully. target_auc = {final_auc}")
        print(f"T007d: Research validated. target_auc configured to {final_auc}")
        return 0
        
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        logger.error(f"T007d FAILED: {str(e)}")
        print(f"ERROR: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error in T007d: {str(e)}")
        print(f"UNEXPECTED ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
