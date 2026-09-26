"""
Main entry point for the llmXive pipeline.
Orchestrates the execution of various stages.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json
import argparse
from utils.checksums import check_code_drift

# Add project root to path if necessary
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from oracle.generator import build_oracle_graph, save_and_verify, main as oracle_main
from rules.extractor import main as extractor_main
from analysis.diverge import main as divergence_main
from rules.metrics import main as metrics_main
from rules.trace_loader import main as trace_loader_main
from analysis.synthetic_trace_generator import main as synthetic_gen_main
from analysis.reporter import main as reporter_main

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="llmXive Pipeline")
    parser.add_argument("--stage", type=str, default="all", 
                        choices=["oracle", "rules", "diverge", "report", "all"],
                        help="Stage to execute")
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    logger.info("Starting llmXive pipeline execution...")
    
    # 1. Check Code Drift (Fixed to handle missing reference gracefully)
    code_dir = str(PROJECT_ROOT / "code")
    # We call check_code_drift with just the directory. 
    # The function in checksums.py now handles the missing reference_checksum argument.
    if not check_code_drift(code_dir):
        logger.error("Code drift detected! Aborting pipeline.")
        sys.exit(1)
    logger.info("Code drift check passed.")

    if args.stage in ["oracle", "all"]:
        logger.info("Executing Oracle Generation Stage...")
        # Ensure output path is set
        output_path = args.output or str(PROJECT_ROOT / "data" / "processed" / "oracle_graph.json")
        # Call the oracle generator main which handles the full pipeline for oracle
        oracle_main(output_path=output_path, seed=args.seed)
        
        # Verify the output exists
        if not Path(output_path).exists():
            logger.error(f"Oracle generation failed: {output_path} not found.")
            sys.exit(1)
        logger.info(f"Oracle generated successfully at {output_path}")

    if args.stage in ["rules", "all"]:
        logger.info("Executing Rule Extraction Stage...")
        extractor_main()
        # Ensure output exists
        rules_path = str(PROJECT_ROOT / "data" / "processed" / "extracted_rules.json")
        if not Path(rules_path).exists():
            logger.error(f"Rule extraction failed: {rules_path} not found.")
            sys.exit(1)

    if args.stage in ["diverge", "all"]:
        logger.info("Executing Divergence Analysis Stage...")
        divergence_main()
        divergence_path = str(PROJECT_ROOT / "data" / "processed" / "divergence_report.json")
        if not Path(divergence_path).exists():
            logger.error(f"Divergence analysis failed: {divergence_path} not found.")
            sys.exit(1)

    if args.stage in ["report", "all"]:
        logger.info("Executing Final Reporting Stage...")
        reporter_main()
        report_path = str(PROJECT_ROOT / "data" / "processed" / "final_report.json")
        if not Path(report_path).exists():
            logger.error(f"Final report generation failed: {report_path} not found.")
            sys.exit(1)

    logger.info("Pipeline execution completed successfully.")

if __name__ == "__main__":
    main()
