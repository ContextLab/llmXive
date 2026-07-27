import os
import sys
import json
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
from tqdm import tqdm

# Import memory monitor for RAM enforcement
try:
    from utils.memory_monitor import check_memory_limit
except ImportError:
    # Fallback if running as script directly without package structure
    def check_memory_limit(limit_mb=6144):
        import psutil
        import os
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / (1024 * 1024)
        if mem_mb > limit_mb:
            raise MemoryError(f"Memory limit exceeded: {mem_mb:.2f}MB > {limit_mb}MB")

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

# Output paths
INGREDIENT_PAIRS_PATH = PROCESSED_DIR / "ingredient_pairs.parquet"
EMBEDDINGS_PATH = RAW_DIR / "recipe1m_embeddings.parquet"
OUTPUT_PATH = PROCESSED_DIR / "flavor_similarity.parquet"
LOG_PATH = DATA_DIR / "similarity_computation_log.json"

def load_ingredient_pairs() -> pd.DataFrame:
    """Load the preprocessed ingredient pairs."""
    if not INGREDIENT_PAIRS_PATH.exists():
        raise FileNotFoundError(f"Ingredient pairs file not found: {INGREDIENT_PAIRS_PATH}. Run T013/T015 first.")
    
    df = pd.read_parquet(INGREDIENT_PAIRS_PATH)
    required_cols = ['ingredient_1', 'ingredient_2']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Ingredient pairs file missing required columns: {required_cols}")
    return df

def load_embeddings() -> Dict[str, np.ndarray]:
    """Load ingredient embeddings from the downloaded dataset."""
    if not EMBEDDINGS_PATH.exists():
        raise FileNotFoundError(f"Embeddings file not found: {EMBEDDINGS_PATH}. Run T051/T013 first.")
    
    # Load embeddings parquet
    # Expected schema: ingredient_id, embedding_vector (as list or array)
    df = pd.read_parquet(EMBEDDINGS_PATH)
    
    if 'ingredient_id' not in df.columns or 'embedding_vector' not in df.columns:
        raise ValueError(f"Embeddings file missing required columns. Found: {df.columns.tolist()}")
    
    embeddings = {}
    for _, row in df.iterrows():
        emb = np.array(row['embedding_vector'], dtype=np.float32)
        embeddings[row['ingredient_id']] = emb
    
    return embeddings

def compute_cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))

def main():
    """Main execution for T016: Semantic Similarity computation."""
    print("Starting T016: Semantic Similarity computation...")
    
    # Ensure output directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    log_data = {
        "status": "STARTED",
        "timestamp": pd.Timestamp.now().isoformat(),
        "input_pairs": None,
        "valid_pairs": 0,
        "missing_embeddings": 0,
        "output_path": str(OUTPUT_PATH)
    }

    try:
        # 1. Load ingredient pairs
        print("Loading ingredient pairs...")
        pairs_df = load_ingredient_pairs()
        log_data["input_pairs"] = len(pairs_df)
        print(f"  Loaded {len(pairs_df)} pairs.")

        # 2. Load embeddings
        print("Loading embeddings...")
        embeddings = load_embeddings()
        print(f"  Loaded {len(embeddings)} ingredient embeddings.")

        # 3. Compute similarities
        print("Computing cosine similarities...")
        results = []
        missing_count = 0
        
        # Batch processing to manage memory
        batch_size = 5000
        total = len(pairs_df)
        
        for i in tqdm(range(0, total, batch_size), desc="Processing batches"):
            batch = pairs_df.iloc[i:i+batch_size]
            check_memory_limit(limit_mb=6144) # Enforce RAM limit
            
            for _, row in batch.iterrows():
                ing1 = row['ingredient_1']
                ing2 = row['ingredient_2']
                
                # Check if both ingredients have embeddings
                if ing1 not in embeddings or ing2 not in embeddings:
                    missing_count += 1
                    continue
                
                sim = compute_cosine_similarity(embeddings[ing1], embeddings[ing2])
                results.append({
                    'ingredient_1': ing1,
                    'ingredient_2': ing2,
                    'flavor_similarity': sim
                })
            
            # Force garbage collection periodically
            if i % (batch_size * 5) == 0:
                gc.collect()

        # 4. Create output DataFrame
        if not results:
            print("Warning: No valid pairs with embeddings found. Creating empty output.")
            output_df = pd.DataFrame(columns=['ingredient_1', 'ingredient_2', 'flavor_similarity'])
        else:
            output_df = pd.DataFrame(results)
        
        # 5. Save results
        print(f"Saving results to {OUTPUT_PATH}...")
        output_df.to_parquet(OUTPUT_PATH, index=False)
        
        log_data["status"] = "SUCCESS"
        log_data["valid_pairs"] = len(results)
        log_data["missing_embeddings"] = missing_count
        log_data["completion_time"] = pd.Timestamp.now().isoformat()
        
        print(f"  Saved {len(results)} similarity records.")
        print(f"  Skipped {missing_count} pairs due to missing embeddings.")

    except Exception as e:
        log_data["status"] = "FAILED"
        log_data["error"] = str(e)
        print(f"Error during computation: {e}")
        raise
    finally:
        # Always write log
        with open(LOG_PATH, 'w') as f:
            json.dump(log_data, f, indent=2)
        print(f"Log written to {LOG_PATH}")

if __name__ == "__main__":
    main()
