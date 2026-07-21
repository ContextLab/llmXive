"""
Main Orchestration Script for the Impact of Incidental Music on Autobiographical Memory Retrieval.

This script runs the full pipeline in the strict order required by the specification:
1. Data Ingestion (T023 -> T015 -> T014 -> T016)
2. Cue Matching (T022 -> T047 -> T024)
3. Aggregation (T025 -> T026 -> T027 -> T036)
4. Modeling (T033 -> T034 -> T044 -> T045)

Critical Ordering Constraint:
- Fallback Check (T023) MUST run BEFORE Frequency Filter (T015) to prevent false fallback triggers.
- Frequency Filter (T015) MUST run BEFORE Score Calculation (T014/T016).
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
    """Run the full pipeline in the correct sequential order."""
    logger.info("Starting full pipeline...")

    # 1. Setup
    root = get_project_root()
    ensure_directories()

    # 2. Data Ingestion Phase (Strict Order: T023 -> T015 -> T014 -> T016)
    logger.info("Phase 1: Data Ingestion (Order: Fallback Check -> Frequency Filter -> Score Calculation)")
    try:
        import data_ingestion
        # T023: Fallback Check (Global Exposure)
        # T015: Frequency Filter
        # T014/T016: Score Calculation (Ratio & Residualized)
        # The main() function in data_ingestion.py is responsible for executing these steps in the correct internal order.
        data_ingestion.main()
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        raise

    # 3. Cue Matching Phase
    logger.info("Phase 2: Cue Matching")
    try:
        import cue_matching
        cue_matching.main()
    except Exception as e:
        logger.error(f"Cue matching failed: {e}")
        raise

    # 4. Aggregation Phase
    logger.info("Phase 3: Aggregation")
    try:
        import aggregation
        aggregation.main()
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise

    # 5. Modeling Phase
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