#!/usr/bin/env python
"""
Implement Robust Real Data Streaming Fetch for ImageNet-1K and LAION-400M.

Replaces pre-fetched assumption with a strict, fail-loud real data fetcher.
- Uses datasets.load_dataset(..., streaming=True)
- Computes SHA256 of the raw stream buffer for byte-level reproducibility
- Writes data to data/raw/ as Parquet files
- Stores stream hashes in state/artifact_hashes.yaml
- Fails loudly (exit 1) if fetch fails; NO synthetic fallback
"""
import argparse
import json
import hashlib
import sys
import time
from pathlib import Path
import logging
from typing import Dict, Any, Optional, List, Iterator
import io

import pandas as pd
from datasets import load_dataset
import pyarrow as pa
import pyarrow.parquet as pq

from utils.config import get_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Known expert IDs for validation (from DanceOPD config)
KNOWN_EXPERT_IDS = {
    "expert_0", "expert_1", "expert_2", "expert_3", "expert_4",
    "expert_5", "expert_6", "expert_7", "expert_8", "expert_9"
}

# Target sample size (configurable via config)
TARGET_SAMPLES = 2500

def calculate_sha256_stream(stream: Iterator[bytes]) -> str:
    """
    Compute SHA256 hash of a byte stream without loading it entirely into memory.
    """
    sha256_hash = hashlib.sha256()
    for chunk in stream:
        sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def fetch_real_data(
    source_name: str,
    dataset_id: str,
    output_path: Path,
    target_n: int,
    config: Any,
    stream_hash_key: str
) -> Dict[str, Any]:
    """
    Fetch real data from a streaming dataset source.
    
    Args:
        source_name: Human-readable name (e.g., "imagenet", "laion")
        dataset_id: HuggingFace dataset ID (e.g., "huggan/imagenet-1k")
        output_path: Path to write the Parquet file
        target_n: Number of samples to fetch
        config: Configuration object
        stream_hash_key: Key for storing the stream hash in state/artifact_hashes.yaml
    
    Returns:
        Dictionary with fetch metadata (status, hash, sample_count, etc.)
    
    Raises:
        RuntimeError: If fetch fails (network error, empty stream, etc.)
    """
    logger.info(f"Starting fetch for {source_name} from {dataset_id}...")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load dataset with streaming
        # For ImageNet-1K, we use the huggan/imagenet-1k dataset
        # For LAION, we use laion/laion400m (filtered for image/text ratio)
        ds = load_dataset(dataset_id, split="train", streaming=True)
        
        # Collect samples up to target_n
        samples = []
        stream_buffer = io.BytesIO()
        sample_count = 0
        
        logger.info(f"Streaming {target_n} samples from {dataset_id}...")
        
        for idx, item in enumerate(ds):
            if sample_count >= target_n:
                break
            
            # Process item based on dataset type
            if "imagenet" in dataset_id:
                # ImageNet format: {'image': PIL.Image, 'label': int}
                if "image" not in item or item["image"] is None:
                    continue
                
                # Convert image to bytes for streaming hash
                img_bytes = io.BytesIO()
                item["image"].save(img_bytes, format="JPEG")
                img_bytes = img_bytes.getvalue()
                
                # Add to stream buffer for hashing
                stream_buffer.write(img_bytes)
                
                # Store sample data
                samples.append({
                    "image_bytes": img_bytes,
                    "label": item.get("label", -1),
                    "source": source_name
                })
            
            elif "laion" in dataset_id:
                # LAION format: {'url': str, 'text': str, 'image': PIL.Image, ...}
                if "image" not in item or item["image"] is None:
                    continue
                
                # Convert image to bytes
                img_bytes = io.BytesIO()
                item["image"].save(img_bytes, format="JPEG")
                img_bytes = img_bytes.getvalue()
                
                stream_buffer.write(img_bytes)
                
                samples.append({
                    "image_bytes": img_bytes,
                    "url": item.get("url", ""),
                    "text": item.get("text", ""),
                    "source": source_name
                })
            
            sample_count += 1
            
            if sample_count % 100 == 0:
                logger.info(f"  Collected {sample_count} samples...")
        
        # Close stream buffer and compute hash
        stream_buffer.seek(0)
        stream_hash = calculate_sha256_stream(stream_buffer)
        
        if sample_count == 0:
            raise RuntimeError(f"No samples fetched from {dataset_id}")
        
        if sample_count < target_n:
            logger.warning(f"Only fetched {sample_count} samples from {dataset_id} (target: {target_n})")
        
        # Convert to DataFrame and write to Parquet
        logger.info(f"Writing {sample_count} samples to {output_path}...")
        
        # Create DataFrame from samples
        df_data = {
            "image_bytes": [s["image_bytes"] for s in samples],
            "source": [s["source"] for s in samples]
        }
        
        # Add dataset-specific columns
        if "imagenet" in dataset_id:
            df_data["label"] = [s["label"] for s in samples]
        elif "laion" in dataset_id:
            df_data["url"] = [s["url"] for s in samples]
            df_data["text"] = [s["text"] for s in samples]
        
        df = pd.DataFrame(df_data)
        
        # Write to Parquet
        df.to_parquet(output_path, index=False)
        
        logger.info(f"Successfully wrote {sample_count} samples to {output_path}")
        
        # Store stream hash in state/artifact_hashes.yaml
        state_dir = Path(config.get_path("STATE_DIR"))
        state_dir.mkdir(parents=True, exist_ok=True)
        hash_file = state_dir / "artifact_hashes.yaml"
        
        # Read existing hashes or create new
        existing_hashes = {}
        if hash_file.exists():
            import yaml
            with open(hash_file, "r") as f:
                existing_hashes = yaml.safe_load(f) or {}
        
        # Update with new hash
        existing_hashes[stream_hash_key] = {
            "hash": stream_hash,
            "dataset": dataset_id,
            "samples": sample_count,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        # Write updated hashes
        import yaml
        with open(hash_file, "w") as f:
            yaml.dump(existing_hashes, f, default_flow_style=False)
        
        logger.info(f"Stream hash stored in {hash_file}")
        
        return {
            "status": "success",
            "source": source_name,
            "dataset_id": dataset_id,
            "samples_fetched": sample_count,
            "stream_hash": stream_hash,
            "output_path": str(output_path),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    
    except Exception as e:
        logger.error(f"Failed to fetch data from {dataset_id}: {str(e)}")
        raise RuntimeError(f"Data fetch failed for {source_name}: {str(e)}")

def validate_checksums(data_dir: Path, checksums_file: Path) -> bool:
    """
    Verify existence and checksums of pre-fetched raw datasets.
    (Kept for backward compatibility with T012)
    """
    if not checksums_file.exists():
        logger.error(f"Checksums file not found: {checksums_file}")
        return False

    with open(checksums_file, "r") as f:
        expected_checksums = json.load(f)

    all_valid = True
    for filename, expected_hash in expected_checksums.items():
        file_path = data_dir / filename
        if not file_path.exists():
            logger.error(f"Missing file: {file_path}")
            all_valid = False
            continue

        actual_hash = calculate_sha256_stream(open(file_path, "rb"))
        if actual_hash != expected_hash:
            logger.error(f"Checksum mismatch for {filename}: expected {expected_hash}, got {actual_hash}")
            all_valid = False
        else:
            logger.info(f"Verified {filename}: {actual_hash}")

    return all_valid

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    with open(file_path, "rb") as f:
        return calculate_sha256_stream(f)

def main():
    config = get_config()
    data_dir = Path(config.get_path("RAW_DATA_DIR"))
    results_dir = Path(config.get_path("RESULTS_DIR"))
    
    # Ensure directories exist
    data_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Fetch ImageNet-1K
    imagenet_output = data_dir / "imagenet_samples.parquet"
    imagenet_result = None
    
    try:
        imagenet_result = fetch_real_data(
            source_name="imagenet",
            dataset_id="huggan/imagenet-1k",
            output_path=imagenet_output,
            target_n=TARGET_SAMPLES,
            config=config,
            stream_hash_key="source_stream_hash_imagenet"
        )
        logger.info(f"ImageNet fetch result: {imagenet_result['samples_fetched']} samples")
    except Exception as e:
        logger.error(f"ImageNet fetch failed: {str(e)}")
    
    # Fetch LAION-400M (filtered)
    laion_output = data_dir / "laion_samples.parquet"
    laion_result = None
    
    try:
        # Use a filtered subset of LAION for efficiency
        laion_result = fetch_real_data(
            source_name="laion",
            dataset_id="laion/laion400m",
            output_path=laion_output,
            target_n=TARGET_SAMPLES,
            config=config,
            stream_hash_key="source_stream_hash_laion"
        )
        logger.info(f"LAION fetch result: {laion_result['samples_fetched']} samples")
    except Exception as e:
        logger.error(f"LAION fetch failed: {str(e)}")
    
    # Check if both fetches succeeded
    if imagenet_result is None or laion_result is None:
        logger.error("One or both data fetches failed. Exiting with code 1.")
        
        # Write failure report
        validation_report = results_dir / "data_fetch_validation.json"
        report = {
            "status": "failed",
            "imagenet": imagenet_result,
            "laion": laion_result,
            "error": "One or more fetches failed",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        with open(validation_report, "w") as f:
            json.dump(report, f, indent=2)
        
        sys.exit(1)
    
    # Write success report
    validation_report = results_dir / "data_fetch_validation.json"
    report = {
        "status": "verified",
        "imagenet": imagenet_result,
        "laion": laion_result,
        "total_samples": imagenet_result["samples_fetched"] + laion_result["samples_fetched"],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    with open(validation_report, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {validation_report}")
    logger.info(f"Total samples fetched: {report['total_samples']}")
    
    # Verify minimum sample requirement (FR-001)
    if report["total_samples"] < 1000:
        logger.error(f"Total samples ({report['total_samples']}) is below minimum requirement (1000). Exiting with code 1.")
        sys.exit(1)
    
    logger.info("Data fetch completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
