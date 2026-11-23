"""
Radio Metrics Extractor (T046a)

Processes raw radio metrics from T048 (radio_metrics_collector.py) and network stats
from T014a (instrumentor_remote.py) to produce a unified radio_metrics_extracted.json.

This file aggregates per-node SNR and bandwidth measurements, calculates averages,
and writes the result to data/raw/radio_metrics_extracted.json.
"""

import json
import logging
import os
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import logger from existing orchestrator module
from orchestrator.logger import get_logger

logger = get_logger(__name__)

# Output path as specified in tasks.md
OUTPUT_PATH = Path("data/raw/radio_metrics_extracted.json")

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None

def find_latest_run_files(directory: Path, pattern: str) -> List[Path]:
    """
    Find all files matching the pattern in the given directory.
    Returns a list of Path objects sorted by modification time (newest first).
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []

    files = list(directory.glob(pattern))
    # Sort by modification time, newest first
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files

def extract_radio_metrics_from_raw(raw_dir: Path) -> Dict[str, Any]:
    """
    Extract radio metrics from T048 output files.
    Looks for radio_metrics_collector outputs (JSON format).

    Expected input format (from T048):
    {
        "run_id": "run_001",
        "node_id": "node_192_168_1_10",
        "snr_db": 25.5,
        "bandwidth_Mbps": 100.2,
        "timestamp": "..."
    }
    """
    radio_files = find_latest_run_files(raw_dir, "radio_metrics_*.json")
    
    if not radio_files:
        logger.warning("No radio metrics files found in raw directory")
        return {}

    radio_data = {}
    for file_path in radio_files:
        data = load_json_file(file_path)
        if data and isinstance(data, dict):
            node_id = data.get("node_id", "unknown")
            run_id = data.get("run_id", "unknown")
            
            if node_id not in radio_data:
                radio_data[node_id] = {
                    "run_id": run_id,
                    "snr_db": [],
                    "bandwidth_Mbps": []
                }
            
            # Collect measurements (allow multiple samples per node)
            if "snr_db" in data and data["snr_db"] is not None:
                radio_data[node_id]["snr_db"].append(data["snr_db"])
            if "bandwidth_Mbps" in data and data["bandwidth_Mbps"] is not None:
                radio_data[node_id]["bandwidth_Mbps"].append(data["bandwidth_Mbps"])

    return radio_data

def extract_network_stats_from_raw(raw_dir: Path) -> Dict[str, Any]:
    """
    Extract network stats from T014a output files.
    Looks for instrumentor_remote or data_collector outputs.

    Expected input format (from T014a/T017):
    {
        "run_id": "run_001",
        "node_id": "node_192_168_1_10",
        "packet_count": 1500,
        "cpu_utilization_pct": 45.2,
        "packet_loss_rate": 0.02
    }
    """
    # Look for data collector output or instrumentor output
    network_files = find_latest_run_files(raw_dir, "data_collected_*.json")
    if not network_files:
        # Try alternative pattern
        network_files = find_latest_run_files(raw_dir, "*network*.json")
    
    if not network_files:
        logger.warning("No network stats files found in raw directory")
        return {}

    network_data = {}
    for file_path in network_files:
        data = load_json_file(file_path)
        if data and isinstance(data, dict):
            node_id = data.get("node_id", "unknown")
            run_id = data.get("run_id", "unknown")
            
            if node_id not in network_data:
                network_data[node_id] = {
                    "run_id": run_id,
                    "packet_loss_rate": []
                }
            
            if "packet_loss_rate" in data:
                network_data[node_id]["packet_loss_rate"].append(data["packet_loss_rate"])

    return network_data

def aggregate_metrics(radio_data: Dict[str, Any], network_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate per-node metrics into summary statistics.
    Calculates average SNR and bandwidth for the mesh.
    """
    if not radio_data:
        logger.warning("No radio data to aggregate")
        return {
            "run_id": "unknown",
            "avg_snr_db": None,
            "avg_bandwidth_Mbps": None,
            "node_snr_map": {},
            "node_bandwidth_map": {}
        }

    # Use the run_id from the first available data point
    run_id = list(radio_data.values())[0].get("run_id", "unknown")

    node_snr_map = {}
    node_bandwidth_map = {}
    all_snr_values = []
    all_bandwidth_values = []

    for node_id, metrics in radio_data.items():
        snr_values = metrics.get("snr_db", [])
        bandwidth_values = metrics.get("bandwidth_Mbps", [])

        # Calculate average for this node
        if snr_values:
            avg_snr = sum(snr_values) / len(snr_values)
            node_snr_map[node_id] = avg_snr
            all_snr_values.extend(snr_values)
        else:
            node_snr_map[node_id] = None

        if bandwidth_values:
            avg_bandwidth = sum(bandwidth_values) / len(bandwidth_values)
            node_bandwidth_map[node_id] = avg_bandwidth
            all_bandwidth_values.extend(bandwidth_values)
        else:
            node_bandwidth_map[node_id] = None

    # Calculate mesh-wide averages
    avg_snr_db = sum(all_snr_values) / len(all_snr_values) if all_snr_values else None
    avg_bandwidth_Mbps = sum(all_bandwidth_values) / len(all_bandwidth_values) if all_bandwidth_values else None

    return {
        "run_id": run_id,
        "avg_snr_db": avg_snr_db,
        "avg_bandwidth_Mbps": avg_bandwidth_Mbps,
        "node_snr_map": node_snr_map,
        "node_bandwidth_map": node_bandwidth_map
    }

def main():
    """
    Main entry point for radio metrics extraction.
    Reads raw data from data/raw/, processes it, and writes to data/raw/radio_metrics_extracted.json.
    """
    logger.info("Starting radio metrics extraction (T046a)")

    # Define input directory
    raw_dir = Path("data/raw")
    
    if not raw_dir.exists():
        logger.error("Raw data directory does not exist: data/raw")
        raise FileNotFoundError("Raw data directory does not exist: data/raw")

    # Extract metrics from raw files
    radio_data = extract_radio_metrics_from_raw(raw_dir)
    network_data = extract_network_stats_from_raw(raw_dir)

    # Log summary
    logger.info(f"Found {len(radio_data)} nodes with radio metrics")
    logger.info(f"Found {len(network_data)} nodes with network stats")

    # Aggregate metrics
    aggregated = aggregate_metrics(radio_data, network_data)

    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(aggregated, f, indent=2)

    logger.info(f"Radio metrics extracted and saved to {OUTPUT_PATH}")
    logger.info(f"  - run_id: {aggregated['run_id']}")
    logger.info(f"  - avg_snr_db: {aggregated['avg_snr_db']}")
    logger.info(f"  - avg_bandwidth_Mbps: {aggregated['avg_bandwidth_Mbps']}")

    return aggregated

if __name__ == "__main__":
    main()