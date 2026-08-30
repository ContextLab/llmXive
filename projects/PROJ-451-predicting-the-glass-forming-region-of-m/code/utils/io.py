import csv
import json
import os
from typing import Any, Dict, List, Optional, Union
import requests
import logging
from pathlib import Path

# Import config for paths and keys
try:
    from config import get_data_path, get_raw_data_path, get_processed_data_path
except ImportError:
    # Fallback for standalone execution or different project structure
    def get_data_path():
        return Path("data")
    def get_raw_data_path():
        return get_data_path() / "raw"
    def get_processed_data_path():
        return get_data_path() / "processed"

logger = logging.getLogger(__name__)

# Constants for phase labels
VALID_PHASE_LABELS = {'amorphous', 'crystalline', 'glass', 'crystal'}
AMORPHOUS_LABELS = {'amorphous', 'glass'}
CRYSTALLINE_LABELS = {'crystalline', 'crystal'}

def load_csv(filepath: str) -> List[Dict[str, Any]]:
    """Load a CSV file into a list of dictionaries."""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def save_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """Save a list of dictionaries to a CSV file."""
    if not data:
        logger.warning(f"No data to save to {filepath}")
        return
    
    fieldnames = list(data[0].keys())
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def load_json(filepath: str) -> Any:
    """Load a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data: Any, filepath: str) -> None:
    """Save data to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def fetch_materials_project_elements(api_key: str) -> Dict[str, Dict[str, Any]]:
    """Fetch elemental properties from Materials Project API."""
    base_url = os.getenv('MP_API_BASE_URL', 'https://api.materialsproject.org')
    url = f"{base_url}/v3/elements"
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch elements from Materials Project: {e}")
        raise

def fetch_materials_project_composition(api_key: str, composition: str) -> Optional[Dict[str, Any]]:
    """Fetch composition data from Materials Project API."""
    base_url = os.getenv('MP_API_BASE_URL', 'https://api.materialsproject.org')
    url = f"{base_url}/v3/materials/{composition}"
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch composition {composition}: {e}")
        raise

def filter_by_phase_label(data: List[Dict[str, Any]], 
                          phase_column: str = 'phase', 
                          valid_labels: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Filter dataset to exclude compositions lacking definitive phase labels.
    
    Per FR-009: Exclude compositions where the phase label is missing, 
    null, or not one of the definitive categories (amorphous/glass or crystalline/crystal).
    
    Args:
        data: List of composition records.
        phase_column: Name of the column containing phase labels.
        valid_labels: Optional list of allowed labels. Defaults to VALID_PHASE_LABELS.
    
    Returns:
        Filtered list of records with valid phase labels.
    """
    if valid_labels is None:
        valid_labels = list(VALID_PHASE_LABELS)
    
    valid_set = set(label.lower().strip() for label in valid_labels if label)
    filtered = []
    excluded_count = 0
    
    for record in data:
        phase_val = record.get(phase_column)
        
        if phase_val is None or phase_val == '':
            excluded_count += 1
            continue
        
        normalized_phase = str(phase_val).lower().strip()
        
        if normalized_phase in valid_set:
            filtered.append(record)
        else:
            excluded_count += 1
    
    logger.info(f"Phase label filtering: {len(data)} -> {len(filtered)} records. "
                f"Excluded {excluded_count} records with undefined phase labels.")
    
    return filtered

def load_and_filter_dataset(filepath: str, 
                            phase_column: str = 'phase',
                            valid_labels: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Load a dataset from CSV and filter by phase labels.
    
    Combines load_csv and filter_by_phase_label for convenience.
    
    Args:
        filepath: Path to the input CSV file.
        phase_column: Column name containing phase labels.
        valid_labels: List of acceptable phase labels.
    
    Returns:
        Filtered list of records.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found: {filepath}")
    
    data = load_csv(filepath)
    return filter_by_phase_label(data, phase_column, valid_labels)

def ensure_data_directories() -> None:
    """Ensure required data directories exist."""
    get_data_path().mkdir(parents=True, exist_ok=True)
    get_raw_data_path().mkdir(parents=True, exist_ok=True)
    get_processed_data_path().mkdir(parents=True, exist_ok=True)
    (get_data_path() / "results").mkdir(parents=True, exist_ok=True)

def cap_dataset_stratified(data: List[Dict[str, Any]], 
                           max_size: int = 10000,
                           stratify_column: str = 'alloy_system',
                           seed: int = 42) -> List[Dict[str, Any]]:
    """
    Cap dataset size using stratified random sampling by alloy system.
    
    Ensures the dataset does not exceed max_size while preserving
    the distribution of alloy systems.
    
    Args:
        data: Input dataset.
        max_size: Maximum number of records to return.
        stratify_column: Column name to use for stratification.
        seed: Random seed for reproducibility.
    
    Returns:
        Capped dataset.
    """
    import random
    random.seed(seed)
    
    if len(data) <= max_size:
        return data
    
    # Group by alloy system
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for record in data:
        key = record.get(stratify_column, 'unknown')
        if key not in groups:
            groups[key] = []
        groups[key].append(record)
    
    # Calculate proportional sampling
    total_count = len(data)
    sampled_data = []
    
    for key, group in groups.items():
        group_size = len(group)
        # Calculate proportional share
        proportion = group_size / total_count
        sample_size = int(round(proportion * max_size))
        
        # Ensure at least 1 if group is represented, but don't exceed group size
        sample_size = max(1, sample_size) if group_size > 0 else 0
        sample_size = min(sample_size, group_size)
        
        sampled_data.extend(random.sample(group, sample_size))
    
    # If we still have more than max_size due to rounding, truncate
    if len(sampled_data) > max_size:
        sampled_data = random.sample(sampled_data, max_size)
    
    logger.info(f"Stratified cap: {len(data)} -> {len(sampled_data)} records "
                f"(max: {max_size})")
    
    return sampled_data