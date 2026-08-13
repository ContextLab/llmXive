"""
Radio Metrics Extractor (T046a)

Processes raw radio metrics from T048 (SNR/Bandwidth) and network stats from T014a
(packet counts/loss) into a unified `radio_metrics_extracted.json`.

This file is the required input for T032 (Theoretical Bound Validation) and T046c (Phase 6 Validation).

Dependencies:
- T048: Generates raw radio metrics (SNR, Bandwidth) per node.
- T014a: Generates network stats (packet counts, loss) per node.
- T013c: Generates dropout events (optional context).
"""

import json
import logging
import os
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Import logger from the project's orchestrator module
from orchestrator.logger import get_logger

# Constants for file paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = RAW_DATA_DIR / "radio_metrics_extracted.json"

# Input patterns for raw data files
# T048 typically outputs per-node JSON or a consolidated JSON. We assume a consolidated file
# or a directory of per-node files. For robustness, we look for files matching specific patterns.
RADIO_METRICS_PATTERN = "radio_metrics_*.json"
NETWORK_STATS_PATTERN = "network_stats_*.json"
INSTRUMENTATION_PATTERN = "instrumentation_*.json"

logger = get_logger(__name__)


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        return None


def find_latest_run_files(data_dir: Path, pattern: str) -> List[Path]:
    """
    Find files matching a pattern in the data directory.
    Returns a list of Path objects.
    """
    if not data_dir.exists():
        logger.error(f"Data directory does not exist: {data_dir}")
        return []
    
    files = list(data_dir.glob(pattern))
    if not files:
        logger.warning(f"No files found matching pattern: {pattern} in {data_dir}")
    return sorted(files)


def extract_radio_metrics_from_raw(raw_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    """
    Extract SNR and Bandwidth from a raw radio metrics data structure.
    Expected structure (based on T048):
    {
        "node_id": "...",
        "snr_db": float,
        "bandwidth_Mbps": float,
        ...
    }
    """
    snr = raw_data.get("snr_db")
    bandwidth = raw_data.get("bandwidth_Mbps")
    return snr, bandwidth


def extract_network_stats_from_raw(raw_data: Dict[str, Any]) -> Tuple[Optional[int], Optional[float]]:
    """
    Extract packet count and loss rate from a raw network stats data structure.
    Expected structure (based on T014a):
    {
        "node_id": "...",
        "packet_count": int,
        "packet_loss_rate": float,
        ...
    }
    """
    packet_count = raw_data.get("packet_count")
    loss_rate = raw_data.get("packet_loss_rate")
    return packet_count, loss_rate


def aggregate_metrics(raw_files: List[Path]) -> Dict[str, Any]:
    """
    Aggregate metrics from multiple raw data files into a unified structure.
    
    Returns:
        Dict containing:
        - run_id: Identifier for the run (derived from filename or timestamp)
        - avg_snr_db: Average SNR across all nodes
        - avg_bandwidth_Mbps: Average bandwidth across all nodes
        - node_snr_map: Dict mapping node_id -> snr_db
        - node_bandwidth_map: Dict mapping node_id -> bandwidth_Mbps
        - node_packet_map: Dict mapping node_id -> packet_count
        - node_loss_map: Dict mapping node_id -> packet_loss_rate
    """
    node_snr_map = {}
    node_bandwidth_map = {}
    node_packet_map = {}
    node_loss_map = {}
    node_count = 0
    total_snr = 0.0
    total_bandwidth = 0.0
    snr_count = 0
    bandwidth_count = 0

    run_id = None

    for file_path in raw_files:
        data = load_json_file(file_path)
        if not data:
            continue

        # Infer run_id from filename if not present in data
        if run_id is None:
            run_id = file_path.stem.replace("radio_metrics_", "").replace("network_stats_", "")
            # If it's a generic name, use timestamp or a default
            if not run_id:
                run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        node_id = data.get("node_id")
        if not node_id:
            logger.warning(f"Skipping file {file_path} due to missing node_id")
            continue

        # Extract Radio Metrics (from T048)
        if "snr_db" in data or "bandwidth_Mbps" in data:
            snr, bw = extract_radio_metrics_from_raw(data)
            if snr is not None:
                node_snr_map[node_id] = snr
                total_snr += snr
                snr_count += 1
            if bw is not None:
                node_bandwidth_map[node_id] = bw
                total_bandwidth += bw
                bandwidth_count += 1

        # Extract Network Stats (from T014a)
        if "packet_count" in data or "packet_loss_rate" in data:
            packet_count, loss_rate = extract_network_stats_from_raw(data)
            if packet_count is not None:
                node_packet_map[node_id] = packet_count
            if loss_rate is not None:
                node_loss_map[node_id] = loss_rate

        node_count += 1

    # Calculate averages
    avg_snr = total_snr / snr_count if snr_count > 0 else None
    avg_bandwidth = total_bandwidth / bandwidth_count if bandwidth_count > 0 else None

    result = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "node_count": node_count,
        "avg_snr_db": avg_snr,
        "avg_bandwidth_Mbps": avg_bandwidth,
        "node_snr_map": node_snr_map,
        "node_bandwidth_map": node_bandwidth_map,
        "node_packet_map": node_packet_map,
        "node_loss_map": node_loss_map,
        "status": "complete" if node_count > 0 else "empty"
    }

    return result


def main():
    """
    Main entry point for the radio metrics extractor.
    Reads raw data from data/raw/, aggregates it, and writes to data/raw/radio_metrics_extracted.json.
    """
    logger.info("Starting Radio Metrics Extraction (T046a)")

    # Ensure the output directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Find raw files
    # We look for files generated by T048 (radio_metrics_*.json) and T014a (network_stats_*.json or instrumentation_*.json)
    # Since T048 and T014a might write to the same directory, we aggregate all relevant files.
    
    radio_files = find_latest_run_files(RAW_DATA_DIR, RADIO_METRICS_PATTERN)
    network_files = find_latest_run_files(RAW_DATA_DIR, NETWORK_STATS_PATTERN)
    instrument_files = find_latest_run_files(RAW_DATA_DIR, INSTRUMENTATION_PATTERN)

    all_files = list(set(radio_files + network_files + instrument_files))

    if not all_files:
        logger.error("No raw radio or network metric files found. T048 and T014a must run first.")
        # Create an empty result to indicate failure state
        result = {
            "run_id": "failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node_count": 0,
            "avg_snr_db": None,
            "avg_bandwidth_Mbps": None,
            "node_snr_map": {},
            "node_bandwidth_map": {},
            "node_packet_map": {},
            "node_loss_map": {},
            "status": "failed_no_data",
            "error": "No raw data files found. Ensure T048 and T014a have executed."
        }
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        return

    logger.info(f"Found {len(all_files)} raw files to process.")

    # Aggregate
    aggregated = aggregate_metrics(all_files)

    # Write output
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(aggregated, f, indent=2)
        logger.info(f"Successfully wrote aggregated radio metrics to {OUTPUT_FILE}")
    except IOError as e:
        logger.error(f"Failed to write output file: {e}")
        raise


if __name__ == "__main__":
    main()