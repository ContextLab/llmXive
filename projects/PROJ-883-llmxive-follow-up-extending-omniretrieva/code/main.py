"""
Main orchestration script for the llmXive research pipeline.
"""
import os
import sys
import json
import time
import random
from typing import List, Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config import DATA_DIR, PROCESSED_DIR, RESULTS_DIR, EXIT_CODE_THROTTLING_FAILURE
from generators.synthetic_query import SyntheticQueryGenerator
from utils.cpu_throttle import check_throttling_validity, throttled_context, ThrottleError

def main():
    """
    Orchestrate the experiment:
    1. Validate throttling
    2. Generate queries
    3. Execute (simulated for T001)
    4. Log metrics
    """
    print("Starting llmXive research pipeline...")

    # 1. Validate throttling
    if not check_throttling_validity():
        print("ERROR: Throttling validation failed. Aborting.")
        sys.exit(EXIT_CODE_THROTTLING_FAILURE)

    # 2. Generate queries
    generator = SyntheticQueryGenerator(seed=42)
    queries = []
    for qt in ["text", "relational", "graph"]:
        for depth in [1, 2, 3, 4]:
            q = generator.generate_query(qt, depth)
            queries.append(q)
    
    print(f"Generated {len(queries)} queries.")

    # 3. Execute (Simulated for T001 - real executors will be added in T009-T011)
    # We simulate execution time based on complexity and type
    execution_logs = []
    
    for q in queries:
        start = time.time()
        try:
            # Simulate execution with throttling
            with throttled_context(cpu_limit_seconds=10.0, memory_limit_mb=512):
                # Simulate work proportional to complexity
                time.sleep(0.01 * q["complexity_level"]) 
                if q["query_type"] == "graph":
                    time.sleep(0.02 * q["complexity_level"]) # Graph is slower
        except ThrottleError as e:
            execution_logs.append({
                "query_id": q["id"],
                "status": "timeout",
                "latency_ms": -1,
                "error": str(e)
            })
            continue

        latency_ms = (time.time() - start) * 1000
        execution_logs.append({
            "query_id": q["id"],
            "query_type": q["query_type"],
            "complexity_level": q["complexity_level"],
            "status": "success",
            "latency_ms": latency_ms
        })

    # 4. Save raw metrics
    log_path = os.path.join(PROCESSED_DIR, "execution_logs.csv")
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    # Write CSV
    if execution_logs:
        with open(log_path, "w") as f:
            f.write(",".join(execution_logs[0].keys()) + "\n")
            for log in execution_logs:
                f.write(",".join(str(v) for v in log.values()) + "\n")
        print(f"Execution logs saved to {log_path}")
    else:
        print("No execution logs generated.")

if __name__ == "__main__":
    main()
