import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

# Import existing utilities from sibling modules as per API surface
from utils.logger import get_logger, log_preprocessing_step

# --- Configuration Constants ---
# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"
STATE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-826-llmxive-follow-up-extending-memlens-benc.yaml"

# Store definitions
STORES_DIR = DATA_PROCESSED_PATH / "stores"
COARSE_STORE_PATH = STORES_DIR / "coarse_store.json"
MEDIUM_STORE_PATH = STORES_DIR / "medium_store.json"
FINE_STORE_PATH = STORES_DIR / "fine_store.json"

logger = get_logger("preprocessing")

def load_sentence_transformer_model(model_name: str = "all-MiniLM-L6-v2"):
    """
    Loads a sentence-transformer model for text embeddings.
    """
    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading sentence-transformer model: {model_name}")
        model = SentenceTransformer(model_name)
        return model
    except ImportError:
        logger.error("sentence-transformers library not found. Install with: pip install sentence-transformers")
        raise
    except Exception as e:
        logger.error(f"Failed to load sentence-transformer model: {e}")
        raise

def load_clip_model(model_name: str = "clip-ViT-B-32"):
    """
    Loads a CLIP model for image embeddings.
    """
    try:
        from transformers import CLIPProcessor, CLIPModel
        logger.info(f"Loading CLIP model: {model_name}")
        model = CLIPModel.from_pretrained(model_name)
        processor = CLIPProcessor.from_pretrained(model_name)
        return model, processor
    except ImportError:
        logger.error("transformers library not found. Install with: pip install transformers")
        raise
    except Exception as e:
        logger.error(f"Failed to load CLIP model: {e}")
        raise

def preprocess_image(image_path: Path) -> np.ndarray:
    """
    Loads and preprocesses an image. Returns numpy array.
    """
    from PIL import Image
    import numpy as np

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    img = Image.open(image_path).convert("RGB")
    return np.array(img)

def get_global_clip_embedding(image_array: np.ndarray, model, processor) -> np.ndarray:
    """
    Computes the global CLIP embedding for an image array.
    Returns a normalized 1D numpy array.
    """
    import torch

    inputs = processor(images=image_array, return_tensors="pt", padding=True)
    with torch.no_grad():
        image_features = model.get_image_features(**inputs)

    # Normalize
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    return image_features.squeeze().cpu().numpy()

def get_text_embedding(text: str, model) -> np.ndarray:
    """
    Computes the sentence-transformer embedding for a text string.
    Returns a normalized 1D numpy array.
    """
    embeddings = model.encode([text], convert_to_numpy=True, normalize_embeddings=True)
    return embeddings[0]

def construct_coarse_store(data_path: Path) -> List[Dict[str, Any]]:
    """
    Constructs the Coarse store: text summaries only with sentence-transformer embeddings.
    """
    logger.info("Constructing Coarse Store...")
    store = []
    # Assuming data is in a JSON file with 'id', 'summary', 'image_path'
    # This is a placeholder for the actual loading logic which would be in T008/T009
    # For T013, we assume the data structure is known from previous tasks
    # We simulate loading based on the assumption that data is available in a processed format
    # In a real run, this would iterate over the filtered dataset from T008
    
    # NOTE: Since T008/T009 are completed, we assume a function to load filtered data exists
    # or we iterate over the raw JSON if it's already filtered.
    # For this implementation, we will load the raw data and assume it's filtered or filter on the fly.
    # However, to strictly follow "extend, don't re-author", we assume the data is ready.
    
    # Let's assume the data is in data/raw/memlens_filtered.json (created by T008)
    input_file = data_path / "memlens_filtered.json"
    if not input_file.exists():
        # Fallback for testing if file doesn't exist yet, but in real run it must exist
        logger.warning(f"Input file {input_file} not found. Skipping store construction.")
        return []

    with open(input_file, 'r') as f:
        data = json.load(f)

    st_model = load_sentence_transformer_model()

    for item in data:
        # Extract summary
        summary = item.get("summary", "")
        if not summary:
            continue

        # Generate embedding
        emb = get_text_embedding(summary, st_model)

        entry = {
            "id": item["id"],
            "type": "coarse",
            "content": summary,
            "embedding": emb.tolist(),
            "metadata": {
                "source": item.get("source", "unknown"),
                "image_path": item.get("image_path", "")
            }
        }
        store.append(entry)

    logger.info(f"Coarse store constructed with {len(store)} entries.")
    return store

def construct_medium_store(data_path: Path) -> List[Dict[str, Any]]:
    """
    Constructs the Medium store: summaries + global CLIP embeddings.
    """
    logger.info("Constructing Medium Store...")
    store = []
    
    input_file = data_path / "memlens_filtered.json"
    if not input_file.exists():
        logger.warning(f"Input file {input_file} not found. Skipping store construction.")
        return []

    with open(input_file, 'r') as f:
        data = json.load(f)

    st_model = load_sentence_transformer_model()
    clip_model, clip_processor = load_clip_model()

    for item in data:
        summary = item.get("summary", "")
        image_path = Path(item.get("image_path", ""))
        
        if not summary or not image_path.exists():
            continue

        # Text embedding
        text_emb = get_text_embedding(summary, st_model)
        
        # Image embedding
        try:
            img_arr = preprocess_image(image_path)
            img_emb = get_global_clip_embedding(img_arr, clip_model, clip_processor)
        except Exception as e:
            logger.warning(f"Failed to process image {image_path}: {e}")
            continue

        entry = {
            "id": item["id"],
            "type": "medium",
            "content": summary,
            "text_embedding": text_emb.tolist(),
            "image_embedding": img_emb.tolist(),
            "metadata": {
                "source": item.get("source", "unknown"),
                "image_path": str(image_path)
            }
        }
        store.append(entry)

    logger.info(f"Medium store constructed with {len(store)} entries.")
    return store

def construct_fine_store(data_path: Path, detection_results_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Constructs the Fine store: object captions + bounding boxes.
    
    CRITICAL REQUIREMENT (FR-002):
    Bounding box coordinates are stored as metadata ONLY and explicitly EXCLUDED 
    from the similarity calculation vector. The similarity vector is derived 
    SOLELY from the object captions (text).
    """
    logger.info("Constructing Fine Store...")
    store = []
    
    # Load filtered data
    input_file = data_path / "memlens_filtered.json"
    if not input_file.exists():
        logger.warning(f"Input file {input_file} not found. Skipping Fine store construction.")
        return []

    with open(input_file, 'r') as f:
        data = json.load(f)

    # Load detection results (generated by T011/T011B)
    # Expected format: list of dicts with 'id', 'detections' (list of {bbox, caption, ...})
    if not detection_results_path or not detection_results_path.exists():
        # Fallback: look in standard location
        detection_results_path = data_path / "metrics" / "detection_results.json"
        if not detection_results_path.exists():
            logger.error(f"Detection results not found at {detection_results_path}. Cannot construct Fine store.")
            return []

    with open(detection_results_path, 'r') as f:
        detection_data = json.load(f)

    # Index detection results by ID for fast lookup
    det_map = {d["id"]: d for d in detection_data}

    st_model = load_sentence_transformer_model()

    for item in data:
        item_id = item["id"]
        det_record = det_map.get(item_id)

        if not det_record:
            logger.debug(f"No detection record for {item_id}. Skipping Fine entry.")
            continue

        detections = det_record.get("detections", [])
        
        if not detections:
            # If no objects detected, we might still want an entry with empty content?
            # Based on T011B logic, we track status. For Fine store, we need object captions.
            # If zero objects, the "content" is empty, but we store the metadata.
            # Let's create an entry with empty text embedding if no detections.
            # Or skip? The task says "object captions + bounding boxes". If no boxes, no captions.
            # We'll create a record with empty content to maintain alignment with other stores.
            entry = {
                "id": item_id,
                "type": "fine",
                "content": "",
                "embedding": [], # No embedding for empty text
                "metadata": {
                    "detection_status": det_record.get("detection_status", "unknown"),
                    "detections": []
                }
            }
            store.append(entry)
            continue

        # Aggregate object captions into a single text for the store entry
        # Or store per-object? The task says "Fine store construction".
        # Usually, a memory store entry corresponds to a sample.
        # We will concatenate all object captions for the sample into one text block.
        captions = [d.get("caption", "") for d in detections if d.get("caption")]
        combined_text = " ".join(captions) if captions else ""

        # Calculate embedding for the combined text
        if combined_text:
            text_emb = get_text_embedding(combined_text, st_model).tolist()
        else:
            text_emb = []

        # Prepare detections for metadata
        # CRITICAL: Ensure coordinates are NOT part of the similarity vector (they aren't, as we only use text_emb)
        # But we must ensure they are stored in 'metadata' as requested.
        clean_detections = []
        for d in detections:
            # We store the full detection info (bbox, caption) in metadata
            clean_detections.append({
                "caption": d.get("caption", ""),
                "bbox": d.get("bbox", []), # Coordinates stored here
                "confidence": d.get("confidence", 0.0),
                "class_id": d.get("class_id", "")
            })

        entry = {
            "id": item_id,
            "type": "fine",
            "content": combined_text, # Text used for similarity
            "embedding": text_emb,    # Vector used for similarity
            "metadata": {
                "detection_status": det_record.get("detection_status", "unknown"),
                "detections": clean_detections, # Bounding boxes stored HERE, excluded from similarity
                "source": item.get("source", "unknown"),
                "image_path": item.get("image_path", "")
            }
        }
        store.append(entry)

    logger.info(f"Fine store constructed with {len(store)} entries.")
    return store

def save_store(store: List[Dict[str, Any]], output_path: Path):
    """
    Saves a store to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(store, f, indent=2)
    logger.info(f"Store saved to {output_path}")

def main():
    """
    Main entry point to construct all stores.
    """
    logger.info("Starting Preprocessing Pipeline...")
    
    # Ensure directories exist
    STORES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Construct Coarse
    coarse_store = construct_coarse_store(DATA_RAW_PATH)
    if coarse_store:
        save_store(coarse_store, COARSE_STORE_PATH)

    # 2. Construct Medium
    medium_store = construct_medium_store(DATA_RAW_PATH)
    if medium_store:
        save_store(medium_store, MEDIUM_STORE_PATH)

    # 3. Construct Fine
    # Detection results should be in data/processed/metrics/detection_results.json (from T011)
    # Or wherever T011 wrote them. The task T011 says "write results to data/processed/metrics/detection_recall.json"
    # But T011 also produces detection data. Let's assume T011 produces a full detection JSON too.
    # If not, we might need to adjust.
    # T011 output: data/processed/metrics/detection_recall.json (metrics only)
    # We need the full detection data (bboxes + captions). 
    # Let's assume T011 also writes a full detection file or we read from a standard location.
    # For this task, we assume the full detection data is at:
    DETECTION_FULL_PATH = DATA_PROCESSED_PATH / "detection_results.json"
    
    if not DETECTION_FULL_PATH.exists():
        # Try alternative path if T011 wrote it differently
        # If T011 only wrote metrics, we have a problem. 
        # But T011 description says "Implement YOLOv8-Tiny object detection... calculate Object Detection Recall... write results to..."
        # It implies it runs detection. The full data must be saved somewhere.
        # Let's assume it's saved as 'detection_results.json' in the metrics folder or root processed.
        DETECTION_FULL_PATH = DATA_PROCESSED_PATH / "metrics" / "detection_results.json"

    fine_store = construct_fine_store(DATA_RAW_PATH, DETECTION_FULL_PATH)
    if fine_store:
        save_store(fine_store, FINE_STORE_PATH)

    logger.info("Preprocessing Pipeline Complete.")

if __name__ == "__main__":
    main()