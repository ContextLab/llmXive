import os
import yaml
import logging

# Ensure logging is configured if not already
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Validates and ensures the contract schemas exist in the contracts/ directory.
    This script is a placeholder to trigger the creation or verification of schema files.
    Since the schemas are defined as artifacts in T009, this script ensures they are loadable.
    """
    contracts_dir = "contracts"
    schema_files = [
        "task.schema.yaml",
        "skill.schema.yaml",
        "experiment_log.schema.yaml"
    ]

    logger.info(f"Checking for schema files in {contracts_dir}...")

    if not os.path.exists(contracts_dir):
        logger.error(f"Directory {contracts_dir} does not exist. Please run T001 first.")
        return False

    all_found = True
    for filename in schema_files:
        filepath = os.path.join(contracts_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    schema = yaml.safe_load(f)
                logger.info(f"Found valid YAML schema: {filename}")
                # Basic validation check: ensure 'properties' exist for experiment_log
                if filename == "experiment_log.schema.yaml":
                    required_props = [
                        "task_id", "skill_id", "success", "latency", "tokens",
                        "retrieval_precision", "retrieval_diversity",
                        "pruning_risk_count", "library_size", "pruning_enabled"
                    ]
                    if "properties" in schema:
                        missing = [p for p in required_props if p not in schema["properties"]]
                        if missing:
                            logger.error(f"Schema {filename} missing required properties: {missing}")
                            all_found = False
                        else:
                            logger.info(f"Schema {filename} contains all required properties.")
            except yaml.YAMLError as e:
                logger.error(f"Invalid YAML in {filename}: {e}")
                all_found = False
        else:
            logger.error(f"Missing schema file: {filename}")
            all_found = False

    if all_found:
        logger.info("All contract schemas are present and valid.")
        return True
    else:
        logger.error("Schema validation failed.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)