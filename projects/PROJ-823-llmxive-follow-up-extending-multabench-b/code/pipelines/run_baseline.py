"""
Pipeline script to generate frozen embeddings for ALL available datasets.
Implements US1: CPU-Tractable Baseline Generation.

Outputs:
    data/processed/embeddings_{run_id}.parquet
"""
import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
import torch
from tqdm import tqdm

# Project imports based on provided API surface
# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import CONFIG, get_data_path, get_processed_path
from utils.logging import get_logger, log_info, log_warning, log_error, log_debug
from utils.memory_monitor import MemoryMonitor, get_process_memory_mb
from embeddings.generator import EmbeddingGenerator
from embeddings.utils import batch_process_embeddings
from data_loader import DataLoader

logger = get_logger(__name__)

def generate_run_id() -> str:
    """Generate a deterministic run_id based on config and timestamp."""
    # For FR-001 determinism, we include the seed and a fixed timestamp component
    # In production, this might be a git commit hash or specific config hash
    seed = CONFIG.get('random_seed', 42)
    # Use a fixed date format for reproducibility in the "run_id" concept if needed,
    # but usually run_id includes a timestamp to distinguish runs.
    # Per task: "deterministic re-computation". We'll use a hash of the config + seed.
    config_str = f"seed_{seed}_version_1.0"
    run_id = hashlib.sha256(config_str.encode()).hexdigest()[:8]
    return run_id

def load_dataset_list() -> List[Dict[str, Any]]:
    """
    Loads the list of available datasets from the data directory or config.
    Returns a list of dicts with 'dataset_id' and 'path'.
    """
    data_path = get_data_path()
    datasets = []
    
    # Check for a manifest file first
    manifest_path = data_path / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            if isinstance(manifest, list):
                return manifest
    
    # Fallback: Scan directories in data_path
    if not data_path.exists():
        log_error(f"Data directory not found: {data_path}")
        return []

    for item in data_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Assume directory name is dataset_id
            datasets.append({
                "dataset_id": item.name,
                "path": str(item)
            })
    
    log_info(f"Discovered {len(datasets)} datasets in {data_path}")
    return datasets

def process_single_dataset(
    dataset_info: Dict[str, Any],
    generator: EmbeddingGenerator,
    run_id: str
) -> Optional[pd.DataFrame]:
    """
    Process a single dataset to generate embeddings.
    Handles errors gracefully and logs memory usage.
    """
    dataset_id = dataset_info.get('dataset_id', 'unknown')
    data_path = dataset_info.get('path')
    
    log_info(f"Processing dataset: {dataset_id}")
    
    try:
        # Load data
        loader = DataLoader()
        data = loader.load(data_path)
        
        if data is None or len(data) == 0:
            log_warning(f"Dataset {dataset_id} is empty or could not be loaded. Skipping.")
            return None

        # Check for zero variance or missing fields (T016 preparation)
        # If no text/image columns, skip or log warning
        has_text = 'text' in data.columns or 'description' in data.columns
        has_image = 'image' in data.columns or 'image_path' in data.columns
        
        if not has_text and not has_image:
            log_warning(f"Dataset {dataset_id} has no text or image columns. Skipping embedding generation.")
            return None

        # Prepare data for generator
        # Assuming generator expects lists of text and/or image paths
        text_data = data.get('text', data.get('description', [])).tolist() if has_text else []
        image_data = data.get('image', data.get('image_path', [])).tolist() if has_image else []

        if not text_data and not image_data:
            log_warning(f"Dataset {dataset_id} has no valid text or image data after extraction. Skipping.")
            return None

        # Generate embeddings using the batch processor
        # The generator handles the model loading and inference
        embeddings, metadata = batch_process_embeddings(
            generator=generator,
            text_data=text_data,
            image_data=image_data,
            logger=logger
        )

        if embeddings is None or len(embeddings) == 0:
            log_warning(f"No embeddings generated for {dataset_id}.")
            return None

        # Construct result DataFrame
        results = []
        for i, emb in enumerate(embeddings):
            row = {
                'run_id': run_id,
                'dataset_id': dataset_id,
                'row_index': i,
                'embedding': emb,
                'source_type': 'text' if has_text and not has_image else ('image' if has_image and not has_text else 'mixed')
            }
            # Add original row data if needed for traceability
            if i < len(data):
                row['original_data_hash'] = hashlib.md5(str(data.iloc[i]).encode()).hexdigest()
            
            results.append(row)

        df = pd.DataFrame(results)
        log_info(f"Successfully generated {len(df)} embeddings for {dataset_id}")
        return df

    except Exception as e:
        log_error(f"Error processing dataset {dataset_id}: {str(e)}", exc_info=True)
        return None

def main():
    """Main entry point for the baseline generation pipeline."""
    logger.info("Starting Baseline Embedding Generation Pipeline")
    
    # Setup
    run_id = generate_run_id()
    log_info(f"Run ID: {run_id}")
    
    # Initialize memory monitor
    memory_monitor = MemoryMonitor()
    memory_monitor.start()
    
    # Initialize generator
    # The generator is configured in config.py for CPU usage
    generator = EmbeddingGenerator(config=CONFIG)
    
    # Load dataset list
    datasets = load_dataset_list()
    if not datasets:
        log_error("No datasets found to process. Exiting.")
        return 1
    
    log_info(f"Found {len(datasets)} datasets to process.")
    
    all_results = []
    successful_datasets = 0
    failed_datasets = 0
    
    # Process each dataset
    for dataset_info in tqdm(datasets, desc="Processing Datasets"):
        result_df = process_single_dataset(dataset_info, generator, run_id)
        
        if result_df is not None:
            all_results.append(result_df)
            successful_datasets += 1
        else:
            failed_datasets += 1
        
        # Periodic memory check
        mem_mb = get_process_memory_mb()
        if mem_mb > 7000: # 7GB threshold
            log_warning(f"Memory usage high: {mem_mb:.1f} MB. Consider reducing batch size in config.")
            # Optional: Force GC
            import gc
            gc.collect()
    
    memory_monitor.stop()
    total_memory_mb = memory_monitor.get_peak_memory_mb()
    log_info(f"Pipeline completed. Peak memory usage: {total_memory_mb:.1f} MB")
    
    if not all_results:
        log_error("No embeddings were generated. Exiting.")
        return 1
    
    # Concatenate all results
    final_df = pd.concat(all_results, ignore_index=True)
    
    # Ensure embedding column is object type for parquet compatibility with numpy arrays
    # Or convert to list of lists if the parquet engine requires it
    # PyArrow handles numpy arrays in object columns well, but let's be safe
    final_df['embedding'] = final_df['embedding'].apply(lambda x: x.tolist() if isinstance(x, np.ndarray) else x)
    
    # Create output directory
    output_dir = get_processed_path()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / f"embeddings_{run_id}.parquet"
    
    # Save to parquet
    final_df.to_parquet(output_path, index=False)
    
    log_info(f"Embeddings saved to: {output_path}")
    log_info(f"Total records: {len(final_df)}")
    log_info(f"Datasets processed: {successful_datasets}/{len(datasets)}")
    
    # Write metadata summary
    metadata_path = output_dir / f"embeddings_{run_id}_metadata.json"
    metadata = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "total_datasets": len(datasets),
        "successful_datasets": successful_datasets,
        "failed_datasets": failed_datasets,
        "total_records": len(final_df),
        "peak_memory_mb": total_memory_mb,
        "config": {
            "random_seed": CONFIG.get('random_seed'),
            "batch_size": CONFIG.get('batch_size', 32),
            "model_names": generator.model_names
        }
    }
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info("Baseline generation pipeline finished successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
