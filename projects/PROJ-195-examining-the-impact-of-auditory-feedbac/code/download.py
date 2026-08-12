import os
import sys
import hashlib
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging for the download process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/download.log', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
OPENNEURO_DATASET_ID = "ds000246"
OPENNEURO_BASE_URL = f"https://openneuro.org/datasets/{OPENNEURO_DATASET_ID}/"
# Using git-annex to fetch specific subsets is robust, but for pure python/http
# we often rely on the 'datalad' package or direct s3 links if known.
# Given the constraint of "pip installable" or "downloadable URL", and the
# need to subset, we will use the `datalad` library which is standard in neuro.
# If datalad is not installed, we attempt to fetch via the gitattributes parser
# logic provided in the existing skeleton, but we must ensure the logic
# actually filters by size.

# NOTE: The task requires ensuring total size < 14GB.
# We will implement a logic that calculates the size of the full dataset
# (or a representative sample) and if it exceeds the limit, we filter
# the subject list to download only a subset.

def get_available_space(path: Path) -> int:
    """Returns available disk space in bytes for the given path."""
    try:
        stat = os.statvfs(path)
        return stat.f_bavail * stat.f_frsize
    except OSError:
        logger.error(f"Could not determine free space for {path}")
        return 0

def calculate_sha256(file_path: Path) -> str:
    """Calculates SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        return ""

def fetch_gitattributes(dataset_id: str) -> Optional[str]:
    """Fetches the .gitattributes file from the OpenNeuro dataset to parse file sizes."""
    # OpenNeuro datasets are hosted on S3 and mirrored via git-annex.
    # The .gitattributes file contains the lfs pointers and sizes.
    url = f"https://openneuro.org/datasets/{dataset_id}/git-attributes"
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        logger.warning(f"Could not fetch gitattributes from {url}: {e}")
        return None

def parse_gitattributes(content: str) -> List[Dict]:
    """Parses the .gitattributes content to extract file paths and sizes."""
    files = []
    if not content:
        return files
    
    for line in content.splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        # Format: path lfs sha256 size
        parts = line.split()
        if len(parts) >= 4:
            path = parts[0]
            # The size is usually the 4th element (0-indexed: 3) in lfs lines
            # e.g., "sub-01/... .nii.gz lfs sha256 123456789 ..."
            # Sometimes the format varies, we try to find the size integer
            size_str = parts[3] if len(parts) > 3 else parts[-1]
            try:
                size = int(size_str)
            except ValueError:
                continue
            files.append({'path': path, 'size': size})
    return files

def estimate_dataset_size(files: List[Dict]) -> int:
    """Estimates total size of the dataset based on parsed files."""
    return sum(f['size'] for f in files)

def select_subsampled_subjects(files: List[Dict], max_size_bytes: int) -> List[str]:
    """
    Selects a subset of subjects to keep total size under max_size_bytes.
    Returns a list of subject IDs (e.g., ['sub-01', 'sub-02']).
    """
    # Group files by subject
    subjects = {}
    for f in files:
        path = f['path']
        # Extract subject ID: sub-XX/...
        parts = path.split('/')
        if len(parts) > 0 and parts[0].startswith('sub-'):
            sub_id = parts[0]
            if sub_id not in subjects:
                subjects[sub_id] = {'total_size': 0, 'files': []}
            subjects[sub_id]['total_size'] += f['size']
            subjects[sub_id]['files'].append(f)

    # Sort subjects by size (smallest first to maximize count) or just iterate
    # We'll iterate and accumulate until we hit the limit.
    selected_subjects = []
    current_total = 0
    
    # Sort by size to be deterministic
    sorted_subjects = sorted(subjects.items(), key=lambda x: x[1]['total_size'])
    
    for sub_id, data in sorted_subjects:
        if current_total + data['total_size'] <= max_size_bytes:
            selected_subjects.append(sub_id)
            current_total += data['total_size']
        else:
            logger.info(f"Skipping subject {sub_id} (size: {data['total_size']} B) to stay within limit.")
            break
    
    logger.info(f"Selected {len(selected_subjects)} subjects. Total estimated size: {current_total / (1024**3):.2f} GB")
    return selected_subjects

def download_file(url: str, dest_path: Path, expected_sha256: Optional[str] = None):
    """Downloads a file from a URL to dest_path with optional checksum verification."""
    import urllib.request
    logger.info(f"Downloading {url} to {dest_path}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        urllib.request.urlretrieve(url, dest_path)
        if expected_sha256:
            actual_hash = calculate_sha256(dest_path)
            if actual_hash != expected_sha256:
                raise ValueError(f"Checksum mismatch for {dest_path}. Expected {expected_sha256}, got {actual_hash}")
        logger.info(f"Download complete: {dest_path}")
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def main():
    """
    Main entry point for downloading and filtering the dataset.
    Implements T012: Filter dataset to ensure total size < 14GB.
    """
    logger.info("Starting dataset download and filtering process...")
    
    # 1. Check disk space
    max_allowed_size = 14 * (1024 ** 3)  # 14 GB in bytes
    available_space = get_available_space(DATA_RAW_DIR)
    
    if available_space < max_allowed_size:
        logger.warning(f"Available space ({available_space / (1024**3):.2f} GB) is less than 14GB. Adjusting target size.")
        # We will try to download as much as possible, but the task says "ensure total size < 14GB"
        # If space is less, we must subset even more.
        target_size = min(max_allowed_size, available_space)
    else:
        target_size = max_allowed_size

    # 2. Fetch file manifest to estimate size
    logger.info(f"Fetching manifest for {OPENNEURO_DATASET_ID}...")
    gitattributes_content = fetch_gitattributes(OPENNEURO_DATASET_ID)
    
    if not gitattributes_content:
        logger.error("Could not fetch gitattributes. Cannot estimate size or filter subjects.")
        # Fallback: We cannot proceed safely without size estimation for T012
        # In a real scenario, we might default to a small subset, but we must fail loudly if we can't verify.
        # However, the task is to implement the logic. We assume the fetch works in the real environment.
        # If it fails, we raise to stop execution.
        raise RuntimeError("Failed to fetch dataset manifest. Cannot perform size filtering.")

    files = parse_gitattributes(gitattributes_content)
    total_estimated_size = estimate_dataset_size(files)
    
    logger.info(f"Total estimated dataset size: {total_estimated_size / (1024**3):.2f} GB")

    # 3. Filter subjects if necessary
    selected_subjects = []
    if total_estimated_size > target_size:
        logger.info(f"Dataset size ({total_estimated_size / (1024**3):.2f} GB) exceeds limit ({target_size / (1024**3):.2f} GB). Filtering subjects...")
        selected_subjects = select_subsampled_subjects(files, target_size)
    else:
        # If under limit, select all subjects
        selected_subjects = list(set(f['path'].split('/')[0] for f in files if f['path'].startswith('sub-')))
        logger.info(f"Dataset size is within limits. Selecting all {len(selected_subjects)} subjects.")

    # 4. Save the selected subject list to data/processed (or raw metadata)
    # The task says "implement dataset filtering logic". We save the plan here.
    # The actual download happens in subsequent steps or by calling a download function with this list.
    # For T012, we output the filtered list to be used by the rest of the pipeline.
    output_file = DATA_RAW_DIR / "selected_subjects.json"
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            "dataset_id": OPENNEURO_DATASET_ID,
            "target_max_size_gb": 14,
            "estimated_total_size_gb": total_estimated_size / (1024**3),
            "selected_subjects": selected_subjects,
            "count": len(selected_subjects)
        }, f, indent=2)
    
    logger.info(f"Saved selected subjects to {output_file}")
    logger.info(f"Subjects to download: {selected_subjects}")

    # Note: The actual downloading of the data files using git-annex or datalad
    # is a separate operation. This task (T012) ensures the LOGIC to filter
    # is in place and the list is generated.
    # If the project expects this script to *also* download, we would need
    # to integrate `datalad` or `git-annex` calls here.
    # Given the existing skeleton has `download_file` for single files,
    # and the dataset is large, we assume the pipeline uses `datalad` for the bulk.
    # We will add a placeholder call to trigger the download if needed, 
    # but the core T012 requirement is the filtering logic and list generation.
    
    # If we were to download here, we would iterate selected_subjects and use
    # a tool like datalad. Since we cannot guarantee datalad is installed 
    # without adding it to requirements (which we can do), we will add it.
    # However, T002 already listed dependencies. We assume datalad is added there
    # or we use the existing `download_file` for a specific manifest.
    # To be safe and "real", we will log the command to run.
    
    logger.info("Filtering logic complete. To download, run: datalad install -d data/raw ds000246 && datalad get -r data/raw/sub-<subject>")
    logger.info("Or use the selected_subjects.json list to drive a custom download loop.")

    return selected_subjects

if __name__ == "__main__":
    main()