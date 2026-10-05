"""
Main orchestration script for the llmXive automated science pipeline.

This script:
1. Loads configuration and real datasets.
2. Generates synthetic queries with ground-truth plans.
3. Routes queries to appropriate executors (Text, Relational, Graph).
4. Records execution metrics (latency, translation errors).
5. Performs statistical analysis (ANOVA, sensitivity).
6. Persists raw logs and aggregated results to disk.
"""

import os
import sys
import json
import time
import csv
import random
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import CONFIG, EXIT_CODE_THROTTLING_FAILURE
from utils.cpu_throttle import check_throttling_validity, throttled_context, ThrottleError
from utils.data_fetcher import verify_all_datasets, DataFetchError
from generators.reference_engine import ReferenceEngine
from generators.synthetic_query import SyntheticQueryGenerator
from executors.text_executor import TextExecutor
from executors.relational_executor import RelationalExecutor
from executors.graph_executor import GraphExecutor
from analysis.metrics import record_execution_metric, save_metrics_to_file, ExecutionMetric
from analysis.stats import (
    load_execution_logs,
    perform_assumption_checks,
    run_anova,
    calculate_slope_ratios,
    run_post_hoc_tukey,
    perform_sensitivity_analysis
)

def ensure_directories():
    """Ensure required output directories exist."""
    dirs = [
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "results",
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "figures"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def fetch_real_data():
    """Fetch and verify real datasets required for the experiment."""
    try:
        verify_all_datasets()
        print("All real datasets verified successfully.")
    except DataFetchError as e:
        print(f"CRITICAL: Failed to fetch/verify real data: {e}")
        sys.exit(EXIT_CODE_THROTTLING_FAILURE)

def run_experiment():
    """Main experiment loop."""
    ensure_directories()
    
    # 1. Verify Real Data
    # Note: T005/T016c handles URL config and download. We verify here.
    # If datasets are too large, we rely on streaming in executors, 
    # but we ensure the source files are present.
    fetch_real_data()
    
    # 2. Check Throttling Validity
    # Must abort if throttling cannot be applied correctly (T016b)
    if not check_throttling_validity():
        print("CRITICAL: CPU throttling validation failed. Aborting run.")
        sys.exit(EXIT_CODE_THROTTLING_FAILURE)
    
    # 3. Initialize Components
    reference_engine = ReferenceEngine()
    query_generator = SyntheticQueryGenerator(reference_engine)
    
    # Initialize Executors
    text_executor = TextExecutor()
    relational_executor = RelationalExecutor()
    graph_executor = GraphExecutor()
    
    # 4. Generate Queries
    # T006/T017: Generate queries with integer complexity_level (1, 2, 3, 4+)
    # T007: Reference engine provides ground_truth_plan
    num_queries = CONFIG.get("num_queries", 100)
    queries = query_generator.generate(num_queries)
    
    print(f"Generated {len(queries)} queries.")
    
    # 5. Execute Queries and Record Metrics
    all_metrics = []
    
    for idx, query in enumerate(queries):
        print(f"Executing query {idx+1}/{len(queries)} (Type: {query['source_type']}, Complexity: {query['complexity_level']})")
        
        source_type = query["source_type"]
        complexity = query["complexity_level"]
        
        # Select Executor
        if source_type == "text":
            executor = text_executor
        elif source_type == "relational":
            executor = relational_executor
        elif source_type == "graph":
            executor = graph_executor
        else:
            print(f"Unknown source type: {source_type}, skipping.")
            continue
        
        # Execute with Throttling
        start_time = time.time()
        execution_result = None
        error_flag = False
        
        try:
            with throttled_context(timeout=CONFIG.get("timeout_seconds", 60)):
                execution_result = executor.execute(query)
        except ThrottleError as e:
            print(f"Execution timed out or throttled: {e}")
            execution_result = {"status": "timeout", "latency": None}
            error_flag = True
        except Exception as e:
            print(f"Execution error: {e}")
            execution_result = {"status": "error", "latency": None}
            error_flag = True
        
        end_time = time.time()
        raw_latency_ms = (end_time - start_time) * 1000 if not error_flag and execution_result and execution_result.get("latency") else None
        
        # If executor returned a latency, use that (it might be simulated internal time)
        # Otherwise, use wall clock if not timed out
        if execution_result and execution_result.get("latency") is not None:
            raw_latency_ms = execution_result["latency"]
        elif raw_latency_ms is None:
            raw_latency_ms = 0.0 # Or handle as missing

        # Record Metric
        metric = record_execution_metric(
            query_id=query["id"],
            source_type=source_type,
            complexity_level=complexity,
            ground_truth_plan=query.get("ground_truth_plan"),
            executed_plan=execution_result.get("plan") if execution_result else None,
            latency_ms=raw_latency_ms,
            success=not error_flag,
            timeout=error_flag and "timeout" in str(execution_result)
        )
        all_metrics.append(metric)
    
    # 6. Persist Raw Logs (Task T021 Requirement)
    raw_logs_path = PROJECT_ROOT / "data" / "processed" / "execution_logs.csv"
    save_metrics_to_file(all_metrics, raw_logs_path)
    print(f"Raw metrics saved to {raw_logs_path}")
    
    # 7. Perform Statistical Analysis
    print("Performing statistical analysis...")
    
    # Load logs for analysis (to ensure consistency)
    logs_df = load_execution_logs(raw_logs_path)
    
    # ANOVA
    anova_results = run_anova(logs_df, "latency_ms", "complexity_level", "source_type")
    
    # Slope Ratios
    slope_ratios = calculate_slope_ratios(logs_df, "latency_ms", "complexity_level", "source_type")
    
    # Post-hoc Tukey
    tukey_results = run_post_hoc_tukey(logs_df, "latency_ms", "source_type")
    
    # Sensitivity Analysis (T020 dependency: uses raw logs)
    sensitivity_results = perform_sensitivity_analysis(logs_df, "latency_ms", "complexity_level", "source_type")
    
    # Aggregate Results
    aggregated_stats = {
        "anova": anova_results,
        "slope_ratios": slope_ratios,
        "post_hoc_tukey": tukey_results,
        "sensitivity_analysis": sensitivity_results,
        "total_queries": len(all_metrics),
        "successful_queries": sum(1 for m in all_metrics if m.success)
    }
    
    # Persist Aggregated Stats (Task T021 Requirement)
    stats_path = PROJECT_ROOT / "data" / "results" / "anova_results.json"
    with open(stats_path, "w") as f:
        json.dump(aggregated_stats, f, indent=2, default=str)
    print(f"Aggregated stats saved to {stats_path}")
    
    return aggregated_stats

def main():
    """Entry point."""
    try:
        results = run_experiment()
        print("Experiment completed successfully.")
        return 0
    except Exception as e:
        print(f"Experiment failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
