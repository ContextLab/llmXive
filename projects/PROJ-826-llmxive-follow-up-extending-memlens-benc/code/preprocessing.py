"""
Preprocessing utilities for MemLens benchmark extension.

This module handles:
- Data loading and schema validation
- Memory store construction (Coarse, Medium, Fine)
- Embedding generation and image preprocessing
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

import numpy as np
import jsonschema
from sentence_transformers import SentenceTransformer
from PIL import Image
import torch

from utils.logger import get_logger, log_preprocessing_step
import config

# Configure logging
logger = get_logger("preprocessing")

# Schema definitions for validation
MEMLENS_SAMPLE_SCHEMA = {
    "type": "object",
    "required": ["id", "question", "image_path", "answers", "metadata"],
    "properties": {
        "id": {"type": "string"},
        "question": {"type": "string"},
        "image_path": {"type": "string"},
        "answers": {
            "type": "array",
            "items": {"type": "string"}
        },
        "metadata": {
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "category": {"type": "string"},
                "timestamp": {"type": "string"}
            }
        }
    }
}

MEMORY_STORE_ENTRY_SCHEMA = {
    "type": "object",
    "required": ["id", "embedding", "content"],
    "properties": {
        "id": {"type": "string"},
        "embedding": {
            "type": "array",
            "items": {"type": "number"}
        },
        "content": {"type": "string"},
        "metadata": {
            "type": "object"
        }
    }
}

# Global model caches
_SENTENCE_TRANSFORMER_MODEL = None
_CLIP_MODEL = None
_CLIP_PREPROCESS = None


def load_sentence_transformer_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """Load or retrieve cached sentence transformer model."""
    global _SENTENCE_TRANSFORMER_MODEL
    if _SENTENCE_TRANSFORMER_MODEL is None:
        logger.info(f"Loading sentence transformer model: {model_name}")
        _SENTENCE_TRANSFORMER_MODEL = SentenceTransformer(model_name)
    return _SENTENCE_TRANSFORMER_MODEL


def load_clip_model(model_name: str = "clip-ViT-B-32"):
    """Load or retrieve cached CLIP model and preprocess."""
    global _CLIP_MODEL, _CLIP_PREPROCESS
    if _CLIP_MODEL is None:
        logger.info(f"Loading CLIP model: {model_name}")
        from transformers import CLIPProcessor, CLIPModel
        _CLIP_MODEL = CLIPModel.from_pretrained(model_name)
        _CLIP_PREPROCESS = CLIPProcessor.from_pretrained(model_name)
    return _CLIP_MODEL, _CLIP_PREPROCESS


def validate_schema(data: Any, schema: Dict, instance_name: str = "data") -> bool:
    """
    Validate data against a JSON schema.
    
    Args:
        data: Data to validate
        schema: JSON schema definition
        instance_name: Name for error messages
        
    Returns:
        True if valid, raises jsonschema.ValidationError if invalid
    """
    try:
        jsonschema.validate(instance=data, schema=schema)
        logger.debug(f"{instance_name} passed schema validation")
        return True
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"{instance_name} failed schema validation: {e.message}")
        raise


def load_memlens_dataset(data_path: str) -> List[Dict[str, Any]]:
    """
    Load the MemLens dataset from JSON files.
    
    Args:
        data_path: Path to the raw dataset directory or JSON file
        
    Returns:
        List of validated dataset samples
    """
    data_path = Path(data_path)
    samples = []
    
    if data_path.is_file() and data_path.suffix == '.json':
        files = [data_path]
    elif data_path.is_dir():
        files = list(data_path.glob("*.json"))
        if not files:
            raise FileNotFoundError(f"No JSON files found in {data_path}")
    else:
        raise FileNotFoundError(f"Data path not found: {data_path}")
    
    logger.info(f"Loading dataset from: {data_path}")
    
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Handle both single object and list of objects
        if isinstance(data, dict):
            data = [data]
        
        for item in data:
            try:
                validate_schema(item, MEMLENS_SAMPLE_SCHEMA, f"Sample from {file_path.name}")
                samples.append(item)
            except jsonschema.exceptions.ValidationError as e:
                logger.warning(f"Skipping invalid sample from {file_path}: {e.message}")
                continue
    
    logger.info(f"Loaded {len(samples)} valid samples")
    return samples


def preprocess_image(image_path: str, target_size: Tuple[int, int] = (224, 224)) -> Image.Image:
    """
    Load and preprocess an image.
    
    Args:
        image_path: Path to the image file
        target_size: Target dimensions (width, height)
        
    Returns:
        Preprocessed PIL Image
    """
    try:
        img = Image.open(image_path).convert('RGB')
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        return img
    except Exception as e:
        logger.error(f"Failed to load image {image_path}: {e}")
        raise


def get_global_clip_embedding(image: Image.Image) -> np.ndarray:
    """
    Get the global CLIP embedding for an image.
    
    Args:
        image: Preprocessed PIL Image
        
    Returns:
        numpy array of shape (embedding_dim,)
    """
    model, preprocess = load_clip_model()
    inputs = preprocess(images=image, return_tensors="pt", padding=True)
    
    with torch.no_grad():
        image_features = model.get_image_features(**inputs)
        # Normalize
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    
    return image_features.squeeze().numpy()


def get_text_embedding(text: str, model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """
    Get text embedding using sentence transformer.
    
    Args:
        text: Input text
        model_name: Sentence transformer model name
        
    Returns:
        numpy array of shape (embedding_dim,)
    """
    model = load_sentence_transformer_model(model_name)
    embedding = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
    return embedding


def construct_coarse_store(samples: List[Dict[str, Any]], output_path: str) -> List[Dict[str, Any]]:
    """
    Construct Coarse memory store (text summaries only).
    
    Args:
        samples: List of dataset samples
        output_path: Path to save the store
        
    Returns:
        List of store entries
    """
    store = []
    logger.info("Constructing Coarse store...")
    
    for sample in samples:
        # Use question + answer as content for coarse store
        content = f"Question: {sample['question']}\nAnswers: {'; '.join(sample['answers'])}"
        embedding = get_text_embedding(content)
        
        entry = {
            "id": sample["id"],
            "embedding": embedding.tolist(),
            "content": content,
            "metadata": {
                "source": sample.get("metadata", {}).get("source", "unknown"),
                "category": sample.get("metadata", {}).get("category", "unknown"),
                "store_type": "coarse"
            }
        }
        
        try:
            validate_schema(entry, MEMORY_STORE_ENTRY_SCHEMA, f"Coarse entry {sample['id']}")
            store.append(entry)
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"Invalid coarse entry for {sample['id']}: {e.message}")
            continue
    
    save_store(store, output_path)
    logger.info(f"Coarse store constructed with {len(store)} entries")
    return store


def construct_medium_store(samples: List[Dict[str, Any]], image_dir: str, output_path: str) -> List[Dict[str, Any]]:
    """
    Construct Medium memory store (summaries + global CLIP embeddings).
    
    Args:
        samples: List of dataset samples
        image_dir: Directory containing images
        output_path: Path to save the store
        
    Returns:
        List of store entries
    """
    store = []
    logger.info("Constructing Medium store...")
    image_dir = Path(image_dir)
    
    for sample in samples:
        try:
            image_path = image_dir / sample["image_path"]
            if not image_path.exists():
                logger.warning(f"Image not found for {sample['id']}: {image_path}")
                continue
            
            image = preprocess_image(str(image_path))
            image_embedding = get_global_clip_embedding(image)
            
            # Text content same as coarse
            text_content = f"Question: {sample['question']}\nAnswers: {'; '.join(sample['answers'])}"
            text_embedding = get_text_embedding(text_content)
            
            # Combine embeddings (simple concatenation for now)
            combined_embedding = np.concatenate([text_embedding, image_embedding])
            
            entry = {
                "id": sample["id"],
                "embedding": combined_embedding.tolist(),
                "content": text_content,
                "metadata": {
                    "source": sample.get("metadata", {}).get("source", "unknown"),
                    "category": sample.get("metadata", {}).get("category", "unknown"),
                    "store_type": "medium",
                    "image_path": str(image_path)
                }
            }
            
            validate_schema(entry, MEMORY_STORE_ENTRY_SCHEMA, f"Medium entry {sample['id']}")
            store.append(entry)
            
        except Exception as e:
            logger.error(f"Failed to construct medium entry for {sample['id']}: {e}")
            continue
    
    save_store(store, output_path)
    logger.info(f"Medium store constructed with {len(store)} entries")
    return store


def construct_fine_store(
    samples: List[Dict[str, Any]],
    image_dir: str,
    object_captions: Dict[str, List[str]],
    bounding_boxes: Dict[str, List[List[float]]],
    output_path: str
) -> List[Dict[str, Any]]:
    """
    Construct Fine memory store (object captions + bounding boxes).
    
    Args:
        samples: List of dataset samples
        image_dir: Directory containing images
        object_captions: Dict mapping sample_id to list of object captions
        bounding_boxes: Dict mapping sample_id to list of bounding boxes
        output_path: Path to save the store
        
    Returns:
        List of store entries
    """
    store = []
    logger.info("Constructing Fine store...")
    
    for sample in samples:
        try:
            sample_id = sample["id"]
            
            # Get object captions for this sample
            captions = object_captions.get(sample_id, [])
            boxes = bounding_boxes.get(sample_id, [])
            
            if not captions:
                logger.warning(f"No object captions for {sample_id}, skipping fine store entry")
                continue
            
            # Create content from object captions
            content = "; ".join(captions)
            embedding = get_text_embedding(content)
            
            entry = {
                "id": sample_id,
                "embedding": embedding.tolist(),
                "content": content,
                "metadata": {
                    "source": sample.get("metadata", {}).get("source", "unknown"),
                    "category": sample.get("metadata", {}).get("category", "unknown"),
                    "store_type": "fine",
                    "object_captions": captions,
                    "bounding_boxes": boxes,
                    "image_path": str(Path(image_dir) / sample["image_path"])
                }
            }
            
            validate_schema(entry, MEMORY_STORE_ENTRY_SCHEMA, f"Fine entry {sample_id}")
            store.append(entry)
            
        except Exception as e:
            logger.error(f"Failed to construct fine entry for {sample['id']}: {e}")
            continue
    
    save_store(store, output_path)
    logger.info(f"Fine store constructed with {len(store)} entries")
    return store


def save_store(store: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save memory store to JSON file.
    
    Args:
        store: List of store entries
        output_path: Path to save the store
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(store, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Store saved to {output_path}")


def main():
    """Main entry point for preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline...")
    
    # Example usage (to be replaced with actual config-based paths)
    data_path = config.get("data.raw_path", "data/raw/memlens")
    image_dir = config.get("data.image_dir", "data/raw/images")
    coarse_output = config.get("paths.coarse_store", "data/processed/coarse_store.json")
    medium_output = config.get("paths.medium_store", "data/processed/medium_store.json")
    fine_output = config.get("paths.fine_store", "data/processed/fine_store.json")
    
    # Load dataset
    samples = load_memlens_dataset(data_path)
    
    # Construct stores
    construct_coarse_store(samples, coarse_output)
    construct_medium_store(samples, image_dir, medium_output)
    # Fine store requires object detection results (to be passed from detection module)
    
    logger.info("Preprocessing pipeline completed.")

if __name__ == "__main__":
    main()