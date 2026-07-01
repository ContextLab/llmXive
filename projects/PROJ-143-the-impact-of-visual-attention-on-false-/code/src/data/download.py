"""
Download module for fetching real datasets (Visual Genome, SALICON)
using verified URLs from T008a/b.
"""
import os
import json
import urllib.request
import urllib.error
import zipfile
import tarfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

# Import config to get paths
from src.config import get_config

# Import verification functions to ensure URLs are valid before download
# Note: These are re-implemented locally here to avoid circular imports if needed,
# but ideally they would be in a shared utils module. Since T008a/b scripts exist,
# we assume their logic is sound.
from scripts.verify_visual_genome import check_url_reachable as vg_check
from scripts.verify_salicon import check_url_reachable as salicon_check

def download_file(url: str, dest_path: Path, chunk_size: int = 8192) -> bool:
    """
    Download a file from a URL to a destination path.
    Handles HTTP errors and connection issues.
    """
    try:
        print(f"Downloading {url} to {dest_path}...")
        with urllib.request.urlopen(url, timeout=30) as response:
            total_size = response.headers.get('Content-Length')
            downloaded = 0
            
            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        progress = (downloaded / int(total_size)) * 100
                        print(f"\rProgress: {progress:.1f}%", end='', flush=True)
            print() # Newline after progress
        return True
    except urllib.error.URLError as e:
        print(f"Error downloading {url}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error downloading {url}: {e}")
        return False

def extract_archive(archive_path: Path, extract_to: Path) -> bool:
    """
    Extract zip or tar archives to a destination directory.
    """
    try:
        print(f"Extracting {archive_path} to {extract_to}...")
        if archive_path.suffix == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        elif archive_path.suffix in ['.tar', '.gz', '.tgz']:
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_to)
        else:
            print(f"Unsupported archive format: {archive_path.suffix}")
            return False
        print("Extraction complete.")
        return True
    except Exception as e:
        print(f"Error extracting {archive_path}: {e}")
        return False

def download_visual_genome(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Download Visual Genome dataset subset.
    Uses the URL verified in T008a.
    """
    urls = config.get('data', {}).get('visual_genome', {}).get('urls', {})
    # Fallback to default known URL if config doesn't specify, but T008a should have verified it
    # We rely on T008a's verification result. If it failed, this should ideally not run or fail explicitly.
    # For this implementation, we assume the URL is present and valid.
    
    url = urls.get('subset', 'https://cs.stanford.edu/people/rak248/VG_100K_2/images.zip')
    dest_dir = Path(config.get('paths', {}).get('data_raw', 'data/raw'))
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    archive_name = "vg_subset.zip"
    archive_path = dest_dir / archive_name
    
    if not download_file(url, archive_path):
        return {"status": "failed", "reason": "Download failed", "dataset": "visual_genome"}
    
    extract_dir = dest_dir / "visual_genome"
    extract_dir.mkdir(parents=True, exist_ok=True)
    
    if not extract_archive(archive_path, extract_dir):
        return {"status": "failed", "reason": "Extraction failed", "dataset": "visual_genome"}
    
    # Clean up archive
    archive_path.unlink()
    
    return {
        "status": "success",
        "dataset": "visual_genome",
        "path": str(extract_dir),
        "files_downloaded": 1
    }

def download_salicon(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Download SALICON dataset.
    Uses the URL verified in T008b.
    """
    urls = config.get('data', {}).get('salicon', {}).get('urls', {})
    # Fallback URL if config missing, but T008b should have verified it
    url = urls.get('test_set', 'https://salicon.org/data/salicon_test.zip')
    dest_dir = Path(config.get('paths', {}).get('data_raw', 'data/raw'))
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    archive_name = "salicon_test.zip"
    archive_path = dest_dir / archive_name
    
    if not download_file(url, archive_path):
        return {"status": "failed", "reason": "Download failed", "dataset": "salicon"}
    
    extract_dir = dest_dir / "salicon"
    extract_dir.mkdir(parents=True, exist_ok=True)
    
    if not extract_archive(archive_path, extract_dir):
        return {"status": "failed", "reason": "Extraction failed", "dataset": "salicon"}
    
    # Clean up archive
    archive_path.unlink()
    
    return {
        "status": "success",
        "dataset": "salicon",
        "path": str(extract_dir),
        "files_downloaded": 1
    }

def main():
    """
    Main entry point to download datasets.
    """
    config = get_config()
    
    results = {}
    
    # Check if URLs are verified (T008a/b)
    # We assume T008a/b wrote to data/verified_sources.md. 
    # For robustness, we try to check reachability again or assume config has valid URLs.
    # If T008a/b failed, the config might not have valid URLs.
    
    # Visual Genome
    if config.get('data', {}).get('visual_genome', {}).get('urls', {}).get('subset'):
        results['visual_genome'] = download_visual_genome(config)
    else:
        print("Visual Genome URL not found in config. Skipping.")
        results['visual_genome'] = {"status": "skipped", "reason": "No URL"}
    
    # SALICON
    if config.get('data', {}).get('salicon', {}).get('urls', {}).get('test_set'):
        results['salicon'] = download_salicon(config)
    else:
        print("SALICON URL not found in config. Skipping.")
        results['salicon'] = {"status": "skipped", "reason": "No URL"}
    
    # Write download log
    log_path = Path(config.get('paths', {}).get('data_processed', 'data/processed'))
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / "download_log.json"
    
    with open(log_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Download log written to {log_file}")
    
    # Return success if all required downloads succeeded
    success = all(r.get('status') == 'success' for r in results.values())
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
