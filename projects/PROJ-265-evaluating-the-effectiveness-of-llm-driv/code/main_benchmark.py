"""
Main orchestrator for User Story 3: Performance Benchmarking and Statistical Analysis.

This script:
1. Loads valid (original, simplified) pairs from data/processed/valid_pairs.jsonl
2. Runs benchmarks on each pair using code/benchmark/runner.py
3. Aggregates results and computes means
4. Performs statistical analysis using code/benchmark/stats.py
5. Outputs results to data/processed/benchmark_results.json and results/summary.csv
"""
import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error
from benchmark.runner import run_benchmark_pipeline, load_valid_pairs
from benchmark.stats import run_statistical_analysis, analyze_benchmark_results

logger = get_logger(__name__)


def load_valid_pairs_safe(pairs_path: Path) -> List[Dict[str, Any]]:
    """
    Safely load valid pairs with error handling.
    
    Args:
        pairs_path: Path to valid_pairs.jsonl
        
    Returns:
        List of valid pair dictionaries
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is empty or malformed
    """
    if not pairs_path.exists():
        raise FileNotFoundError(f"Valid pairs file not found: {pairs_path}")
    
    pairs = load_valid_pairs(pairs_path)
    
    if not pairs:
        raise ValueError("Valid pairs file is empty or contains no valid entries")
    
    logger.info(f"Loaded {len(pairs)} valid pairs from {pairs_path}")
    return pairs


def run_full_benchmark_pipeline(
    pairs_path: Path,
    output_results_path: Path,
    output_summary_path: Path
) -> Dict[str, Any]:
    """
    Run the complete benchmark pipeline:
    1. Load valid pairs
    2. Run benchmarks on each pair
    3. Aggregate results
    4. Perform statistical analysis
    5. Save results and summary
    
    Args:
        pairs_path: Path to valid_pairs.jsonl
        output_results_path: Path to save detailed benchmark results
        output_summary_path: Path to save summary CSV
        
    Returns:
        Dictionary containing pipeline results and metadata
    """
    log_stage_start("full_benchmark_pipeline", {
        "pairs_path": str(pairs_path),
        "output_results": str(output_results_path),
        "output_summary": str(output_summary_path)
    })
    
    try:
        # Step 1: Load valid pairs
        logger.info("Step 1: Loading valid pairs...")
        pairs = load_valid_pairs_safe(pairs_path)
        
        # Step 2: Run benchmarks
        logger.info(f"Step 2: Running benchmarks on {len(pairs)} pairs...")
        benchmark_results = run_benchmark_pipeline(pairs)
        
        if not benchmark_results:
            raise ValueError("No benchmark results generated")
        
        logger.info(f"Generated {len(benchmark_results)} benchmark results")
        
        # Step 3: Save detailed results
        logger.info("Step 3: Saving detailed benchmark results...")
        output_results_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_results_path, 'w', encoding='utf-8') as f:
            json.dump(benchmark_results, f, indent=2, default=str)
        
        # Step 4: Perform statistical analysis
        logger.info("Step 4: Performing statistical analysis...")
        statistical_results = run_statistical_analysis(benchmark_results)
        
        # Step 5: Generate summary
        logger.info("Step 5: Generating summary CSV...")
        summary_data = analyze_benchmark_results(benchmark_results, statistical_results)
        
        output_summary_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write summary CSV
        import csv
        with open(output_summary_path, 'w', newline='', encoding='utf-8') as f:
            if summary_data:
                writer = csv.DictWriter(f, fieldnames=summary_data[0].keys())
                writer.writeheader()
                writer.writerows(summary_data)
        
        # Compile final results
        final_results = {
            "pipeline_status": "completed",
            "pairs_processed": len(pairs),
            "benchmarks_completed": len(benchmark_results),
            "statistical_analysis": {
                "normality_tests": statistical_results.get("normality_tests", {}),
                "significance_tests": statistical_results.get("significance_tests", {}),
                "effect_sizes": statistical_results.get("effect_sizes", {})
            },
            "summary_stats": {
                "total_pairs": len(pairs),
                "significant_results": len([r for r in summary_data if r.get("significant") == True]),
                "non_significant_results": len([r for r in summary_data if r.get("significant") == False])
            },
            "output_files": {
                "detailed_results": str(output_results_path),
                "summary_csv": str(output_summary_path)
            }
        }
        
        log_stage_complete("full_benchmark_pipeline", final_results)
        return final_results
        
    except Exception as e:
        log_stage_error("full_benchmark_pipeline", str(e))
        raise


def main():
    """
    Main entry point for the benchmark orchestration script.
    """
    logger.info("=" * 60)
    logger.info("Starting LLM Code Simplification Benchmark Pipeline (US3)")
    logger.info("=" * 60)
    
    # Define paths
    project_root = Path(__file__).parent.parent
    pairs_path = project_root / "data" / "processed" / "valid_pairs.jsonl"
    results_path = project_root / "data" / "processed" / "benchmark_results.json"
    summary_path = project_root / "results" / "summary.csv"
    
    # Verify input exists
    if not pairs_path.exists():
        logger.error(f"Input file not found: {pairs_path}")
        logger.error("Please ensure T026b (main_filter_drift.py) has been completed first.")
        sys.exit(1)
    
    try:
        # Run the full pipeline
        results = run_full_benchmark_pipeline(
            pairs_path=pairs_path,
            output_results_path=results_path,
            output_summary_path=summary_path
        )
        
        # Log final summary
        logger.info("=" * 60)
        logger.info("Pipeline Completed Successfully!")
        logger.info(f"Pairs Processed: {results['pairs_processed']}")
        logger.info(f"Benchmarks Completed: {results['benchmarks_completed']}")
        logger.info(f"Significant Results: {results['summary_stats']['significant_results']}")
        logger.info(f"Non-Significant Results: {results['summary_stats']['non_significant_results']}")
        logger.info(f"Results saved to: {results['output_files']['detailed_results']}")
        logger.info(f"Summary saved to: {results['output_files']['summary_csv']}")
        logger.info("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())