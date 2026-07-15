import os
import csv
import json
import sys
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class AggregatedResult:
    """Data structure for a single aggregated benchmark result row."""
    size: int
    fpr: float
    impl: str
    rep_id: int
    memory_mb: float
    latency_ms: float
    query_count: int
    theoretical_memory_bits: float

def validate_query_count(query_count: int) -> bool:
    """
    Validate that query_count is greater than 0.
    
    Args:
        query_count: The number of queries executed in a benchmark run.
        
    Returns:
        True if query_count > 0, False otherwise.
        
    Raises:
        ValueError: If query_count is not a positive integer.
    """
    if query_count <= 0:
        raise ValueError(f"Query count must be greater than 0, got {query_count}")
    return True

def aggregate_runs(
    runs: List[Dict[str, Any]],
    theoretical_baselines: Optional[Dict[Tuple[int, float, str], float]] = None
) -> List[AggregatedResult]:
    """
    Aggregate benchmark runs into a list of AggregatedResult objects.
    
    This function validates that each run has a positive query_count and
    attaches theoretical memory bits if baselines are provided.
    
    Args:
        runs: List of raw benchmark run dictionaries containing keys:
              size, fpr, impl, rep_id, memory_mb, latency_ms, query_count
        theoretical_baselines: Optional dict mapping (size, fpr, impl) -> theoretical_memory_bits
        
    Returns:
        List of validated AggregatedResult objects.
        
    Raises:
        ValueError: If any run has query_count <= 0.
    """
    aggregated = []
    
    for run in runs:
        # Validate query count first - abort if invalid
        validate_query_count(run['query_count'])
        
        # Retrieve theoretical memory bits if available
        key = (run['size'], run['fpr'], run['impl'])
        theoretical_bits = 0.0
        if theoretical_baselines and key in theoretical_baselines:
            theoretical_bits = theoretical_baselines[key]
        
        result = AggregatedResult(
            size=run['size'],
            fpr=run['fpr'],
            impl=run['impl'],
            rep_id=run['rep_id'],
            memory_mb=run['memory_mb'],
            latency_ms=run['latency_ms'],
            query_count=run['query_count'],
            theoretical_memory_bits=theoretical_bits
        )
        aggregated.append(result)
        
    return aggregated

def write_results_csv(
    results: List[AggregatedResult],
    output_path: str
) -> None:
    """
    Write aggregated results to a CSV file.
    
    Args:
        results: List of AggregatedResult objects to write.
        output_path: Path to the output CSV file.
        
    The CSV will contain headers:
    size, fpr, impl, rep_id, memory_mb, latency_ms, query_count, theoretical_memory_bits
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = [
        'size', 'fpr', 'impl', 'rep_id', 'memory_mb', 
        'latency_ms', 'query_count', 'theoretical_memory_bits'
    ]
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow(asdict(result))
            
    print(f"Results written to {output_path}")

def main():
    """
    Main entry point for the aggregator script.
    
    This function is designed to be called by the benchmark runner
    after all benchmark runs are complete. It loads raw results,
    validates them, aggregates them with theoretical baselines,
    and writes the final CSV.
    """
    # Paths relative to project root
    results_dir = "results/benchmarks"
    raw_results_path = os.path.join(results_dir, "raw_results.json")
    baselines_path = os.path.join(results_dir, "theoretical_baselines.json")
    output_csv_path = os.path.join(results_dir, "aggregated_results.csv")
    
    # Check if raw results exist
    if not os.path.exists(raw_results_path):
        print(f"Error: Raw results file not found at {raw_results_path}")
        print("Please run the benchmark suite first.")
        sys.exit(1)
        
    # Load raw results
    with open(raw_results_path, 'r') as f:
        raw_runs = json.load(f)
        
    print(f"Loaded {len(raw_runs)} raw benchmark runs.")
    
    # Load theoretical baselines if available
    theoretical_baselines = None
    if os.path.exists(baselines_path):
        with open(baselines_path, 'r') as f:
            baselines_data = json.load(f)
            # Convert string keys back to tuple keys
            theoretical_baselines = {}
            for key_str, value in baselines_data.items():
                # Format: "(size, fpr, impl)" -> (size, fpr, impl)
                key_str_clean = key_str.strip("()").replace("'", "").replace(" ", "")
                parts = key_str_clean.split(",")
                key = (int(parts[0]), float(parts[1]), parts[2])
                theoretical_baselines[key] = value
        print(f"Loaded {len(theoretical_baselines)} theoretical baseline entries.")
    
    # Aggregate and validate
    try:
        aggregated = aggregate_runs(raw_runs, theoretical_baselines)
    except ValueError as e:
        print(f"CRITICAL ERROR: {e}")
        print("Aborting aggregation due to invalid query counts.")
        sys.exit(1)
        
    print(f"Successfully aggregated {len(aggregated)} valid runs.")
    
    # Write final CSV
    write_results_csv(aggregated, output_csv_path)
    
    # Generate summary stats
    if aggregated:
        total_queries = sum(r.query_count for r in aggregated)
        print(f"Total queries processed: {total_queries}")
        print("Aggregation complete.")

if __name__ == "__main__":
    main()