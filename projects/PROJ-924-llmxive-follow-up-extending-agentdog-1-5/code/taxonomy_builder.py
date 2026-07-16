"""
taxonomy_builder.py

Generates centroid embeddings for the AgentDoG 1.5 taxonomy categories.
Uses 'all-MiniLM-L6-v2' on CPU with batching to ensure memory usage < 100MB.
Input: data/raw/taxonomy.json (produced by T005d)
Output: data/processed/taxonomy_centroids.json
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports if running as script
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

import numpy as np
from sentence_transformers import SentenceTransformer
from config import get_path, ensure_directories, get_config_summary
from utils import save_json_file, load_json_file
from data_loader import fetch_taxonomy

# Constants
MODEL_NAME = "all-MiniLM-L6-v2"
INPUT_FILE_REL = "data/raw/taxonomy.json"
OUTPUT_FILE_REL = "data/processed/taxonomy_centroids.json"
BATCH_SIZE = 32  # Small batch to fit <100MB RAM on CPU
MAX_TOKENS = 128 # Truncate to fit model and save memory

def load_taxonomy(input_path: Path) -> Dict[str, Any]:
    """
    Loads the taxonomy JSON structure.
    Expected format: {"categories": [{"id": "...", "name": "...", "description": "..."}, ...]}
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Taxonomy file not found at {input_path}. "
                                "Please ensure T005d has run successfully.")
    return load_json_file(input_path)

def build_centroids(taxonomy_data: Dict[str, Any], model: SentenceTransformer) -> List[Dict[str, Any]]:
    """
    Iterates through taxonomy categories, constructs a text representation
    (name + description), encodes it, and computes the centroid.
    Since each category is a single entry initially, the centroid is just the embedding of that entry.
    If the taxonomy structure groups items under categories later, this would aggregate them.
    For now, we assume 1 item -> 1 centroid per category.
    """
    categories = taxonomy_data.get("categories", [])
    if not categories:
        raise ValueError("Taxonomy file contains no categories.")

    print(f"Processing {len(categories)} categories...")
    results = []

    # Prepare texts in batches to manage memory
    # We process in chunks to avoid loading all embeddings into memory at once if the list is huge,
    # though for a taxonomy it's likely manageable. We'll stick to batched encoding.
    
    texts = []
    category_map = {} # index -> category info
    
    for idx, cat in enumerate(categories):
        name = cat.get("name", "")
        desc = cat.get("description", "")
        # Combine name and description for embedding context
        text = f"{name}: {desc}" if desc else name
        texts.append(text)
        category_map[idx] = {
            "id": cat.get("id"),
            "name": name,
            "description": desc,
            "original": cat
        }

    # Batch encoding
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i : i + BATCH_SIZE]
        # Truncate if necessary (model usually handles, but good practice)
        batch_texts = [t[:MAX_TOKENS] for t in batch_texts]
        
        embeddings = model.encode(batch_texts, convert_to_numpy=True, show_progress_bar=False)
        all_embeddings.append(embeddings)
        
        # Log progress
        if (i + BATCH_SIZE) % (BATCH_SIZE * 10) == 0 or (i + BATCH_SIZE) == len(texts):
            print(f"  Encoded {min(i + BATCH_SIZE, len(texts))} / {len(texts)} categories...")

    all_embeddings = np.vstack(all_embeddings) if all_embeddings else np.array([])

    # Construct output
    for idx, cat_info in category_map.items():
        if len(all_embeddings) > idx:
            emb = all_embeddings[idx].tolist()
            results.append({
                "category_id": cat_info["id"],
                "category_name": cat_info["name"],
                "centroid_embedding": emb,
                "embedding_dim": len(emb),
                "source_text": f"{cat_info['name']}: {cat_info['description']}"
            })
        else:
            # Should not happen if logic is correct
            results.append({
                "category_id": cat_info["id"],
                "category_name": cat_info["name"],
                "centroid_embedding": [],
                "embedding_dim": 0,
                "source_text": f"{cat_info['name']}: {cat_info['description']}",
                "error": "Embedding generation failed for this category"
            })

    return results

def main():
    """Main entry point for the taxonomy builder."""
    print("Starting Taxonomy Centroid Builder...")
    
    # 1. Ensure directories exist
    input_path = get_path(INPUT_FILE_REL)
    output_path = get_path(OUTPUT_FILE_REL)
    ensure_directories([output_path])

    # 2. Load Taxonomy
    print(f"Loading taxonomy from {input_path}...")
    try:
        taxonomy_data = load_taxonomy(input_path)
    except FileNotFoundError as e:
        print(f"CRITICAL ERROR: {e}")
        print("This task depends on T005d (fetch_taxonomy). Please run T005d first.")
        sys.exit(1)

    # 3. Load Model (CPU-first)
    print(f"Loading model '{MODEL_NAME}' (CPU)...")
    try:
        model = SentenceTransformer(MODEL_NAME, device="cpu")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to load model '{MODEL_NAME}'.")
        print(f"Reason: {e}")
        print("Ensure 'sentence-transformers' is installed and the model is available.")
        sys.exit(1)

    # 4. Build Centroids
    print("Building centroids...")
    centroids = build_centroids(taxonomy_data, model)

    # 5. Save Output
    print(f"Saving centroids to {output_path}...")
    save_json_file(output_path, {
        "model": MODEL_NAME,
        "embedding_dim": len(centroids[0]["centroid_embedding"]) if centroids else 0,
        "total_categories": len(centroids),
        "centroids": centroids
    })

    print("Taxonomy centroid generation complete.")
    print(get_config_summary())

if __name__ == "__main__":
    main()
