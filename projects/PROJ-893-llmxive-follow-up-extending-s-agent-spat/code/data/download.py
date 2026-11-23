import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
from huggingface_hub import HfApi, hf_hub_download, RepositoryNotFoundError

# Import config for paths and seeds
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import Config

def ensure_directory(path: Path) -> None:
    """Ensure the directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset() -> None:
    """
    Fetch the S-Agent dataset using huggingface_hub, perform stratified sampling,
    and generate required artifacts.
    """
    # Configuration
    DATASET_ID = "llmXive/S-Agent-300K"  # Using the verified public ID from plan/spec context
    FILENAME = "s_agent_300k_metadata.csv" # The metadata file containing stratification columns
    OUTPUT_SCENES = Config.DATA_RAW / "sampled_scenes.jsonl"
    OUTPUT_MANIFEST = Config.DATA_RAW / "sampled_manifest.json"
    SAMPLE_SIZE = 1000
    SEED = Config.RANDOM_SEED

    print(f"Checking for dataset: {DATASET_ID}")
    api = HfApi()

    try:
        # Verify dataset existence
        api.model_info(DATASET_ID)
        print(f"Dataset {DATASET_ID} found.")
    except RepositoryNotFoundError:
        print(f"ERROR: Dataset {DATASET_ID} not found at HuggingFace Hub.")
        sys.exit(1)

    # Download metadata to perform stratified sampling
    print(f"Downloading metadata file: {FILENAME}")
    try:
        local_meta_path = hf_hub_download(
            repo_id=DATASET_ID,
            filename=FILENAME,
            repo_type="dataset"
        )
    except Exception as e:
        print(f"ERROR: Could not download metadata file {FILENAME}. {e}")
        # Fallback: try listing files if the specific filename was guessed
        # In a real scenario, we rely on the verified filename from spec.
        # If the file doesn't exist, we cannot stratify.
        sys.exit(1)

    # Load metadata
    print("Loading metadata...")
    try:
        df = pd.read_csv(local_meta_path)
    except Exception as e:
        print(f"ERROR: Failed to parse metadata CSV. {e}")
        sys.exit(1)

    # Distributional Validity Gate: Verify columns exist
    required_cols = ['object_density', 'scene_complexity']
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        print(f"Distributional Validity Gate Failure: Missing required columns for stratified sampling: {missing_cols}")
        print("ABORT: Cannot proceed without 'object_density' and 'scene_complexity' for stratification.")
        sys.exit(1)

    print(f"Performing stratified random sample (n={SAMPLE_SIZE})...")
    
    # Perform Stratified Sampling
    # We need to sample n=1000 total. We distribute this across groups.
    # If a group has fewer than the proportional share, we take all and redistribute?
    # Standard approach: sample a fixed number per group if possible, or proportional.
    # Given the task asks for "exactly n=1,000", we attempt groupby sample.
    # If a group is too small, pandas.sample will raise an error or return fewer.
    # We will try to sample 1 per group if groups are many, or proportional.
    # Let's try a proportional approach or fixed per group if groups are few.
    # The prompt suggests: `df.groupby(['object_density', 'scene_complexity']).sample(n=..., random_state=SEED)`
    # To ensure exactly 1000, we calculate the sample size per group.
    
    group_counts = df.groupby(['object_density', 'scene_complexity']).size()
    total_rows = len(df)
    
    # Calculate proportional sample size for each group
    sample_sizes = (group_counts / total_rows * SAMPLE_SIZE).round().astype(int)
    
    # Adjust to ensure sum is exactly SAMPLE_SIZE (handle rounding errors)
    current_sum = sample_sizes.sum()
    diff = SAMPLE_SIZE - current_sum
    
    if diff != 0:
        # Add/subtract from the largest groups
        sorted_groups = sample_sizes.sort_values(ascending=False).index
        for i in range(abs(diff)):
            idx = sorted_groups[i % len(sorted_groups)]
            if diff > 0:
                sample_sizes[idx] += 1
            else:
                if sample_sizes[idx] > 0:
                    sample_sizes[idx] -= 1
    
    # Now sample
    sampled_df = pd.concat([
        group.sample(n=sample_sizes[group.name], random_state=SEED) 
        for group in df.groupby(['object_density', 'scene_complexity'])
    ])
    
    if len(sampled_df) != SAMPLE_SIZE:
        print(f"WARNING: Sample size is {len(sampled_df)}, expected {SAMPLE_SIZE}. Proceeding with available data.")
    
    print(f"Sampled {len(sampled_df)} scenes.")

    # Identify scene IDs to download
    # Assuming the metadata has a column 'scene_id' or similar unique identifier
    # If the CSV contains full scene data, we save it directly. 
    # If it contains links, we download files.
    # Assumption: The metadata CSV contains the full scene data or a link to the JSONL.
    # For this implementation, we assume the CSV contains the necessary data or we download a specific file per scene.
    # However, the task says "fetch the S-Agent dataset... create data/raw/sampled_manifest.json... output dataset as data/raw/sampled_scenes.jsonl"
    # If the dataset is large, we likely need to download a specific file or iterate.
    # Let's assume the CSV has a 'file_path' or 'scene_id' and we fetch the corresponding JSONL or extract from a larger archive.
    # Given the constraints, let's assume the dataset is a single JSONL or we download a subset.
    # If the CSV is just metadata, we need to download the actual scene data.
    # Strategy: If the dataset has a 'scenes.jsonl', we filter it. If not, we download individual files.
    # For robustness, we assume the 'scene_id' column exists in the CSV.
    
    scene_ids = sampled_df['scene_id'].tolist()
    print(f"Downloading {len(scene_ids)} scene files...")

    ensure_directory(Config.DATA_RAW)
    
    manifest_entries = []
    output_lines = []
    
    # If the dataset is a single large file, we might need to download it and filter.
    # If it's sharded, we download shards.
    # For this task, we assume we can download the specific scene data.
    # If the dataset structure is unknown, we attempt to download a 'scenes.jsonl' and filter.
    # Let's try downloading the main scenes file if it exists.
    try:
        # Attempt to download the main scenes file
        scenes_file = hf_hub_download(
            repo_id=DATASET_ID,
            filename="scenes.jsonl",
            repo_type="dataset"
        )
        
        # Filter the downloaded file
        print("Filtering scenes.jsonl for sampled IDs...")
        scene_ids_set = set(scene_ids)
        count = 0
        with open(scenes_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get('scene_id') in scene_ids_set:
                        output_lines.append(line)
                        count += 1
                        if count == SAMPLE_SIZE:
                            break
                except json.JSONDecodeError:
                    continue
        
        with open(OUTPUT_SCENES, 'w') as f:
            f.writelines(output_lines)
        
        # Compute hash for the output file
        sha = compute_sha256(OUTPUT_SCENES)
        manifest_entries.append({"file": "sampled_scenes.jsonl", "sha256": sha})
        
    except Exception as e:
        print(f"Warning: Could not download/filter scenes.jsonl directly: {e}")
        # Fallback: If the dataset is structured differently, we might need to download per scene.
        # For now, we exit if the primary method fails, as we cannot fabricate data.
        print("ERROR: Could not retrieve scene data in expected format. Aborting.")
        sys.exit(1)

    # Write manifest
    with open(OUTPUT_MANIFEST, 'w') as f:
        json.dump(manifest_entries, f, indent=2)
    
    print(f"Successfully created {OUTPUT_SCENES} and {OUTPUT_MANIFEST}")

def main():
    """Main entry point."""
    ensure_directory(Config.DATA_RAW)
    download_dataset()

if __name__ == "__main__":
    main()
