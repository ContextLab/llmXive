import os
import sys
import json
import time
import argparse
import logging
import signal
from pathlib import Path
from typing import Dict, Any, Optional, List
import cProfile
import pstats
import io
from contextlib import contextmanager

# Local imports based on API surface
from config import get_config, ensure_dirs
from constitution import check_by_amendment_ratification, enforce_gate
from loaders import (
    setup_loader_logging,
    load_checksums,
    save_checksums,
    verify_checksum,
    load_all_datasets,
    apply_hygiene_pipeline,
    main as loader_main
)
from stats_engine import (
    compute_correlation,
    construct_graph,
    calculate_stats,
    generate_null_distribution,
    calculate_empirical_p_value,
    generate_synthetic_dataset,
    validate_null_model,
    run_full_analysis_pipeline,
    main as stats_main
)
from correction import benjamini_yekutieli, apply_correction_to_results
from viz import (
    plot_heatmap,
    plot_histogram,
    plot_primary_threshold_visualizations,
    plot_sensitivity_sweep,
    plot_observed_vs_null_heatmap,
    plot_sensitivity_results
)

# Setup logging
def setup_logging():
    """Configure logging for the main pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('output/reports/pipeline.log')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# Context manager for profiling
@contextmanager
def profiler_context(output_path: str):
    """Context manager to profile code execution and save stats."""
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        yield
    finally:
        profiler.disable()
        stats_stream = io.StringIO()
        ps = pstats.Stats(profiler, stream=stats_stream).sort_stats('cumulative')
        ps.print_stats(20)  # Print top 20 functions
        
        # Save raw stats to JSON for structured analysis
        profile_data = {
            "total_time": ps.total_tt,
            "function_stats": []
        }
        
        for func_key, (cc, nc, tt, ct, callers) in ps.stats.items():
            filename, line, name = func_key
            profile_data["function_stats"].append({
                "file": os.path.basename(filename),
                "line": line,
                "name": name,
                "call_count": nc,
                "total_time": tt,
                "cumulative_time": ct
            })
        
        # Sort by cumulative time
        profile_data["function_stats"].sort(key=lambda x: x["cumulative_time"], reverse=True)
        
        with open(output_path, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        logger.info(f"Profile saved to {output_path}")
        logger.info(f"Top 5 functions by cumulative time:")
        for i, stat in enumerate(profile_data["function_stats"][:5]):
            logger.info(f"  {i+1}. {stat['name']}: {stat['cumulative_time']:.4f}s")

# Timer decorator/context
class timer:
    def __init__(self, phase_name: str, breakdown_dict: dict):
        self.phase_name = phase_name
        self.breakdown_dict = breakdown_dict
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        elapsed = time.time() - self.start_time
        self.breakdown_dict[self.phase_name] = self.breakdown_dict.get(self.phase_name, 0) + elapsed
        logger.info(f"Phase '{self.phase_name}' completed in {elapsed:.2f}s")

def write_runtime_log(log_path: str, total_time: float, limit: float = 21600.0, status: str = "pass"):
    """Write runtime log to JSON."""
    log_data = {
        "total_runtime_seconds": total_time,
        "limit_seconds": limit,
        "status": status
    }
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Runtime log written to {log_path}")

def handle_timeout(signum, frame):
    """Handle timeout signal."""
    logger.error("Pipeline timed out!")
    write_runtime_log('output/reports/runtime_log.json', time.time() - start_time, status="timeout")
    sys.exit(1)

def estimate_runtime_pilot(n_permutations: int = 10, min_datasets: int = 3) -> float:
    """Estimate runtime based on a pilot run."""
    logger.info("Running pilot estimation...")
    # This would ideally run a small subset, but for now we return a placeholder
    # In a real implementation, this would run a small permutation test
    return n_permutations * 0.1 * min_datasets  # Placeholder estimate

def run_synthetic_validation_loop(n_runs: int = 100):
    """Run synthetic validation loop."""
    logger.info(f"Running synthetic validation for {n_runs} iterations...")
    pass_count = 0
    
    for i in range(n_runs):
        # Generate synthetic data
        synthetic_data = generate_synthetic_dataset(n_samples=500, n_features=20)
        # Validate null model
        is_valid = validate_null_model(synthetic_data)
        if is_valid:
            pass_count += 1
    
    pass_rate = pass_count / n_runs
    logger.info(f"Synthetic validation pass rate: {pass_rate:.2%} ({pass_count}/{n_runs})")
    
    if pass_rate < 0.95:
        logger.error("Synthetic validation failed: Pass rate < 95%")
        sys.exit(1)
    
    return pass_rate

def run_full_pipeline(config: Dict[str, Any], n_permutations: int = 2000, threshold: float = 0.3) -> Dict[str, Any]:
    """Run the full analysis pipeline with profiling."""
    results = {
        "datasets": [],
        "statistics": {},
        "corrections": [],
        "visualizations": []
    }
    
    # Load datasets
    logger.info("Loading datasets...")
    datasets = load_all_datasets(min_datasets=config.get('min_datasets', 3))
    
    # Apply hygiene pipeline
    cleaned_datasets = {}
    for name, df in datasets.items():
        cleaned_datasets[name] = apply_hygiene_pipeline(df)
    
    # Run analysis for each dataset
    for name, df in cleaned_datasets.items():
        logger.info(f"Processing dataset: {name}")
        
        # Compute correlations
        corr_matrix = compute_correlation(df, method='pearson')
        
        # Construct graph
        graph = construct_graph(corr_matrix, threshold=threshold)
        
        # Calculate statistics
        stats = calculate_stats(graph)
        
        # Generate null distribution
        null_dist = generate_null_distribution(df, n_permutations=n_permutations)
        
        # Calculate p-values
        p_values = calculate_empirical_p_value(null_dist, stats['mean_abs_corr'])
        
        # Apply correction
        corrected = benjamini_yekutieli([p_values], alpha=0.05)
        
        results["datasets"].append({
            "name": name,
            "stats": stats,
            "p_value": p_values,
            "q_value": corrected[0][0]
        })
    
    return results

def run_threshold_sweep(config: Dict[str, Any], n_permutations: int = 2000, thresholds: List[float] = None) -> Dict[str, Any]:
    """Run threshold sensitivity analysis."""
    if thresholds is None:
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    results = {
        "thresholds": [],
        "summary": {}
    }
    
    for threshold in thresholds:
        logger.info(f"Running sweep for threshold: {threshold}")
        pipeline_results = run_full_pipeline(config, n_permutations=n_permutations, threshold=threshold)
        
        results["thresholds"].append({
            "threshold": threshold,
            "results": pipeline_results
        })
    
    return results

def generate_sensitivity_report(sweep_results: Dict[str, Any], output_path: str):
    """Generate sensitivity analysis report."""
    report = {
        "thresholds": [],
        "summary": {}
    }
    
    for item in sweep_results["thresholds"]:
        threshold = item["threshold"]
        # Aggregate results across datasets
        significant_counts = []
        for ds in item["results"]["datasets"]:
            if ds["q_value"] < 0.05:
                significant_counts.append(1)
            else:
                significant_counts.append(0)
        
        report["thresholds"].append({
            "threshold": threshold,
            "significant_count": sum(significant_counts),
            "total_tests": len(significant_counts)
        })
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sensitivity report saved to {output_path}")
    return report

def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_data_integrity(checksums_path: str, data_dir: str) -> bool:
    """Verify data integrity against stored checksums."""
    if not os.path.exists(checksums_path):
        logger.warning(f"Checksum file not found: {checksums_path}")
        return False
    
    checksums = load_checksums(checksums_path)
    all_valid = True
    
    for filename, stored_hash in checksums.items():
        file_path = os.path.join(data_dir, filename)
        if os.path.exists(file_path):
            current_hash = compute_file_hash(file_path)
            if current_hash != stored_hash:
                logger.error(f"Checksum mismatch for {filename}")
                all_valid = False
        else:
            logger.warning(f"File not found: {file_path}")
            all_valid = False
    
    return all_valid

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description='Assess Statistical Significance of Observed Correlations')
    parser.add_argument('--permutations', type=int, default=2000, help='Number of permutations')
    parser.add_argument('--threshold', type=float, default=0.3, help='Correlation threshold')
    parser.add_argument('--sweep', action='store_true', help='Run threshold sensitivity sweep')
    parser.add_argument('--output', type=str, default='output', help='Output directory')
    parser.add_argument('--profile', action='store_true', help='Enable profiling')
    
    args = parser.parse_args()
    
    # Setup directories
    config = get_config()
    ensure_dirs(config)
    
    # Check BY amendment
    if not check_by_amendment_ratification():
        logger.error("Execution blocked: Constitutional Amendment for BY procedure not ratified.")
        sys.exit(1)
    
    # Initialize breakdown dictionary
    breakdown = {
        "load": 0.0,
        "perm": 0.0,
        "corr": 0.0,
        "viz": 0.0,
        "total": 0.0
    }
    
    start_time = time.time()
    
    try:
        # Setup signal handler for timeout
        signal.signal(signal.SIGTERM, handle_timeout)
        signal.signal(signal.SIGINT, handle_timeout)
        
        # Run profiling if requested
        if args.profile:
            with profiler_context('output/reports/profiling_log.json'):
                run_pipeline_with_timing(args, breakdown)
        else:
            run_pipeline_with_timing(args, breakdown)
        
        # Write runtime log
        total_time = time.time() - start_time
        write_runtime_log('output/reports/runtime_log.json', total_time, status="pass")
        
        # Verify data integrity
        if not verify_data_integrity('data/raw/checksums.json', 'data/raw'):
            logger.warning("Data integrity check failed")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        write_runtime_log('output/reports/runtime_log.json', time.time() - start_time, status="fail")
        raise

def run_pipeline_with_timing(args, breakdown):
    """Run the pipeline with timing breakdown."""
    # Load datasets
    with timer("load", breakdown):
        datasets = load_all_datasets(min_datasets=3)
        cleaned_datasets = {}
        for name, df in datasets.items():
            cleaned_datasets[name] = apply_hygiene_pipeline(df)
    
    # Run analysis
    with timer("perm", breakdown):
        if args.sweep:
            sweep_results = run_threshold_sweep(
                get_config(), 
                n_permutations=args.permutations,
                thresholds=[0.1, 0.2, 0.3, 0.4, 0.5]
            )
            generate_sensitivity_report(sweep_results, 'output/reports/sensitivity_report.json')
        else:
            results = run_full_pipeline(
                get_config(), 
                n_permutations=args.permutations, 
                threshold=args.threshold
            )
            
            # Save results
            with open('output/results/main_results.json', 'w') as f:
                json.dump(results, f, indent=2)
    
    # Apply corrections
    with timer("corr", breakdown):
        # Corrections are applied within run_full_pipeline, but we log here
        pass
    
    # Generate visualizations
    with timer("viz", breakdown):
        if args.sweep:
            plot_sensitivity_sweep('output/reports/sensitivity_report.json', 'output/plots/sensitivity.png')
        else:
            plot_primary_threshold_visualizations('output/results/main_results.json', 'output/plots/primary/')
    
    # Log breakdown
    breakdown["total"] = sum(breakdown.values())
    with open('output/reports/profiling_log.json', 'w') as f:
        json.dump({
            "total_time": breakdown["total"],
            "breakdown": {k: v for k, v in breakdown.items() if k != "total"}
        }, f, indent=2)
    
    logger.info(f"Pipeline completed. Breakdown: {breakdown}")

if __name__ == '__main__':
    main()