import argparse
import json
import logging
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

# Local imports based on API surface
from config import ExecutionConfig, get_config, set_config_override
from data.loader import (
    DataFetchError,
    RAMExceededError,
    LowPowerError,
    LowNumericColumnsError,
    fetch_and_save_dataset,
    process_and_validate,
    load_all_datasets
)
from data.processor import (
    MissingValueError,
    process_dataset,
    generate_cleaning_report,
    generate_statistical_summaries
)
from narrative.baseline import run_baseline_analysis
from narrative.inspector import run_inspector_analysis
from narrative.sensitivity_aggregator import run_aggregation_pipeline
from narrative.synthesizer import run_synthesis_pipeline
from narrative.flag_propagator import propagate_low_power_flag, write_propagated_report
from evaluation.bias import calculate_confirmation_bias
from evaluation.rubric import calculate_narrative_depth
from evaluation.blinding import generate_blinded_pairs
from evaluation.simulate_experts import simulate_expert_scoring, run_kappa_check
from evaluation.traceability import verify_traceability

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="LLMxive Automated Science Pipeline")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset identifier from registry")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory")
    parser.add_argument("--skip-load", action="store_true", help="Skip data loading stage")
    parser.add_argument("--skip-process", action="store_true", help="Skip data processing stage")
    parser.add_argument("--skip-narrative", action="store_true", help="Skip narrative generation stage")
    parser.add_argument("--skip-eval", action="store_true", help="Skip evaluation stage")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()

def apply_config_overrides(args: argparse.Namespace) -> None:
    """Apply command line arguments to global configuration."""
    config = get_config()
    config.random_seed = args.seed
    config.output_dir = args.output_dir
    if args.verbose:
        config.log_level = "DEBUG"
    set_config_override(config)

def run_load_stage(dataset_id: str, output_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Run the data loading stage.
    Implements robust error handling: catches DataFetchError, logs it, and skips the dataset.
    """
    logger.info(f"Starting load stage for dataset: {dataset_id}")
    try:
        # Attempt to fetch and save the dataset
        # This function is expected to raise DataFetchError on failure
        local_path = fetch_and_save_dataset(dataset_id, output_dir / "raw")
        
        if not local_path.exists():
            raise FileNotFoundError(f"Dataset file not found after download: {local_path}")
        
        logger.info(f"Dataset loaded successfully to: {local_path}")
        return {"path": str(local_path), "status": "loaded"}
    
    except DataFetchError as e:
        # CRITICAL: Handle DataFetchError by logging and skipping
        logger.error(f"DataFetchError encountered for {dataset_id}: {str(e)}")
        logger.warning(f"Skipping dataset {dataset_id} due to fetch failure. Pipeline proceeding to next item.")
        # Return None to indicate dataset was skipped
        return None
    
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error during load stage for {dataset_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def run_process_stage(dataset_info: Dict[str, Any], output_dir: Path) -> Optional[Dict[str, Any]]:
    """Run the data processing stage (cleaning, summaries)."""
    if dataset_info is None:
        return None
        
    logger.info("Starting process stage")
    try:
        input_path = Path(dataset_info["path"])
        cleaned_path = output_dir / "processed" / f"{input_path.stem}_cleaned.csv"
        
        # Process dataset
        df_clean = process_dataset(input_path, str(cleaned_path))
        
        # Generate reports
        cleaning_report = generate_cleaning_report(df_clean, output_dir / "reports" / "cleaning.json")
        stats_summary = generate_statistical_summaries(df_clean, output_dir / "reports" / "stats.json")
        
        logger.info("Process stage completed successfully")
        return {
            "cleaned_path": str(cleaned_path),
            "cleaning_report": cleaning_report,
            "stats_summary": stats_summary
        }
    except MissingValueError as e:
        logger.warning(f"Missing value issue: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error in process stage: {str(e)}")
        return None

def run_narrative_stage(processed_data: Dict[str, Any], output_dir: Path) -> Optional[Dict[str, Any]]:
    """Run the narrative generation stage (Baseline + Inspector + Synthesis)."""
    if processed_data is None:
        return None
        
    logger.info("Starting narrative stage")
    try:
        cleaned_path = Path(processed_data["cleaned_path"])
        
        # 1. Baseline Analysis
        baseline_result = run_baseline_analysis(cleaned_path, output_dir / "baseline.json")
        
        # 2. Inspector Analysis
        inspector_result = run_inspector_analysis(
            cleaned_path, 
            baseline_result, 
            output_dir / "inspector.json"
        )
        
        # 3. Sensitivity Aggregation
        sensitivity_result = run_aggregation_pipeline(
            inspector_result, 
            output_dir / "sensitivity_report.json"
        )
        
        # 4. Synthesis
        synthesis_result = run_synthesis_pipeline(
            baseline_result,
            sensitivity_result,
            output_dir / "synthesis_story.json"
        )
        
        # 5. Flag Propagation (Low Power)
        # Check if low_power flag was set during earlier stages
        # (Assuming it's passed via context or checked in synthesizer)
        write_propagated_report(synthesis_result, output_dir / "flag_report.json")
        
        logger.info("Narrative stage completed successfully")
        return {
            "baseline": baseline_result,
            "inspector": inspector_result,
            "sensitivity": sensitivity_result,
            "synthesis": synthesis_result
        }
    except Exception as e:
        logger.error(f"Error in narrative stage: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def run_evaluation_stage(narrative_results: Dict[str, Any], output_dir: Path) -> Optional[Dict[str, Any]]:
    """Run the evaluation stage (Bias, Depth, Traceability)."""
    if narrative_results is None:
        return None
        
    logger.info("Starting evaluation stage")
    try:
        synthesis_path = output_dir / "synthesis_story.json"
        
        # 1. Confirmation Bias
        bias_metrics = calculate_confirmation_bias(narrative_results, output_dir / "bias_metrics.json")
        
        # 2. Narrative Depth (Blinding + Simulation)
        blinded_pairs = generate_blinded_pairs(narrative_results)
        scores = simulate_expert_scoring(blinded_pairs)
        kappa = run_kappa_check(scores)
        depth_metrics = calculate_narrative_depth(scores, kappa, output_dir / "depth_metrics.json")
        
        # 3. Traceability
        traceability_metrics = verify_traceability(synthesis_path, output_dir / "traceability_metrics.json")
        
        logger.info("Evaluation stage completed successfully")
        return {
            "bias": bias_metrics,
            "depth": depth_metrics,
            "traceability": traceability_metrics
        }
    except Exception as e:
        logger.error(f"Error in evaluation stage: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def main():
    """Main entry point for the pipeline."""
    args = parse_arguments()
    apply_config_overrides(args)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting pipeline for dataset: {args.dataset}")
    
    # Stage 1: Load
    dataset_info = run_load_stage(args.dataset, output_dir)
    if dataset_info is None:
        logger.warning(f"Pipeline aborted for {args.dataset} due to load failure (skipped).")
        return 0 # Return 0 to indicate graceful skip, not a crash
    
    # Stage 2: Process
    if not args.skip_process:
        processed_data = run_process_stage(dataset_info, output_dir)
        if processed_data is None:
            logger.warning(f"Pipeline aborted for {args.dataset} due to processing failure.")
            return 1
    else:
        processed_data = dataset_info # Pass raw info if skipping process (edge case)
    
    # Stage 3: Narrative
    if not args.skip_narrative:
        narrative_results = run_narrative_stage(processed_data, output_dir)
        if narrative_results is None:
            logger.warning(f"Pipeline aborted for {args.dataset} due to narrative failure.")
            return 1
    else:
        narrative_results = None
    
    # Stage 4: Evaluation
    if not args.skip_eval and narrative_results:
        eval_results = run_evaluation_stage(narrative_results, output_dir)
        if eval_results is None:
            logger.warning(f"Pipeline completed with warnings for {args.dataset} (evaluation failed).")
            # Don't fail the whole run if eval fails, just log
    
    logger.info(f"Pipeline completed successfully for {args.dataset}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())