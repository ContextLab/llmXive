"""
Main Orchestration Script for the Impact of Incidental Music on Autobiographical Memory Retrieval.

This script runs the full pipeline in the correct order:
1. Data Ingestion (T023 -> T015 -> T014 -> T016)
2. Cue Matching (T022 -> T047 -> T024)
3. Aggregation (T025 -> T026 -> T027 -> T036)
4. Modeling (T033 -> T034 -> T044 -> T045)
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_project_root, ensure_directories, get_config_dict
from utils import get_logger, setup_logging

logger = get_logger(__name__)

def run_pipeline():
    """Run the full pipeline."""
    logger.info("Starting full pipeline...")

    # 1. Setup
    root = get_project_root()
    ensure_directories()

    # 2. Data Ingestion
    logger.info("Phase 1: Data Ingestion")
    try:
        import data_ingestion
        data_ingestion.main()
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        raise

    # 3. Cue Matching
    logger.info("Phase 2: Cue Matching")
    try:
        import cue_matching
        cue_matching.main()
    except Exception as e:
        logger.error(f"Cue matching failed: {e}")
        raise

    # 4. Aggregation
    logger.info("Phase 3: Aggregation")
    try:
        import aggregation
        aggregation.main()
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise

    # 5. Modeling
    logger.info("Phase 4: Modeling")
    try:
        import modeling
        modeling.main()
    except Exception as e:
        logger.error(f"Modeling failed: {e}")
        raise

    logger.info("Pipeline completed successfully.")

def main():
    """Entry point."""
    setup_logging()
    run_pipeline()

if __name__ == "__main__":
    main()
