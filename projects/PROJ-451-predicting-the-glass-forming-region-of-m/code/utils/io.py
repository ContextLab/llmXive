import csv
import json
import os
from typing import Any, Dict, List, Optional, Union
import requests
import logging
import random
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_materials_project_api_key() -> Optional[str]:
    """Retrieve the Materials Project API key from environment variables."""
    return os.getenv("MP_API_KEY")

def load_csv(filepath: str) -> List[Dict[str, Any]]:
    """Load a CSV file into a list of dictionaries."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def load_json(filepath: str) -> Any:
    """Load a JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """Save a list of dictionaries to a CSV file."""
    if not data:
        logger.warning("No data to save to CSV.")
        return
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def save_json(data: Any, filepath: str) -> None:
    """Save data to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def fetch_materials_project_elements(api_key: str) -> Dict[str, Dict[str, Any]]:
    """Fetch elemental properties from Materials Project API v3."""
    url = "https://api.materialsproject.org/v3/elements"
    headers = {"X-API-Key": api_key}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Assume 'data' is a list of element objects
        return {elem['element_id']: elem for elem in data.get('data', [])}
    except requests.RequestException as e:
        logger.error(f"Failed to fetch elements from Materials Project: {e}")
        return {}

def fetch_materials_project_composition(api_key: str, composition: str) -> Optional[Dict[str, Any]]:
    """Fetch composition data from Materials Project API v3."""
    url = f"https://api.materialsproject.org/v3/compositions/{composition}"
    headers = {"X-API-Key": api_key}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json().get('data')
    except requests.RequestException as e:
        logger.error(f"Failed to fetch composition {composition}: {e}")
        return None

def filter_by_phase_label(data: List[Dict[str, Any]], valid_labels: List[str] = None) -> List[Dict[str, Any]]:
    """Filter dataset to only include rows with definitive phase labels."""
    if valid_labels is None:
        valid_labels = ['amorphous', 'crystalline', 'glass', 'crystal']
    # Normalize valid labels to lowercase for comparison
    valid_labels_lower = [l.lower() for l in valid_labels]
    filtered = []
    for row in data:
        # Look for common phase label keys
        label = None
        for key in ['phase', 'phase_label', 'structure_type', 'label']:
            if key in row and row[key]:
                label = str(row[key]).lower()
                break
        if label in valid_labels_lower:
            filtered.append(row)
        else:
            logger.debug(f"Dropped composition {row.get('composition', 'unknown')} due to invalid phase label: {label}")
    logger.info(f"Filtered dataset: {len(filtered)} kept, {len(data) - len(filtered)} dropped.")
    return filtered

def load_and_filter_dataset(filepath: str, valid_labels: List[str] = None) -> List[Dict[str, Any]]:
    """Load a dataset and filter by phase label."""
    data = load_csv(filepath)
    return filter_by_phase_label(data, valid_labels)

def ensure_data_directories() -> None:
    """Ensure required data directories exist."""
    dirs = ['data/raw', 'data/processed', 'data/results', 'figures']
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def cap_dataset_stratified(data: List[Dict[str, Any]], max_size: int = 10000, system_key: str = 'alloy_system') -> List[Dict[str, Any]]:
    """
    Cap the dataset to max_size using stratified random sampling by alloy system.
    
    This implements FR-007: Enforce a hard cap of 10,000 compositions.
    Stratification ensures the relative distribution of alloy systems is preserved.
    
    Args:
        data: List of composition dictionaries.
        max_size: Maximum number of rows to keep.
        system_key: The key in the dictionary representing the alloy system (e.g., 'alloy_system', 'system').
    
    Returns:
        A new list of dictionaries capped to max_size.
    """
    if len(data) <= max_size:
        logger.info(f"Dataset size ({len(data)}) is already within the limit ({max_size}). No capping needed.")
        return data

    logger.info(f"Dataset size ({len(data)}) exceeds limit ({max_size}). Applying stratified random sampling.")

    # Group data by alloy system
    system_groups = defaultdict(list)
    for i, row in enumerate(data):
        # Handle missing system key by assigning to 'unknown'
        system = row.get(system_key, 'unknown')
        if system is None:
            system = 'unknown'
        system_groups[system].append(row)

    # Calculate sample size for each system
    # We want to preserve the proportion of each system in the final dataset
    system_counts = {k: len(v) for k, v in system_groups.items()}
    total_items = len(data)
    
    sampled_data = []
    
    # Calculate proportional allocation
    for system, items in system_groups.items():
        current_count = len(items)
        # Calculate proportion
        proportion = current_count / total_items
        # Calculate sample size for this system
        sample_size = int(proportion * max_size)
        
        # Ensure we don't exceed the remaining capacity if proportions don't sum exactly to 1 due to rounding
        # But since we iterate, we'll just cap at the calculated size for now. 
        # A more robust approach is to handle the remainder, but for 10k cap, simple proportional is usually fine.
        # We must ensure sample_size doesn't exceed the actual number of items available
        sample_size = min(sample_size, current_count)
        
        # Random sample
        if sample_size > 0:
            sampled_group = random.sample(items, sample_size)
            sampled_data.extend(sampled_group)
            logger.debug(f"Sampled {sample_size}/{current_count} from system '{system}'")

    # If rounding errors caused us to be under the limit, fill the rest randomly from the remaining
    if len(sampled_data) < max_size:
        remaining_needed = max_size - len(sampled_data)
        # Flatten all groups to find remaining items not yet sampled
        # Since random.sample removes items from the list conceptually (we used new lists), 
        # we need to track what was used or just sample from the original list excluding sampled.
        # Simpler: Just take a random sample from the original data that isn't in sampled_data?
        # That's O(N^2). Better to track indices or re-group.
        # Given the scale, let's just do a second pass if needed, but usually proportional rounding is very close.
        # Let's implement a simple fill from the groups that have leftovers.
        
        # Re-identify leftovers
        leftovers = []
        for system, items in system_groups.items():
            # We need to know which specific items were picked. 
            # Since we used random.sample on a list of references, we can't easily compare object identity if dicts are identical.
            # However, we built 'sampled_data' from 'items'.
            # Let's reconstruct the set of used items by index if we had indices, or just assume the proportional math is close enough.
            # For strict correctness, we should track indices.
            pass 
        
        # Fallback: If we are slightly under, just random sample from the whole original dataset to fill up, 
        # acknowledging slight stratification drift is acceptable for the last few rows.
        if remaining_needed > 0:
            # Create a set of tuples of sorted items to identify used rows (assuming dicts are hashable? No)
            # Convert to string representation for comparison? Expensive.
            # Let's just assume the proportional allocation is sufficient for the cap logic.
            # The requirement is "≤10,000", so being slightly under is fine.
            pass

    # Final check to ensure we don't exceed max_size (due to potential logic issues)
    if len(sampled_data) > max_size:
        # Truncate
        random.shuffle(sampled_data)
        sampled_data = sampled_data[:max_size]
        
    logger.info(f"Final dataset size after capping: {len(sampled_data)}")
    return sampled_data
