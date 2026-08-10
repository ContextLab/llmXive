"""
src/main.py: Orchestration script for the llmXive follow-up pipeline.

This script implements the Reference-Validator gate before data loading
to ensure citation integrity, then orchestrates the full pipeline execution.

Flow:
1. Validate Reference Citations (Gate)
2. Load Data (IA-Bench + WISE-Verified)
3. Compute Syntactic Complexity Scores
4. Route Prompts (Low/Med/High)
5. Execute Hybrid Pipeline (Rule-based vs Agent)
6. Measure Fidelity & Regression Analysis
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config import CONFIG, SEEDS
from src.utils import setup_logging, get_logger
from src.utils.data_loader import (
    load_ia_bench,
    load_wise_verified,
    validate_references,
    ReferenceValidator
)
from src.scoring.run_scoring import run_scoring_pipeline
from src.pipeline.runner import run_hybrid_pipeline
from src.fidelity.run_fidelity_analysis import run_fidelity_analysis

logger = get_logger(__name__)

def validate_citations_gate():
    """
    Reference-Validator Gate:
    Verifies that the data sources cited in the plan/spec match the actual
    dataset IDs being fetched. This must run BEFORE any data loading.
    """
    logger.info(">>> GATE: Reference-Validator Citation Check")
    
    validator = ReferenceValidator()
    
    # Validate IA-Bench citation
    ia_valid = validator.validate_citation(
        source_name="IA-Bench",
        expected_citation=CONFIG.CITATIONS.get("IA_BENCH", "Unknown"),
        dataset_id="llmXive/ia-bench" # Or the actual ID from plan.md
    )
    
    # Validate WISE-Verified citation
    wise_valid = validator.validate_citation(
        source_name="WISE-Verified",
        expected_citation=CONFIG.CITATIONS.get("WISE_VERIFIED", "Unknown"),
        dataset_id="llmXive/wise-verified" # Or the actual ID from plan.md
    )
    
    if not (ia_valid and wise_valid):
        logger.error("Citation validation FAILED. Aborting pipeline to prevent data drift.")
        raise RuntimeError("Reference-Validator Gate Failed: Citation mismatch detected.")
    
    logger.info(">>> GATE PASSED: Citations verified successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="llmXive Orchestration Script")
    parser.add_argument("--skip-scoring", action="store_true", help="Skip scoring phase")
    parser.add_argument("--skip-routing", action="store_true", help="Skip routing/execution phase")
    parser.add_argument("--skip-fidelity", action="store_true", help="Skip fidelity analysis phase")
    args = parser.parse_args()

    # Setup logging
    setup_logging(level=logging.INFO)
    logger.info("Starting llmXive Pipeline Orchestration")

    try:
        # 1. GATE: Validate Citations
        validate_citations_gate()

        # 2. Load Data (Side effects: downloads to data/raw/)
        logger.info("Loading datasets...")
        # These functions handle their own validation and failure modes
        # as per T006a-g and T007
        ia_data = load_ia_bench()
        wise_data = load_wise_verified()
        
        # Validate references specifically
        validate_references(ia_data)

        # 3. Scoring Phase
        if not args.skip_scoring:
            logger.info(">>> Phase 1: Syntactic Complexity Scoring")
            run_scoring_pipeline(ia_data, wise_data)
        else:
            logger.warning("Skipping Scoring Phase (already done or requested)")

        # 4. Routing & Execution Phase
        if not args.skip_routing:
            logger.info(">>> Phase 2: Hybrid Routing & Real Execution")
            # This triggers the actual agent pipeline for high-complexity prompts
            run_hybrid_pipeline()
        else:
            logger.warning("Skipping Routing Phase (already done or requested)")

        # 5. Fidelity Analysis Phase
        if not args.skip_fidelity:
            logger.info(">>> Phase 3: Fidelity Measurement & Regression")
            run_fidelity_analysis()
        else:
            logger.warning("Skipping Fidelity Analysis Phase (already done or requested)")

        logger.info("Pipeline execution completed successfully.")

    except RuntimeError as e:
        logger.error(f"Pipeline failed with critical error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during pipeline execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()