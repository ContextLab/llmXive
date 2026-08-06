"""
Main entry point for the prompt complexity evaluation pipeline.
Orchestrates data fetching, prompt generation, LLM querying, code execution,
and statistical analysis.
"""

import argparse
import sys
from pathlib import Path

from config import Paths, get_project_id
from utils.logger import get_logger, setup_structured_logger
from data.fetcher import download_human_eval, load_human_eval
from prompts.generator import generate_prompt_variants
from llm.orchestrator import run_orchestrator
from data.storage import save_variants_to_parquet
from execution.write_results import run_execution_and_analysis, write_results_to_csv
from analysis.stats import run_full_analysis, write_analysis_summary_to_csv
from utils.versioning import record_data_generation_state

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run the prompt complexity evaluation pipeline.")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Number of HumanEval problems to process (None = all)."
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip fetching HumanEval dataset if already present."
    )
    args = parser.parse_args()

    project_id = get_project_id()
    logger.info(f"Starting pipeline for project: {project_id}")

    # 1. Fetch Data
    if not args.skip_fetch:
        logger.info("Fetching HumanEval dataset...")
        download_human_eval()
    
    logger.info("Loading HumanEval dataset...")
    problems = load_human_eval()
    if args.sample_size:
        problems = problems[:args.sample_size]
        logger.info(f"Using sample of {args.sample_size} problems.")
    
    logger.info(f"Loaded {len(problems)} problems.")

    # 2. Generate Prompts
    logger.info("Generating prompt variants...")
    variants = generate_prompt_variants(problems)
    logger.info(f"Generated {len(variants)} prompt variants.")

    # 3. Save Variants
    logger.info("Saving prompt variants to parquet...")
    save_variants_to_parquet(variants)
    logger.info(f"Saved to {Paths.PROCESSED_DATA_DIR / 'prompt_variants.parquet'}")

    # 4. Query LLM
    logger.info("Querying LLM for code generation...")
    # The orchestrator returns GeneratedCode objects which include the metadata
    generated_codes = run_orchestrator(variants)
    logger.info(f"Received {len(generated_codes)} code samples from LLM.")

    # 5. Execute and Analyze
    logger.info("Executing code and running analysis...")
    # This function handles execution, aggregation, and writing execution_outcomes.csv
    run_execution_and_analysis(generated_codes)
    logger.info(f"Execution results written to {Paths.RESULTS_DIR / 'execution_outcomes.csv'}")

    # 6. Statistical Analysis
    logger.info("Running statistical analysis...")
    analysis_results = run_full_analysis()
    write_analysis_summary_to_csv(analysis_results)
    logger.info(f"Analysis summary written to {Paths.RESULTS_DIR / 'analysis_summary.csv'}")

    # 7. Versioning
    logger.info("Updating project state with artifact hashes...")
    record_data_generation_state()

    logger.info("Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
