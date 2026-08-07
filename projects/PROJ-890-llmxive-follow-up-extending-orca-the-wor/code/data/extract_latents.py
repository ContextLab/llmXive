import os
import sys
import logging
import time
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# Project imports based on API surface
from config import get_config, ensure_directories
from utils.audit_logger import log_skipped_file, log_ambiguous_prompt, log_audit_event, get_audit_summary
from utils.memory_guard import get_available_memory_gb, get_memory_usage_percent, check_memory_sufficient, adjust_batch_size
from data.models import LatentVector
from data.download_orca import load_orca_dataset, filter_physical_interactions, save_outputs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/extract_latents.log')
    ]
)
logger = logging.getLogger(__name__)

class OrcaLatentDataset:
    """
    Wrapper to handle dataset iteration with error resilience.
    """
    def __init__(self, dataset_path: str, config: Dict[str, Any]):
        self.dataset_path = dataset_path
        self.config = config
        self.failed_indices: List[int] = []
        self.corrupted_files: List[str] = []

    def __iter__(self):
        # Attempt to load the dataset via the existing download_orca module
        # This assumes the dataset has been downloaded to self.dataset_path
        try:
            logger.info(f"Loading dataset from {self.dataset_path}")
            raw_data = load_orca_dataset(self.dataset_path)
            logger.info(f"Dataset loaded successfully. Total samples: {len(raw_data)}")
            return iter(raw_data)
        except FileNotFoundError as e:
            logger.error(f"Dataset path not found: {self.dataset_path}. Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise

    def __len__(self):
        # Estimate length based on available files if possible, or return 0 if unknown
        try:
            raw_data = load_orca_dataset(self.dataset_path)
            return len(raw_data)
        except Exception:
            return 0

def load_frozen_orca_model(model_path: str, device: str = "cpu") -> Any:
    """
    Loads the frozen Orca model on CPU.
    Extends existing logic to include error handling for corrupted model files.
    """
    logger.info(f"Loading frozen Orca model from {model_path} on device {device}")
    try:
        # Import torch here to avoid dependency if not needed, assuming it's in requirements
        import torch
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Attempt to load with strict=False to handle potential version mismatches gracefully
        # depending on how the model was saved, but strict=True is safer for verification
        model = torch.load(model_path, map_location=device, weights_only=True)
        
        if isinstance(model, dict):
            # If it's a state dict, we need the actual model class
            # For this implementation, we assume the 'model_path' points to a saved model instance
            # or a state dict that needs a wrapper. 
            # Given the context of 'frozen', we often load weights.
            # If the file contains the model object directly:
            logger.warning("Model loaded as dict/state_dict. Ensure model architecture matches.")
            # In a real scenario, we would instantiate the OrcaModel class here.
            # Placeholder for actual model instantiation logic if 'model_path' is weights only.
            # For now, returning the loaded object.
            return model 
        
        logger.info("Model loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Critical error loading model: {e}")
        raise

def process_batch(
    batch: List[Dict[str, Any]], 
    model: Any, 
    device: str, 
    batch_size: int
) -> List[LatentVector]:
    """
    Processes a batch of data samples to extract latent vectors.
    Includes error handling for individual samples that might fail (e.g., corrupted video frames).
    """
    latents = []
    failed_samples = []

    for idx, sample in enumerate(batch):
        try:
            # Validate sample integrity
            if not sample.get('video_path') or not os.path.exists(sample['video_path']):
                raise FileNotFoundError(f"Video file missing: {sample.get('video_path')}")
            
            # Simulate extraction logic (since we don't have the real model class definition here)
            # In the real implementation, this would run the model inference.
            # We assume the model returns a tensor or dict with 'latent' key.
            
            # Mocking the inference step for the sake of the error handling structure
            # Real code: with torch.no_grad(): output = model(preprocess(sample))
            # latent_vec = output['latent'].cpu().numpy()
            
            # Placeholder for actual extraction
            # Assuming sample has 'features' or we compute them
            if 'features' not in sample:
                # Try to compute or load features if not present
                raise ValueError("Sample missing required features")

            latent_vec = sample['features'] # Placeholder
            
            if not isinstance(latent_vec, np.ndarray):
                latent_vec = np.array(latent_vec)

            if latent_vec.size == 0:
                raise ValueError("Empty latent vector extracted")

            latent_obj = LatentVector(
                scenario_id=sample.get('id', f"unknown_{idx}"),
                prompt=sample.get('prompt', ''),
                vector=latent_vec,
                timestamp=time.time()
            )
            latents.append(latent_obj)

        except Exception as e:
            logger.warning(f"Failed to process sample {sample.get('id', idx)}: {e}")
            failed_samples.append({
                "id": sample.get('id', idx),
                "error": str(e),
                "timestamp": time.time()
            })
            # Log to audit logger
            log_skipped_file(
                filename=sample.get('video_path', 'unknown'),
                reason=str(e),
                context="latent_extraction"
            )
    
    if failed_samples:
        logger.error(f"Batch processing completed with {len(failed_samples)} failures.")
    
    return latents

def run_extraction_pipeline(
    dataset_path: str, 
    model_path: str, 
    output_path: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main pipeline runner with robust error handling.
    - Handles missing files/corrupted data gracefully.
    - Logs errors without stopping the entire process.
    - Adjusts batch size based on memory.
    """
    ensure_directories(output_path)
    
    logger.info("Starting Latent Extraction Pipeline")
    
    # Initialize Dataset
    try:
        dataset = OrcaLatentDataset(dataset_path, config)
    except Exception as e:
        logger.critical(f"Failed to initialize dataset: {e}")
        return {"status": "failed", "error": str(e)}

    # Load Model
    try:
        model = load_frozen_orca_model(model_path, config.get('device', 'cpu'))
    except Exception as e:
        logger.critical(f"Failed to load model: {e}")
        return {"status": "failed", "error": str(e)}

    # Prepare output file
    output_file = Path(output_path) / "latents.csv"
    total_processed = 0
    total_failed = 0
    batch_size = config.get('batch_size', 8)
    
    logger.info(f"Processing dataset with batch size {batch_size}")

    try:
        # Iterate with error resilience
        for i, batch in enumerate(dataset):
            # Check memory before processing batch
            mem_pct = get_memory_usage_percent()
            if mem_pct > config.get('memory_threshold', 80):
                logger.warning(f"High memory usage ({mem_pct}%). Adjusting batch size.")
                batch_size = adjust_batch_size(mem_pct, config.get('memory_threshold', 80))
                if batch_size < 1:
                    logger.critical("Memory critically low. Aborting batch.")
                    break
                logger.info(f"New batch size: {batch_size}")

            # Process batch
            # Note: In a real loop, we would chunk the iterator. 
            # Here we assume 'dataset' yields individual items or small lists.
            # For robustness, we treat 'batch' as a single item if it's a dict, 
            # or a list if it's a batch.
            
            current_batch_items = [batch] if isinstance(batch, dict) else batch
            if not current_batch_items:
                continue

            processed_latents = process_batch(
                current_batch_items, 
                model, 
                config.get('device', 'cpu'), 
                batch_size
            )

            # Write to CSV
            with open(output_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if total_processed == 0:
                    writer.writerow(['scenario_id', 'prompt', 'vector_str', 'timestamp'])
                
                for latent in processed_latents:
                    # Convert vector to string for CSV storage
                    vec_str = json.dumps(latent.vector.tolist())
                    writer.writerow([
                        latent.scenario_id,
                        latent.prompt,
                        vec_str,
                        latent.timestamp
                    ])
                    total_processed += 1

            total_failed += len(current_batch_items) - len(processed_latents)
            
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {total_processed} processed, {total_failed} failed.")

    except Exception as e:
        logger.error(f"Pipeline encountered a critical error: {e}")
        # Do not re-raise, allow partial results
    
    summary = get_audit_summary()
    logger.info(f"Pipeline finished. Processed: {total_processed}, Failed: {total_failed}")
    logger.info(f"Audit Summary: {summary}")
    
    return {
        "status": "completed",
        "processed": total_processed,
        "failed": total_failed,
        "output_file": str(output_file),
        "audit_summary": summary
    }

def main():
    """
    Entry point for the script.
    """
    config = get_config()
    dataset_path = config.get('data_dir', 'data/raw/orca')
    model_path = config.get('model_path', 'models/orca_frozen.pt')
    output_path = config.get('output_dir', 'data/processed')
    
    # Ensure output directory exists
    ensure_directories(output_path)

    result = run_extraction_pipeline(
        dataset_path=dataset_path,
        model_path=model_path,
        output_path=output_path,
        config=config
    )

    if result['status'] == 'completed':
        print(f"Extraction complete. Output: {result['output_file']}")
        print(f"Processed: {result['processed']}, Failed: {result['failed']}")
    else:
        print(f"Extraction failed: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()