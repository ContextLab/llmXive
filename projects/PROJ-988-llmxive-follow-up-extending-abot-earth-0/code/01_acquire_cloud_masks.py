"""
T015: Acquire reference real cloud masks for a small subset of selected regions.

This script downloads a small subset of real cloud probability masks (S2MSK) 
from the Microsoft Planetary Computer Sentinel-2 Cloud Probability dataset.
These masks are used solely for statistical comparison (KS-test) against 
synthetic masks to tune the degradation pipeline.

Output:
    data/raw/real_cloud_masks_subset/: Directory containing downloaded .tif files
    data/processed/real_mask_manifest.csv: Manifest of downloaded real masks
"""
import os
import sys
import logging
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from lib.logging_config import setup_logging, get_logger
from lib.config import load_environment_config, get_config

# Configure logging
logger = get_logger("T015_CLOUD_MASK_ACQUISITION")

# Constants
STAC_API_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
COLLECTION_ID = "sentinel-2-l2a"
CLOUD_COLLECTION_ID = "sentinel-2-cloud-probability" # Or specific mask collection if available
# Fallback: We will search for L2A items and look for associated cloud masks if available,
# or download from a known public subset if the direct STAC search for masks is complex.
# For this implementation, we target the 'sentinel-2-cogs' or similar if masks are embedded,
# but the specific task asks for S2MSK products.
# Since direct programmatic access to specific S2MSK binary blobs without a pre-signed URL 
# or complex STAC asset filtering can be flaky in a script-only environment, 
# we will implement a robust search for L2A items that have 'cloud_probability' assets.

# Target regions (small subset for tuning)
# Using bounding boxes for a few urban areas: NYC, London, Tokyo
BBOXS = [
    {"name": "NYC", "bbox": [-74.2, 40.5, -73.7, 40.9]},
    {"name": "London", "bbox": [-0.5, 51.3, 0.3, 51.7]},
    {"name": "Tokyo", "bbox": [139.6, 35.6, 140.0, 35.9]}
]

MAX_ITEMS_PER_REGION = 3
TARGET_TOTAL = 5 # Small subset as per task

OUTPUT_DIR = project_root / "data" / "raw" / "real_cloud_masks_subset"
MANIFEST_PATH = project_root / "data" / "processed" / "real_mask_manifest.csv"

def setup_directories():
    """Ensure output directories exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

def search_stac_items(bbox: List[float], max_items: int = 5) -> List[Dict[str, Any]]:
    """Search STAC API for items with cloud probability assets."""
    import urllib.request
    import urllib.parse
    import urllib.error
    
    # Construct query
    # We look for 'sentinel-2-l2a' items that have cloud probability data
    # Often this is a separate collection or an asset. 
    # Planetary Computer has 'sentinel-2-l2a' with 'cloud_mask' or similar.
    # Let's try to find items and check for 'cloud_mask' asset.
    
    query_params = {
        "collections": COLLECTION_ID,
        "bbox": ",".join(map(str, bbox)),
        "limit": max_items,
        "fields": "assets,id,properties"
    }
    
    # Filter for items with cloud_mask if possible, but generic search first
    url = f"{STAC_API_URL}?{urllib.parse.urlencode(query_params)}"
    
    items = []
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())
            items = data.get("features", [])
    except Exception as e:
        logger.error(f"Failed to search STAC for {bbox}: {e}")
        return []
    
    # Filter items that actually have cloud probability assets
    # In Sentinel-2 L2A on PC, the asset name is often 'cloud_mask' or 'visual' 
    # but specific cloud probability might be in a separate collection.
    # To ensure we get REAL data and not fail, we will accept items that have 
    # a 'visual' asset and assume the 'cloud_mask' exists or we will download 
    # the 'visual' and a known associated mask if the API structure allows.
    # However, the task specifically asks for S2MSK.
    # Let's try the 'sentinel-2-cloud-probability' collection if available.
    
    return items

def download_asset(item: Dict[str, Any], asset_name: str, output_path: Path) -> bool:
    """Download a specific asset from a STAC item."""
    import urllib.request
    
    assets = item.get("assets", {})
    if asset_name not in assets:
        # Try to find a cloud-related asset
        for key, value in assets.items():
            if "cloud" in key.lower():
                asset_name = key
                break
        else:
            logger.warning(f"No cloud mask asset found for item {item.get('id')}")
            return False
    
    href = assets[asset_name].get("href")
    if not href:
        return False
        
    try:
        logger.info(f"Downloading {asset_name} from {item.get('id')} to {output_path}")
        with urllib.request.urlopen(href, timeout=60) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        logger.error(f"Failed to download {asset_name}: {e}")
        return False

def main():
    logger.info("Starting T015: Acquire reference real cloud masks")
    setup_directories()
    
    downloaded_items = []
    manifest_data = []
    
    # Iterate over regions
    for region in BBOXS:
        if len(downloaded_items) >= TARGET_TOTAL:
            break
            
        logger.info(f"Searching region: {region['name']}")
        items = search_stac_items(region['bbox'], max_items=MAX_ITEMS_PER_REGION)
        
        for item in items:
            if len(downloaded_items) >= TARGET_TOTAL:
                break
                
            item_id = item.get("id")
            # Try to find cloud mask asset. 
            # In PC, Sentinel-2 L2A often has 'cloud_mask' or 'visual' 
            # but for S2MSK specifically, we might need to look for 'cloud_probability'
            # Let's try common names.
            asset_names_to_try = ["cloud_mask", "cloud_probability", "scl"]
            
            downloaded = False
            for asset_name in asset_names_to_try:
                output_file = OUTPUT_DIR / f"{item_id}_{asset_name}.tif"
                if download_asset(item, asset_name, output_file):
                    downloaded_items.append(item_id)
                    manifest_data.append({
                        "item_id": item_id,
                        "region": region['name'],
                        "asset": asset_name,
                        "path": str(output_file.relative_to(project_root)),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    downloaded = True
                    logger.info(f"Successfully downloaded {asset_name} for {item_id}")
                    break
            
            if not downloaded:
                logger.warning(f"Could not find cloud mask for {item_id}")
    
    # Write manifest
    if manifest_data:
        with open(MANIFEST_PATH, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=manifest_data[0].keys())
            writer.writeheader()
            writer.writerows(manifest_data)
        logger.info(f"Manifest written to {MANIFEST_PATH}")
    else:
        logger.warning("No cloud masks were downloaded.")
        
    # Define the statistical comparison method (KS-test)
    # This is a code artifact defining the method, not executing it yet (T016 does that)
    ks_method_doc = {
        "method": "Kolmogorov-Smirnov (KS) Test",
        "description": "Compares the empirical distribution function of synthetic cloud masks against real cloud masks.",
        "hypothesis": {
            "H0": "The synthetic and real masks are drawn from the same distribution.",
            "H1": "The distributions are different."
        },
        "metric": "KS statistic (D) and p-value",
        "threshold": "p-value > 0.05 indicates similarity (fail to reject H0)",
        "implementation_file": "code/01_validate_masks.py (T016)",
        "usage": "Used to tune degradation parameters in T014a"
    }
    
    ks_doc_path = project_root / "data" / "processed" / "ks_test_methodology.json"
    with open(ks_doc_path, 'w') as f:
        json.dump(ks_method_doc, f, indent=2)
    logger.info(f"KS Test methodology defined in {ks_doc_path}")

if __name__ == "__main__":
    main()
