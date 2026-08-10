import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from datasets import load_dataset

# Ensure project root is in path for imports if running as script
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Import config to ensure project initialization if needed
try:
    from src.utils.config import get_config, SocraticConfig
except ImportError:
    # Fallback if config isn't ready yet, though T006 should be done
    pass

def ensure_data_dirs(base_path: Path) -> None:
    """Create data directories: raw, processed, results if they don't exist."""
    dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the state manifest containing expected checksums."""
    if not manifest_path.exists():
        # If manifest doesn't exist, we cannot verify. 
        # Per task requirement, we should fail loudly if we can't verify against manifest.
        # However, for the downloader to run, we might need to create a default manifest
        # or assume the task implies the manifest exists in state/.
        # We will raise an error if the manifest is missing, as per "Verify checksums match state/ manifest".
        raise FileNotFoundError(f"State manifest not found at {manifest_path}")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

def verify_checksums(dataset_name: str, downloaded_files: List[Path], manifest: Dict[str, Any]) -> bool:
    """Verify downloaded files against the manifest checksums."""
    if dataset_name not in manifest:
        raise ValueError(f"No checksum entry found for dataset: {dataset_name}")
    
    expected_checksums = manifest[dataset_name]
    
    if len(downloaded_files) != len(expected_checksums.get("files", [])):
        # Log warning but proceed if structure differs, or fail strictly?
        # Strict verification:
        raise ValueError(f"File count mismatch for {dataset_name}. Expected {len(expected_checksums.get('files', []))}, got {len(downloaded_files)}")

    for file_info in expected_checksums.get("files", []):
        file_name = file_info.get("name")
        expected_hash = file_info.get("checksum")
        
        # Find the actual downloaded file
        matched_file = None
        for f in downloaded_files:
            if f.name == file_name:
                matched_file = f
                break
        
        if matched_file is None:
            raise FileNotFoundError(f"Downloaded file {file_name} not found in downloaded list")
        
        actual_hash = compute_file_hash(matched_file)
        
        if actual_hash != expected_hash:
            raise ValueError(f"Checksum mismatch for {file_name}: expected {expected_hash}, got {actual_hash}")
    
    return True

def download_dataset(
    dataset_id: str,
    output_dir: Path,
    config_name: Optional[str] = None,
    split: Optional[str] = None
) -> List[Path]:
    """
    Download a dataset from HuggingFace Hub.
    
    Args:
        dataset_id: HuggingFace dataset ID (e.g., 'openai/gsm8k')
        output_dir: Directory to save the dataset files
        config_name: Optional configuration name (e.g., 'main' for gsm8k)
        split: Optional split to download (e.g., 'train', 'test')
    
    Returns:
        List of paths to downloaded files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load dataset
    # Note: load_dataset caches data by default in ~/.cache/huggingface
    # For this task, we want to ensure we have the data available and verify it.
    # We will load it, then save the raw parquet/csv files to our data/raw directory
    # to perform checksum verification against a manifest of those specific files.
    
    try:
        ds = load_dataset(dataset_id, config_name=config_name, split=split, trust_remote_code=True)
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset {dataset_id}: {e}")
    
    # Save to parquet to have a single file for checksum verification
    # This is a common pattern for HuggingFace datasets
    file_name = f"{dataset_id.replace('/', '_')}.parquet"
    if config_name:
        file_name = f"{dataset_id.replace('/', '_')}_{config_name}.parquet"
    if split:
        file_name = f"{dataset_id.replace('/', '_')}_{config_name}_{split}.parquet"
    
    output_file = output_dir / file_name
    
    # Save the dataset
    ds.to_parquet(str(output_file))
    
    return [output_file]

def download_all_datasets(base_path: Path, manifest_path: Path) -> Dict[str, List[Path]]:
    """
    Download all datasets listed in the manifest and verify checksums.
    
    Args:
        base_path: Project root path
        manifest_path: Path to the state manifest JSON
    
    Returns:
        Dictionary mapping dataset names to lists of downloaded file paths.
    """
    ensure_data_dirs(base_path)
    manifest = load_manifest(manifest_path)
    
    downloaded_datasets = {}
    
    # Expected datasets based on T012 description: GSM8K and MATH
    # The manifest should define these.
    datasets_to_download = [
        {"id": "openai/gsm8k", "config": "main", "splits": ["train", "test"]},
        {"id": "hendrycks/math", "config": None, "splits": ["train", "test"]} # Note: MATH might have different config
    ]
    
    for ds_info in datasets_to_download:
        ds_id = ds_info["id"]
        config = ds_info.get("config")
        splits = ds_info.get("splits", ["train", "test"])
        
        print(f"Downloading {ds_id}...")
        all_files = []
        
        for split in splits:
            try:
                files = download_dataset(ds_id, base_path / "data" / "raw", config_name=config, split=split)
                all_files.extend(files)
                print(f"  Downloaded split {split}: {files}")
            except Exception as e:
                print(f"  Error downloading split {split}: {e}")
                # Continue to next split or fail? Fail loudly per constraints.
                raise e
        
        # Verify checksums
        try:
            verify_checksums(ds_id, all_files, manifest)
            print(f"  Checksums verified for {ds_id}")
        except Exception as e:
            print(f"  Checksum verification failed for {ds_id}: {e}")
            raise e
        
        downloaded_datasets[ds_id] = all_files
    
    return downloaded_datasets

def main():
    """Main entry point for the dataset downloader."""
    # Determine project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent.parent
    
    manifest_path = project_root / "state" / "manifest.json"
    
    if not manifest_path.exists():
        print(f"Error: Manifest not found at {manifest_path}")
        print("Please ensure the state/manifest.json file exists with checksums for GSM8K and MATH.")
        sys.exit(1)
    
    print(f"Starting dataset download. Base path: {project_root}")
    print(f"Manifest path: {manifest_path}")
    
    try:
        results = download_all_datasets(project_root, manifest_path)
        print("Download and verification completed successfully.")
        for ds_name, files in results.items():
            print(f"  {ds_name}: {len(files)} files")
    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()