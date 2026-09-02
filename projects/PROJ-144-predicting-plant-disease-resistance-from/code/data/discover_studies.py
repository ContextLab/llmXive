import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Any

# Constants for API configuration
METABOLOMICS_WORKBENCH_API_BASE = "https://www.metabolomicsworkbench.org/data/studies"
SEARCH_ENDPOINT = f"{METABOLOMICS_WORKBENCH_API_BASE}/REST/StudySearch.php"

def search_plant_metabolomics_studies() -> List[Dict[str, Any]]:
    """
    Query the Metabolomics Workbench API for plant metabolomics studies.
    
    Returns:
        List of dictionaries containing study_id, title, and download_url.
        
    Raises:
        requests.RequestException: If the API call fails.
        ValueError: If the response does not contain expected data.
    """
    params = {
        "subject_type": "plant",
        "data_type": "metabolomics",
        "format": "json"
    }
    
    try:
        response = requests.get(SEARCH_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch plant metabolomics studies: {e}")
    
    data = response.json()
    
    # The API typically returns a structure like {'STUDIES': [...]} or similar.
    # We need to handle the specific response format of MW.
    studies = []
    
    # Handle potential variations in response structure
    if isinstance(data, list):
        raw_studies = data
    elif isinstance(data, dict) and 'STUDIES' in data:
        raw_studies = data['STUDIES']
    elif isinstance(data, dict) and 'studies' in data:
        raw_studies = data['studies']
    else:
        # If it's a dict but not in expected format, try to iterate keys or treat as single study
        raw_studies = [data] if isinstance(data, dict) else []

    for study in raw_studies:
        if not isinstance(study, dict):
            continue
            
        study_id = study.get('STUDY_ID') or study.get('study_id')
        title = study.get('TITLE') or study.get('title') or study.get('study_title')
        download_url = study.get('DOWNLOAD_URL') or study.get('download_url') or study.get('url')
        
        if study_id:
            studies.append({
                "study_id": str(study_id),
                "title": str(title) if title else f"Study {study_id}",
                "download_url": str(download_url) if download_url else None
            })
    
    return studies

def save_study_manifest(studies: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save the list of studies to a JSON manifest file.
    
    Args:
        studies: List of study dictionaries.
        output_path: Path to the output JSON file.
        
    Raises:
        IOError: If the file cannot be written.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(studies, f, indent=2)

def main() -> None:
    """
    Main entry point for discovering plant metabolomics studies.
    """
    output_path = "data/raw/study_manifest.json"
    
    print(f"Searching Metabolomics Workbench for plant metabolomics studies...")
    try:
        studies = search_plant_metabolomics_studies()
        
        if not studies:
            print("Warning: No plant metabolomics studies found in the API response.")
            # Still save an empty list to satisfy the output requirement, 
            # but subsequent tasks will likely fail or handle this gracefully.
        else:
            print(f"Found {len(studies)} studies.")
            # Log first few for verification
            for s in studies[:3]:
                print(f"  - {s['study_id']}: {s['title']}")
        
        save_study_manifest(studies, output_path)
        print(f"Manifest saved to {output_path}")
        
    except Exception as e:
        print(f"Error during study discovery: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
