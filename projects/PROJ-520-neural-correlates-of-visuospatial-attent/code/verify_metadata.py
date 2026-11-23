"""
Verification script for T051: Verify metadata.json contains required fields and no synthetic data.

This script validates that data/processed/metadata.json:
1. Contains 'data_source_url' field
2. Contains 'fetch_method' field
3. Does NOT contain indicators of synthetic/fallback data
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_metadata(metadata_path: Path) -> Optional[Dict[str, Any]]:
    """Load metadata.json file."""
    if not metadata_path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        return None
    
    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in metadata file: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading metadata file: {e}")
        return None

def verify_required_fields(metadata: Dict[str, Any]) -> bool:
    """Verify that required fields exist in metadata."""
    required_fields = ['data_source_url', 'fetch_method']
    missing_fields = []
    
    for field in required_fields:
        if field not in metadata:
            missing_fields.append(field)
        elif not metadata[field]:
            missing_fields.append(f"{field} (empty)")
    
    if missing_fields:
        logger.error(f"Missing or empty required fields: {missing_fields}")
        return False
    
    logger.info("All required fields present and non-empty")
    return True

def check_for_synthetic_indicators(metadata: Dict[str, Any]) -> bool:
    """Check for indicators of synthetic or fallback data."""
    synthetic_indicators = [
        'synthetic', 'mock', 'fake', 'placeholder', 'sample_data',
        'generated', 'simulated', 'landmark_fallback', 'fallback_data'
    ]
    
    found_indicators = []
    
    # Check top-level keys and values
    for key, value in metadata.items():
        key_str = str(key).lower()
        val_str = str(value).lower() if isinstance(value, str) else ''
        
        for indicator in synthetic_indicators:
            if indicator in key_str or indicator in val_str:
                found_indicators.append(f"{key}: {value}")
    
    # Check nested structures
    def check_nested(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                check_nested(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_nested(item, f"{path}[{i}]")
        elif isinstance(obj, str):
            for indicator in synthetic_indicators:
                if indicator in obj.lower():
                    found_indicators.append(f"{path}: {obj}")
    
    check_nested(metadata)
    
    if found_indicators:
        logger.error(f"Found potential synthetic data indicators: {found_indicators}")
        return False
    
    logger.info("No synthetic data indicators found")
    return True

def validate_metadata(metadata_path: Path) -> bool:
    """Main validation function."""
    logger.info(f"Validating metadata file: {metadata_path}")
    
    # Load metadata
    metadata = load_metadata(metadata_path)
    if metadata is None:
        return False
    
    # Verify required fields
    if not verify_required_fields(metadata):
        return False
    
    # Check for synthetic indicators
    if not check_for_synthetic_indicators(metadata):
        return False
    
    # Display metadata summary
    logger.info("Metadata validation successful!")
    logger.info(f"  - data_source_url: {metadata.get('data_source_url', 'N/A')}")
    logger.info(f"  - fetch_method: {metadata.get('fetch_method', 'N/A')}")
    
    return True

def main():
    """Entry point for the verification script."""
    # Determine paths
    project_root = Path(__file__).parent.parent
    metadata_path = project_root / "data" / "processed" / "metadata.json"
    
    success = validate_metadata(metadata_path)
    
    if not success:
        logger.error("Metadata verification FAILED")
        sys.exit(1)
    else:
        logger.info("Metadata verification PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
