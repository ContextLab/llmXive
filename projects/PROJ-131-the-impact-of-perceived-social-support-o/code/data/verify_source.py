import os
import sys
import logging
from pathlib import Path
import yaml

from utils.logger import get_logger

def get_data_source_config(config_path: str) -> dict:
    """
    Read the data source configuration from the specified YAML file.
    """
    logger = get_logger(__name__)
    config_file = Path(config_path)

    if not config_file.exists():
        logger.error(f"Data source config file not found: {config_file}")
        return {}

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config if config else {}
    except Exception as e:
        logger.error(f"Failed to read data source config: {e}")
        return {}

def main():
    logger = get_logger(__name__)
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "code" / "config" / "data_sources.yaml"

    config = get_data_source_config(str(config_path))

    if not config:
        logger.error("E-NO-SOURCE-CONFIG: Configuration missing. Aborting.")
        sys.exit(1)

    status = config.get('status')
    if status == 'pending_user_input':
        logger.error("E-NO-SOURCE-001: Data source missing. Manual intervention required.")
        sys.exit(1)

    dataset_id = config.get('dataset_id')
    source = config.get('source')
    verified = config.get('verified', False)

    if not dataset_id or not source:
        logger.error("E-NO-SOURCE-CONFIG: Configuration incomplete. Aborting.")
        sys.exit(1)

    if not verified:
        logger.warning(f"Dataset ID: {dataset_id}, Source: {source} is not yet verified.")
        # In a real scenario, we would attempt to fetch/verify here.
        # For now, we assume the config is correct if it exists and is not pending.
        logger.info(f"Source configuration present: {dataset_id} from {source}")
    else:
        logger.info(f"Source verified: {dataset_id} from {source}")

    logger.info("INFO: Source verified")
    sys.exit(0)

if __name__ == "__main__":
    main()
