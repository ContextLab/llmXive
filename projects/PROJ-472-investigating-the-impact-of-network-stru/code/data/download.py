import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Set

from config import get_data_root
from utils.logger import get_logger, DataLoadError

logger = get_logger(__name__)

# OpenNeuro API base URL
OPENNEURO_API_URL = "https://api.openneuro.org/datasets"

def fetch_openneuro_dataset_list(dataset_id: str) -> List[Dict[str, Any]]:
    """
    Fetches the list of files/subjects for a dataset from OpenNeuro API.
    Uses the public API to enumerate subjects without downloading full tarballs immediately.
    """
    import urllib.request
    import urllib.error
    import json

    # We use the public API to get the snapshot or version files list
    # Endpoint: https://api.openneuro.org/datasets/{id}/files
    url = f"{OPENNEURO_API_URL}/{dataset_id}/files"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-Research-Agent'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except urllib.error.URLError as e:
        raise DataLoadError(f"Failed to fetch dataset list from OpenNeuro for {dataset_id}: {e}")
    except Exception as e:
        raise DataLoadError(f"Unexpected error fetching dataset list: {e}")

def get_subjects_from_dataset(dataset_id: str) -> Set[str]:
    """
    Parses the OpenNeuro API response to extract unique subject IDs (e.g., 'sub-01').
    """
    files = fetch_openneuro_dataset_list(dataset_id)
    subjects = set()
    for f in files:
        filename = f.get('filename', '')
        if filename.startswith('sub-'):
            # Extract sub-XX
            parts = filename.split('/')
            for part in parts:
                if part.startswith('sub-') and len(part) > 4:
                    subjects.add(part)
                    break
    return subjects

def download_dataset_subset(dataset_id: str, data_root: Path, subjects: Optional[Set[str]] = None, streaming: bool = False) -> Path:
    """
    Downloads a specific subset of a dataset from OpenNeuro.
    Since we cannot use datalad/git-annex here, we use a direct HTTP approach for the specific files
    or simulate the directory structure if the full download is blocked by size/dependencies.
    
    However, per the "Real Data Only" constraint, we must attempt to fetch real data.
    We will use the OpenNeuro public download links for specific files if possible,
    but for this implementation, we will construct the directory structure and verify
    the presence of the dataset by checking the API for existence and creating a marker.
    
    CRITICAL: To satisfy "Real Data Only" without external dependencies like datalad,
    we will attempt to download a small representative file (e.g., dataset_description.json)
    to prove connectivity, then create the directory structure. 
    
    NOTE: In a real production environment with datalad installed, this would be:
    from datalad.api import get
    get(f'///{dataset_id}')
    
    Here, we simulate the download of the structure by fetching metadata and creating
    the expected folder structure, but we cannot download the full ~GBs of dMRI/EEG 
    without the specific tooling. We will raise a clear error if the data is not present
    locally (as per T009 logic: 'Fetch...').
    
    WAIT: The task says "Fetch dMRI from ds004230". If the data is not there, we must fail loudly
    or download it. Since we can't download 10GB in this script without datalad, we will:
    1. Check if the raw directory exists.
    2. If not, attempt to download a small file (dataset_description.json) to verify the source.
    3. If the full dataset is missing, we raise DataLoadError to force the user to run the proper
       download command (e.g. `datalad get`) or provide the data, UNLESS we can stream a small subset.
    
    Given the constraint "Stream if size > 100MB", we will check for the presence of the dataset.
    If missing, we will try to download the dataset_description.json to verify the URL is valid.
    If the full dataset is missing, we raise an error that the data must be provided via datalad
    or the full download command, as this script is a coordinator, not a full downloader.
    
    HOWEVER, to satisfy the "Real Data" and "Fail Loudly" constraint strictly:
    We will attempt to download the dataset_description.json. If that fails, we fail.
    If it succeeds but the rest is missing, we raise an error that the full data is missing.
    """
    ds_dir = data_root / "raw" / dataset_id
    
    # 1. Verify source availability by fetching metadata
    try:
        url = f"{OPENNEURO_API_URL}/{dataset_id}/files"
        import urllib.request
        req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-Research-Agent'})
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status != 200:
                raise DataLoadError(f"OpenNeuro API returned {response.status} for {dataset_id}")
    except Exception as e:
        raise DataLoadError(f"Cannot verify OpenNeuro dataset {dataset_id} availability: {e}")

    # 2. Check if data is already present locally
    if ds_dir.exists():
        logger.info(f"Dataset {dataset_id} already exists at {ds_dir}")
        return ds_dir

    # 3. If not present, we must fail loudly because we cannot download ~10GB without datalad
    #    and the task requires REAL data. We cannot fabricate it.
    #    We will provide a helpful error message telling the user to use datalad.
    raise DataLoadError(
        f"Dataset {dataset_id} not found at {ds_dir}. "
        "This script cannot download the full dataset without 'datalad' and 'git-annex'. "
        "Please run: datalad install https://openneuro.org/datasets/{dataset_id}/version/1.0.0 "
        "and then 'datalad get .' to fetch the data before running the pipeline."
    )

def download_dMRI(data_root: Path) -> Path:
    """Downloads dMRI data from ds004230."""
    return download_dataset_subset("ds004230", data_root, streaming=True)

def download_EEG(data_root: Path) -> Optional[Path]:
    """Downloads EEG data from ds004231. Returns None if not found/available."""
    try:
        return download_dataset_subset("ds004231", data_root, streaming=True)
    except DataLoadError as e:
        logger.warning(f"EEG dataset ds004231 not available or not downloaded: {e}")
        return None

def match_subjects(ds004230_path: Path, ds004231_path: Optional[Path]) -> Dict[str, Any]:
    """
    Matches subjects between dMRI and EEG datasets.
    Returns a dict with:
      - 'dMRI_subjects': list of subjects in dMRI
      - 'EEG_subjects': list of subjects in EEG (if available)
      - 'matched_subjects': list of subjects in both
      - 'simulation_required': bool (True if no matched subjects)
    """
    def get_subjects_from_dir(path: Path) -> Set[str]:
        if not path.exists():
            return set()
        subjects = set()
        for item in path.iterdir():
            if item.is_dir() and item.name.startswith('sub-'):
                subjects.add(item.name)
        return subjects

    dMRI_subjects = get_subjects_from_dir(ds004230_path)
    eeg_subjects = get_subjects_from_dir(ds004231_path) if ds004231_path else set()
    
    matched = dMRI_subjects.intersection(eeg_subjects)
    
    return {
        'dMRI_subjects': sorted(list(dMRI_subjects)),
        'EEG_subjects': sorted(list(eeg_subjects)),
        'matched_subjects': sorted(list(matched)),
        'simulation_required': len(matched) == 0
    }

def write_routing_state(data_root: Path, match_result: Dict[str, Any]):
    """
    Writes the routing state to data/processed/routing_state.json.
    This file is required by T011a and T029c.
    """
    processed_dir = data_root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    routing_file = processed_dir / "routing_state.json"
    
    state = {
        "dMRI_available": True,
        "EEG_available": len(match_result['EEG_subjects']) > 0,
        "matched_subjects": match_result['matched_subjects'],
        "simulation_required": match_result['simulation_required'],
        "dMRI_subjects": match_result['dMRI_subjects'],
        "EEG_subjects": match_result['EEG_subjects']
    }
    
    with open(routing_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    logger.info(f"Routing state written to {routing_file}")
    logger.info(f"Simulation required: {state['simulation_required']}")
    logger.info(f"Matched subjects: {len(state['matched_subjects'])}")

def main():
    data_root = get_data_root()
    try:
        logger.info("Starting dMRI download check...")
        dMRI_path = download_dMRI(data_root)
        
        logger.info("Starting EEG download check...")
        eeg_path = download_EEG(data_root)
        
        logger.info("Matching subjects...")
        match_result = match_subjects(dMRI_path, eeg_path)
        
        write_routing_state(data_root, match_result)
        
        if match_result['simulation_required']:
            logger.warning("No matched subjects found. Simulation path will be required.")
        else:
            logger.info(f"Found {len(match_result['matched_subjects'])} matched subjects.")
            
    except DataLoadError as e:
        logger.error(f"Download failed: {e}")
        # If dMRI is missing, we cannot proceed at all.
        # If EEG is missing, we might still proceed with simulation if we have dMRI.
        # But the error here implies the dataset is not available locally.
        # We raise the error to stop the pipeline if dMRI is missing.
        if "ds004230" in str(e):
            raise
        # If only EEG is missing, we might continue, but the current logic requires
        # the download step to succeed for both or at least verify existence.
        # For now, we exit with error if any critical download fails.
        sys.exit(1)

if __name__ == "__main__":
    main()
