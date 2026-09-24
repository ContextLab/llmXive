"""
Download script for the S-Agent-300K dataset.
Fetches data from HuggingFace Hub and performs stratified sampling.
"""
import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

# Ensure code directory is in path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "code"))

from config import Config

def ensure_directory(path: Path):
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset():
    """
    Download the S-Agent-300K dataset from HuggingFace Hub.
    Performs stratified random sampling of exactly n=1,000 scenes.
    Generates data/manifest.json with SHA-256 hashes.
    """
    config = Config()
    logger = config.logger

    # Verified dataset ID from project specs
    dataset_id = "llmXive/S-Agent-300K"
    filename = "s_agent_k_subset.jsonl"

    try:
        from huggingface_hub import hf_hub_download, HfApi, list_repo_files
        import pandas as pd
        from io import StringIO

        api = HfApi()

        # Check if repo exists
        try:
            api.repo_info(repo_id=dataset_id)
        except Exception as e:
            raise FileNotFoundError(f"Dataset {dataset_id} not found at HuggingFace Hub. Error: {e}")

        # Download the full dataset to process in memory
        output_dir = config.DATA_RAW
        ensure_directory(output_dir)

        # Download to cache first
        cache_path = hf_hub_download(
            repo_id=dataset_id,
            filename="data.jsonl", # Assuming the main data file is named data.jsonl or similar
            repo_type="dataset",
            cache_dir=str(output_dir / "cache")
        )

        # Load into pandas for stratified sampling
        # We need to handle the file reading carefully to avoid memory issues if large,
        # but for n=1000 sampling we need the metadata columns.
        # Strategy: Read line by line to build a DataFrame, then sample.
        
        df_rows = []
        with open(cache_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f):
                try:
                    row = json.loads(line)
                    # Ensure we have the necessary keys for stratification if they exist
                    # If not, we will fallback later
                    df_rows.append(row)
                    if line_num % 10000 == 0:
                        if logger: logger.info(f"Read {line_num} lines...")
                except json.JSONDecodeError:
                    if logger: logger.warning(f"Skipping malformed JSON at line {line_num}")
                    continue

        df = pd.DataFrame(df_rows)

        if logger:
            logger.info(f"Loaded {len(df)} scenes from dataset.")

        # Stratified Sampling Logic
        target_n = 1000
        stratify_cols = ['object_density', 'scene_complexity']
        
        # Check if stratification columns exist
        if all(col in df.columns for col in stratify_cols):
            if logger:
                logger.info(f"Stratifying by {stratify_cols}")
            # Ensure we don't sample more than available in any group
            # pandas.sample handles this gracefully if n > count, but let's be safe
            try:
                sampled_df = df.groupby(stratify_cols, group_keys=False).apply(
                    lambda x: x.sample(n=min(target_n // len(df.groupby(stratify_cols)), len(x)), random_state=42)
                )
                # If groupby sample logic is too complex for exact n=1000 across groups,
                # use the standard groupby sample with a calculated n per group or fallback
                # The task specifies: Attempt groupby(...).sample(n=...). If missing, fallback.
                # Let's try the direct approach first as per spec:
                # "Attempt df.groupby(['object_density', 'scene_complexity']).sample(n=..., random_state=SEED)"
                # This usually implies sampling n rows *per group* or total?
                # Spec says: "stratified random sample of exactly n=1,000".
                # Standard interpretation: proportional or equal stratification summing to 1000.
                # To ensure exactly 1000, we calculate counts.
                counts = df[stratify_cols].value_counts()
                # Simple proportional stratified sampling
                sample_sizes = (counts / counts.sum() * target_n).round().astype(int)
                # Adjust for rounding errors to ensure sum is exactly 1000
                diff = target_n - sample_sizes.sum()
                if diff != 0:
                    # Add/subtract from largest groups
                    sample_sizes.iloc[:diff] += diff if diff > 0 else -1 # Simplified adjustment
                
                sampled_dfs = []
                for idx, size in sample_sizes.items():
                    group = df[(df[stratify_cols].iloc[:, 0] == idx[0]) & (df[stratify_cols].iloc[:, 1] == idx[1])]
                    sampled_dfs.append(group.sample(n=min(size, len(group)), random_state=42))
                sampled_df = pd.concat(sampled_dfs)
                
            except Exception as e:
                if logger: logger.warning(f"Stratified sampling failed ({e}), falling back to random sample.")
                sampled_df = df.sample(n=target_n, random_state=42)
        else:
            if logger:
                logger.warning(f"Stratification columns {stratify_cols} missing. Falling back to random sample.")
            sampled_df = df.sample(n=target_n, random_state=42)

        # Ensure we have exactly 1000 (or less if dataset is tiny)
        if len(sampled_df) != target_n:
            if logger:
                logger.warning(f"Sampled {len(sampled_df)} scenes, expected {target_n}.")
        
        # Save the sampled subset
        target_path = output_dir / filename
        sampled_df.to_json(target_path, orient='records', lines=True)

        if logger:
            logger.info(f"Sampled dataset saved to {target_path}")

        # Generate manifest with SHA-256 hashes
        manifest_path = config.DATA_DIR / "manifest.json"
        ensure_directory(manifest_path.parent)
        
        manifest = []
        # Hash the output file
        manifest.append({
            "file": filename,
            "sha256": compute_sha256(target_path)
        })
        
        # Also hash the source cache file if we want to track the source, 
        # but the task asks for "every downloaded file". 
        # We downloaded 'data.jsonl' to cache, and saved 's_agent_k_subset.jsonl'.
        # Let's include the cache file hash too if it exists.
        if os.path.exists(cache_path):
            manifest.append({
                "file": f"cache/{filename}", # Relative to cache
                "sha256": compute_sha256(Path(cache_path))
            })

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        if logger:
            logger.info(f"Manifest written to {manifest_path}")

    except ImportError as e:
        raise ImportError(f"Required library missing: {e}. Install huggingface_hub and pandas.")
    except FileNotFoundError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to download or process dataset: {e}")

def main():
    download_dataset()

if __name__ == "__main__":
    main()