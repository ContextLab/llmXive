"""
Data Loader Module (T005).

Implements streaming dataset loading for COCO and ImageNet.
Explicitly excludes ChestX-ray14 per Plan Spec Amendments.
Fails loudly if real data fetch fails.
"""
import os
import logging
from typing import Iterator, Dict, Any, Optional, List
import torch
from torch.utils.data import DataLoader, Dataset
from datasets import load_dataset
from torchvision import transforms
import PIL.Image as Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class COCOStreamingDataset(Dataset):
    """
    Wrapper for COCO streaming dataset to interface with PyTorch DataLoader.
    Note: Streaming=True in datasets.load_dataset returns an iterable, not a map-style dataset.
    This class is a placeholder for map-style access if needed, but we primarily use iterators.
    """
    def __init__(self, split="train"):
        self.split = split
        logger.warning("COCOStreamingDataset is used for map-style fallback. Prefer get_coco_iterator.")
        try:
            self.dataset = load_dataset("coco", split=split, streaming=True)
        except Exception as e:
            raise RuntimeError(f"Failed to load COCO dataset: {e}")

    def __len__(self):
        # Unknown for streaming, return a large number or handle differently
        return 10000 

    def __getitem__(self, idx):
        # Streaming datasets don't support random access by index efficiently
        # This method is likely not used in the streaming pipeline
        iterator = iter(self.dataset)
        for _ in range(idx):
            try:
                next(iterator)
            except StopIteration:
                break
        try:
            return next(iterator)
        except StopIteration:
            raise IndexError("Index out of range for streaming dataset")

def get_dataloader(batch_size=8, split="train"):
    """
    Create a DataLoader for COCO.
    """
    dataset = COCOStreamingDataset(split=split)
    # Since it's streaming, we might need to wrap it or use the iterator directly
    # For now, return a standard dataloader, but note that streaming behavior is special
    return DataLoader(dataset, batch_size=batch_size, num_workers=0)

def get_coco_iterator(split="train") -> Iterator[Dict[str, Any]]:
    """
    Returns an iterator for COCO dataset.
    Loads real data from HuggingFace Hub.
    Fails loudly if fetch fails.
    """
    logger.info("Initializing COCO streaming iterator...")
    try:
        # Use streaming=True to avoid downloading full dataset to disk
        ds = load_dataset("coco", split=split, streaming=True)
        # Map to ensure consistent output format
        def transform_example(example):
            # Ensure image is loaded if it's a path, or pass through if already loaded
            if 'image' in example and example['image'] is not None:
                if isinstance(example['image'], str):
                    # If it's a path, load it (unlikely in streaming HF datasets usually they are loaded)
                    example['image'] = Image.open(example['image']).convert('RGB')
                elif hasattr(example['image'], 'load'):
                    example['image'] = example['image'].convert('RGB')
            return example
        
        return ds.map(transform_example)
    except Exception as e:
        logger.error("CRITICAL: Failed to fetch real COCO data. Aborting.")
        raise RuntimeError(f"Failed to fetch real COCO data: {e}")

def get_imagenet_iterator(split="validation") -> Iterator[Dict[str, Any]]:
    """
    Returns an iterator for ImageNet-1K dataset.
    Loads real data from HuggingFace Hub.
    Fails loudly if fetch fails.
    """
    logger.info("Initializing ImageNet streaming iterator...")
    try:
        # ImageNet is large, use streaming
        ds = load_dataset("imagenet-1k", split=split, streaming=True)
        
        def transform_example(example):
            if 'image' in example and example['image'] is not None:
                if isinstance(example['image'], str):
                    example['image'] = Image.open(example['image']).convert('RGB')
                elif hasattr(example['image'], 'load'):
                    example['image'] = example['image'].convert('RGB')
            return example

        return ds.map(transform_example)
    except Exception as e:
        logger.error("CRITICAL: Failed to fetch real ImageNet data. Aborting.")
        raise RuntimeError(f"Failed to fetch real ImageNet data: {e}")

def main():
    """
    Entry point for testing data loading (T005).
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-only", action="store_true", help="Trigger download test.")
    args = parser.parse_args()

    logger.info("Testing data loaders...")
    
    # Test COCO
    logger.info("Fetching COCO sample...")
    coco_iter = get_coco_iterator()
    try:
        sample = next(iter(coco_iter))
        logger.info(f"COCO sample loaded: keys={sample.keys()}, image type={type(sample.get('image'))}")
    except StopIteration:
        logger.warning("COCO dataset empty.")
    except Exception as e:
        raise RuntimeError(f"COCO fetch failed: {e}")

    # Test ImageNet
    logger.info("Fetching ImageNet sample...")
    imagenet_iter = get_imagenet_iterator()
    try:
        sample = next(iter(imagenet_iter))
        logger.info(f"ImageNet sample loaded: keys={sample.keys()}, image type={type(sample.get('image'))}")
    except StopIteration:
        logger.warning("ImageNet dataset empty.")
    except Exception as e:
        raise RuntimeError(f"ImageNet fetch failed: {e}")

    logger.info("Data loader test passed.")

if __name__ == "__main__":
    main()
