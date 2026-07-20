"""
Main entry point for the baseline latent vector extraction pipeline (T015).

This script:
1. Loads the reasoning dataset using the verified loader.
2. Pairs questions by task type and assigns PairIDs.
3. Extracts hidden state vectors for 'thought' tokens.
4. Normalizes vectors to unit length (L2).
5. Saves results to data/processed/baseline_vectors.csv.
"""
import os
import sys
import csv
import logging
import json
from typing import List, Dict, Any, Iterator

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

from config import PipelineConfig, OutputPaths, DataConfig, ModelConfig
from data_loader import load_reasoning_dataset, get_pairing_data, pair_questions_by_task_type, ConfigurationError
from model_utils import load_frozen_model, extract_thought_vector
from streaming_utils import stream_dataset, batch_iterator
from memory_monitor import check_memory_limit, get_current_memory_mb, memory_monitor, MemoryLimitExceeded

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_config() -> PipelineConfig:
    """Load pipeline configuration."""
    # Default configuration - in real usage, this might load from a YAML/JSON file
    data_config = DataConfig(
        dataset_name="big_bench_reasoning",
        split="train",
        streaming=True,
        batch_size=32
    )
    
    model_config = ModelConfig(
        model_name="google/flan-t5-small",  # Distilled variant for CPU
        hidden_layer_index=-1,
        thought_token_name="thought"
    )
    
    output_config = OutputPaths(
        base_dir="data/processed",
        baseline_vectors_file="baseline_vectors.csv",
        pairing_config_file="pairing_config.json"
    )
    
    return PipelineConfig(
        data=data_config,
        model=model_config,
        output=output_config
    )

def ensure_output_directory(output_dir: str) -> None:
    """Create output directory if it doesn't exist."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

def write_baseline_vectors(
    vectors: List[Dict[str, Any]],
    output_path: str
) -> None:
    """Write baseline vectors to CSV file."""
    if not vectors:
        logger.warning("No vectors to write.")
        return

    # Determine fieldnames from the first vector
    first_vector = vectors[0]
    fieldnames = list(first_vector.keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(vectors)
    
    logger.info(f"Wrote {len(vectors)} vectors to {output_path}")

def extract_baseline_vectors(config: PipelineConfig) -> List[Dict[str, Any]]:
    """
    Main extraction loop:
    1. Load dataset
    2. Pair questions by task type
    3. Extract thought vectors
    4. Normalize to unit length
    5. Return list of dicts for CSV writing
    """
    logger.info("Starting baseline vector extraction...")
    
    # Load and pair data
    logger.info("Loading and pairing dataset...")
    try:
        paired_data = pair_questions_by_task_type(
            dataset_name=config.data.dataset_name,
            split=config.data.split,
            streaming=config.data.streaming,
            batch_size=config.data.batch_size
        )
    except ConfigurationError as e:
        logger.error(f"Failed to load dataset: {e}")
        raise
    
    # Load model and tokenizer
    logger.info("Loading model and tokenizer...")
    model, tokenizer = load_frozen_model(config.model.model_name)
    
    # Initialize storage
    all_vectors = []
    processed_count = 0
    total_estimated = 0  # We don't know total in streaming mode
    
    logger.info("Processing pairs and extracting vectors...")
    
    # Process in batches to respect memory limits
    batch_size = config.data.batch_size
    
    for batch_idx, batch in enumerate(batch_iterator(paired_data, batch_size)):
        # Check memory before processing batch
        current_mem = get_current_memory_mb()
        if current_mem > 6500:  # 6.5GB threshold, leaving headroom
            logger.warning(f"Memory usage high: {current_mem:.1f}MB. Proceeding with caution.")
        
        for item in batch:
            try:
                # Extract thought vector
                thought_vector = extract_thought_vector(
                    model=model,
                    input_ids=item['input_ids'],
                    thought_token_pos=item['thought_token_pos']
                )
                
                # Normalize to unit length (L2 normalization)
                norm = (thought_vector ** 2).sum().sqrt()
                if norm > 1e-9:
                    normalized_vector = thought_vector / norm
                else:
                    normalized_vector = thought_vector  # Avoid division by zero
                
                # Convert to list for CSV storage
                vector_list = normalized_vector.tolist()
                
                # Create record
                record = {
                    'PairID': item['pair_id'],
                    'task_type': item['task_type'],
                    'question_a': item.get('question_a', ''),
                    'question_b': item.get('question_b', ''),
                    'vector_dimension': len(vector_list),
                    'vector_data': ','.join(map(str, vector_list))
                }
                
                all_vectors.append(record)
                processed_count += 1
                
                # Log progress every 100 items
                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} pairs...")
                    
            except Exception as e:
                logger.error(f"Error processing pair {item.get('pair_id', 'unknown')}: {e}")
                continue
    
    logger.info(f"Extraction complete. Processed {processed_count} pairs.")
    return all_vectors

def save_pairing_config(paired_data: Any, config: PipelineConfig) -> None:
    """Save pairing configuration metadata."""
    # Extract metadata from paired_data if available
    pairing_info = {
        'total_pairs': 0,
        'task_types': [],
        'extraction_timestamp': None,
        'config': {
            'dataset': config.data.dataset_name,
            'split': config.data.split
        }
    }
    
    # Try to get basic stats (may vary based on paired_data structure)
    try:
        # If paired_data is iterable, count items
        if hasattr(paired_data, '__iter__'):
            # For streaming, we can't count without consuming, so we'll estimate
            pairing_info['note'] = "Streaming mode - total count estimated"
    except:
        pass
    
    output_path = os.path.join(config.output.base_dir, config.output.pairing_config_file)
    ensure_output_directory(os.path.dirname(output_path))
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(pairing_info, f, indent=2)
    
    logger.info(f"Saved pairing config to {output_path}")

def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Baseline Latent Vector Extraction Pipeline (T015)")
    logger.info("=" * 60)
    
    try:
        # Load configuration
        config = load_config()
        
        # Ensure output directory exists
        ensure_output_directory(config.output.base_dir)
        
        # Load and pair dataset
        logger.info("Loading dataset...")
        paired_data = pair_questions_by_task_type(
            dataset_name=config.data.dataset_name,
            split=config.data.split,
            streaming=config.data.streaming,
            batch_size=config.data.batch_size
        )
        
        # Extract baseline vectors
        vectors = extract_baseline_vectors(config)
        
        # Save results
        output_path = os.path.join(config.output.base_dir, config.output.baseline_vectors_file)
        write_baseline_vectors(vectors, output_path)
        
        # Save pairing config
        save_pairing_config(paired_data, config)
        
        logger.info("=" * 60)
        logger.info("Pipeline completed successfully!")
        logger.info(f"Output: {output_path}")
        logger.info("=" * 60)
        
    except MemoryLimitExceeded as e:
        logger.error(f"Memory limit exceeded: {e}")
        sys.exit(1)
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()