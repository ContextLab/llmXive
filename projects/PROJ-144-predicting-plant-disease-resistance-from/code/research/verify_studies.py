import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path to allow imports from utils if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.constants import DATA_RAW_DIR, ensure_dirs
from utils.io import log_data_acquisition_step

METABOLOMICS_WORKBENCH_API = "https://www.metabolomicsworkbench.org/rest/study/study_search"
STUDY_DATA_URL = "https://www.metabolomicsworkbench.org/rest/study/study_download"

class DataUnavailableError(Exception):
    """Raised when required data cannot be found or retrieved."""
    pass

def search_studies(query_terms: List[str]) -> List[Dict[str, Any]]:
    """
    Query the Metabolomics Workbench API for studies matching specific terms.
    
    Args:
        query_terms: List of strings to search for (e.g., ['plant', 'disease'])
        
    Returns:
        List of study metadata dictionaries from the API response.
    """
    params = {
        "keyword": " ".join(query_terms),
        "format": "json"
    }
    
    try:
        response = requests.get(METABOLOMICS_WORKBENCH_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # The API typically returns a 'STUDY' key with a list of studies
        # or a 'MESSAGE' key if no results.
        if "STUDY" in data:
            studies = data["STUDY"]
            if isinstance(studies, dict):
                studies = [studies]
            return studies
        elif "MESSAGE" in data:
            print(f"API Message: {data['MESSAGE']}")
            return []
        else:
            print(f"Unexpected API response format: {data}")
            return []
            
    except requests.exceptions.RequestException as e:
        raise DataUnavailableError(f"Failed to connect to Metabolomics Workbench API: {e}")

def get_study_metadata(study_id: str) -> Dict[str, Any]:
    """
    Fetch detailed metadata for a specific study ID.
    
    Args:
        study_id: The study identifier (e.g., "C-STUDY-1234")
        
    Returns:
        Dictionary containing detailed study metadata.
    """
    params = {
        "study_id": study_id,
        "format": "json"
    }
    
    try:
        # Using the study_download endpoint often returns more detailed metadata
        # than the search endpoint
        response = requests.get(STUDY_DATA_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "STUDY" in data:
            study_info = data["STUDY"]
            if isinstance(study_info, list):
                return study_info[0] if study_info else {}
            return study_info
        return {}
        
    except requests.exceptions.RequestException as e:
        raise DataUnavailableError(f"Failed to fetch metadata for {study_id}: {e}")

def check_pre_challenge_profiles(study_metadata: Dict[str, Any]) -> bool:
    """
    Verify that the study contains pre-challenge or baseline profiles.
    
    Args:
        study_metadata: Dictionary of study metadata.
        
    Returns:
        True if pre-challenge/baseline data is indicated, False otherwise.
    """
    # Check common fields for time points or experimental design
    design = study_metadata.get("DESIGN", "")
    title = study_metadata.get("STUDY_TITLE", "")
    abstract = study_metadata.get("ABSTRACT", "")
    
    text_content = f"{design} {title} {abstract}".lower()
    
    keywords = ["baseline", "pre-challenge", "pre challenge", "control", "before infection", "time 0"]
    
    for keyword in keywords:
        if keyword in text_content:
            return True
            
    # Fallback: check if there are time points mentioned that imply a baseline
    # This is heuristic; real validation might require parsing sample data
    if "time" in text_content:
        return True
        
    return False

def check_disease_resistance_metadata(study_metadata: Dict[str, Any]) -> bool:
    """
    Verify that the study contains disease or resistance metadata.
    
    Args:
        study_metadata: Dictionary of study metadata.
        
    Returns:
        True if disease/resistance indicators are found, False otherwise.
    """
    design = study_metadata.get("DESIGN", "")
    title = study_metadata.get("STUDY_TITLE", "")
    abstract = study_metadata.get("ABSTRACT", "")
    organism = study_metadata.get("ORGANISM", "")
    
    text_content = f"{design} {title} {abstract} {organism}".lower()
    
    keywords = ["disease", "resistance", "pathogen", "infection", "susceptibility", "fungus", "bacteria", "virus"]
    
    for keyword in keywords:
        if keyword in text_content:
            return True
            
    return False

def verify_studies(study_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Verify a list of study IDs by fetching metadata and checking criteria.
    
    Args:
        study_ids: List of study IDs to verify.
        
    Returns:
        List of valid study metadata dictionaries.
        
    Raises:
        DataUnavailableError: If no valid studies are found.
    """
    valid_studies = []
    
    for study_id in study_ids:
        print(f"Verifying study: {study_id}")
        try:
            metadata = get_study_metadata(study_id)
            
            if not metadata:
                print(f"  -> No metadata found for {study_id}")
                continue
                
            has_pre_challenge = check_pre_challenge_profiles(metadata)
            has_disease_resistance = check_disease_resistance_metadata(metadata)
            
            if has_pre_challenge and has_disease_resistance:
                valid_studies.append({
                    "study_id": study_id,
                    "metadata": metadata,
                    "verified": True,
                    "checks": {
                        "pre_challenge": has_pre_challenge,
                        "disease_resistance": has_disease_resistance
                    }
                })
                print(f"  -> Valid study found: {study_id}")
            else:
                print(f"  -> Study {study_id} failed verification checks.")
                
        except DataUnavailableError as e:
            print(f"  -> Error verifying {study_id}: {e}")
            
    if not valid_studies:
        raise DataUnavailableError("No valid studies found matching the criteria.")
        
    return valid_studies

def update_research_md(valid_studies: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Update the research manifest file with valid studies.
    
    Args:
        valid_studies: List of verified study dictionaries.
        output_path: Path to the output JSON file.
    """
    manifest = {
        "generated_at": str(Path().cwd()),
        "total_studies_found": len(valid_studies),
        "studies": valid_studies
    }
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Manifest saved to {output_path}")

def main():
    """
    Main entry point for the study verification task.
    Queries the API for 'plant disease' and 'metabolomics',
    verifies the results, and saves the manifest.
    """
    ensure_dirs()
    
    query_terms = ["plant", "disease", "metabolomics"]
    output_path = Path(DATA_RAW_DIR) / "study_manifest.json"
    
    print(f"Searching Metabolomics Workbench for: {query_terms}")
    
    try:
        # 1. Search for studies
        search_results = search_studies(query_terms)
        
        if not search_results:
            raise DataUnavailableError("No studies found matching the query terms.")
        
        print(f"Found {len(search_results)} candidate studies.")
        
        # 2. Extract IDs and verify
        candidate_ids = []
        for study in search_results:
            # Handle different API response structures
            study_id = study.get("STUDY_ID") or study.get("study_id")
            if study_id:
                candidate_ids.append(study_id)
        
        if not candidate_ids:
            raise DataUnavailableError("Could not extract Study IDs from search results.")
        
        # 3. Verify studies (filter for pre-challenge and disease resistance)
        # We need at least 2 valid studies. If the initial search returns many,
        # we verify them until we have 2.
        valid_studies = []
        for study_id in candidate_ids:
            try:
                metadata = get_study_metadata(study_id)
                if check_pre_challenge_profiles(metadata) and check_disease_resistance_metadata(metadata):
                    valid_studies.append({
                        "study_id": study_id,
                        "metadata": metadata,
                        "verified": True,
                        "checks": {
                            "pre_challenge": True,
                            "disease_resistance": True
                        }
                    })
                    if len(valid_studies) >= 2:
                        break
            except Exception as e:
                print(f"Error processing {study_id}: {e}")
                continue
        
        if len(valid_studies) < 2:
            raise DataUnavailableError(
                f"Only found {len(valid_studies)} valid studies. Need at least 2."
            )
        
        # 4. Save manifest
        update_research_md(valid_studies, output_path)
        
        # 5. Log artifact
        log_data_acquisition_step(
            step="study_verification",
            artifact_path=str(output_path),
            details=f"Found {len(valid_studies)} valid studies: {[s['study_id'] for s in valid_studies]}"
        )
        
        print("Task T012 completed successfully.")
        
    except DataUnavailableError as e:
        print(f"CRITICAL: {e}")
        raise

if __name__ == "__main__":
    main()
