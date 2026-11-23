#!/usr/bin/env python
"""
Robust Real Data Streaming Fetch (T042)

Checks for data availability in two tiers:
1. Pre-fetched: Check for data/raw/imagenet_samples.parquet and data/raw/laion_samples.parquet
2. Stream: If pre-fetched missing, attempt to stream from huggan/imagenet-1k and laion/laion400m.

Constraint: Only exit with code 1 if both tiers fail.
Real Data Only: If streaming, use datasets.load_dataset(..., streaming=True).
Fail Loud: If the stream fails, raise an explicit exception and exit with code 1.
Reproducibility: Compute SHA256 hash of raw stream buffer and store in state/artifact_hashes.yaml.
Target N=2500. Dynamic Adjustment: Warn if < 2500 but >= 1000, exit if < 1000.
"""
import argparse
import json
import hashlib
import sys
import time
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
import pandas as pd
import pyarrow.parquet as pq
from io import BytesIO

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Import from existing project files
try:
    from utils.config import get_config, get_path
except ImportError:
    # Fallback for direct execution
    logger.warning("utils.config not found, using default paths")
    CONFIG = None
else:
    CONFIG = get_config()

# Constants
TARGET_N = 2500
MIN_N = 1000
DATA_RAW_DIR = "data/raw"
STATE_DIR = "state"
ARTIFACT_HASHES_FILE = "state/artifact_hashes.yaml"
VALIDATION_REPORT_FILE = "data/results/data_fetch_validation.json"

# Dataset sources
DATASET_CONFIGS = {
    "imagenet": {
        "name": "huggan/imagenet-1k",
        "output_file": "imagenet_samples.parquet",
        "columns": ["image", "label"],
        "streaming": True
    },
    "laion": {
        "name": "laion/laion400m",
        "output_file": "laion_samples.parquet",
        "columns": ["url", "caption"],
        "streaming": True,
        "filter_key": "url",  # Filter for valid URLs
        "filter_value": None  # Will filter for non-empty
    }
}

def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent

def calculate_sha256_stream(buffer: BytesIO) -> str:
    """Calculate SHA256 hash of a stream buffer."""
    buffer.seek(0)
    sha256_hash = hashlib.sha256()
    for chunk in iter(lambda: buffer.read(8192), b""):
        sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Load a YAML file safely."""
    try:
        import yaml
        if file_path.exists():
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    except ImportError:
        logger.warning("PyYAML not installed, using JSON fallback for state")
        json_path = file_path.with_suffix('.json')
        if json_path.exists():
            with open(json_path, 'r') as f:
                return json.load(f)
        return {}

def save_yaml_file(file_path: Path, data: Dict[str, Any]):
    """Save data to a YAML file safely."""
    try:
        import yaml
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
    except ImportError:
        logger.warning("PyYAML not installed, using JSON fallback for state")
        json_path = file_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)

def check_pre_fetched_data(dataset_name: str, data_dir: Path) -> Tuple[bool, Optional[Path]]:
    """Check if pre-fetched data exists and verify checksums."""
    output_file = DATASET_CONFIGS[dataset_name]["output_file"]
    file_path = data_dir / output_file
    
    if not file_path.exists():
        logger.info(f"Pre-fetched data not found: {file_path}")
        return False, None
    
    # Verify checksum if manifest exists
    manifest_file = data_dir / "checksums.json"
    if manifest_file.exists():
        try:
            with open(manifest_file, 'r') as f:
                checksums = json.load(f)
            expected_hash = checksums.get(output_file)
            if expected_hash:
                actual_hash = calculate_sha256(file_path)
                if actual_hash != expected_hash:
                    logger.warning(f"Checksum mismatch for {output_file}. Expected: {expected_hash}, Got: {actual_hash}")
                    return False, None
                logger.info(f"Checksum verified for {output_file}")
        except Exception as e:
            logger.warning(f"Could not verify checksum: {e}")
    
    logger.info(f"Pre-fetched data found: {file_path}")
    return True, file_path

def stream_dataset(dataset_name: str, target_n: int = TARGET_N) -> Tuple[pd.DataFrame, str]:
    """Stream dataset from Hugging Face and return DataFrame with stream hash."""
    logger.info(f"Starting to stream dataset: {dataset_name}")
    
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("datasets library not installed. Run: pip install datasets")
        raise RuntimeError("datasets library required for streaming")
    
    config = DATASET_CONFIGS[dataset_name]
    dataset_name_full = config["name"]
    
    try:
        # Load dataset in streaming mode
        dataset = load_dataset(
            dataset_name_full,
            streaming=config["streaming"],
            trust_remote_code=True
        )
        
        # Get the first split (usually 'train')
        split_name = next(iter(dataset))
        split_dataset = dataset[split_name]
        
        # Collect samples
        samples = []
        stream_buffer = BytesIO()
        sample_count = 0
        
        logger.info(f"Streaming from {dataset_name_full}...")
        
        for item in split_dataset:
            if sample_count >= target_n:
                break
            
            # Process item based on dataset type
            if dataset_name == "imagenet":
                # ImageNet: convert image to bytes if needed
                if "image" in item and item["image"] is not None:
                    # Convert PIL Image to bytes
                    img_bytes = BytesIO()
                    item["image"].save(img_bytes, format="JPEG")
                    item["image_bytes"] = img_bytes.getvalue()
                    samples.append(item)
                    stream_buffer.write(img_bytes.getvalue())
                    sample_count += 1
            elif dataset_name == "laion":
                # LAION: filter for valid URLs
                if config["filter_key"] in item and item[config["filter_key"]]:
                    samples.append(item)
                    # Write URL and caption to buffer for hashing
                    buffer_data = f"{item[config['filter_key']]}|{item.get('caption', '')}\n".encode()
                    stream_buffer.write(buffer_data)
                    sample_count += 1
            
            # Log progress
            if sample_count % 100 == 0:
                logger.info(f"Streamed {sample_count} samples...")
        
        # Calculate stream hash
        stream_hash = calculate_sha256_stream(stream_buffer)
        logger.info(f"Stream hash for {dataset_name}: {stream_hash}")
        
        # Convert to DataFrame
        if not samples:
            raise ValueError(f"No samples collected from {dataset_name}")
        
        df = pd.DataFrame(samples)
        logger.info(f"Successfully streamed {len(df)} samples from {dataset_name}")
        
        return df, stream_hash
        
    except Exception as e:
        logger.error(f"Failed to stream dataset {dataset_name}: {e}")
        raise RuntimeError(f"Streaming failed for {dataset_name}: {e}")

def validate_checksums(data_dir: Path, dataset_name: str) -> bool:
    """Validate checksums for a dataset."""
    output_file = DATASET_CONFIGS[dataset_name]["output_file"]
    file_path = data_dir / output_file
    
    if not file_path.exists():
        return False
    
    manifest_file = data_dir / "checksums.json"
    if not manifest_file.exists():
        logger.warning(f"No checksum manifest found for {dataset_name}")
        return True  # No manifest to verify against
    
    try:
        with open(manifest_file, 'r') as f:
            checksums = json.load(f)
        
        expected_hash = checksums.get(output_file)
        if not expected_hash:
            logger.warning(f"No checksum found for {output_file} in manifest")
            return True
        
        actual_hash = calculate_sha256(file_path)
        if actual_hash != expected_hash:
            logger.error(f"Checksum mismatch for {output_file}")
            return False
        
        logger.info(f"Checksum verified for {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error validating checksums: {e}")
        return False

def fetch_real_data(dataset_name: str, target_n: int = TARGET_N) -> Tuple[bool, Optional[Path], Optional[str]]:
    """
    Fetch real data with tiered strategy.
    Returns: (success, file_path, stream_hash)
    """
    data_dir = get_project_root() / DATA_RAW_DIR
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Tier 1: Check pre-fetched data
    pre_fetched, file_path = check_pre_fetched_data(dataset_name, data_dir)
    if pre_fetched:
        logger.info(f"Using pre-fetched data for {dataset_name}")
        # Verify checksums
        if validate_checksums(data_dir, dataset_name):
            return True, file_path, None
        else:
            logger.warning("Pre-fetched data checksum verification failed, will try streaming")
    
    # Tier 2: Stream from source
    logger.info(f"Pre-fetched data not available or invalid, streaming {dataset_name}")
    try:
        df, stream_hash = stream_dataset(dataset_name, target_n)
        
        # Validate sample count
        actual_n = len(df)
        if actual_n < MIN_N:
            logger.error(f"Stream yielded only {actual_n} samples (< {MIN_N}). Exiting.")
            raise RuntimeError(f"Insufficient samples: {actual_n} < {MIN_N}")
        elif actual_n < target_n:
            logger.warning(f"Stream yielded {actual_n} samples (< {target_n}). Proceeding with warning.")
        
        # Write to Parquet
        output_file = DATASET_CONFIGS[dataset_name]["output_file"]
        file_path = data_dir / output_file
        
        # Convert any non-serializable columns (like PIL Images) to bytes
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if it contains PIL Images or similar
                try:
                    df[col] = df[col].apply(lambda x: x.tobytes() if hasattr(x, 'tobytes') else x)
                except:
                    pass
        
        df.to_parquet(file_path, index=False)
        logger.info(f"Wrote {actual_n} samples to {file_path}")
        
        # Save checksum
        checksums_file = data_dir / "checksums.json"
        checksums = {}
        if checksums_file.exists():
            with open(checksums_file, 'r') as f:
                checksums = json.load(f)
        
        checksums[output_file] = calculate_sha256(file_path)
        with open(checksums_file, 'w') as f:
            json.dump(checksums, f, indent=2)
        
        return True, file_path, stream_hash
        
    except Exception as e:
        logger.error(f"Failed to fetch real data for {dataset_name}: {e}")
        return False, None, None

def update_artifact_hashes(dataset_name: str, stream_hash: Optional[str]):
    """Update state/artifact_hashes.yaml with stream hash."""
    if not stream_hash:
        return
    
    project_root = get_project_root()
    state_dir = project_root / STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    
    hashes_file = state_dir / ARTIFACT_HASHES_FILE
    existing_hashes = load_yaml_file(hashes_file)
    
    key = f"source_stream_hash_{dataset_name}"
    existing_hashes[key] = stream_hash
    
    save_yaml_file(hashes_file, existing_hashes)
    logger.info(f"Updated artifact hashes for {dataset_name}: {stream_hash}")

def write_validation_report(dataset_name: str, status: str, source_tier: str, file_path: Optional[str] = None):
    """Write validation report to data/results/data_fetch_validation.json."""
    project_root = get_project_root()
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = results_dir / VALIDATION_REPORT_FILE
    
    report = {
        "dataset": dataset_name,
        "status": status,
        "source_tier": source_tier,
        "file_path": str(file_path) if file_path else None,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {report_file}")

def main():
    """Main entry point for data fetching."""
    parser = argparse.ArgumentParser(description="Fetch real data with tiered strategy")
    parser.add_argument("--datasets", nargs='+', default=["imagenet", "laion"],
                      help="Datasets to fetch (imagenet, laion)")
    parser.add_argument("--target-n", type=int, default=TARGET_N,
                      help="Target number of samples per dataset")
    args = parser.parse_args()
    
    logger.info(f"Starting data fetch for datasets: {args.datasets}")
    
    all_success = True
    
    for dataset_name in args.datasets:
        if dataset_name not in DATASET_CONFIGS:
            logger.error(f"Unknown dataset: {dataset_name}")
            all_success = False
            continue
        
        success, file_path, stream_hash = fetch_real_data(dataset_name, args.target_n)
        
        if success:
            logger.info(f"Successfully fetched {dataset_name}")
            if stream_hash:
                update_artifact_hashes(dataset_name, stream_hash)
            write_validation_report(dataset_name, "verified", "stream" if stream_hash else "prefetch", file_path)
        else:
            logger.error(f"Failed to fetch {dataset_name}")
            write_validation_report(dataset_name, "failed", "none", None)
            all_success = False
    
    if not all_success:
        logger.error("One or more datasets failed to fetch")
        sys.exit(1)
    
    logger.info("All datasets fetched successfully")
    sys.exit(0)

if __name__ == "__main__":
    main()
