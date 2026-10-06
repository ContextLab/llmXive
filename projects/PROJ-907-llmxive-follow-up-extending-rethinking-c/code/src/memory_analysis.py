import os
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_memory_usage_gb() -> float:
    """Returns current RAM usage in GB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return mem_info.rss / (1024 ** 3)
    except ImportError:
        logger.warning("psutil not installed. Returning 0.0.")
        return 0.0

def parse_memory_log(log_path: str) -> List[Dict[str, Any]]:
    """Parses the memory log file and returns a list of entries."""
    entries = []
    with open(log_path, 'r') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries

def compute_memory_statistics(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes statistics from memory log entries."""
    if not entries:
        return {
            "peak_memory_gb": 0.0,
            "average_memory_gb": 0.0,
            "status": "NO_DATA"
        }
    
    memory_values = [entry['memory_gb'] for entry in entries]
    peak_memory = max(memory_values)
    average_memory = sum(memory_values) / len(memory_values)
    
    status = "PASS" if peak_memory < 7.0 else "FAIL"
    
    return {
        "peak_memory_gb": peak_memory,
        "average_memory_gb": average_memory,
        "status": status
    }

def generate_markdown_report(stats: Dict[str, Any]) -> str:
    """Generates a markdown report from memory statistics."""
    report = f"""
    # Memory Usage Report

    - **Peak Memory**: {stats['peak_memory_gb']:.2f} GB
    - **Average Memory**: {stats['average_memory_gb']:.2f} GB
    - **Status**: {stats['status']}
    """
    return report

def save_json_profile(stats: Dict[str, Any], output_path: str):
    """Saves memory profile to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)

def run_memory_analysis(log_path: str, output_path: str):
    """Runs the full memory analysis."""
    entries = parse_memory_log(log_path)
    stats = compute_memory_statistics(entries)
    save_json_profile(stats, output_path)
    
    # Generate markdown report
    report = generate_markdown_report(stats)
    report_path = output_path.replace('.json', '.md')
    with open(report_path, 'w') as f:
        f.write(report)
    logger.info(f"Saved memory report to {report_path}")

def main():
    """Entry point for the memory analysis script."""
    log_path = os.getenv('MEMORY_LOG_PATH', 'data/results/memory_profile_raw.jsonl')
    output_path = os.getenv('MEMORY_PROFILE_PATH', 'data/results/memory_profile.json')
    run_memory_analysis(log_path, output_path)

if __name__ == "__main__":
    main()
