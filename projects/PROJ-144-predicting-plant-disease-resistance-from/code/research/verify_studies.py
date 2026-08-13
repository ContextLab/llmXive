import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import constants
from utils.constants import DATA_RAW_DIR, STATE_DIR

MANIFEST_PATH = DATA_RAW_DIR / "study_manifest.json"

def get_study_metadata(study_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches metadata for a study from Metabolomics Workbench API.
    API Endpoint: https://www.metabolomicsworkbench.org/data/study_summary.php?STUDY_ID={study_id}
    """
    url = f"https://www.metabolomicsworkbench.org/data/study_summary.php?STUDY_ID={study_id}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Warning: Could not fetch metadata for {study_id}: {e}")
        return None

def verify_studies(study_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Verifies a list of study IDs and constructs the manifest.
    """
    manifest = []
    for study_id in study_ids:
        print(f"Verifying study: {study_id}")
        
        # Try to get metadata
        metadata = get_study_metadata(study_id)
        
        # Construct download URL
        download_url = f"https://www.metabolomicsworkbench.org/data/download.php?STUDY_ID={study_id}&TYPE=STUDY"
        
        entry = {
            "study_id": study_id,
            "title": metadata.get("STUDY_TITLE", "Unknown Title") if metadata else "Unknown Title",
            "download_url": download_url
        }
        manifest.append(entry)
        print(f"  - Verified: {entry['title']}")

    return manifest

def main():
    """
    Main entry point to generate study_manifest.json.
    """
    # Import study IDs from config
    try:
        from config import STUDY_IDS
    except ImportError:
        print("Error: STUDY_IDS not found in config.py. Please define them.")
        sys.exit(1)

    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    manifest = verify_studies(STUDY_IDS)

    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest generated successfully: {MANIFEST_PATH}")
    print(f"Total studies: {len(manifest)}")

if __name__ == "__main__":
    main()
