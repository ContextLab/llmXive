import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np

# Import existing utilities from sibling modules as per API surface
# Note: We assume these are available in the project context
# If not, they should be implemented in their respective files first

def load_sentence_transformer_model(model_name: str = "all-MiniLM-L6-v2"):
    """Load a sentence-transformer model for text embeddings."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_name)
        return model
    except ImportError:
        raise ImportError("sentence-transformers is required. Install via: pip install sentence-transformers")

def load_clip_model(model_name: str = "openai/clip-vit-base-patch32"):
    """Load a CLIP model for image embeddings."""
    try:
        from transformers import CLIPProcessor, CLIPModel
        model = CLIPModel.from_pretrained(model_name)
        processor = CLIPProcessor.from_pretrained(model_name)
        return model, processor
    except ImportError:
        raise ImportError("transformers and torch are required. Install via: pip install transformers torch")

def validate_schema(data: Dict, schema: Dict) -> bool:
    """Validate data against a schema."""
    # Basic validation - check required keys exist
    required_keys = schema.get("required", [])
    for key in required_keys:
        if key not in data:
            return False
    return True

def load_memlens_dataset(dataset_path: str) -> List[Dict]:
    """Load the MemLens dataset from a directory or file."""
    data = []
    path = Path(dataset_path)
    
    if path.is_dir():
        # Load all JSON files in the directory
        for json_file in path.glob("*.json"):
            with open(json_file, 'r') as f:
                dataset = json.load(f)
                if isinstance(dataset, list):
                    data.extend(dataset)
                else:
                    data.append(dataset)
    elif path.is_file() and path.suffix == '.json':
        with open(path, 'r') as f:
            dataset = json.load(f)
            if isinstance(dataset, list):
                data = dataset
            else:
                data = [dataset]
    else:
        raise ValueError(f"Unsupported dataset path: {dataset_path}")
    
    return data

def preprocess_image(image_path: str) -> Any:
    """Preprocess an image for CLIP model."""
    try:
        from PIL import Image
        img = Image.open(image_path).convert("RGB")
        return img
    except Exception as e:
        raise RuntimeError(f"Failed to load image {image_path}: {e}")

def get_global_clip_embedding(image: Any, processor, model, device: str = "cpu") -> np.ndarray:
    """Get a global CLIP embedding for an image."""
    import torch
    inputs = processor(images=image, return_tensors="pt", padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
    
    # Normalize the embedding
    embeddings = outputs.cpu().numpy()
    return embeddings[0] / np.linalg.norm(embeddings[0])

def get_text_embedding(text: str, model) -> np.ndarray:
    """Get a sentence-transformer embedding for text."""
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding

def construct_coarse_store(dataset: List[Dict], output_path: str) -> Dict:
    """Construct a Coarse memory store with text summaries and sentence-transformer embeddings."""
    logger = logging.getLogger(__name__)
    model = load_sentence_transformer_model()
    
    store = {
        "type": "coarse",
        "entries": [],
        "metadata": {
            "embedding_model": "all-MiniLM-L6-v2",
            "total_entries": 0
        }
    }
    
    for idx, item in enumerate(dataset):
        # Extract text summary (assuming it's in 'summary' or 'text' field)
        text = item.get("summary") or item.get("text") or ""
        
        if not text:
            logger.warning(f"Skipping entry {idx}: no text content")
            continue
        
        # Generate embedding
        embedding = get_text_embedding(text, model)
        
        entry = {
            "id": item.get("id", idx),
            "text": text,
            "embedding": embedding.tolist(),
            "metadata": {
                "source": item.get("source", "unknown"),
                "timestamp": item.get("timestamp", None)
            }
        }
        
        store["entries"].append(entry)
    
    store["metadata"]["total_entries"] = len(store["entries"])
    
    # Save to disk
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(store, f, indent=2)
    
    logger.info(f"Coarse store constructed with {store['metadata']['total_entries']} entries")
    return store

def construct_medium_store(dataset: List[Dict], output_path: str) -> Dict:
    """Construct a Medium memory store with summaries, global CLIP embeddings, and text embeddings."""
    logger = logging.getLogger(__name__)
    text_model = load_sentence_transformer_model()
    clip_model, clip_processor = load_clip_model()
    
    store = {
        "type": "medium",
        "entries": [],
        "metadata": {
            "text_embedding_model": "all-MiniLM-L6-v2",
            "image_embedding_model": "openai/clip-vit-base-patch32",
            "total_entries": 0
        }
    }
    
    for idx, item in enumerate(dataset):
        # Extract text summary
        text = item.get("summary") or item.get("text") or ""
        
        # Extract image path
        image_path = item.get("image_path") or item.get("image")
        
        if not text:
            logger.warning(f"Skipping entry {idx}: no text content")
            continue
        
        entry_data = {
            "id": item.get("id", idx),
            "text": text,
            "metadata": {
                "source": item.get("source", "unknown"),
                "timestamp": item.get("timestamp", None),
                "image_path": image_path
            }
        }
        
        # Add text embedding
        text_embedding = get_text_embedding(text, text_model)
        entry_data["text_embedding"] = text_embedding.tolist()
        
        # Add image embedding if image exists
        if image_path and os.path.exists(image_path):
            try:
                image = preprocess_image(image_path)
                image_embedding = get_global_clip_embedding(image, clip_processor, clip_model)
                entry_data["image_embedding"] = image_embedding.tolist()
            except Exception as e:
                logger.warning(f"Failed to process image for entry {idx}: {e}")
        else:
            logger.warning(f"No valid image for entry {idx}")
        
        store["entries"].append(entry_data)
    
    store["metadata"]["total_entries"] = len(store["entries"])
    
    # Save to disk
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(store, f, indent=2)
    
    logger.info(f"Medium store constructed with {store['metadata']['total_entries']} entries")
    return store

def construct_fine_store(dataset: List[Dict], output_path: str) -> Dict:
    """
    Construct a Fine memory store with object captions and bounding boxes.
    
    CRITICAL: Bounding box coordinates are stored as metadata ONLY and explicitly
    excluded from similarity calculation vectors. Only the object captions (text)
    are used for embeddings and similarity retrieval.
    
    This ensures that spatial information does not interfere with semantic similarity
    matching, adhering to Plan Phase 2 and FR-002.
    """
    logger = logging.getLogger(__name__)
    model = load_sentence_transformer_model()
    
    store = {
        "type": "fine",
        "entries": [],
        "metadata": {
            "embedding_model": "all-MiniLM-L6-v2",
            "total_entries": 0,
            "note": "Bounding box coordinates are stored in metadata ONLY and excluded from similarity vectors"
        }
    }
    
    for idx, item in enumerate(dataset):
        # Extract object captions (from detection results)
        object_captions = item.get("object_captions", [])
        bounding_boxes = item.get("bounding_boxes", [])
        detection_status = item.get("detection_status", "unknown")
        
        # Skip if no objects detected or detection failed
        if not object_captions or detection_status in ["fallback", "zero_detection"]:
            logger.debug(f"Skipping entry {idx}: no valid object detections (status: {detection_status})")
            continue
        
        # Join object captions into a single text for embedding
        # This creates a composite semantic representation of all detected objects
        combined_caption = " ".join(object_captions)
        
        # Generate embedding from object captions ONLY (no coordinates)
        embedding = get_text_embedding(combined_caption, model)
        
        entry = {
            "id": item.get("id", idx),
            # Primary text for semantic matching
            "object_captions": object_captions,
            "combined_caption": combined_caption,
            # Embedding derived ONLY from text captions (coordinates excluded)
            "embedding": embedding.tolist(),
            # Spatial data stored as metadata ONLY - NOT used in similarity calculation
            "metadata": {
                "bounding_boxes": bounding_boxes,  # Coordinates here, but excluded from vectors
                "detection_status": detection_status,
                "source": item.get("source", "unknown"),
                "timestamp": item.get("timestamp", None),
                "num_objects": len(object_captions),
                # Explicit flag to indicate coordinates are metadata-only
                "coordinates_excluded_from_similarity": True
            }
        }
        
        store["entries"].append(entry)
    
    store["metadata"]["total_entries"] = len(store["entries"])
    
    # Save to disk
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(store, f, indent=2)
    
    logger.info(f"Fine store constructed with {store['metadata']['total_entries']} entries")
    logger.info("Bounding box coordinates stored as metadata only - excluded from similarity vectors")
    return store

def save_store(store: Dict, output_path: str) -> None:
    """Save a memory store to disk as JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(store, f, indent=2)

def main():
    """Main function to demonstrate Fine store construction."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Construct Fine memory store from MemLens dataset")
    parser.add_argument("--dataset", type=str, required=True, help="Path to MemLens dataset")
    parser.add_argument("--output", type=str, required=True, help="Output path for Fine store")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Load dataset
    logger.info(f"Loading dataset from {args.dataset}")
    dataset = load_memlens_dataset(args.dataset)
    logger.info(f"Loaded {len(dataset)} entries")
    
    # Construct Fine store
    logger.info("Constructing Fine store...")
    store = construct_fine_store(dataset, args.output)
    
    logger.info(f"Fine store saved to {args.output}")
    logger.info(f"Total entries: {store['metadata']['total_entries']}")
    logger.info("Verification: Coordinates are stored as metadata only and excluded from similarity vectors")

if __name__ == "__main__":
    main()
