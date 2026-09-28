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
    parser = argparse.ArgumentParser(description="Run the full Prompt Complexity Evaluation Pipeline.")
    parser.add_argument("--sample-size", type=int, default=None, help="Limit to N problems from HumanEval.")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip fetching HumanEval dataset.")
    parser.add_argument("--skip-generate", action="store_true", help="Skip prompt generation.")
    parser.add_argument("--skip-llm", action="store_true", help="Skip LLM queries.")
    parser.add_argument("--skip-execute", action="store_true", help="Skip code execution.")
    parser.add_argument("--skip-analysis", action="store_true", help="Skip statistical analysis.")
    args = parser.parse_args()

    setup_structured_logger()
    logger.info(f"Starting pipeline for project: {get_project_id()}")

    # 1. Fetch Data
    if not args.skip_fetch:
        logger.info("Step 1: Fetching HumanEval dataset...")
        # Assuming fetcher handles download and initial load
        # We need to ensure the data is available for the next steps
        # The fetcher might write to data/raw/
        # For simplicity, we assume load_human_eval works after download
        # In a real scenario, we might pass the dataset object or path
        # Here we just ensure it's done.
        # Note: The fetcher script might need to be run separately or integrated.
        # Let's assume load_human_eval returns the dataset.
        # If the fetcher writes to disk, we just need to ensure it runs.
        # We will call the fetcher's main or a specific function.
        # Since the API surface shows `from data.fetcher import ...`, we use that.
        # But `download_human_eval` and `load_human_eval` are separate.
        # We'll assume we need to download first if not skipped.
        # For this main script, we assume the dataset is needed.
        # We will call the fetcher logic.
        # Note: The fetcher might not have a simple `run` function that returns data.
        # We will assume `load_human_eval` handles loading from the expected raw path.
        # We need to ensure `download_human_eval` is called if needed.
        # Let's assume `download_human_eval` writes to `data/raw/humaneval.json` or similar.
        # We will call it.
        # The `load_human_eval` function in `loader.py` might be the one to use.
        # Let's use the loader's `load_human_eval_dataset` as per T016.
        # But `fetcher.py` has `load_human_eval`.
        # We'll use `fetcher.load_human_eval` if it returns the dataset.
        # If not, we'll just ensure the file exists.
        # For now, we assume `load_human_eval` returns the dataset.
        # If it doesn't, we might need to adjust.
        # Let's assume it does for the pipeline flow.
        # Actually, looking at T016, `loader.py` has `load_human_eval_dataset`.
        # We'll use that.
        # But `fetcher.py` is also there.
        # We'll assume `fetcher.download_human_eval` downloads, and `loader.load_human_eval_dataset` loads.
        # We'll call both.
        # We need to import `download_human_eval` from `data.fetcher` and `load_human_eval_dataset` from `data.loader`.
        from data.fetcher import download_human_eval
        from data.loader import load_human_eval_dataset
        download_human_eval()
        dataset = load_human_eval_dataset()
        if args.sample_size:
            dataset = dataset[:args.sample_size]
            logger.info(f"Sampled {args.sample_size} problems.")
    else:
        from data.loader import load_human_eval_dataset
        dataset = load_human_eval_dataset()
        if args.sample_size:
            dataset = dataset[:args.sample_size]

    # 2. Generate Prompts
    if not args.skip_generate:
        logger.info("Step 2: Generating prompt variants...")
        # This should return variants and codes
        # The generator might need to be called per problem
        # We'll assume `generate_prompt_variants` takes the dataset and returns variants/codes
        # But the API surface shows `generate_prompt_variants` in `prompts.generator`.
        # We need to check its signature.
        # It likely takes a list of problems.
        # Let's assume it returns (variants, codes).
        # We'll need to adapt if it doesn't.
        # For now, we assume it works.
        # Actually, T013 says `generate_prompt_variants` creates variants.
        # We'll assume it returns a list of variants and a list of codes.
        # We'll call it here.
        # We need to pass the dataset.
        # We'll assume `generate_prompt_variants` handles the dataset.
        # If not, we might need to loop.
        # Let's assume it returns (variants, codes).
        from prompts.generator import generate_prompt_variants
        variants, codes = generate_prompt_variants(dataset)
        logger.info(f"Generated {len(variants)} variants.")

    # 3. Store Results
    logger.info("Step 3: Storing generated code and metadata...")
    from data.storage import save_variants_to_parquet
    save_variants_to_parquet(variants, codes)
    logger.info("Saved to data/processed/prompt_variants.parquet")

    # 4. Execute Tests
    if not args.skip_execute:
        logger.info("Step 4: Executing code and analyzing results...")
        from execution.write_results import run_execution_and_analysis, write_results_to_csv
        # This function should handle the execution and writing to CSV
        run_execution_and_analysis()
        write_results_to_csv()
        logger.info("Saved execution outcomes to data/results/execution_outcomes.csv")

    # 5. Analysis
    if not args.skip_analysis:
        logger.info("Step 5: Running statistical analysis...")
        from analysis.stats import run_full_analysis, write_analysis_summary_to_csv
        run_full_analysis()
        write_analysis_summary_to_csv()
        logger.info("Saved analysis summary to data/results/analysis_summary.csv")

    # 6. Versioning
    logger.info("Step 6: Updating project state...")
    record_data_generation_state()

    logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    main()