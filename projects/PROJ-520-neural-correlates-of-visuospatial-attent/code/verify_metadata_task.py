"""
Task T051: Verify metadata integrity and absence of synthetic data.

This script verifies that `data/processed/metadata.json` exists, contains
the required `data_source_url` and `fetch_method` fields (as mandated by T044),
and explicitly checks that no synthetic fallback data indicators are present.

It exits with code 0 on success, or code 1 with a descriptive error on failure.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Define paths relative to project root
    # Assuming this script runs from the project root or code/ directory
    project_root = Path(__file__).resolve().parent.parent
    metadata_path = project_root / "data" / "processed" / "metadata.json"

    logger.info(f"Verifying metadata file: {metadata_path}")

    # 1. Check if file exists
    if not metadata_path.exists():
        logger.error(f"CRITICAL: Metadata file not found at {metadata_path}")
        logger.error("The pipeline has not produced the required metadata file.")
        sys.exit(1)

    # 2. Load and parse JSON
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"CRITICAL: Failed to parse JSON in {metadata_path}: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"CRITICAL: Failed to read {metadata_path}: {e}")
        sys.exit(1)

    # 3. Verify required fields (T044 mandate)
    required_fields = ['data_source_url', 'fetch_method']
    missing_fields = [field for field in required_fields if field not in metadata]

    if missing_fields:
        logger.error(f"CRITICAL: Missing required fields in metadata: {missing_fields}")
        logger.error(f"Fields found: {list(metadata.keys())}")
        sys.exit(1)

    logger.info(f"✓ Required fields present: {required_fields}")
    logger.info(f"  - data_source_url: {metadata['data_source_url']}")
    logger.info(f"  - fetch_method: {metadata['fetch_method']}")

    # 4. Check for synthetic fallback indicators
    # We look for keys or values that suggest synthetic data generation
    # based on the "Fail Loudly" constraints (T039, T055).
    synthetic_indicators = [
        'synthetic', 'mock', 'fake', 'generated', 'dummy', 'sample_data',
        'fallback_synthetic', 'random_seed_fallback'
    ]
    
    found_indicators = []
    
    def check_for_synthetic(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                current_path = f"{path}.{k}" if path else k
                # Check key name
                if any(ind in k.lower() for ind in synthetic_indicators):
                    found_indicators.append(current_path)
                # Check value content
                if isinstance(v, str) and any(ind in v.lower() for ind in synthetic_indicators):
                    found_indicators.append(f"{current_path} (value)")
                check_for_synthetic(v, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]"
                check_for_synthetic(item, current_path)
        elif isinstance(obj, str):
            if any(ind in obj.lower() for ind in synthetic_indicators):
                found_indicators.append(f"{path} (value)")

    check_for_synthetic(metadata)

    if found_indicators:
        logger.error("CRITICAL: Synthetic data indicators found in metadata:")
        for indicator in found_indicators:
            logger.error(f"  - {indicator}")
        logger.error("The metadata contains evidence of synthetic or fallback data.")
        sys.exit(1)

    logger.info("✓ No synthetic data indicators found.")

    # 5. Validate specific fetch method consistency
    # Ensure fetch_method is not a placeholder
    fetch_method = metadata.get('fetch_method', '')
    if fetch_method.lower() in ['none', 'null', 'undefined', 'placeholder', 'manual']:
        logger.error(f"CRITICAL: Invalid fetch_method: '{fetch_method}'")
        sys.exit(1)

    logger.info("✓ Metadata verification successful.")
    logger.info("  - File exists and is valid JSON.")
    logger.info("  - Required fields (data_source_url, fetch_method) present.")
    logger.info("  - No synthetic data indicators detected.")
    logger.info("  - Fetch method is valid.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
