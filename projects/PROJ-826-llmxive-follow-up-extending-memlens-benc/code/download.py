import hashlib
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional

from datasets import load_dataset


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_memlens_dataset(output_dir: Path) -> Dict[str, Path]:
    """
    Fetch the MemLens dataset from HuggingFace and save it locally.
    
    Returns a dictionary mapping artifact names to their file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load the MemLens dataset from HuggingFace
    # Using the specific dataset name from the MemLens paper repository
    dataset_name = "memlens/memlens-benchmark"
    
    try:
        dataset = load_dataset(dataset_name, split="train")
    except Exception as e:
        # Fallback to a known stable subset if the full dataset fails
        # This ensures the pipeline can proceed with real data
        print(f"Warning: Could not load full dataset ({e}). Attempting fallback...")
        # Try loading a specific configuration if available, or just take a sample
        # For this implementation, we assume the dataset loads successfully or fails loudly.
        # In a real scenario, we might need to check available configs.
        raise RuntimeError(f"Failed to download MemLens dataset: {e}")
    
    # Save the dataset to parquet files for efficient processing
    # The dataset typically contains 'image', 'question', 'answer', 'context'
    artifact_paths = {}
    
    # Save to a single parquet file for the main data
    data_file = output_dir / "memlens_dataset.parquet"
    dataset.to_parquet(str(data_file))
    artifact_paths["dataset"] = data_file
    
    # Also save metadata if available (e.g., splits, stats)
    # For now, we just save the main dataset file
    
    return artifact_paths


def compute_checksums(artifact_paths: Dict[str, Path]) -> Dict[str, str]:
    """Compute SHA-256 checksums for all artifacts."""
    checksums = {}
    for name, path in artifact_paths.items():
        if path.exists():
            checksums[name] = calculate_sha256(path)
        else:
            checksums[name] = "MISSING"
    return checksums


def update_state_file(
    checksums: Dict[str, str], 
    project_root: Path, 
    dataset_dir: Path
) -> None:
    """
    Update the state YAML file with artifact hashes and download status.
    
    Writes to: state/projects/<project_id>.yaml
    """
    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Project ID derived from the directory structure
    project_id = "PROJ-826-llmxive-follow-up-extending-memlens-benc"
    state_file = state_dir / f"{project_id}.yaml"
    
    # Load existing state if it exists
    existing_state = {}
    if state_file.exists():
        with open(state_file, "r") as f:
            existing_state = yaml.safe_load(f) or {}
    
    # Prepare the new state entry for this download run
    # We only update the 'artifacts' section for the download task
    download_state = {
        "downloaded_at": None,  # Could be set to datetime.now().isoformat()
        "dataset_dir": str(dataset_dir),
        "artifacts": {}
    }
    
    for name, hash_val in checksums.items():
        download_state["artifacts"][name] = {
            "path": str(dataset_dir / (name + ".parquet")),
            "sha256": hash_val
        }
    
    # Update the main state structure
    existing_state["download_status"] = "completed"
    existing_state["last_updated"] = None  # Can be set dynamically
    existing_state["artifacts"] = download_state["artifacts"]
    
    with open(state_file, "w") as f:
        yaml.dump(existing_state, f, default_flow_style=False, sort_keys=False)


def main() -> int:
    """
    Main entry point for downloading the MemLens dataset and updating state.
    
    Returns 0 on success, 1 on failure.
    """
    # Determine project root (assuming script is in code/)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    output_dir = project_root / "data" / "raw" / "memlens"
    
    print(f"Downloading MemLens dataset to {output_dir}...")
    
    try:
        # Download the dataset
        artifact_paths = download_memlens_dataset(output_dir)
        
        # Compute checksums
        checksums = compute_checksums(artifact_paths)
        
        # Update state file
        update_state_file(checksums, project_root, output_dir)
        
        print("Download completed successfully.")
        print("State file updated with artifact hashes.")
        
        return 0
        
    except Exception as e:
        print(f"Error during download: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())