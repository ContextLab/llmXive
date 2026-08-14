"""
Script to explicitly record NLCD 2019 provenance in metadata.yaml.

This satisfies Constitution Principle VI (Habitat Data Provenance) by
ensuring the exact version, date, and source URL of the downloaded
NLCD 2019 raster are recorded in the project metadata.

Usage:
    python data/record_nlcd_provenance.py
"""
import os
import sys
import logging
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from utils.config import get_data_dir, get_raw_data_dir
from utils.provenance import compute_file_hash

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NLCD 2019 Specific Constants
NLCD_2019_VERSION = "NLCD_2019_Land_Cover_Land_Use"
NLCD_2019_RELEASE_DATE = "2020-12"  # Official release date
NLCD_2019_SOURCE_URL = (
    "https://www.mrlc.gov/data/legislation/nlcd-2019-land-cover-land-use"
)
NLCD_2019_CITATION = (
    "Wickham, J., Stehman, S.V., Gass, L., Dewitz, J., Fry, J., Wade, T., "
    "and Sorenson, D., 2021, Thematic accuracy assessment of the 2019 National "
    "Land Cover Database (NLCD): U.S. Geological Survey Scientific Investigations "
    "Report 2021-5028, 19 p., https://doi.org/10.3133/sir20215028."
)

def load_metadata(metadata_path: Path) -> Dict[str, Any]:
    """Load existing metadata.yaml or return empty dict if not found."""
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_metadata(metadata: Dict[str, Any], metadata_path: Path) -> None:
    """Save metadata dictionary to YAML file."""
    with open(metadata_path, 'w', encoding='utf-8') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

def record_nlcd_provenance(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Record NLCD 2019 provenance information in the metadata dictionary.
    
    Args:
        metadata: Existing metadata dictionary to update.
        
    Returns:
        Updated metadata dictionary with NLCD provenance.
    """
    # Create or update the nlcd section
    if 'nlcd' not in metadata:
        metadata['nlcd'] = {}
    
    nlcd_section = metadata['nlcd']
    
    # Record core provenance fields
    nlcd_section['version'] = NLCD_2019_VERSION
    nlcd_section['release_date'] = NLCD_2019_RELEASE_DATE
    nlcd_section['source_url'] = NLCD_2019_SOURCE_URL
    nlcd_section['citation'] = NLCD_2019_CITATION
    nlcd_section['extraction_date'] = datetime.now().isoformat()
    
    # Add data source description
    nlcd_section['description'] = (
        "National Land Cover Database (NLCD) 2019 Land Cover/ Land Use data. "
        "Provides 30-meter resolution land cover data for the conterminous United States."
    )
    
    nlcd_section['coordinate_system'] = "NAD83 / Conus Albers (EPSG:5070)"
    nlcd_section['spatial_resolution'] = "30 meters"
    nlcd_section['temporal_resolution'] = "Single year composite (2019)"
    
    logger.info(f"Recorded NLCD 2019 provenance: version={NLCD_2019_VERSION}")
    
    return metadata

def verify_nlcd_file_exists(raw_data_dir: Path) -> Optional[Path]:
    """
    Verify that the NLCD 2019 data file exists in the raw data directory.
    
    Args:
        raw_data_dir: Path to the raw data directory.
        
    Returns:
        Path to the NLCD file if found, None otherwise.
    """
    # Look for common NLCD file patterns
    possible_patterns = [
        "nlcd_2019.zip",
        "nlcd_2019_land_cover.zip",
        "NLCD_2019*.zip",
        "NLCD_2019_Land_Cover_Land_Use.zip"
    ]
    
    for pattern in possible_patterns:
        for file_path in raw_data_dir.glob(pattern):
            logger.info(f"Found NLCD file: {file_path.name}")
            return file_path
    
    # Also check subdirectories
    for file_path in raw_data_dir.rglob("*.zip"):
        if "nlcd" in file_path.name.lower() and "2019" in file_path.name:
            logger.info(f"Found NLCD file: {file_path.name}")
            return file_path
    
    logger.warning("NLCD 2019 file not found in raw data directory. "
                  "Provenance recorded without file hash.")
    return None

def compute_and_record_hash(file_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute and record the SHA-256 hash of the NLCD file.
    
    Args:
        file_path: Path to the NLCD file.
        metadata: Metadata dictionary to update.
        
    Returns:
        Updated metadata dictionary with file hash.
    """
    if file_path.exists():
        file_hash = compute_file_hash(file_path)
        metadata['nlcd']['file_hash'] = file_hash
        metadata['nlcd']['file_size_bytes'] = file_path.stat().st_size
        metadata['nlcd']['file_name'] = file_path.name
        logger.info(f"Recorded file hash: {file_hash[:16]}...")
    else:
        logger.warning(f"Cannot compute hash: file not found at {file_path}")
    
    return metadata

def main() -> int:
    """
    Main entry point for recording NLCD provenance.
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        # Determine paths
        data_dir = get_data_dir()
        metadata_path = data_dir / "metadata.yaml"
        raw_data_dir = get_raw_data_dir()
        
        logger.info(f"Project data directory: {data_dir}")
        logger.info(f"Metadata file: {metadata_path}")
        logger.info(f"Raw data directory: {raw_data_dir}")
        
        # Load existing metadata
        metadata = load_metadata(metadata_path)
        
        # Record NLCD provenance
        metadata = record_nlcd_provenance(metadata)
        
        # Verify and record file hash if file exists
        nlcd_file = verify_nlcd_file_exists(raw_data_dir)
        if nlcd_file:
            metadata = compute_and_record_hash(nlcd_file, metadata)
        
        # Save updated metadata
        save_metadata(metadata, metadata_path)
        
        logger.info(f"Successfully recorded NLCD provenance in {metadata_path}")
        logger.info(f"NLCD Version: {metadata['nlcd']['version']}")
        logger.info(f"NLCD Source: {metadata['nlcd']['source_url']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to record NLCD provenance: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
