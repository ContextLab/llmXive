import os
import sys
import logging
import time
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# Project-relative imports based on API surface
from config import get_config, ensure_directories
from data.models import LatentVector, LatentVectorPydantic
from utils.audit_logger import log_skipped_file, log_audit_event, get_audit_summary
from utils.memory_guard import adjust_batch_size, get_memory_usage_percent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/extract_latents.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
BATCH_SIZE_INITIAL = 16
BATCH_SIZE_MIN = 1

class OrcaLatentDataset:
    """
    Dataset wrapper for Orca video clips with error handling for corrupted/missing files.
    """
    def __init__(self, scenarios_path: str):
        self.scenarios_path = Path(scenarios_path)
        self.config = get_config()
        self.items: List[Dict[str, Any]] = []
        self._load_scenarios()

    def _load_scenarios(self) -> None:
        """Load scenarios from CSV, skipping corrupted rows."""
        if not self.scenarios_path.exists():
            raise FileNotFoundError(f"Scenarios file not found: {self.scenarios_path}")

        logger.info(f"Loading scenarios from {self.scenarios_path}")
        skipped_count = 0
        loaded_count = 0

        try:
            with open(self.scenarios_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    try:
                        # Validate required fields
                        if not row.get('video_id') or not row.get('prompt'):
                            raise ValueError("Missing required fields: video_id or prompt")
                        
                        # Try to parse metadata if it exists
                        if 'metadata' in row and row['metadata']:
                            try:
                                row['metadata'] = json.loads(row['metadata'])
                            except json.JSONDecodeError as e:
                                logger.warning(f"Row {row_num}: Invalid metadata JSON for video_id {row.get('video_id')}: {e}")
                                log_skipped_file(
                                    filename=f"row_{row_num}",
                                    reason=f"Invalid metadata JSON: {str(e)}",
                                    task="latent_extraction"
                                )
                                skipped_count += 1
                                continue

                        self.items.append(row)
                        loaded_count += 1

                    except Exception as e:
                        logger.warning(f"Row {row_num}: Error processing row - {str(e)}")
                        log_skipped_file(
                            filename=f"row_{row_num}",
                            reason=f"Processing error: {str(e)}",
                            task="latent_extraction"
                        )
                        skipped_count += 1
                        continue

        except Exception as e:
            logger.error(f"Failed to read scenarios file: {str(e)}")
            raise

        logger.info(f"Loaded {loaded_count} valid scenarios, skipped {skipped_count} corrupted rows")
        log_audit_event(
            event_type="dataset_load",
            details={
                "total_rows": loaded_count + skipped_count,
                "valid_rows": loaded_count,
                "skipped_rows": skipped_count,
                "source_file": str(self.scenarios_path)
            }
        )

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        return self.items[idx]

    def get_batch(self, indices: List[int]) -> List[Dict[str, Any]]:
        """Get multiple items by indices with error handling."""
        batch = []
        for idx in indices:
            try:
                batch.append(self[idx])
            except IndexError:
                logger.warning(f"Batch index {idx} out of range")
                continue
        return batch


def load_frozen_orca_model(model_name: str = "microsoft/orca-math-word-problems-200k") -> Any:
    """
    Load the frozen Orca model on CPU.
    
    Args:
        model_name: HuggingFace model identifier
        
    Returns:
        Loaded model instance
    """
    try:
        from transformers import AutoModel, AutoTokenizer
        import torch
        
        logger.info(f"Loading model: {model_name}")
        
        # Load tokenizer and model on CPU
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModel.from_pretrained(model_name, trust_remote_code=True, torch_dtype=torch.float32)
        
        # Ensure model is in eval mode and on CPU
        model.eval()
        model = model.cpu()
        
        # Freeze parameters
        for param in model.parameters():
            param.requires_grad = False
        
        logger.info("Model loaded successfully on CPU")
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise


def process_batch(
    batch: List[Dict[str, Any]], 
    model: Any, 
    tokenizer: Any,
    batch_size: int
) -> List[LatentVector]:
    """
    Process a batch of scenarios to extract latent vectors.
    
    Args:
        batch: List of scenario dictionaries
        model: Frozen Orca model
        tokenizer: Model tokenizer
        batch_size: Current batch size for memory management
        
    Returns:
        List of LatentVector objects
    """
    config = get_config()
    embedding_dim = config.get('EMBEDDING_DIM', 4096)
    
    latents = []
    failed_indices = []
    
    for i, scenario in enumerate(batch):
        video_id = scenario.get('video_id', f'unknown_{i}')
        prompt = scenario.get('prompt', '')
        
        try:
            # Tokenize input
            inputs = tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=config.get('MAX_TOKEN_LENGTH', 512)
            )
            
            # Move to CPU
            inputs = {k: v.cpu() for k, v in inputs.items()}
            
            # Extract latent (using last hidden state mean pooling)
            with torch.no_grad():
                outputs = model(**inputs)
                
                # Get last hidden state
                last_hidden_state = outputs.last_hidden_state
                
                # Mean pooling over sequence length
                attention_mask = inputs['attention_mask']
                sum_embeddings = torch.sum(last_hidden_state * attention_mask.unsqueeze(-1), dim=1)
                mask_sum = torch.clamp(attention_mask.sum(dim=1, keepdim=True), min=1e-9)
                mean_embedding = sum_embeddings / mask_sum
                
                # Ensure correct shape
                latent_vector = mean_embedding.squeeze(0).numpy()
                
                if len(latent_vector) != embedding_dim:
                    logger.warning(f"Video {video_id}: Latent dimension mismatch ({len(latent_vector)} vs {embedding_dim}), padding/truncating")
                    if len(latent_vector) < embedding_dim:
                        latent_vector = np.pad(latent_vector, (0, embedding_dim - len(latent_vector)))
                    else:
                        latent_vector = latent_vector[:embedding_dim]
                
                latent_obj = LatentVector(
                    video_id=video_id,
                    prompt=prompt,
                    vector=latent_vector.tolist(),
                    shape=(embedding_dim,)
                )
                latents.append(latent_obj)
                
        except Exception as e:
            logger.error(f"Failed to process video {video_id}: {str(e)}")
            log_skipped_file(
                filename=video_id,
                reason=f"Latent extraction error: {str(e)}",
                task="latent_extraction"
            )
            failed_indices.append(i)
            continue
    
    if failed_indices:
        logger.warning(f"Failed to process {len(failed_indices)} items in batch")
    
    return latents


def run_extraction_pipeline(
    scenarios_path: str,
    output_path: str,
    model_name: str = "microsoft/orca-math-word-problems-200k"
) -> Dict[str, int]:
    """
    Run the full latent extraction pipeline with error handling.
    
    Args:
        scenarios_path: Path to input scenarios CSV
        output_path: Path to output latents CSV
        model_name: HuggingFace model identifier
        
    Returns:
        Dictionary with processing statistics
    """
    start_time = time.time()
    config = get_config()
    
    # Ensure output directory exists
    ensure_directories([str(Path(output_path).parent)])
    
    # Load dataset with error handling
    try:
        dataset = OrcaLatentDataset(scenarios_path)
    except FileNotFoundError as e:
        logger.error(f"Dataset loading failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading dataset: {str(e)}")
        raise
    
    if len(dataset) == 0:
        logger.warning("No valid scenarios found in dataset")
        return {"processed": 0, "skipped": 0, "failed": 0}
    
    # Load model
    try:
        model, tokenizer = load_frozen_orca_model(model_name)
    except Exception as e:
        logger.error(f"Model loading failed: {str(e)}")
        raise
    
    # Initialize batch processing
    batch_size = BATCH_SIZE_INITIAL
    total_processed = 0
    total_skipped = 0
    total_failed = 0
    
    logger.info(f"Starting extraction pipeline with {len(dataset)} items")
    
    # Process in batches
    with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['video_id', 'prompt', 'latent_vector', 'shape'])
        
        idx = 0
        while idx < len(dataset):
            # Adjust batch size based on memory
            memory_usage = get_memory_usage_percent()
            if memory_usage > config.get('MEMORY_CRITICAL_THRESHOLD', 80):
                batch_size = adjust_batch_size(batch_size, batch_size // 2)
                logger.info(f"Memory usage high ({memory_usage}%), reduced batch size to {batch_size}")
            
            # Get current batch
            end_idx = min(idx + batch_size, len(dataset))
            current_batch = dataset.get_batch(list(range(idx, end_idx)))
            
            if not current_batch:
                idx += batch_size
                continue
            
            # Process batch
            try:
                latents = process_batch(current_batch, model, tokenizer, batch_size)
                
                # Write to CSV
                for latent in latents:
                    writer.writerow([
                        latent.video_id,
                        latent.prompt,
                        json.dumps(latent.vector),
                        str(latent.shape)
                    ])
                    total_processed += 1
                
                total_skipped += len(current_batch) - len(latents)
                
            except Exception as e:
                logger.error(f"Batch processing failed at index {idx}: {str(e)}")
                # Mark all in batch as failed
                total_failed += len(current_batch)
                
                # Reduce batch size and retry
                if batch_size > BATCH_SIZE_MIN:
                    batch_size = adjust_batch_size(batch_size, batch_size // 2)
                    logger.info(f"Reduced batch size to {batch_size} for retry")
                    continue
                else:
                    logger.error("Batch size already at minimum, skipping batch")
                    total_skipped += len(current_batch)
            
            idx = end_idx
            
            # Log progress
            if idx % 10 == 0 or idx == len(dataset):
                elapsed = time.time() - start_time
                rate = idx / elapsed if elapsed > 0 else 0
                logger.info(f"Progress: {idx}/{len(dataset)} ({100*idx/len(dataset):.1f}%), "
                          f"Rate: {rate:.2f} items/sec, "
                          f"Batch size: {batch_size}")
    
    # Final statistics
    stats = {
        "processed": total_processed,
        "skipped": total_skipped,
        "failed": total_failed,
        "total_time_seconds": time.time() - start_time
    }
    
    # Log summary
    audit_summary = get_audit_summary()
    logger.info(f"Pipeline completed. Stats: {stats}")
    logger.info(f"Audit summary: {audit_summary}")
    
    log_audit_event(
        event_type="pipeline_complete",
        details=stats
    )
    
    return stats


def main():
    """Main entry point for latent extraction."""
    config = get_config()
    
    # Default paths
    scenarios_path = config.get('SCENARIOS_PATH', 'data/raw/scenarios.csv')
    output_path = config.get('LATENTS_PATH', 'data/processed/latents.csv')
    model_name = config.get('MODEL_NAME', 'microsoft/orca-math-word-problems-200k')
    
    logger.info(f"Starting latent extraction pipeline")
    logger.info(f"Scenarios: {scenarios_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Model: {model_name}")
    
    try:
        stats = run_extraction_pipeline(scenarios_path, output_path, model_name)
        
        if stats['processed'] == 0:
            logger.error("No latents were successfully extracted")
            sys.exit(1)
        
        logger.info(f"Successfully extracted {stats['processed']} latent vectors")
        logger.info(f"Skipped: {stats['skipped']}, Failed: {stats['failed']}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()