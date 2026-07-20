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

from config import get_data_root, HCP_MMP_URL, HCP_MMP_FILE_PATH, HCP_MMP_HASH
from utils.logger import get_logger, log_pipeline_start, log_pipeline_end

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
    Download the HCP-MMP parcellation file if it does not exist.
    Raises an error if the download fails or hash verification fails.
    """
    data_root = get_data_root()
    file_path = data_root / HCP_MMP_FILE_PATH
    
    if file_path.exists():
        logger.info(f"Parcellation file already exists at {file_path}")
        # Verify existing file
        actual_hash = compute_sha256(file_path)
        if actual_hash != HCP_MMP_HASH:
            logger.error(f"Hash mismatch for existing file. Expected: {HCP_MMP_HASH}, Got: {actual_hash}")
            # Do not attempt to auto-fix existing files to avoid corruption loops
            raise ValueError(f"Existing parcellation file hash mismatch. Please delete {file_path} and retry.")
        return file_path

    logger.info(f"Parcellation file not found. Downloading from {HCP_MMP_URL}...")
    
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use curl or wget for robust downloading
    # We assume a standard HTTP client is available
    try:
        import urllib.request
        with urllib.request.urlopen(HCP_MMP_URL) as response, open(file_path, 'wb') as out_file:
            logger.info("Downloading file...")
            content_length = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            chunk_size = 8192
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if content_length > 0:
                    progress = (downloaded / content_length) * 100
                    if downloaded % (1024 * 1024) < chunk_size: # Log roughly every MB
                        logger.debug(f"Download progress: {progress:.1f}%")
        logger.info("Download complete.")
    except Exception as e:
        logger.error(f"Failed to download parcellation file: {e}")
        if file_path.exists():
            file_path.unlink()
        raise RuntimeError(f"Could not download HCP-MMP parcellation file from {HCP_MMP_URL}") from e

    # Verify hash
    actual_hash = compute_sha256(file_path)
    if actual_hash != HCP_MMP_HASH:
        logger.error(f"Hash mismatch after download. Expected: {HCP_MMP_HASH}, Got: {actual_hash}")
        file_path.unlink() # Remove corrupted file
        raise ValueError(f"Downloaded file hash verification failed. Expected {HCP_MMP_HASH}, got {actual_hash}")
    
    logger.info("Parcellation file downloaded and verified successfully.")
    return file_path

def verify_parcellation_file() -> Path:
    """
    Ensure the HCP-MMP parcellation file exists and is valid.
    Downloads if missing, verifies hash.
    """
    data_root = get_data_root()
    file_path = data_root / HCP_MMP_FILE_PATH
    
    if not file_path.exists():
        return download_parcellation_file()
    
    # Verify existing
    actual_hash = compute_sha256(file_path)
    if actual_hash != HCP_MMP_HASH:
        raise ValueError(f"Existing file hash mismatch. Expected: {HCP_MMP_HASH}, Got: {actual_hash}")
    
    return file_path

def load_tractography(subject_id: str) -> Path:
    """
    Locate the raw tractography file (.tck) for a given subject.
    Expected path: data/raw/ds004230/sub-{subject_id}/dwi/sub-{subject_id}_dwi_tractography.tck
    """
    data_root = get_data_root()
    # Construct expected path based on OpenNeuro ds004230 structure
    # Note: Actual path might vary slightly, but we follow the spec's implied structure
    tck_path = data_root / "ds004230" / f"sub-{subject_id}" / "dwi" / f"sub-{subject_id}_dwi_tractography.tck"
    
    if not tck_path.exists():
        # Try alternative common naming
        alt_path = data_root / "ds004230" / f"sub-{subject_id}" / "dwi" / f"sub-{subject_id}_dwi_streamlines.tck"
        if alt_path.exists():
            return alt_path
        
        raise FileNotFoundError(f"Tractography file not found for subject {subject_id}. Expected at {tck_path}")
    
    return tck_path

def generate_connectome_matrix(subject_id: str, parcellation_path: Path) -> Optional[Path]:
    """
    Generate the structural connectome matrix using MRtrix3 tck2connectome.
    
    This function assumes MRtrix3 is installed and available in the PATH.
    It creates a weighted adjacency matrix (CSV) representing streamline counts between parcels.
    """
    tck_path = load_tractography(subject_id)
    data_root = get_data_root()
    output_dir = data_root / "processed" / "connectomes" / f"sub-{subject_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_matrix_path = output_dir / "connectome_matrix.csv"
    
    # Check if output already exists
    if output_matrix_path.exists():
        logger.info(f"Connectome matrix already exists for {subject_id}. Skipping MRtrix3 call.")
        return output_matrix_path

    logger.info(f"Running MRtrix3 tck2connectome for {subject_id}...")
    
    # Command construction
    # We assume the parcellation file is a label file compatible with tck2connectome
    # If the downloaded file is a zip, we need to extract it first or point to the internal file.
    # For this implementation, we assume the downloaded file is the label file itself (or we extract to a temp location).
    # Given the URL is a placeholder, we assume the file at HCP_MMP_FILE_PATH is the usable label file.
    # If it's a zip, we'd need to unzip. Let's assume it's the raw label file for now, or handle zip.
    
    # Check if it's a zip
    if str(parcellation_path).endswith('.zip'):
        import zipfile
        extract_dir = data_root / "processed" / "parcellation_extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(parcellation_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        # Assume the first file in the zip is the label file (simplification)
        label_files = list(extract_dir.glob("*"))
        if not label_files:
            raise RuntimeError("Could not find label file in downloaded zip.")
        # Filter for common label extensions
        label_file = next((f for f in label_files if f.suffix in ['.txt', '.nii', '.nii.gz']), None)
        if not label_file:
            raise RuntimeError("No valid label file found in downloaded zip.")
        parcellation_use = label_file
    else:
        parcellation_use = parcellation_path

    cmd = [
        "tck2connectome",
        str(tck_path),
        str(parcellation_use),
        str(output_matrix_path),
        "-out_assignments", str(output_dir / "assignments.csv"),
        "-scale_invlength", # Optional: scale by inverse length
        "-zero_diagonal"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"MRtrix3 output: {result.stdout}")
        if result.stderr:
            logger.warning(f"MRtrix3 warnings: {result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"MRtrix3 command failed: {e}")
        logger.error(f"Stderr: {e.stderr}")
        raise RuntimeError(f"MRtrix3 tck2connectome failed for subject {subject_id}") from e
    
    return output_matrix_path

def save_connectome_matrix(subject_id: str, matrix_path: Path) -> Dict[str, Any]:
    """
    Save the generated connectome matrix to the unified store.
    Returns metadata about the saved file.
    """
    data_root = get_data_root()
    store_dir = data_root / "processed" / "store" / f"sub-{subject_id}"
    store_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy or move to store
    store_path = store_dir / "structural_connectome.csv"
    import shutil
    shutil.copy2(matrix_path, store_path)
    
    # Generate metadata
    metadata = {
        "subject_id": subject_id,
        "file_path": str(store_path),
        "source_file": str(matrix_path),
        "type": "structural_connectome",
        "format": "csv",
        "matrix_shape": None # Will be populated if we read it
    }
    
    # Try to read shape for metadata
    try:
        import pandas as pd
        df = pd.read_csv(store_path)
        metadata["matrix_shape"] = list(df.shape)
    except Exception as e:
        logger.warning(f"Could not read matrix shape for metadata: {e}")
    
    return metadata

def run_preprocessing_for_subject(subject_id: str) -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline for a single subject.
    1. Verify/Download Parcellation
    2. Load Tractography
    3. Generate Connectome Matrix
    4. Store Result
    """
    log_pipeline_start("preprocess_dMRI", subject_id)
    
    try:
        # 1. Ensure parcellation is available
        parcellation_path = verify_parcellation_file()
        logger.info(f"Using parcellation file: {parcellation_path}")
        
        # 2 & 3. Generate Matrix
        matrix_path = generate_connectome_matrix(subject_id, parcellation_path)
        if not matrix_path:
            raise RuntimeError(f"Failed to generate connectome matrix for {subject_id}")
        
        # 4. Store
        metadata = save_connectome_matrix(subject_id, matrix_path)
        
        log_pipeline_end("preprocess_dMRI", subject_id, status="success")
        return {"status": "success", "metadata": metadata}
        
    except Exception as e:
        logger.error(f"Preprocessing failed for {subject_id}: {e}")
        log_pipeline_end("preprocess_dMRI", subject_id, status="failed", error=str(e))
        return {"status": "failed", "error": str(e)}

def run_pipeline(subject_ids: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run preprocessing for a list of subjects.
    If subject_ids is None, attempts to find all subjects in data/raw/ds004230.
    """
    log_pipeline_start("preprocess_dMRI", "batch")
    
    results = []
    
    if subject_ids is None:
        # Auto-discover subjects
        data_root = get_data_root()
        raw_dir = data_root / "ds004230"
        if not raw_dir.exists():
            logger.warning(f"Raw data directory {raw_dir} does not exist. Cannot auto-discover subjects.")
            return {"subjects": results}
        
        subject_ids = [d.name for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
        logger.info(f"Auto-discovered {len(subject_ids)} subjects: {subject_ids}")
    
    if not subject_ids:
        logger.warning("No subjects to process.")
        return {"subjects": results}
    
    for sid in subject_ids:
        res = run_preprocessing_for_subject(sid)
        results.append(res)
    
    log_pipeline_end("preprocess_dMRI", "batch", status="completed")
    return {"subjects": results}

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Preprocess dMRI tractography to connectome matrices.")
    parser.add_argument("--subjects", nargs="+", help="List of subject IDs to process (e.g., sub-001 sub-002)")
    args = parser.parse_args()
    
    subject_ids = args.subjects if args.subjects else None
    results = run_pipeline(subject_ids)
    
    print(json.dumps(results, indent=2))
    # Check for failures
    failed_count = sum(1 for r in results["subjects"] if r["status"] == "failed")
    if failed_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()