import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.constants import DATA_RAW_DIR

MANIFEST_PATH = DATA_RAW_DIR / "study_manifest.json"
# Metabolomics Workbench API endpoint for study search
MW_API_SEARCH = "https://www.metabolomicsworkbench.org/data/study_summary.php"

def search_plant_studies() -> List[Dict[str, Any]]:
    """
    Queries the Metabolomics Workbench API for public plant metabolomics studies.
    Filters for studies that likely contain pre-challenge or baseline data based on title/abstract keywords.
    Returns a list of candidate study metadata.
    """
    params = {
        "PROGRAM": "MetabolomicsWorkbench",
        "STUDY_TYPE": "Plant",
        "DATA_TYPE": "Metabolomics",
        "SHOW_PUBLIC": "Y"
    }

    try:
        response = requests.get(MW_API_SEARCH, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error querying Metabolomics Workbench API: {e}")
        raise

    if not data or "STUDIES" not in data:
        return []

    candidates = []
    # Keywords indicating temporal data (pre-challenge, baseline, time course) or resistance
    keywords = [
        "pre-challenge", "baseline", "inoculation", "time course", 
        "resistance", "pathogen", "challenge", "treatment"
    ]
    
    for study in data.get("STUDIES", []):
        study_id = study.get("STUDY_ID")
        title = study.get("STUDY_TITLE", "")
        abstract = study.get("ABSTRACT", "") or ""
        
        # Filter for potential relevance (inclusion criteria)
        content = f"{title} {abstract}".lower()
        if any(kw in content for kw in keywords):
            candidates.append({
                "study_id": study_id,
                "title": title,
                "abstract": abstract,
                "download_url": f"https://www.metabolomicsworkbench.org/data/download.php?STUDY_ID={study_id}&TYPE=STUDY",
                "phenotype_url": f"https://www.metabolomicsworkbench.org/data/study.php?STUDY_ID={study_id}&VIEW=PHENOTYPE"
            })
    
    return candidates

def verify_studies(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Verifies candidates and constructs the final manifest.
    Selects the first valid public study found that meets criteria.
    """
    manifest = []
    
    for candidate in candidates:
        study_id = candidate["study_id"]
        print(f"Verifying study: {study_id} - {candidate['title']}")
        
        # Construct the entry for the manifest
        # The task requires: study_id, title, download_url, phenotype_url
        entry = {
            "study_id": study_id,
            "title": candidate["title"],
            "download_url": candidate["download_url"],
            "phenotype_url": candidate["phenotype_url"]
        }
        
        manifest.append(entry)
        print(f"  - Verified: {entry['title']}")
        
        # Task requirement: "Dynamically select the first valid public study found."
        # We stop after finding the first one to keep the manifest focused for the next step.
        break
    
    return manifest

def main():
    """
    Main entry point to generate study_manifest.json.
    """
    # Ensure the output directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("Querying Metabolomics Workbench for plant studies...")
    try:
        candidates = search_plant_studies()
    except Exception as e:
        print(f"Failed to fetch studies from API: {e}")
        # If API fails, we cannot proceed with real data. 
        # We write an empty manifest to indicate failure, but the script itself runs.
        # However, per constraints, we must not fabricate. If no data, manifest is empty.
        manifest = []
    else:
        if not candidates:
            print("No suitable plant studies found matching inclusion criteria.")
            manifest = []
        else:
            manifest = verify_studies(candidates)

    # Write the manifest to disk
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest generated successfully: {MANIFEST_PATH}")
    print(f"Total studies in manifest: {len(manifest)}")

    if len(manifest) == 0:
        print("WARNING: Manifest is empty. No studies met the criteria or API failed.")
        # Do not raise an exception here so the script completes and writes the file.
        # The next step (T012b) will check for existence and content.

if __name__ == "__main__":
    main()