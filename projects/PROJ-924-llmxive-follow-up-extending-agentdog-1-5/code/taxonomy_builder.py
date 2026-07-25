import json
import os
import sys
import tracemalloc
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import get_path, get_max_memory_gb, get_centroid_model
from utils import load_json_file, save_json_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MAX_RAM_GB = 7.0

def load_taxonomy(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load the mapped taxonomy from JSON."""
    if path is None:
        path = str(get_path("data/raw/taxonomy_agentdog.json"))
    logger.info(f"Loading taxonomy from {path}")
    return load_json_file(path)

def build_centroids(taxonomy: List[Dict[str, Any]], model_name: str = "all-MiniLM-L6-v2") -> Dict[str, Any]:
    """
    Build centroid embeddings for the taxonomy categories.
    Enforces a strict peak RAM limit of < 7GB using tracemalloc.
    
    Args:
        taxonomy: List of taxonomy entries with 'category' and 'subcategories'.
        model_name: HuggingFace model name for embeddings.
        
    Returns:
        Dictionary containing 'centroids' (list of {category, embedding}) and 'stats'.
        
    Raises:
        MemoryError: If peak RAM usage exceeds MAX_RAM_GB.
    """
    logger.info(f"Starting centroid generation with model: {model_name}")
    
    # Start memory profiling
    tracemalloc.start()
    peak_memory_mb = 0.0
    
    try:
        # Check if we can import the model (lazy import to avoid heavy load if not needed)
        # We assume sentence-transformers is installed as per requirements.txt
        from sentence_transformers import SentenceTransformer
        
        # Load model
        logger.info("Loading SentenceTransformer model...")
        model = SentenceTransformer(model_name)
        
        # Process taxonomy entries
        centroids = []
        current_memory_mb, _ = tracemalloc.get_traced_memory()
        peak_memory_mb = max(peak_memory_mb, current_memory_mb / 1024 / 1024)
        
        # Check memory after model load
        if peak_memory_mb / 1024 > MAX_RAM_GB:
            raise MemoryError(f"Peak memory after model load ({peak_memory_mb/1024:.2f} GB) exceeds limit of {MAX_RAM_GB} GB")
        
        # Extract categories and their descriptions for embedding
        # Assuming taxonomy structure: [{'category': 'Name', 'description': 'Desc', ...}, ...]
        texts_to_embed = []
        category_map = {}
        
        for idx, entry in enumerate(taxonomy):
            category_name = entry.get('category', f"Unknown_{idx}")
            description = entry.get('description', '')
            # Combine category name and description for better embedding
            text = f"{category_name}: {description}".strip() if description else category_name
            texts_to_embed.append(text)
            category_map[idx] = category_name
        
        logger.info(f"Processing {len(texts_to_embed)} taxonomy categories...")
        
        # Process in batches to manage memory
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(texts_to_embed), batch_size):
            batch_texts = texts_to_embed[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch_texts)} items)")
            
            # Generate embeddings
            batch_embeddings = model.encode(batch_texts, convert_to_numpy=True, show_progress_bar=False)
            
            # Convert to list of lists if necessary
            if len(batch_embeddings.shape) == 1:
                batch_embeddings = batch_embeddings.reshape(1, -1)
                
            all_embeddings.extend(batch_embeddings.tolist())
            
            # Check memory after each batch
            current_memory_mb, _ = tracemalloc.get_traced_memory()
            peak_memory_mb = max(peak_memory_mb, current_memory_mb / 1024 / 1024)
            
            # Strict check: if we exceed 7GB, raise immediately
            if peak_memory_mb / 1024 > MAX_RAM_GB:
                raise MemoryError(
                    f"Peak memory usage ({peak_memory_mb/1024:.2f} GB) exceeded limit of {MAX_RAM_GB} GB "
                    f"during centroid generation at batch {i//batch_size + 1}"
                )
        
        # Build result structure
        for idx, emb in enumerate(all_embeddings):
          centroids.append({
              "category": category_map[idx],
              "embedding": emb
          })
        
        logger.info(f"Centroid generation complete. Peak memory: {peak_memory_mb/1024:.2f} GB")
        
        return {
            "centroids": centroids,
            "stats": {
                "total_categories": len(centroids),
                "peak_memory_gb": peak_memory_mb / 1024,
                "model_used": model_name
            }
        }
        
    finally:
        # Stop memory profiling
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        logger.info(f"Memory profiling stopped. Final: {current/1024/1024:.2f} MB, Peak: {peak/1024/1024:.2f} MB")

def save_centroids(data: Dict[str, Any], path: Optional[str] = None) -> str:
    """Save centroids to JSON file."""
    if path is None:
        path = str(get_path("data/processed/taxonomy_centroids.json"))
    
    logger.info(f"Saving centroids to {path}")
    save_json_file(path, data)
    logger.info("Centroids saved successfully")
    return path

def main():
    """Main entry point for taxonomy centroid generation."""
    logger.info("Starting taxonomy centroid generation pipeline")
    
    # Load taxonomy
    taxonomy_path = str(get_path("data/raw/taxonomy_agentdog.json"))
    if not os.path.exists(taxonomy_path):
        raise FileNotFoundError(f"Taxonomy file not found at {taxonomy_path}. Run T013-map first.")
    
    taxonomy = load_taxonomy(taxonomy_path)
    if not taxonomy:
        raise ValueError("Taxonomy is empty. Cannot generate centroids.")
    
    # Build centroids with memory monitoring
    model_name = get_centroid_model()
    result = build_centroids(taxonomy, model_name)
    
    # Save results
    output_path = save_centroids(result)
    
    logger.info(f"Pipeline completed successfully. Output: {output_path}")
    return output_path

if __name__ == "__main__":
    main()