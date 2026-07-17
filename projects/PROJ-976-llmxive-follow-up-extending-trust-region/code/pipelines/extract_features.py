"""
Pipeline to extract lexical and syntactic diversity features from teacher outputs.

This script integrates with data_loader.py to process both Book Corpus and BEIR datasets.
It computes features without GPU usage and saves results to data/processed/.
"""
import json
from pathlib import Path
from typing import List, Dict, Any
import os
import logging
from code.config import DATA_PROCESSED_DIR, DATA_RAW_DIR
from code.utils.data_loader import load_book_corpus, load_beir
from code.metrics.lexical import compute_lexical_features
from code.metrics.syntactic import compute_syntactic_features

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_dataset(
    dataset_name: str,
    text_field: str,
    load_function,
    output_filename: str,
    batch_size: int = 100
) -> str:
    """
    Process a dataset by extracting features and saving to a JSON file.
    
    Args:
        dataset_name: Name of the dataset for logging
        text_field: Field name containing the text to analyze
        load_function: Function to load the dataset (load_book_corpus or load_beir)
        output_filename: Name of the output file in data/processed/
        batch_size: Number of samples to process before writing a batch
        
    Returns:
        Path to the output file
    """
    logger.info(f"Starting feature extraction for {dataset_name}")
    
    # Ensure output directory exists
    output_dir = Path(DATA_PROCESSED_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_filename
    
    # Load dataset
    logger.info(f"Loading {dataset_name} dataset...")
    try:
        dataset = load_function()
        logger.info(f"Loaded {len(dataset)} samples from {dataset_name}")
    except Exception as e:
        logger.error(f"Failed to load {dataset_name}: {e}")
        raise
    
    # Process samples in batches
    features_list = []
    batch_count = 0
    total_samples = len(dataset)
    
    for i, sample in enumerate(dataset):
        if text_field not in sample:
            logger.warning(f"Sample {i} missing field '{text_field}', skipping")
            continue
            
        text = sample[text_field]
        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            logger.warning(f"Sample {i} has empty or invalid text, skipping")
            continue
        
        # Compute features
        try:
            lexical_features = compute_lexical_features(text)
            syntactic_features = compute_syntactic_features(text)
            
            # Combine features
            sample_features = {
                "sample_id": i,
                "text_length": len(text),
                **lexical_features,
                **syntactic_features
            }
            features_list.append(sample_features)
            
        except Exception as e:
            logger.warning(f"Failed to process sample {i}: {e}")
            continue
        
        # Write batch periodically
        if len(features_list) % batch_size == 0 and len(features_list) > 0:
            with open(output_path, 'a') as f:
                for feat in features_list[-batch_size:]:
                    f.write(json.dumps(feat) + '\n')
            batch_count += 1
            logger.info(f"Processed {len(features_list)}/{total_samples} samples ({batch_count} batches written)")
    
    # Write remaining samples
    if len(features_list) % batch_size != 0:
        with open(output_path, 'a') as f:
            for feat in features_list[-(len(features_list) % batch_size):]:
                f.write(json.dumps(feat) + '\n')
        logger.info("Wrote remaining samples")
    
    logger.info(f"Feature extraction complete for {dataset_name}. "
               f"Total features: {len(features_list)}, Output: {output_path}")
    
    return str(output_path)

def main():
    """Main entry point for feature extraction pipeline."""
    logger.info("Starting feature extraction pipeline")
    
    # Process Book Corpus
    book_corpus_path = process_dataset(
        dataset_name="Book Corpus",
        text_field="text",
        load_function=load_book_corpus,
        output_filename="book_corpus_features.jsonl",
        batch_size=500
    )
    
    # Process BEIR
    beir_path = process_dataset(
        dataset_name="BEIR",
        text_field="text",
        load_function=load_beir,
        output_filename="beir_features.jsonl",
        batch_size=500
    )
    
    logger.info(f"Pipeline complete. Outputs: {book_corpus_path}, {beir_path}")
    return [book_corpus_path, beir_path]

if __name__ == "__main__":
    main()