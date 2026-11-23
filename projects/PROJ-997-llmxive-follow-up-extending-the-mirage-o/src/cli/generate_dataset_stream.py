"""
Streaming data loader for dataset generation.
Loads GSM8K dataset in chunks to avoid OOM on limited runners.
"""
import logging
from pathlib import Path
from typing import Iterator, Dict, Any, Optional
from datasets import load_dataset

logger = logging.getLogger(__name__)

def load_gsm8k_streaming(cache_dir: Optional[str] = None) -> Iterator[Dict[str, Any]]:
    """
    Load GSM8K dataset in streaming mode.
    
    Args:
        cache_dir: Optional cache directory for the dataset.
        
    Yields:
        Dictionary containing 'question' and 'answer' fields.
    """
    logger.info("Loading GSM8K dataset in streaming mode...")
    try:
        dataset = load_dataset(
            "gsm8k",
            "main",
            split="train",
            streaming=True,
            cache_dir=cache_dir
        )
        logger.info("Successfully loaded GSM8K dataset in streaming mode.")
        for sample in dataset:
            yield sample
    except Exception as e:
        logger.error(f"Failed to load GSM8K dataset: {e}")
        raise

def load_dataset_streaming(
    dataset_name: str = "gsm8k",
    config_name: str = "main",
    split: str = "train",
    cache_dir: Optional[str] = None
) -> Iterator[Dict[str, Any]]:
    """
    Generic streaming dataset loader.
    
    Args:
        dataset_name: Name of the dataset to load.
        config_name: Configuration name for the dataset.
        split: Dataset split to load.
        cache_dir: Optional cache directory.
        
    Yields:
        Dictionary containing sample data.
    """
    logger.info(f"Loading dataset: {dataset_name}/{config_name} split={split} in streaming mode...")
    try:
        dataset = load_dataset(
            dataset_name,
            config_name,
            split=split,
            streaming=True,
            cache_dir=cache_dir
        )
        logger.info(f"Successfully loaded dataset: {dataset_name}/{config_name}")
        for sample in dataset:
            yield sample
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}/{config_name}: {e}")
        raise
