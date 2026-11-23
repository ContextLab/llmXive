import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the paths to the result CSVs based on completed tasks
# T013: baseline_results.csv
# T019a: lazy_results.csv
# T019b: greedy_results.csv
# T019c: noisy_lazy_results.csv
# T019d: noisy_greedy_results.csv
# Note: T013b is noisy_baseline_results.csv

RESULTS_FILES = [
    "data/processed/baseline_results.csv",
    "data/processed/lazy_results.csv",
    "data/processed/greedy_results.csv",
    "data/processed/noisy_baseline_results.csv",
    "data/processed/noisy_lazy_results.csv",
    "data/processed/noisy_greedy_results.csv"
]

def load_results_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Load results from a CSV file.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        List of dictionaries representing each row.
    """
    results = []
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"File not found: {file_path}. Skipping.")
        return results
    
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                try:
                    row['accuracy'] = float(row['accuracy'])
                    row['nodes_visited'] = int(row['nodes_visited'])
                    row['latency_ms'] = float(row['latency_ms'])
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error converting row in {file_path}: {e}")
                    continue
                results.append(row)
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
    return results

def count_timeout_tasks(results: List[Dict[str, Any]]) -> int:
    """
    Count the number of tasks that timed out.
    
    Args:
        results: List of result dictionaries.
        
    Returns:
        Count of tasks with status 'timeout'.
    """
    return sum(1 for r in results if r.get('status') == 'timeout')

def count_completed_tasks(results: List[Dict[str, Any]]) -> int:
    """
    Count the number of tasks that completed successfully.
    
    Args:
        results: List of result dictionaries.
        
    Returns:
        Count of tasks with status 'completed'.
    """
    return sum(1 for r in results if r.get('status') == 'completed')

def aggregate_timeout_stats() -> Dict[str, Any]:
    """
    Aggregate timeout statistics from all result CSVs.
    
    Returns:
        Dictionary containing timeout statistics.
    """
    stats = {
        "total_tasks": 0,
        "total_timeouts": 0,
        "total_completed": 0,
        "files": {}
    }
    
    for file_path in RESULTS_FILES:
        results = load_results_from_csv(file_path)
        if not results:
            continue
            
        file_name = Path(file_path).name
        timeouts = count_timeout_tasks(results)
        completed = count_completed_tasks(results)
        
        stats["files"][file_name] = {
            "total": len(results),
            "timeouts": timeouts,
            "completed": completed
        }
        
        stats["total_tasks"] += len(results)
        stats["total_timeouts"] += timeouts
        stats["total_completed"] += completed
    
    if stats["total_tasks"] > 0:
        stats["timeout_rate"] = stats["total_timeouts"] / stats["total_tasks"]
    else:
        stats["timeout_rate"] = 0.0
        
    return stats

def save_stats_report(stats: Dict[str, Any], output_path: str = "data/processed/stats_report.json") -> None:
    """
    Save the aggregated statistics to a JSON file.
    
    Args:
        stats: Dictionary containing statistics.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Stats report saved to {output_path}")

def main():
    """
    Main function to run the timeout aggregation analysis.
    """
    logger.info("Starting timeout aggregation analysis...")
    
    stats = aggregate_timeout_stats()
    
    # Save the report
    save_stats_report(stats)
    
    # Print summary
    print("\n--- Timeout Aggregation Summary ---")
    print(f"Total Tasks Processed: {stats['total_tasks']}")
    print(f"Total Timeouts: {stats['total_timeouts']}")
    print(f"Total Completed: {stats['total_completed']}")
    print(f"Overall Timeout Rate: {stats['timeout_rate']:.2%}")
    print("-----------------------------------")
    
    if stats['files']:
        print("\nPer-File Breakdown:")
        for file_name, file_stats in stats['files'].items():
            print(f"  {file_name}: {file_stats['timeouts']}/{file_stats['total']} timeouts")
    
    logger.info("Timeout aggregation analysis completed.")

if __name__ == "__main__":
    main()