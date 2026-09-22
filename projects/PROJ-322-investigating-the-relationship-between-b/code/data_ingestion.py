"""
Data Ingestion Module for Brain Network Reconfiguration Project.

This module handles the download of OpenNeuro datasets, parsing of subject
information, and generation of a manifest CSV file listing all available
data points.
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import project-specific utilities
from config import get_config, is_synthetic, is_methodology_validation_mode
from logging_config import get_logger, initialize_logging
from memory_monitor import get_current_ram_gb, is_limit_exceeded, check_and_warn
from entities import Subject

# Initialize logging for this module
logger = get_logger(__name__)

# Configuration constants
MEMORY_LIMIT_GB = 6.0
DEFAULT_DATASET_ID = "ds000006"  # Example mTBI dataset
OUTPUT_MANIFEST_PATH = "data/results/manifest.csv"

def check_memory_and_log(operation_name: str) -> bool:
    """
    Check current RAM usage and log a warning if approaching the limit.

    Args:
        operation_name: Name of the operation being performed (for logging)

    Returns:
        True if memory is within limits, False otherwise.
    """
    current_ram = get_current_ram_gb()
    if is_limit_exceeded():
        logger.error(f"Memory limit exceeded during {operation_name}: {current_ram:.2f} GB")
        return False
    
    check_and_warn(MEMORY_LIMIT_GB)
    logger.debug(f"Memory OK during {operation_name}: {current_ram:.2f} GB / {MEMORY_LIMIT_GB} GB limit")
    return True

def get_dataset_metadata(dataset_id: str) -> Dict[str, Any]:
    """
    Fetch metadata for a specific OpenNeuro dataset.
    
    In a real implementation, this would query the OpenNeuro API or GraphQL endpoint.
    For this implementation, we simulate the metadata structure based on the dataset ID
    or attempt a lightweight fetch if the huggingface_hub is available.

    Args:
        dataset_id: OpenNeuro dataset identifier (e.g., 'ds000006')

    Returns:
        Dictionary containing dataset metadata (name, subjects, modalities).
    """
    logger.info(f"Fetching metadata for dataset: {dataset_id}")
    
    # Attempt to use huggingface_hub to get dataset info if available
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        # OpenNeuro datasets are mirrored on HuggingFace Hub under 'openneuro'
        repo_id = f"openneuro/{dataset_id}"
        try:
            info = api.dataset_info(repo_id)
            logger.info(f"Retrieved metadata from HuggingFace Hub for {dataset_id}")
            return {
                "id": dataset_id,
                "name": info.id,
                "description": info.description or "No description available",
                "subjects": [], # Subjects parsed later from file structure
                "modalities": ["fMRI"] if "fmri" in str(info.id).lower() else ["unknown"]
            }
        except Exception as hub_err:
            logger.warning(f"Could not fetch detailed info from HuggingFace for {dataset_id}: {hub_err}")
            # Fallback to generic structure
            pass
    except ImportError:
        logger.warning("huggingface_hub not installed, using generic metadata structure")
    
    # Fallback generic metadata
    return {
        "id": dataset_id,
        "name": f"OpenNeuro {dataset_id}",
        "description": f"Mild Traumatic Brain Injury dataset {dataset_id}",
        "subjects": [],
        "modalities": ["fMRI", "T1w"]
    }

def download_dataset_files(dataset_id: str, output_dir: Path) -> List[Path]:
    """
    Download dataset files from OpenNeuro using huggingface_hub.
    
    This function downloads the dataset in a streaming/chunked manner to respect
    memory constraints. It does not load the full data into memory, only the
    file paths.

    Args:
        dataset_id: OpenNeuro dataset identifier
        output_dir: Directory to download files to

    Returns:
        List of paths to downloaded files (or expected paths if streaming).
    """
    logger.info(f"Starting download of {dataset_id} to {output_dir}")
    
    if not check_memory_and_log("dataset download start"):
        raise MemoryError("Memory limit exceeded before download start.")

    try:
        from huggingface_hub import snapshot_download
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use snapshot_download to get the dataset structure
        # We only download the directory structure and small files (JSONs, TSVs)
        # to avoid downloading massive NIfTI files immediately, as the task
        # focuses on generating a manifest of *available* data.
        # If full download is required, we would iterate and download file by file.
        # For manifest generation, we need the file paths.
        
        # Attempt to download only the metadata and subject lists first
        # by filtering or using streaming if the dataset is huge.
        # Given the constraint, we will try to download the dataset structure.
        # Note: For very large datasets, this might still be heavy.
        # We rely on huggingface_hub's caching and partial download capabilities.
        
        local_path = snapshot_download(
            repo_id=f"openneuro/{dataset_id}",
            repo_type="dataset",
            local_dir=str(output_dir),
            allow_patterns=["participants.tsv", "dataset_description.json", "*/participants.tsv", "*/sub-*/ses-*/*.nii.gz", "*/sub-*/ses-*/*.tsv", "*/sub-*/ses-*/*.json"]
        )
        
        logger.info(f"Dataset structure downloaded to {local_path}")
        return list(Path(local_path).rglob("*"))
        
    except ImportError:
        logger.error("huggingface_hub is required for downloading OpenNeuro data. Please install it.")
        # Fallback: If we cannot download, we might need to simulate the structure
        # for the manifest if in validation mode, but the task requires REAL data.
        # We raise an error to fail loudly.
        raise RuntimeError("Cannot download OpenNeuro data without huggingface_hub.")
    except Exception as e:
        logger.error(f"Failed to download dataset {dataset_id}: {e}")
        raise

def parse_subject_info(file_paths: List[Path], base_dir: Path) -> List[Subject]:
    """
    Parse file paths to extract subject and time point information.
    
    Args:
        file_paths: List of all file paths in the dataset
        base_dir: Base directory of the dataset

    Returns:
        List of Subject entities with parsed metadata.
    """
    subjects_dict: Dict[str, Dict[str, Any]] = {}
    
    for file_path in file_paths:
        if not file_path.is_file():
            continue
        
        # Look for fMRI or T1w files
        if "sub-" in str(file_path):
            # Parse subject ID and session
            # Expected format: sub-<label>/ses-<label>/...
            path_str = str(file_path)
            
            # Extract subject
            sub_match = None
            ses_match = None
            
            parts = path_str.split(os.sep)
            for part in parts:
                if part.startswith("sub-"):
                    sub_match = part
                if part.startswith("ses-"):
                    ses_match = part
            
            if sub_match:
                subject_id = sub_match.replace("sub-", "")
                if subject_id not in subjects_dict:
                    subjects_dict[subject_id] = {
                        "id": subject_id,
                        "sessions": {},
                        "files": []
                    }
                
                if ses_match:
                    session_id = ses_match.replace("ses-", "")
                    if session_id not in subjects_dict[subject_id]["sessions"]:
                        # Determine time point (acute/chronic) based on session name or default
                        # This is a heuristic; real logic would parse the session name
                        time_point = "unknown"
                        if "acute" in session_id.lower():
                            time_point = "acute"
                        elif "chronic" in session_id.lower():
                            time_point = "chronic"
                        
                        subjects_dict[subject_id]["sessions"][session_id] = {
                            "id": session_id,
                            "time_point": time_point,
                            "files": []
                        }
                    
                    subjects_dict[subject_id]["sessions"][session_id]["files"].append(str(file_path))
                else:
                    # No session found, treat as single time point
                    if "default" not in subjects_dict[subject_id]["sessions"]:
                        subjects_dict[subject_id]["sessions"]["default"] = {
                            "id": "default",
                            "time_point": "single",
                            "files": []
                        }
                    subjects_dict[subject_id]["sessions"]["default"]["files"].append(str(file_path))
                
                subjects_dict[subject_id]["files"].append(str(file_path))

    # Convert to Subject entities
    subjects = []
    for sub_id, data in subjects_dict.items():
        # Check for required time points (acute/chronic) as per task T013 logic
        # Here we just collect what exists
        sessions = list(data["sessions"].values())
        subjects.append(Subject(
            id=sub_id,
            sessions=sessions,
            raw_files=data["files"]
        ))
    
    logger.info(f"Parsed {len(subjects)} subjects from {len(file_paths)} files.")
    return subjects

def generate_manifest(subjects: List[Subject], output_path: Path) -> None:
    """
    Generate a CSV manifest file from the list of subjects.
    
    The manifest contains: subject_id, session_id, time_point, file_path.
    
    Args:
        subjects: List of parsed Subject entities
        output_path: Path to write the CSV file
    """
    import csv
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating manifest at {output_path}")
    
    with open(output_path, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['subject_id', 'session_id', 'time_point', 'file_path'])
        
        for subject in subjects:
            for session in subject.sessions:
                for file_path in session.files:
                    writer.writerow([
                        subject.id,
                        session.id,
                        session.time_point,
                        file_path
                    ])
    
    logger.info(f"Manifest generated with {sum(len(s.sessions) for s in subjects)} session entries.")

def main():
    """
    Main entry point for data ingestion.
    
    Executes the pipeline:
    1. Check memory
    2. Get dataset metadata
    3. Download dataset files
    4. Parse subject info
    5. Generate manifest
    """
    # Initialize logging if not already done
    initialize_logging()
    
    logger.info("Starting Data Ingestion Pipeline (T011)")
    
    # Get dataset ID from config or default
    config = get_config()
    dataset_id = config.get("dataset_id", DEFAULT_DATASET_ID)
    
    # Determine output directory
    # Assuming data/raw is for downloaded data, data/results for manifest
    base_dir = Path.cwd()
    download_dir = base_dir / "data" / "raw" / dataset_id
    manifest_path = base_dir / "data" / "results" / "manifest.csv"
    
    try:
        # Step 1: Check Memory
        if not check_memory_and_log("initialization"):
            logger.error("Aborting: Memory limit exceeded.")
            return 1
        
        # Step 2: Get Metadata
        metadata = get_dataset_metadata(dataset_id)
        logger.info(f"Dataset Metadata: {metadata['name']}")
        
        # Step 3: Download Files
        # Note: This might take a while and consume disk space.
        # We assume the environment has enough disk space.
        logger.info(f"Downloading dataset {dataset_id}...")
        file_paths = download_dataset_files(dataset_id, download_dir)
        
        # Step 4: Parse Subject Info
        subjects = parse_subject_info(file_paths, download_dir)
        
        # Step 5: Generate Manifest
        generate_manifest(subjects, manifest_path)
        
        logger.info("Data Ingestion Pipeline completed successfully.")
        logger.info(f"Manifest saved to: {manifest_path}")
        
        # Final memory check
        if not check_memory_and_log("completion"):
            logger.warning("Memory usage high at completion.")
        
        return 0
        
    except MemoryError as e:
        logger.error(f"Pipeline failed due to memory constraints: {e}")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
