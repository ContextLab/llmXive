"""
Data collector to aggregate raw logs from nodes and write to CSV.
"""
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from orchestrator.logger import get_logger

logger = get_logger(__name__)

def collect_and_save_logs(run_id: str, node_logs: List[Dict[str, Any]], output_dir: Path):
    """
    Aggregate raw logs from nodes and write to a CSV file in data/raw/.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"run_{run_id}_raw.csv"
    
    logger.info(f"Writing raw logs to {output_path}")
    
    if not node_logs:
        logger.warning("No logs to write.")
        return

    # Define CSV headers based on expected schema
    headers = [
        "timestamp", "run_id", "node_id", "cpu_utilization_pct", 
        "packet_count", "throughput_ops", "latency_ms"
    ]
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        
        for log in node_logs:
            # Ensure all keys exist, fill with defaults if missing
            row = {k: log.get(k, '') for k in headers}
            writer.writerow(row)
    
    logger.info(f"Successfully wrote {len(node_logs)} records to {output_path}")
