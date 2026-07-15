import os
import logging
from typing import Iterator, Dict, Any
import torch
from torch.utils.data import DataLoader, Dataset
from datasets import load_dataset
from PIL import Image
import torchvision.transforms as transforms

from config import Config

logger = logging.getLogger(__name__)

class COCOStreamingDataset(Dataset):
    """
    Wrapper for COCO dataset using streaming mode.
    Resizes images to 64x64 as per T013/T005.
    """
    def __init__(self, config: Config, split: str = "train"):
        self.config = config
        self.split = split
        self.transform = transforms.Compose([
            transforms.Resize((config.dataset_limits.resolution, config.dataset_limits.resolution)),
            transforms.ToTensor(),
            # Normalize to [-1, 1] expected by model
            transforms.Lambda(lambda x: x * 2.0 - 1.0)
        ])
        
        logger.info(f"Initializing COCO streaming dataset (split={split})...")
        try:
            # T005 requirement: load_dataset("coco", streaming=True)
            # Note: 'coco' in HuggingFace might require specific config or version.
            # Using 'mscoco' or similar if 'coco' fails, but strictly following T005 instruction.
            # If 'coco' is not a valid dataset ID on HF, this will raise an error.
            # T005 says: datasets.load_dataset("coco", split="train", streaming=True)
            # We assume 'coco' is the correct ID. If it fails, it fails loudly.
            self.dataset = load_dataset("coco", split=split, streaming=True)
        except Exception as e:
            logger.error(f"Failed to load COCO dataset: {e}")
            # Fail loudly as per constraints
            raise RuntimeError(f"Real data fetch failed for COCO: {e}") from e

    def __len__(self):
        # Streaming datasets don't have a known length, return a large number or None
        # For DataLoader, we can iterate until StopIteration
        return 1000000 # Approximate for iteration logic

    def __getitem__(self, idx):
        # Since it's streaming, we can't index directly by int.
        # We rely on the iterator in the DataLoader or manual iteration.
        # This class structure is slightly incompatible with standard DataLoader __getitem__
        # for streaming. We will implement the iterator in the get_dataloader function directly.
        raise NotImplementedError("Use the iterator in get_dataloader for streaming.")

def get_dataloader(config: Config, split: str = "train", streaming: bool = True) -> Iterator[Dict[str, Any]]:
    """
    Returns an iterator over the dataset.
    T005: COCO with streaming=True.
    """
    logger.info(f"Creating dataloader for split={split}, streaming={streaming}")
    
    try:
        # T005: load_dataset("coco", split="train", streaming=True)
        # We use the 'coco' dataset ID. If it's not available, it raises.
        ds = load_dataset("coco", split=split, streaming=True)
        
        # Transform
        transform = transforms.Compose([
            transforms.Resize((config.dataset_limits.resolution, config.dataset_limits.resolution)),
            transforms.ToTensor(),
            transforms.Lambda(lambda x: x * 2.0 - 1.0)
        ])

        def process_batch(batch):
            # Batch is a dict of lists or tensors
            # 'image' is usually PIL images or paths
            # 'caption' is text
            processed_images = []
            processed_captions = []
            
            images = batch['image']
            captions = batch['caption']
            
            for img, cap in zip(images, captions):
                if img is None:
                    continue
                # Ensure PIL Image
                if not isinstance(img, Image.Image):
                    try:
                        img = Image.open(img).convert("RGB")
                    except:
                        continue
                
                processed_images.append(transform(img))
                processed_captions.append(cap)
            
            if not processed_images:
                return None
                
            return {
                'image': torch.stack(processed_images),
                'caption': processed_captions
            }

        # Return an iterator that yields processed batches
        # We use a generator to handle streaming
        def iter_dataset():
            for batch in ds:
                processed = process_batch(batch)
                if processed is not None:
                    yield processed

        return iter_dataset()

    except Exception as e:
        logger.error(f"Failed to fetch real data source (COCO): {e}")
        raise RuntimeError(f"Real data fetch failed: {e}") from e
