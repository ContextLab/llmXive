"""
Compute Semantic Similarity (T016).

Computes cosine similarity between Recipe1M embeddings for ingredient pairs.
Excludes pairs with missing embeddings and logs statistics.
Output: data/processed/flavor_similarity.parquet
"""
import os
import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial.distance import cosine
from tqdm import tqdm

# Import from local utils if needed, otherwise standard
try:
    from utils.memory_monitor import check_memory_limit
except ImportError:
    def check_memory_limit(limit_mb=6144):
        # Fallback if memory monitor not fully set up yet
        pass

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

EMBEDDINGS_FILE = RAW_DIR / "recipe1m_embeddings.parquet"
INGREDIENT_PAIRS_FILE = PROCESSED_DIR / "ingredient_pairs.csv"
OUTPUT_FILE = PROCESSED_DIR / "flavor_similarity.parquet"
LOG_FILE = PROCESSED_DIR / "similarity_log.json"

def load_ingredient_pairs():
    """Load the ingredient pairs dataframe."""
    if not INGREDIENT_PAIRS_FILE.exists():
        raise FileNotFoundError(f"Ingredient pairs file not found: {INGREDIENT_PAIRS_FILE}")
    
    # Try to load as CSV, fallback to parquet if needed based on task history
    try:
        df = pd.read_csv(INGREDIENT_PAIRS_FILE)
    except Exception:
        try:
            df = pd.read_parquet(INGREDIENT_PAIRS_FILE.with_suffix('.parquet'))
        except Exception:
            raise FileNotFoundError(f"Could not load ingredient pairs from {INGREDIENT_PAIRS_FILE}")
    
    return df

def load_embeddings():
    """Load Recipe1M embeddings from the raw dataset."""
    if not EMBEDDINGS_FILE.exists():
        # Fallback check: maybe it's in a subfolder or different name
        # Attempt to find embeddings in raw directory
        raw_files = list(RAW_DIR.glob("*.parquet"))
        if not raw_files:
            raise FileNotFoundError(f"Embeddings file not found at {EMBEDDINGS_FILE} and no parquet files in {RAW_DIR}")
        
        # Heuristic: look for a file containing 'embedding' or 'recipe1m'
        embeddings_file = None
        for f in raw_files:
            name = f.name.lower()
            if 'embedding' in name or 'recipe1m' in name:
                embeddings_file = f
                break
        
        if not embeddings_file:
            # If still not found, raise error as per strict data policy
            raise FileNotFoundError(f"Embeddings file not found at {EMBEDDINGS_FILE}. Please run T051/T013 first.")
        else:
            EMBEDDINGS_FILE = embeddings_file

    try:
        # Recipe1M embeddings are often large; load in chunks if necessary
        # Assuming standard Recipe1M structure with 'embedding' column
        df = pd.read_parquet(EMBEDDINGS_FILE)
        
        # Verify required columns
        if 'ingredient' not in df.columns and 'ingredient_id' not in df.columns:
            raise ValueError(f"Embeddings file must contain 'ingredient' or 'ingredient_id' column. Found: {df.columns.tolist()}")
        
        # Normalize column name
        if 'ingredient_id' in df.columns:
            df = df.rename(columns={'ingredient_id': 'ingredient'})
        
        # Ensure embedding column exists
        if 'embedding' not in df.columns:
            # Check for common variations
            emb_cols = [c for c in df.columns if 'embed' in c.lower()]
            if emb_cols:
                df = df.rename(columns={emb_cols[0]: 'embedding'})
            else:
                raise ValueError(f"Embeddings file must contain 'embedding' column. Found: {df.columns.tolist()}")
        
        # Convert embeddings to numpy arrays
        # The embedding column might be stored as lists or arrays in parquet
        def parse_embedding(emb):
            if isinstance(emb, np.ndarray):
                return emb
            elif isinstance(emb, list):
                return np.array(emb, dtype=np.float32)
            else:
                return None

        df['embedding_vec'] = df['embedding'].apply(parse_embedding)
        
        # Filter out rows where embedding parsing failed
        valid_df = df[df['embedding_vec'].notna()].copy()
        
        return valid_df[['ingredient', 'embedding_vec']]
        
    except Exception as e:
        raise RuntimeError(f"Failed to load embeddings: {e}")

def compute_cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors."""
    if vec1 is None or vec2 is None:
        return np.nan
    
    # Handle zero vectors (though unlikely in embeddings)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    # Cosine similarity = dot product / (norm1 * norm2)
    similarity = np.dot(vec1, vec2) / (norm1 * norm2)
    
    # Clip to [-1, 1] to handle floating point errors
    return float(np.clip(similarity, -1.0, 1.0))

def process_similarity(pairs_df, embeddings_df, log_events):
    """
    Process ingredient pairs and compute cosine similarity.
    
    Args:
        pairs_df: DataFrame with ingredient pairs
        embeddings_df: DataFrame with ingredient embeddings
        log_events: List to append log entries
        
    Returns:
        DataFrame with similarity scores
    """
    # Create a lookup dictionary for embeddings
    emb_lookup = embeddings_df.set_index('ingredient')['embedding_vec'].to_dict()
    
    total_pairs = len(pairs_df)
    processed = 0
    missing_embeddings = 0
    valid_similarities = 0
    
    results = []
    
    # Check memory limit periodically
    check_memory_limit()
    
    for idx, row in tqdm(pairs_df.iterrows(), total=total_pairs, desc="Computing Similarity"):
        # Get ingredient names (handle potential column name variations)
        ing1 = row.get('ingredient_1') or row.get('ingredient1') or row.get('ingredient_A')
        ing2 = row.get('ingredient_2') or row.get('ingredient2') or row.get('ingredient_B')
        
        if pd.isna(ing1) or pd.isna(ing2):
            missing_embeddings += 1
            results.append({
                'ingredient_1': ing1,
                'ingredient_2': ing2,
                'cosine_similarity': np.nan,
                'status': 'missing_embedding'
            })
            continue
        
        # Retrieve embeddings
        vec1 = emb_lookup.get(ing1)
        vec2 = emb_lookup.get(ing2)
        
        if vec1 is None or vec2 is None:
            missing_embeddings += 1
            results.append({
                'ingredient_1': ing1,
                'ingredient_2': ing2,
                'cosine_similarity': np.nan,
                'status': 'missing_embedding'
            })
            continue
        
        # Compute similarity
        sim = compute_cosine_similarity(vec1, vec2)
        
        if not np.isnan(sim):
            valid_similarities += 1
        
        results.append({
            'ingredient_1': ing1,
            'ingredient_2': ing2,
            'cosine_similarity': sim,
            'status': 'computed'
        })
        
        processed += 1
        
        # Check memory every 10k rows
        if processed % 10000 == 0:
            check_memory_limit()
    
    log_events.append({
        'event': 'similarity_computation_complete',
        'total_pairs': total_pairs,
        'processed': processed,
        'missing_embeddings': missing_embeddings,
        'valid_similarities': valid_similarities,
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
    })
    
    return pd.DataFrame(results)

def main():
    """Main entry point for T016."""
    print("Starting Semantic Similarity computation (T016)...")
    
    # Ensure output directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    log_events = []
    
    try:
        # Step 1: Load ingredient pairs
        print("Loading ingredient pairs...")
        pairs_df = load_ingredient_pairs()
        print(f"Loaded {len(pairs_df)} ingredient pairs.")
        
        # Step 2: Load embeddings
        print("Loading embeddings...")
        embeddings_df = load_embeddings()
        print(f"Loaded {len(embeddings_df)} ingredient embeddings.")
        
        # Step 3: Compute similarities
        print("Computing cosine similarities...")
        start_time = time.time()
        result_df = process_similarity(pairs_df, embeddings_df, log_events)
        elapsed = time.time() - start_time
        
        log_events.append({
            'event': 'processing_time',
            'elapsed_seconds': elapsed
        })
        
        # Step 4: Save results
        print(f"Saving results to {OUTPUT_FILE}...")
        result_df.to_parquet(OUTPUT_FILE, index=False)
        print(f"Saved {len(result_df)} rows to {OUTPUT_FILE}")
        
        # Step 5: Save log
        log_file_path = LOG_FILE
        with open(log_file_path, 'w') as f:
            json.dump(log_events, f, indent=2)
        print(f"Log saved to {log_file_path}")
        
        # Summary
        valid_count = result_df['cosine_similarity'].notna().sum()
        print(f"\nT016 Complete:")
        print(f"  - Total pairs processed: {len(result_df)}")
        print(f"  - Valid similarities computed: {valid_count}")
        print(f"  - Missing embeddings excluded: {len(result_df) - valid_count}")
        print(f"  - Output file: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"Error during T016 execution: {e}")
        log_events.append({
            'event': 'error',
            'error_message': str(e),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
        })
        
        # Still save log even on error
        log_file_path = LOG_FILE
        with open(log_file_path, 'w') as f:
            json.dump(log_events, f, indent=2)
        
        sys.exit(1)

if __name__ == "__main__":
    main()
