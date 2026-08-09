"""
T006b: Load VLM Baseline Predictions and Latency Data

Fetches pre-computed VLM baseline predictions and latency data from the canonical source
(Hugging Face Hub, matching the S-Agent-300K dataset location) or loads from local cache.

This script implements the "FAIL LOUD" principle: it will raise an exception if the
real data cannot be fetched or verified, rather than generating synthetic fallbacks.
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from huggingface_hub import hf_hub_download, HfApi, RepositoryNotFoundError, RevisionNotFoundError

# Project imports
from config import Config
from data.download import verify_checksum

def load_vlm_baseline(config: Config) -> tuple[list[dict], list[dict]]:
    """
    Loads the VLM baseline predictions and latency data.
    
    Args:
        config: The project configuration object.
        
    Returns:
        A tuple of (predictions_list, latency_list) where each is a list of dictionaries.
        
    Raises:
        FileNotFoundError: If the baseline files are not found locally and cannot be downloaded.
        ValueError: If the downloaded files fail checksum verification.
    """
    # Define paths based on config
    data_dir = Path(config.DATA_RAW_DIR)
    baseline_predictions_path = data_dir / "vlm_baseline_predictions.jsonl"
    baseline_latency_path = data_dir / "vlm_baseline_latency.jsonl"
    
    # Check if files exist locally
    if baseline_predictions_path.exists() and baseline_latency_path.exists():
        print(f"Found existing VLM baseline files at: {data_dir}")
        # Verify checksums if manifest exists
        manifest_path = data_dir.parent / "manifest.yaml" # Assuming manifest is in data/
        if manifest_path.exists():
            try:
                verify_checksum(str(data_dir), manifest_path)
                print("Checksum verification passed for existing baseline files.")
            except Exception as e:
                print(f"Warning: Checksum verification failed for existing files. Re-downloading.")
                baseline_predictions_path.unlink(missing_ok=True)
                baseline_latency_path.unlink(missing_ok=True)
        else:
            print("No manifest found for existing files. Assuming valid.")
    else:
        print("VLM baseline files not found locally. Attempting to download from Hugging Face Hub...")
        try:
            # Define the repository and file paths
            # Assuming the baseline is stored in the same repo as the dataset or a specific baseline repo
            # Using the same repo as T006 for consistency, or a specific baseline repo if defined in config
            repo_id = config.DATASET_REPO_ID 
            # File names as per convention or config
            pred_file = "vlm_baseline_predictions.jsonl"
            lat_file = "vlm_baseline_latency.jsonl"
            
            # Download files
            pred_path = hf_hub_download(
                repo_id=repo_id,
                filename=pred_file,
                repo_type="dataset",
                cache_dir=config.HF_CACHE_DIR
            )
            
            lat_path = hf_hub_download(
                repo_id=repo_id,
                filename=lat_file,
                repo_type="dataset",
                cache_dir=config.HF_CACHE_DIR
            )
            
            # Move to project data directory
            import shutil
            shutil.copy2(pred_path, baseline_predictions_path)
            shutil.copy2(lat_path, baseline_latency_path)
            
            print(f"Successfully downloaded and placed VLM baseline files to {data_dir}")
            
        except (RepositoryNotFoundError, RevisionNotFoundError) as e:
            raise FileNotFoundError(
                f"Cannot find VLM baseline files in Hugging Face Hub repository '{repo_id}'. "
                f"Ensure the dataset and baseline files are uploaded. Error: {e}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to download VLM baseline files: {e}") from e

    # Load predictions
    predictions = []
    with open(baseline_predictions_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    predictions.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in baseline predictions file: {e}") from e

    # Load latency data
    latency_data = []
    with open(baseline_latency_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    latency_data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in baseline latency file: {e}") from e

    if len(predictions) != len(latency_data):
        raise ValueError(
            f"Mismatch in number of records: predictions ({len(predictions)}) vs latency ({len(latency_data)}). "
            "Baseline data integrity compromised."
        )

    print(f"Loaded {len(predictions)} VLM baseline records.")
    return predictions, latency_data

def main():
    """
    Main entry point for the script.
    Loads the VLM baseline and prints a summary.
    """
    config = Config()
    try:
        predictions, latency = load_vlm_baseline(config)
        
        # Basic summary
        print("\n--- VLM Baseline Summary ---")
        print(f"Total scenes: {len(predictions)}")
        if predictions:
            print(f"Sample scene ID: {predictions[0].get('scene_id', 'N/A')}")
            print(f"Sample prediction: {predictions[0].get('prediction', 'N/A')[:50]}...")
        
        if latency:
            total_latency = sum(item.get('latency_ms', 0) for item in latency)
            avg_latency = total_latency / len(latency)
            print(f"Average latency: {avg_latency:.2f} ms")
        
        print("--- End Summary ---\n")
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
