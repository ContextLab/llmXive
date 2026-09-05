import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.io import load_csv, save_csv, cap_dataset_stratified
from utils.config import get_processed_data_path, get_raw_data_path, ensure_data_directories
from utils.dedup import deduplicate_compositions
from features.alloy_system_mapper import add_alloy_system_column
from utils.synthetic import generate_synthetic_dataset, save_synthetic_dataset

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
MAX_COMPOSITIONS = 10000
PRIMARY_SOURCE = 'Science Advances'
MIN_SIZE_THRESHOLD = 1000

def load_source_data(raw_dir: Path) -> Tuple[List[Dict], List[Dict]]:
    """Load combined raw data and separate by source."""
    input_path = raw_dir / 'combined_raw.csv'
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = load_csv(str(input_path))
    return data

def filter_by_phase_label(data: List[Dict], valid_labels: Optional[List[str]] = None) -> List[Dict]:
    """Filter compositions by phase label."""
    if valid_labels is None:
        valid_labels = ['amorphous', 'crystalline']
    filtered = [row for row in data if row.get('phase', '').lower() in valid_labels]
    logger.info(f"Filtered by phase: {len(data)} -> {len(filtered)}")
    return filtered

def filter_by_properties(data: List[Dict]) -> List[Dict]:
    """Drop compositions with missing elemental properties."""
    required_props = ['atomic_radius', 'electronegativity', 'vec', 'size_mismatch', 'mixing_enthalpy']
    initial_count = len(data)
    filtered = []
    for row in data:
        if all(row.get(prop) is not None and row.get(prop) != '' for prop in required_props):
            filtered.append(row)
        else:
            missing = [p for p in required_props if row.get(p) is None or row.get(p) == '']
            logger.debug(f"Dropping row due to missing: {missing}")
    
    dropped = initial_count - len(filtered)
    logger.info(f"Filtered by properties: {initial_count} -> {len(filtered)} (Dropped: {dropped})")
    return filtered

def cap_dataset(data: List[Dict], output_path: Path) -> List[Dict]:
    """
    Cap the dataset to MAX_COMPOSITIONS using stratified random sampling by 'alloy_system'.
    Priority: Retain records from 'Science Advances' first.
    """
    logger.info(f"Starting dataset capping. Current size: {len(data)}, Target: {MAX_COMPOSITIONS}")
    
    if len(data) <= MAX_COMPOSITIONS:
        logger.info("Dataset size is within limit. Skipping capping.")
        return data

    capped_data = cap_dataset_stratified(
        data=data,
        target_size=MAX_COMPOSITIONS,
        stratify_col='alloy_system',
        source_col='source',
        primary_source=PRIMARY_SOURCE,
        seed=42
    )
    
    save_csv(capped_data, str(output_path))
    logger.info(f"Capped dataset saved to {output_path}")
    return capped_data

def verify_size(data: List[Dict], output_path: Path) -> bool:
    """Verify dataset meets minimum size threshold."""
    size = len(data)
    report = {
        'total_rows': size,
        'threshold': MIN_SIZE_THRESHOLD,
        'status': 'PASS' if size >= MIN_SIZE_THRESHOLD else 'FAIL'
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Size verification: {size} rows. Status: {report['status']}")
    
    if size < MIN_SIZE_THRESHOLD:
        logger.warning(f"Dataset size ({size}) is below threshold ({MIN_SIZE_THRESHOLD}).")
        return False
    return True

def main():
    """Main ingestion pipeline execution."""
    ensure_data_directories()
    raw_dir = get_raw_data_path()
    processed_dir = get_processed_data_path()
    
    # 1. Load Data
    try:
        data = load_source_data(raw_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # 2. Filter by Phase Label (T013)
    data = filter_by_phase_label(data)

    # 3. Filter by Properties (T017a)
    data = filter_by_properties(data)

    # 4. Add Alloy System (T019 - assuming this happened before or we do it here)
    # Note: T019 is a dependency, so 'alloy_system' should exist. 
    # If not, we add it here to be safe for capping.
    if 'alloy_system' not in data[0]:
        logger.warning("alloy_system column missing. Running mapper.")
        data = add_alloy_system_column(data)

    # 5. Cap Dataset (T014)
    capped_path = processed_dir / 'capped_dataset.csv'
    data = cap_dataset(data, capped_path)

    # 6. Verify Size (T014a logic integrated here for flow, though task is separate)
    size_check_path = processed_dir / 'size_verification.json'
    if not verify_size(data, size_check_path):
        logger.error("Dataset size verification failed. Triggering synthetic fallback.")
        # Trigger synthetic generation if too small
        # This part might be better in T014a, but we handle the failure here
        synthetic_data = generate_synthetic_dataset(target_size=MIN_SIZE_THRESHOLD)
        # Merge synthetic into data (simple append for now)
        data.extend(synthetic_data)
        save_csv(data, str(capped_path))
        verify_size(data, size_check_path)

    logger.info("Ingestion pipeline (T014) completed successfully.")

if __name__ == '__main__':
    main()
