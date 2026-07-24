import os
import sys
import hashlib
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import HCP_MMP_FILE_PATH, HCP_MMP_URL, HCP_MMP_HASH, get_data_root, ensure_directories
from utils.logger import get_logger, ResearchError, DataLoadError
from utils.data_setup import compute_file_checksum, load_checksums, save_checksums

logger = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_parcellation_file() -> Path:
    """
    Download the HCP-MMP parcellation file if it doesn't exist.
    Returns the path to the downloaded file.
    """
    data_root = get_data_root()
    raw_dir = data_root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    file_path = raw_dir / HCP_MMP_FILE_PATH
    url = HCP_MMP_URL

    if file_path.exists():
        logger.info(f"Parcellation file already exists at {file_path}")
        return file_path

    logger.info(f"Downloading HCP-MMP parcellation from {url}")
    logger.info(f"Saving to {file_path}")

    # Use curl for downloading as it's robust and available in most environments
    # Alternatively, one could use urllib or requests if available
    try:
        import urllib.request
        with urllib.request.urlopen(url) as response, open(file_path, 'wb') as out_file:
            content_length = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            chunk_size = 8192
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if content_length:
                    logger.info(f"Downloaded {downloaded}/{content_length} bytes")
    except Exception as e:
        logger.error(f"Failed to download parcellation file: {e}")
        raise DataLoadError(f"Failed to download parcellation file: {e}")

    logger.info(f"Download complete: {file_path}")
    return file_path

def verify_parcellation_file(file_path: Path) -> bool:
    """
    Verify the downloaded file against the expected hash.
    If the hash in config is a placeholder, compute and save the real hash.
    Returns True if verification passes.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Parcellation file not found at {file_path}")

    calculated_hash = compute_sha256(file_path)
    logger.info(f"Calculated SHA-256 hash: {calculated_hash}")

    # Check if we need to update the placeholder hash
    if HCP_MMP_HASH == "PLACEHOLDER_HASH_TO_BE_UPDATED":
        logger.info("Detected placeholder hash. Updating state file with real hash.")
        data_root = get_data_root()
        processed_dir = data_root / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        hash_file = processed_dir / "parcellation_hash.json"
        
        # Save the new hash
        with open(hash_file, 'w') as f:
            json.dump({"hash": calculated_hash, "source": HCP_MMP_URL}, f, indent=2)
        
        logger.info(f"Saved real hash to {hash_file}")
        # Note: In a real scenario, we might update config.py dynamically, 
        # but for this task, we just save the state file.
        return True
    
    # If a real hash is expected, verify it
    # For this implementation, we assume if it's not a placeholder, it's the expected hash
    # In a production system, we would compare calculated_hash with the expected one
    # and raise an error if they don't match.
    # Since the task says T010 updates the state, we assume the placeholder is handled above.
    # If we reach here with a non-placeholder, it means we are verifying against a known good hash.
    # However, the current config has a placeholder. If this code runs with a real hash in config:
    if calculated_hash != HCP_MMP_HASH:
        raise ResearchError(
            f"Hash mismatch! Expected: {HCP_MMP_HASH}, Calculated: {calculated_hash}. "
            "File may be corrupted or from an incorrect source."
        )
    
    logger.info("Parcellation file hash verified successfully.")
    return True

def load_tractography(subject_id: str) -> Path:
    """
    Locate the tractography file (.tck) for a given subject.
    Expects the file to be in data/raw/dMRI/sub-{id}/sub-{id}_dwi.tck or similar.
    """
    data_root = get_data_root()
    raw_dir = data_root / "raw" / "dMRI"
    
    # Look for .tck files in the subject directory
    subject_dir = raw_dir / f"sub-{subject_id}"
    if not subject_dir.exists():
        raise FileNotFoundError(f"Subject directory not found: {subject_dir}")
    
    tck_files = list(subject_dir.glob("*.tck"))
    if not tck_files:
        # Try common naming conventions
        possible_names = [
            f"sub-{subject_id}_dwi.tck",
            f"{subject_id}_dwi.tck",
            f"sub-{subject_id}_tracks.tck"
        ]
        for name in possible_names:
            candidate = subject_dir / name
            if candidate.exists():
                return candidate
        raise FileNotFoundError(f"No .tck file found for subject {subject_id} in {subject_dir}")
    
    if len(tck_files) > 1:
        logger.warning(f"Multiple .tck files found for {subject_id}, using the first one: {tck_files[0]}")
    
    return tck_files[0]

def generate_connectome_matrix(tck_path: Path, parcellation_path: Path, subject_id: str) -> Path:
    """
    Generate a connectome matrix using MRtrix3's tck2connectome.
    Returns the path to the output .tsv file.
    """
    data_root = get_data_root()
    processed_dir = data_root / "processed" / "connectomes" / f"sub-{subject_id}"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_tsv = processed_dir / "connectome.tsv"
    assignments_txt = processed_dir / "assignments.txt"
    
    # Check if MRtrix3 is available
    try:
        result = subprocess.run(['which', 'tck2connectome'], capture_output=True, text=True)
        if result.returncode != 0:
            raise ResearchError("MRtrix3 'tck2connectome' command not found. Please install MRtrix3.")
    except Exception as e:
        raise ResearchError(f"Failed to check for MRtrix3: {e}")
    
    # Prepare the command
    # Note: This assumes the parcellation file is a .mif or can be converted.
    # The HCP_MMP file is a .zip containing .mif files. We need to handle extraction.
    # For simplicity, we assume the zip contains a single .mif file or we extract it first.
    # In a real scenario, we would extract the zip and use the .mif file.
    
    # Extract the zip if it's a zip file
    if parcellation_path.suffix == '.zip':
        import zipfile
        extract_dir = processed_dir.parent / "parcellation_extracted"
        extract_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(parcellation_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        # Find the .mif file
        mif_files = list(extract_dir.glob("*.mif"))
        if not mif_files:
            raise ResearchError(f"No .mif file found in extracted parcellation: {extract_dir}")
        nodes_mif = mif_files[0]
        logger.info(f"Using extracted nodes file: {nodes_mif}")
    else:
        nodes_mif = parcellation_path
    
    cmd = [
        'tck2connectome',
        str(tck_path),
        str(nodes_mif),
        str(output_tsv),
        '-scale_invlength',
        '-out_assignments', str(assignments_txt)
    ]
    
    logger.info(f"Running MRtrix3 command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"MRtrix3 command failed with return code {e.returncode}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise ResearchError(f"MRtrix3 tck2connectome failed: {e.stderr}")
    
    logger.info(f"Connectome matrix generated: {output_tsv}")
    return output_tsv

def save_connectome_matrix(connectome_tsv: Path, subject_id: str) -> Dict[str, Any]:
    """
    Save the connectome matrix metadata and verify the output.
    Returns a dictionary with metadata.
    """
    if not connectome_tsv.exists():
        raise FileNotFoundError(f"Connectome TSV file not found: {connectome_tsv}")
    
    # Read the TSV to get dimensions
    try:
        import pandas as pd
        df = pd.read_csv(connectome_tsv, sep='\t', header=None)
        n_nodes = df.shape[0]
        n_edges = df.shape[1] if df.shape[0] > 0 else 0
    except Exception as e:
        logger.warning(f"Could not read TSV for dimensions: {e}")
        n_nodes = 0
        n_edges = 0
    
    metadata = {
        "subject_id": subject_id,
        "file_path": str(connectome_tsv),
        "n_nodes": n_nodes,
        "n_edges": n_edges,
        "format": "tsv",
        "processed": True
    }
    
    logger.info(f"Saved connectome metadata for {subject_id}: {metadata}")
    return metadata

def run_preprocessing_for_subject(subject_id: str) -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline for a single subject.
    1. Verify parcellation file.
    2. Load tractography.
    3. Generate connectome matrix.
    4. Save metadata.
    """
    logger.info(f"Starting preprocessing for subject: {subject_id}")
    
    # 1. Verify parcellation
    data_root = get_data_root()
    raw_dir = data_root / "raw"
    parcellation_path = raw_dir / HCP_MMP_FILE_PATH
    
    if not parcellation_path.exists():
        logger.info("Parcellation file missing, downloading...")
        parcellation_path = download_parcellation_file()
    
    verify_parcellation_file(parcellation_path)
    
    # 2. Load tractography
    tck_path = load_tractography(subject_id)
    
    # 3. Generate connectome
    connectome_tsv = generate_connectome_matrix(tck_path, parcellation_path, subject_id)
    
    # 4. Save metadata
    metadata = save_connectome_matrix(connectome_tsv, subject_id)
    
    logger.info(f"Preprocessing complete for subject {subject_id}")
    return metadata

def run_pipeline(subject_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Run the preprocessing pipeline for all subjects.
    If subject_ids is None, it will attempt to find all subjects in data/raw/dMRI.
    """
    data_root = get_data_root()
    raw_dMRI_dir = data_root / "raw" / "dMRI"
    
    if subject_ids is None:
        # Auto-discover subjects
        if not raw_dMRI_dir.exists():
            logger.warning(f"Raw dMRI directory not found: {raw_dMRI_dir}")
            return []
        subject_dirs = [d for d in raw_dMRI_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
        subject_ids = [d.name.replace("sub-", "") for d in subject_dirs]
        logger.info(f"Discovered {len(subject_ids)} subjects: {subject_ids}")
    
    if not subject_ids:
        logger.warning("No subjects to process.")
        return []
    
    results = []
    for subject_id in subject_ids:
        try:
            result = run_preprocessing_for_subject(subject_id)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process subject {subject_id}: {e}")
            # Continue with other subjects
            continue
    
    logger.info(f"Pipeline complete. Processed {len(results)} subjects successfully.")
    return results

def main():
    """Main entry point for the script."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting dMRI preprocessing pipeline (T010)")
    
    # Ensure directories exist
    ensure_directories()
    
    # Run pipeline
    results = run_pipeline()
    
    if not results:
        logger.warning("No subjects were processed. Check if raw dMRI data is available.")
        sys.exit(1)
    
    logger.info(f"Successfully processed {len(results)} subjects.")
    sys.exit(0)

if __name__ == "__main__":
    main()
