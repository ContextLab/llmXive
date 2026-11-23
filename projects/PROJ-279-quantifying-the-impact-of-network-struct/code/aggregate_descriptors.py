"""
Module to aggregate topological and vibrational descriptors into a single CSV file.
Implements T025a logic and executes aggregation for T025b.
"""
import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from config.env_config import get_processed_dir, get_config
from logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

def load_processed_configs() -> List[Dict[str, Any]]:
    """
    Loads the list of validated configuration IDs and their basic metadata.
    In a real pipeline, this would read from the graph metadata or validation report.
    For this aggregation step, we assume the existence of descriptor files generated
    by T022 (Ring Stats), T023 (Steinhardt), and T024 (VDOS).
    
    Returns a list of dicts: [{'id': 'config_1', 'path': '...'}, ...]
    """
    processed_dir = get_processed_dir()
    validation_report_path = processed_dir / "validation_report.json"
    
    if not validation_report_path.exists():
        raise FileNotFoundError(f"Validation report not found at {validation_report_path}. "
                                "Run T007-exec first.")
    
    with open(validation_report_path, 'r') as f:
        report = json.load(f)
    
    # Extract validated configs
    validated_ids = report.get('validated_configs', [])
    configs = []
    for cfg_id in validated_ids:
        configs.append({
            'id': cfg_id,
            'path': processed_dir / "graphs" / f"{cfg_id}.graphml" # Assumed path based on T018
        })
    
    if not configs:
        logger.warning("No validated configurations found in validation report.")
        
    return configs

def load_vdos_retention_report() -> Dict[str, Any]:
    """
    Loads the VDOS retention report to identify which configs have missing VDOS.
    """
    processed_dir = get_processed_dir()
    retention_path = processed_dir / "vdos_retention_report.json"
    
    if not retention_path.exists():
        logger.warning(f"VDOS retention report not found at {retention_path}. "
                       "Assuming all configs have VDOS or handling missing gracefully.")
        return {"retained_configs": []}
    
    with open(retention_path, 'r') as f:
        return json.load(f)

def _load_ring_stats(config_id: str) -> Optional[Dict[str, float]]:
    """
    Loads ring statistics for a specific config.
    Expected file: data/processed/descriptors/ring_stats_{config_id}.json
    """
    processed_dir = get_processed_dir()
    file_path = processed_dir / "descriptors" / f"ring_stats_{config_id}.json"
    
    if not file_path.exists():
        logger.error(f"Ring stats file not found for {config_id}: {file_path}")
        return None
        
    with open(file_path, 'r') as f:
        return json.load(f)

def _load_steinhardt_stats(config_id: str) -> Optional[Dict[str, float]]:
    """
    Loads Steinhardt parameters for a specific config.
    Expected file: data/processed/descriptors/steinhardt_{config_id}.json
    """
    processed_dir = get_processed_dir()
    file_path = processed_dir / "descriptors" / f"steinhardt_{config_id}.json"
    
    if not file_path.exists():
        logger.error(f"Steinhardt file not found for {config_id}: {file_path}")
        return None
        
    with open(file_path, 'r') as f:
        return json.load(f)

def _load_vdos_vector(config_id: str) -> Optional[List[float]]:
    """
    Loads VDOS vector for a specific config.
    Expected file: data/processed/descriptors/vdos_{config_id}.json
    """
    processed_dir = get_processed_dir()
    file_path = processed_dir / "descriptors" / f"vdos_{config_id}.json"
    
    if not file_path.exists():
        return None
        
    with open(file_path, 'r') as f:
        data = json.load(f)
        # Expecting a list of floats or a dict with 'values'
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'values' in data:
            return data['values']
        else:
            logger.warning(f"Unexpected VDOS format for {config_id}")
            return None

def aggregate_descriptors(configs: List[Dict[str, Any]], 
                          retention_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Aggregates ring stats, Steinhardt Q6, clustering, and VDOS vectors into a single row per config.
    
    Schema:
      config_id, ring_dist, q6, clustering, vdos_vector, data_quality
      
    Logic:
      - If config is in retention_report (VDOS-MISSING), set vdos_vector to null and data_quality to 'topological_only'.
      - Otherwise, load VDOS and set data_quality to 'full'.
    """
    retained_ids = {
        item['id'] for item in retention_report.get('retained_configs', [])
    }
    
    aggregated_rows = []
    
    for cfg in configs:
        cfg_id = cfg['id']
        data_quality = "full"
        vdos_vector = None
        
        # Check if VDOS is missing
        if cfg_id in retained_ids:
            data_quality = "topological_only"
            logger.info(f"Config {cfg_id} marked as topological_only (VDOS missing).")
        else:
            # Try to load VDOS
            vdos_vector = _load_vdos_vector(cfg_id)
            if vdos_vector is None:
                # If not in retention report but file is missing, we still treat as missing
                # but log a discrepancy
                logger.warning(f"Config {cfg_id} not in retention report but VDOS file missing. "
                               "Marking as topological_only.")
                data_quality = "topological_only"
        
        # Load Topological Descriptors
        ring_stats = _load_ring_stats(cfg_id)
        steinhardt_stats = _load_steinhardt_stats(cfg_id)
        
        if ring_stats is None or steinhardt_stats is None:
            logger.error(f"Skipping {cfg_id} due to missing topological descriptors.")
            continue
            
        # Extract specific values
        # ring_stats expected: {'distribution': {3: count, ...}, 'avg_ring_size': float}
        # We'll flatten the distribution or use the average. Let's use average for simplicity in CSV
        ring_dist = ring_stats.get('avg_ring_size', 0.0)
        
        # steinhardt_stats expected: {'q6': float, ...}
        q6 = steinhardt_stats.get('q6', 0.0)
        clustering = steinhardt_stats.get('clustering', 0.0)
        
        # Format VDOS vector as a string for CSV if it exists
        vdos_str = None
        if vdos_vector is not None:
            # Convert list of floats to a comma-separated string
            vdos_str = ",".join([f"{x:.6f}" for x in vdos_vector])
        
        row = {
            'config_id': cfg_id,
            'ring_dist': ring_dist,
            'q6': q6,
            'clustering': clustering,
            'vdos_vector': vdos_str, # Storing as string for CSV compatibility
            'data_quality': data_quality
        }
        
        aggregated_rows.append(row)
        
    return aggregated_rows

def save_aggregated_data(rows: List[Dict[str, Any]], output_path: Path):
    """
    Saves the aggregated descriptors to a CSV file.
    """
    if not rows:
        logger.warning("No data to save.")
        return
        
    fieldnames = ['config_id', 'ring_dist', 'q6', 'clustering', 'vdos_vector', 'data_quality']
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    logger.info(f"Saved {len(rows)} aggregated descriptor rows to {output_path}")

def main():
    """
    Entry point for T025b: Execute Aggregation.
    """
    processed_dir = get_processed_dir()
    output_path = processed_dir / "descriptors.csv"
    
    logger.info("Starting descriptor aggregation (T025b)...")
    
    try:
        # 1. Load validated configs
        configs = load_processed_configs()
        if not configs:
            logger.error("No configurations found to aggregate.")
            return
        
        # 2. Load VDOS retention report
        retention_report = load_vdos_retention_report()
        
        # 3. Aggregate
        aggregated_rows = aggregate_descriptors(configs, retention_report)
        
        # 4. Save
        save_aggregated_data(aggregated_rows, output_path)
        
        logger.info("Aggregation completed successfully.")
        
    except Exception as e:
        logger.exception(f"Aggregation failed: {e}")
        raise

if __name__ == "__main__":
    main()
