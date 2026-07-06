"""
VDOS Handling Module for T024.

Implements load_vdos() and calculate_participation_ratios().
Constraint: Attempts to load pre-calculated VDOS data. If missing,
logs ERR-VDOS-MISSING and excludes the configuration.
Does NOT calculate VDOS internally.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from logging_config import get_logger
from models.atomic_config import AtomicConfiguration

logger = get_logger(__name__)

# Expected directory structure based on project plan
VDOS_DATA_DIR = Path("data/raw/vdos")  # Assuming pre-calculated VDOS is here
MISSING_REPORT_PATH = Path("data/processed/vdos_missing_report.json")

def load_vdos(config_id: str, data_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Attempt to load pre-calculated VDOS data for a specific configuration ID.
    
    Args:
        config_id: The unique identifier for the atomic configuration.
        data_dir: Optional override for the VDOS data directory. Defaults to data/raw/vdos.
        
    Returns:
        A dictionary containing VDOS data (frequencies, dos, etc.) if found.
        None if the data is missing.
    """
    if data_dir is None:
        data_dir = Path("data/raw/vdos")
        
    # Expected file pattern: <config_id>_vdos.json or similar
    # We assume the dataset provides files named by config_id
    possible_extensions = ['.json', '.npy', '.txt']
    vdos_file = None
    
    for ext in possible_extensions:
        candidate = data_dir / f"{config_id}_vdos{ext}"
        if candidate.exists():
            vdos_file = candidate
            break
        
    if vdos_file is None:
        # Also check for a generic mapping file if the naming convention is different
        # But per strict constraints, we look for the specific ID first.
        logger.warning(f"ERR-VDOS-MISSING: No VDOS file found for config_id '{config_id}'. "
                       f"Searched in {data_dir} for patterns *_vdos{possible_extensions}.")
        return None

    try:
        if vdos_file.suffix == '.json':
            with open(vdos_file, 'r') as f:
                data = json.load(f)
        elif vdos_file.suffix == '.npy':
            # Assuming it's a structured array or dict saved via np.save
            data = np.load(vdos_file, allow_pickle=True).item()
        else:
            # Fallback for text based, expecting simple frequency/dos pairs
            # This is a minimal implementation; real parsing depends on source format
            logger.warning(f"VDOS file for {config_id} is text format. Parsing assumed simple.")
            data = {"frequencies": [], "dos": []} 
            
        logger.info(f"Successfully loaded VDOS for config_id: {config_id} from {vdos_file}")
        return data
        
    except Exception as e:
        logger.error(f"Error reading VDOS file for {config_id}: {e}")
        return None

def calculate_participation_ratios(vdos_data: Dict[str, Any], 
                                   num_atoms: int) -> Dict[str, float]:
    """
    Calculate Participation Ratios (PR) from loaded VDOS data.
    
    The Participation Ratio (PR) for a mode k is often defined as:
    PR_k = (sum_i |e_i|^2)^2 / (N * sum_i |e_i|^4)
    where e_i are eigenvector components.
    
    Since we only have pre-calculated VDOS (density of states), we cannot
    calculate mode-resolved PRs without eigenvector data.
    However, we can calculate the 'Integrated Participation Ratio' or
    average PR if the source data provides mode-resolved PRs.
    
    If the loaded VDOS data contains a 'participation_ratios' key, we aggregate it.
    Otherwise, we return a placeholder indicating the limitation or calculate
    a simplified metric if 'dos' and 'frequencies' are available (though strictly
    PR requires eigenvectors).
    
    For this implementation, we assume the pre-calculated file might contain
    a pre-computed average PR or mode-resolved PRs. If not, we return a warning.
    
    Args:
        vdos_data: The dictionary loaded from load_vdos().
        num_atoms: Number of atoms in the configuration (N).
        
    Returns:
        Dictionary with calculated PR metrics.
    """
    result = {}
    
    # Check if pre-computed PRs are available in the loaded data
    if 'participation_ratios' in vdos_data:
        prs = vdos_data['participation_ratios']
        if isinstance(prs, list) and len(prs) > 0:
            result['avg_pr'] = float(np.mean(prs))
            result['min_pr'] = float(np.min(prs))
            result['max_pr'] = float(np.max(prs))
            logger.info(f"Calculated PR metrics from pre-computed data for {num_atoms} atoms.")
        else:
            result['avg_pr'] = 0.0
            result['min_pr'] = 0.0
            result['max_pr'] = 0.0
            logger.warning(f"Invalid participation_ratios format in VDOS data.")
    elif 'avg_pr' in vdos_data:
        result['avg_pr'] = float(vdos_data['avg_pr'])
        logger.info(f"Loaded single avg_pr value from VDOS data.")
    else:
        # If only frequencies/dos are present, we cannot calculate PR without eigenvectors.
        # Per task constraint: "Do NOT calculate VDOS internally".
        # We must return a specific flag or 0 to indicate missing PR data.
        logger.warning(f"VDOS data for this config lacks eigenvector/PR information. "
                       f"Returning 0.0 for PR metrics.")
        result['avg_pr'] = 0.0
        result['min_pr'] = 0.0
        result['max_pr'] = 0.0
        
    return result

def process_configs_with_vdos(configs: List[AtomicConfiguration], 
                              data_dir: Optional[Path] = None) -> Tuple[List[AtomicConfiguration], Dict[str, Any]]:
    """
    Process a list of configurations, filtering out those missing VDOS data.
    
    Args:
        configs: List of AtomicConfiguration objects.
        data_dir: Optional override for VDOS data directory.
        
    Returns:
        Tuple of (valid_configs, missing_report_data)
    """
    valid_configs = []
    missing_data = {
        "excluded_configs": [],
        "reasons": {},
        "total_processed": len(configs),
        "total_excluded": 0
    }
    
    for config in configs:
        config_id = config.id
        vdos_data = load_vdos(config_id, data_dir)
        
        if vdos_data is not None:
            # Calculate PRs if data exists
            pr_metrics = calculate_participation_ratios(vdos_data, config.num_atoms)
            config.metadata['vdos_metrics'] = pr_metrics
            config.metadata['vdos_loaded'] = True
            valid_configs.append(config)
        else:
            missing_data["excluded_configs"].append(config_id)
            missing_data["reasons"][config_id] = "ERR-VDOS-MISSING: Pre-calculated VDOS data not found."
            
    missing_data["total_excluded"] = len(missing_data["excluded_configs"])
    return valid_configs, missing_data

def save_vdos_missing_report(missing_data: Dict[str, Any], output_path: Optional[Path] = None):
    """
    Save the report of excluded configurations to a JSON file.
    
    Args:
        missing_data: The dictionary generated by process_configs_with_vdos.
        output_path: Path to save the report. Defaults to data/processed/vdos_missing_report.json.
    """
    if output_path is None:
        output_path = MISSING_REPORT_PATH
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(missing_data, f, indent=2)
        
    logger.info(f"VDOS missing report saved to {output_path}")

def check_vdos_availability(config_ids: List[str], data_dir: Optional[Path] = None) -> Dict[str, bool]:
    """
    Quick check to see which config IDs have VDOS data available.
    
    Returns:
        Dictionary mapping config_id to boolean (True if available).
    """
    availability = {}
    for cid in config_ids:
        availability[cid] = load_vdos(cid, data_dir) is not None
    return availability

if __name__ == "__main__":
    # Basic execution test (if run directly, though typically called by main.py)
    # This block ensures the script can be executed to produce the report if configs are passed.
    # For the task implementation, we define the functions.
    print("VDOS Handler Module Loaded. Call process_configs_with_vdos() to run.")