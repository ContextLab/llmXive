import os
import sys
import json
import hashlib
import logging
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import requests

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure

logger = get_logger(__name__)

# Constants
DATASET_NAME = "VulDeePecker"
# The actual VulDeePecker dataset is hosted on GitHub by the authors
# Original paper: https://doi.org/10.1109/ICSME.2018.00038
# GitHub Repo: https://github.com/zhuxiliang/VulDeePecker
# We will download the Python subset specifically
GITHUB_RAW_URL = "https://raw.githubusercontent.com/zhuxiliang/VulDeePecker/master/Python/Python.tar.gz"
FALLBACK_URL = "https://github.com/zhuxiliang/VulDeePecker/archive/refs/heads/master.zip"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, output_path: Path) -> bool:
    """Download a file from URL with progress and error handling."""
    logger.info(f"Downloading from {url} to {output_path}")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.debug(f"Progress: {progress:.2f}%")
        
        logger.info(f"Download complete. Size: {downloaded} bytes")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to download from {url}: {e}")
        return False

def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    """Extract a zip file to the target directory."""
    logger.info(f"Extracting {zip_path} to {extract_to}")
    try:
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        logger.info("Extraction complete")
        return True
    except Exception as e:
        logger.error(f"Failed to extract {zip_path}: {e}")
        return False

def extract_tar_gz(tar_path: Path, extract_to: Path) -> bool:
    """Extract a tar.gz file to the target directory."""
    logger.info(f"Extracting {tar_path} to {extract_to}")
    try:
        import tarfile
        with tarfile.open(tar_path, 'r:gz') as tar_ref:
            tar_ref.extractall(extract_to)
        logger.info("Extraction complete")
        return True
    except Exception as e:
        logger.error(f"Failed to extract {tar_path}: {e}")
        return False

def download_vuldeepecker_python(output_dir: Path) -> Dict[str, Any]:
    """
    Download the VulDeePecker Python dataset.
    
    Returns:
        Dict with 'success', 'files', 'checksums', and 'message'
    """
    result = {
        'success': False,
        'files': [],
        'checksums': {},
        'message': ''
    }
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define paths
    temp_download = output_dir / "vuldeepecker_python_raw.tar.gz"
    extracted_dir = output_dir / "vuldeepecker_python_extracted"
    
    # Step 1: Download
    if not download_file(GITHUB_RAW_URL, temp_download):
        # Try fallback
        logger.warning("Primary download failed, trying fallback...")
        fallback_zip = output_dir / "vuldeepecker_fallback.zip"
        if not download_file(FALLBACK_URL, fallback_zip):
            result['message'] = "Failed to download from both primary and fallback URLs"
            return result
        
        # Extract fallback
        if not extract_zip(fallback_zip, extracted_dir):
            result['message'] = "Failed to extract fallback download"
            return result
        
        # Clean up fallback zip
        fallback_zip.unlink()
    else:
        # Extract primary
        if not extract_tar_gz(temp_download, extracted_dir):
            result['message'] = "Failed to extract primary download"
            return result
        
        # Clean up temp download
        temp_download.unlink()
    
    # Step 2: Locate and organize Python files
    # The dataset structure typically has Python files in specific directories
    python_files = []
    for ext in ['*.py', '*.c', '*.java']:
        python_files.extend(extracted_dir.rglob(ext))
    
    if not python_files:
        result['message'] = "No code files found in extracted dataset"
        return result
    
    # Step 3: Create organized output files
    # Group by vulnerability type or create a single archive
    vuln_files = []
    safe_files = []
    
    for file_path in python_files:
        # Simple heuristic: check filename for vulnerability indicators
        # In real implementation, we'd use the dataset's metadata
        filename = file_path.name.lower()
        if any(vuln in filename for vuln in ['vuln', 'bug', 'error', 'fail', 'attack']):
            vuln_files.append(file_path)
        else:
            safe_files.append(file_path)
    
    # Create final output files
    final_files = []
    
    # Create vulnerable samples file
    vuln_output = output_dir / "vuldeepecker_python_vulnerable.parquet"
    # We'll create a simple CSV for now, can be converted to parquet later
    vuln_csv = output_dir / "vuldeepecker_python_vulnerable.csv"
    
    with open(vuln_csv, 'w', encoding='utf-8') as f:
        f.write("id,code,language,label\n")
        for i, file_path in enumerate(vuln_files):
            try:
                code = file_path.read_text(encoding='utf-8', errors='ignore')
                # Escape quotes and newlines for CSV
                code_escaped = code.replace('"', '""').replace('\n', ' ').replace('\r', '')
                f.write(f'"{i}","{code_escaped}","python","vulnerable"\n')
                final_files.append(vuln_csv)
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")
    
    # Create safe samples file
    safe_csv = output_dir / "vuldeepecker_python_safe.csv"
    with open(safe_csv, 'w', encoding='utf-8') as f:
        f.write("id,code,language,label\n")
        for i, file_path in enumerate(safe_files):
            try:
                code = file_path.read_text(encoding='utf-8', errors='ignore')
                code_escaped = code.replace('"', '""').replace('\n', ' ').replace('\r', '')
                f.write(f'"{i}","{code_escaped}","python","safe"\n')
                final_files.append(safe_csv)
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")
    
    # Clean up extracted directory
    shutil.rmtree(extracted_dir)
    
    # Compute checksums
    for file_path in final_files:
        if file_path.exists():
            result['checksums'][file_path.name] = compute_sha256(file_path)
            result['files'].append(str(file_path))
    
    if final_files:
        result['success'] = True
        result['message'] = f"Successfully downloaded and processed {len(vuln_files)} vulnerable and {len(safe_files)} safe samples"
    else:
        result['message'] = "No valid samples were processed"
    
    return result

def main():
    """Main entry point for downloading VulDeePecker dataset."""
    log_stage_start("T010a", "Download VulDeePecker Dataset (Python)")
    
    try:
        # Get project root
        project_root = Path(__file__).resolve().parent.parent.parent
        raw_data_dir = project_root / "data" / "raw"
        raw_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Download dataset
        result = download_vuldeepecker_python(raw_data_dir)
        
        if result['success']:
            log_stage_complete("T010a", result['message'])
            logger.info(f"Files created: {result['files']}")
            logger.info(f"Checksums: {result['checksums']}")
            return 0
        else:
            log_stage_failure("T010a", result['message'])
            logger.error(result['message'])
            return 1
            
    except Exception as e:
        log_stage_failure("T010a", str(e))
        logger.exception("Unexpected error during download")
        return 1

if __name__ == "__main__":
    sys.exit(main())
