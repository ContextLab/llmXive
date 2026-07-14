import argparse
import json
import os
import sys
import gc
import psutil

from code.simulation.test_runner import run_simulation_condition, aggregate_results
from code.simulation.output_writer import write_p_values_raw
from code.simulation.logging_config import setup_file_logging, get_logger, log_debug, log_warning, log_error
from code.simulation import get_rng

logger = get_logger("llmXive.main")

def get_memory_usage_mb() -> float:
    """Returns current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def check_memory_limit(limit_mb: float = 7000) -> bool:
    """Checks if current memory usage is within limit."""
    usage = get_memory_usage_mb()
    if usage > limit_mb:
        log_warning(f"Memory usage {usage:.1f}MB exceeds limit {limit_mb}MB")
        return False
    return True

def force_gc() -> None:
    """Forces garbage collection."""
    gc.collect()

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run statistical test sensitivity simulation.")
    parser.add_argument("--sample-sizes", type=str, default="5,10,20,50,100,200,500",
                        help="Comma-separated list of sample sizes.")
    parser.add_argument("--effect-sizes", type=str, default="0.0,0.2,0.5,0.8",
                        help="Comma-separated list of effect sizes.")
    parser.add_argument("--test-types", type=str, default="t-test,ANOVA,chi-squared",
                        help="Comma-separated list of test types.")
    parser.add_argument("--alpha", type=float, default=0.05,
                        help="Significance level alpha.")
    parser.add_argument("--iterations", type=int, default=1000,
                        help="Number of iterations per condition (use lower for testing).")
    parser.add_argument("--seed", type=int, default=42,
                        help="Base random seed.")
    parser.add_argument("--output-dir", type=str, default="data/simulation",
                        help="Directory to save output files.")
    parser.add_argument("--log-file", action="store_true",
                        help="Enable file logging.")
    return parser.parse_args()

def validate_args(args: argparse.Namespace) -> None:
    if args.iterations < 10:
        log_warning("Iteration count is very low. Results may be noisy.")
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        log_debug(f"Created output directory: {args.output_dir}")

def generate_sample_sizes(sizes_str: str) -> List[int]:
    return [int(x.strip()) for x in sizes_str.split(",")]

def parse_effect_sizes(effects_str: str) -> List[float]:
    return [float(x.strip()) for x in effects_str.split(",")]

def run_simulation_grid(args: argparse.Namespace) -> None:
    sample_sizes = generate_sample_sizes(args.sample_sizes)
    effect_sizes = parse_effect_sizes(args.effect_sizes)
    test_types = [t.strip() for t in args.test_types.split(",")]
    
    rng = get_rng(args.seed)
    
    all_results = []
    
    for n in sample_sizes:
        for effect in effect_sizes:
            for test_type in test_types:
                # Determine if this is a null hypothesis scenario
                # If effect is 0, H0 is true. If effect != 0, H0 is false (Alternative).
                null_hypothesis = (effect == 0.0)
                
                log_debug(f"Running condition: n={n}, effect={effect}, test={test_type}, H0={null_hypothesis}")
                
                # Run simulation
                results = run_simulation_condition(
                    n=n,
                    effect_size=effect,
                    test_type=test_type,
                    alpha=args.alpha,
                    iterations=args.iterations,
                    seed_base=int(rng.integers(0, 2**31 - 1)),
                    null_hypothesis=null_hypothesis
                )
                
                # Aggregate
                agg = aggregate_results(results, alpha=args.alpha)
                
                # Prepare output record
                record = {
                    "sample_size": n,
                    "effect_size": effect,
                    "test_type": test_type,
                    "null_hypothesis": null_hypothesis,
                    "total_iterations": agg["total_iterations"],
                    "valid_iterations": agg["valid_iterations"],
                    "significant_count": agg["significant_count"],
                    "non_significant_count": agg["non_significant_count"],
                    "alpha": args.alpha
                }
                
                # Store raw p-values for detailed analysis if needed
                # (In a real large scale run, we might stream this, but for now we collect)
                # To save memory, we don't store all p-values in the main record if not needed for summary
                # But T016 asks for "raw p-values". We will write them to a separate file or append to CSV.
                # For this implementation, we will write the summary to the main CSV and raw p-values to a separate file if needed,
                # or just include a subset. The task T016 says "p_values_raw.csv containing ... raw p-values".
                # Storing 1000 p-values per row in CSV is heavy. We will assume the "raw p-values" column 
                # might be a JSON string or we write a separate file. 
                # However, T016 description says "containing sample size, effect size, test type, raw p-values, and hypothesis state".
                # Let's write a separate file for raw p-values to keep the summary clean, or if the task implies one file,
                # we'll format p-values as a string.
                # Given the constraint "Write output results to data/simulation/p_values_raw.csv", let's assume we write the detailed list.
                # But to be safe and efficient, we will write the summary to error_rates_summary.csv (T018)
                # and the raw p-values to p_values_raw.csv (T016).
                
                all_results.append(record)
                
                # Check memory
                if not check_memory_limit(6000):
                    force_gc()
                    if not check_memory_limit(6000):
                        log_error("Memory limit exceeded after GC. Stopping.")
                        sys.exit(1)

    # Write results
    # T016: p_values_raw.csv
    # We need to write the raw p-values. Since we didn't store them in 'all_results' to save memory,
    # we need to re-run or store them.
    # Let's adjust: We will store p-values in a list of dicts for the raw file.
    # To avoid memory issues, we will write the raw file incrementally if possible,
    # but for simplicity in this task, we assume 'args.iterations' is manageable (e.g. 1000).
    
    # Re-run logic to capture p-values for T016? No, that's inefficient.
    # Instead, let's modify run_simulation_condition to return p-values in a way we can store.
    # Actually, the 'results' list in run_simulation_condition contains dicts with p_values.
    # We should have passed that to the writer.
    # Let's adjust the flow:
    # 1. Run condition -> get results (list of dicts with p_values)
    # 2. Write raw results to file immediately (or buffer)
    # 3. Aggregate and write summary.
    
    # Since I cannot change the signature of run_simulation_condition easily without breaking other things,
    # and I need to implement T037 (logging) and ensure T016/T018 work.
    # I will assume the 'results' from run_simulation_condition are available.
    # But in the loop above, I discarded them after aggregation.
    # Let's fix the loop to write raw data.
    
    # Redoing the loop structure to ensure T016 is satisfied:
    pass # Logic moved below

def main():
    args = parse_args()
    validate_args(args)
    
    # Setup logging
    if args.log_file:
        setup_file_logging(os.path.join(args.output_dir, "logs"))
    
    log_debug("Simulation started")
    
    sample_sizes = generate_sample_sizes(args.sample_sizes)
    effect_sizes = parse_effect_sizes(args.effect_sizes)
    test_types = [t.strip() for t in args.test_types.split(",")]
    
    rng = get_rng(args.seed)
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    raw_p_values_file = os.path.join(args.output_dir, "p_values_raw.csv")
    summary_file = os.path.join(args.output_dir, "error_rates_summary.csv")
    
    # We will collect summary rows here
    summary_rows = []
    
    # For raw p-values, we will write them row by row to avoid memory issues
    # But writing to CSV row by row for 1000s of rows is slow.
    # We'll use a buffer or just write directly.
    # Let's write directly.
    
    with open(raw_p_values_file, "w", newline="") as f_raw:
        # Header
        f_raw.write("sample_size,effect_size,test_type,null_hypothesis,iteration,p_value\n")
        
        for n in sample_sizes:
            for effect in effect_sizes:
                for test_type in test_types:
                    null_hypothesis = (effect == 0.0)
                    
                    iter_seed = int(rng.integers(0, 2**31 - 1))
                    
                    log_debug(f"Processing: n={n}, effect={effect}, test={test_type}, H0={null_hypothesis}")
                    
                    # Run simulation
                    results = run_simulation_condition(
                        n=n,
                        effect_size=effect,
                        test_type=test_type,
                        alpha=args.alpha,
                        iterations=args.iterations,
                        seed_base=iter_seed,
                        null_hypothesis=null_hypothesis
                    )
                    
                    # Write raw p-values
                    for i, res in enumerate(results):
                        p_val = res.get("p_value")
                        if p_val is not None:
                            f_raw.write(f"{n},{effect},{test_type},{null_hypothesis},{i},{p_val}\n")
                    
                    # Aggregate
                    agg = aggregate_results(results, alpha=args.alpha)
                    
                    # Calculate error rates
                    # If H0 is true (effect=0), significant count is Type I error
                    # If H0 is false (effect!=0), non-significant count is Type II error
                    
                    if null_hypothesis:
                        type_i_rate = agg["significant_count"] / agg["valid_iterations"] if agg["valid_iterations"] > 0 else 0.0
                        type_ii_rate = None
                        power = None
                    else:
                        type_i_rate = None
                        type_ii_rate = agg["non_significant_count"] / agg["valid_iterations"] if agg["valid_iterations"] > 0 else 0.0
                        power = 1.0 - type_ii_rate
                    
                    summary_rows.append({
                        "sample_size": n,
                        "effect_size": effect,
                        "test_type": test_type,
                        "null_hypothesis": null_hypothesis,
                        "alpha": args.alpha,
                        "total_iterations": agg["total_iterations"],
                        "valid_iterations": agg["valid_iterations"],
                        "type_i_error_rate": type_i_rate,
                        "type_ii_error_rate": type_ii_rate,
                        "power": power
                    })
                    
                    # Memory check
                    if not check_memory_limit(6000):
                        force_gc()
    
    # Write summary
    with open(summary_file, "w", newline="") as f_sum:
        if summary_rows:
            headers = list(summary_rows[0].keys())
            f_sum.write(",".join(headers) + "\n")
            for row in summary_rows:
                f_sum.write(",".join(str(row[h]) for h in headers) + "\n")
    
    log_debug(f"Simulation complete. Raw data: {raw_p_values_file}, Summary: {summary_file}")

if __name__ == "__main__":
    main()
