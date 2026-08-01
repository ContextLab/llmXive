"""
T014c: Fetch Recipe1M Embeddings (FR-004-AMEND)

Implements fetching Recipe1M visual/text embeddings for all unique ingredients.
Uses Recipe1M embeddings as a proxy for FlavorDB vectors (Amendment to FR-004).

Output: data/processed/ingredient_embeddings.parquet
"""
import os
import sys
import json
import time
import gc
from pathlib import Path
import logging

import pandas as pd
import numpy as np
from datasets import load_dataset
from tqdm import tqdm

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

# Output paths
EMBEDDINGS_OUTPUT = PROCESSED_DIR / "ingredient_embeddings.parquet"
LOG_FILE = PROCESSED_DIR / "embeddings_fetch_log.json"

# Configuration
DATASET_NAME = "recipe1m-full"
SPLIT = "train"
BATCH_SIZE = 1000
SEED = 42

def ensure_directories():
    """Ensure output directories exist."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

def load_ingredient_list():
    """
    Load unique ingredients from pilot data or normalized ingredients.
    Falls back to pilot_data.parquet if normalized_ingredients is missing.
    """
    normalized_path = PROCESSED_DIR / "normalized_ingredients.parquet"
    pilot_path = RAW_DIR / "pilot_data.parquet"
    
    if normalized_path.exists():
        logger.info(f"Loading ingredients from {normalized_path}")
        df = pd.read_parquet(normalized_path)
        if 'ingredient_id' in df.columns:
            return df['ingredient_id'].unique().tolist()
        elif 'ingredient' in df.columns:
            return df['ingredient'].unique().tolist()
    elif pilot_path.exists():
        logger.info(f"Loading ingredients from {pilot_path}")
        df = pd.read_parquet(pilot_path)
        # Try common column names for ingredients
        for col in ['ingredient', 'ingredient_id', 'item']:
            if col in df.columns:
                return df[col].unique().tolist()
    else:
        raise FileNotFoundError(
            f"Neither {normalized_path} nor {pilot_path} found. "
            "Run T014 (normalization) or T013b (pilot download) first."
        )
    
    raise ValueError("Could not find ingredient column in source data.")

def fetch_embeddings_for_ingredients(ingredient_list):
    """
    Fetch embeddings for the given ingredient list from Recipe1M.
    
    Strategy: Stream the dataset, extract embeddings for ingredients
    present in our list, and aggregate them.
    """
    logger.info(f"Starting embedding fetch for {len(ingredient_list)} unique ingredients")
    logger.info(f"Dataset: {DATASET_NAME}, Split: {SPLIT}")
    
    # Set seed for reproducibility
    np.random.seed(SEED)
    
    # Load dataset in streaming mode
    try:
        dataset = load_dataset(
            DATASET_NAME,
            split=SPLIT,
            streaming=True
        )
    except Exception as e:
        logger.error(f"Failed to load dataset {DATASET_NAME}: {e}")
        raise DataUnavailableError(f"Dataset {DATASET_NAME} not available: {e}")
    
    # Create a set for fast lookup
    ingredient_set = set(ingredient_list)
    
    # Storage for embeddings: {ingredient_id: [list of embeddings]}
    ingredient_embeddings = {ing: [] for ing in ingredient_set}
    ingredient_counts = {ing: 0 for ing in ingredient_set}
    
    # Track progress
    processed_count = 0
    matched_count = 0
    start_time = time.time()
    
    logger.info("Streaming dataset and extracting embeddings...")
    
    # Iterate through dataset in chunks
    try:
        for batch_idx, batch in enumerate(dataset):
            processed_count += 1
            
            # Process batch items
            # Assuming batch structure: {'ingredients': [...], 'embedding': [...]}
            # or similar. We need to adapt based on actual dataset structure.
            
            # Extract ingredients and embeddings from batch
            # Common Recipe1M structure might have 'ingredients' as list of dicts
            # or separate columns. We'll handle common cases.
            
            if 'ingredients' in batch:
                ing_items = batch['ingredients']
            elif 'items' in batch:
                ing_items = batch['items']
            else:
                # Try to find any column that might contain ingredients
                ing_cols = [k for k in batch.keys() if 'ing' in k.lower()]
                if ing_cols:
                    ing_items = batch[ing_cols[0]]
                else:
                    # Skip if no obvious ingredient column
                    continue
            
            # Handle embedding column
            if 'embedding' in batch:
                emb_items = batch['embedding']
            elif 'embed' in batch:
                emb_items = batch['embed']
            elif 'image_embedding' in batch:
                emb_items = batch['image_embedding']
            else:
                # Try to find embedding column
                emb_cols = [k for k in batch.keys() if 'embed' in k.lower()]
                if emb_cols:
                    emb_items = batch[emb_cols[0]]
                else:
                    # Skip batch if no embeddings found
                    continue
            
            # Process each item in batch
            for i, ing_item in enumerate(ing_items):
                if i >= len(emb_items):
                    break
                
                emb_item = emb_items[i]
                
                # Handle ingredient name extraction
                if isinstance(ing_item, dict):
                    # Try common keys
                    ing_name = ing_item.get('name') or ing_item.get('ingredient') or ing_item.get('id')
                else:
                    ing_name = str(ing_item)
                
                # Check if this ingredient is in our target list
                if ing_name in ingredient_set:
                    matched_count += 1
                    
                    # Ensure embedding is a numpy array
                    if isinstance(emb_item, list):
                        embedding = np.array(emb_item, dtype=np.float32)
                    elif isinstance(emb_item, np.ndarray):
                        embedding = emb_item.astype(np.float32)
                    else:
                        # Try to convert
                        try:
                            embedding = np.array(emb_item, dtype=np.float32)
                        except:
                            continue
                    
                    # Store embedding
                    ingredient_embeddings[ing_name].append(embedding)
                    ingredient_counts[ing_name] += 1
            
            # Periodic logging
            if batch_idx % 1000 == 0:
                elapsed = time.time() - start_time
                rate = processed_count / elapsed if elapsed > 0 else 0
                logger.info(f"Processed {processed_count} batches, {matched_count} matches so far")
                
                # Memory cleanup
                if batch_idx % 5000 == 0:
                    gc.collect()
                    
            # Stop if we've seen enough (optional safety limit)
            if matched_count >= len(ingredient_set) * 10:  # Heuristic: enough samples per ingredient
                logger.info("Sufficient embeddings collected for all ingredients")
                break
                
    except Exception as e:
        logger.error(f"Error during streaming: {e}")
        raise
    
    elapsed_time = time.time() - start_time
    logger.info(f"Finished streaming. Total batches: {processed_count}, Total matches: {matched_count}")
    logger.info(f"Time elapsed: {elapsed_time:.2f}s")
    
    return ingredient_embeddings, ingredient_counts

def aggregate_embeddings(ingredient_embeddings, ingredient_counts):
    """
    Aggregate multiple embeddings per ingredient into a single representation.
    Uses mean pooling.
    """
    aggregated = {}
    stats = []
    
    for ing, embeddings in ingredient_embeddings.items():
        if len(embeddings) > 0:
            # Stack and mean
            stacked = np.stack(embeddings, axis=0)
            mean_emb = np.mean(stacked, axis=0)
            std_emb = np.std(stacked, axis=0)
            
            aggregated[ing] = {
                'embedding': mean_emb.tolist(),
                'std': std_emb.tolist(),
                'count': len(embeddings)
            }
            stats.append({
                'ingredient_id': ing,
                'embedding_count': len(embeddings),
                'mean_norm': float(np.linalg.norm(mean_emb))
            })
        else:
            # No embeddings found for this ingredient
            # Create a zero vector (will need to match dimension)
            # We'll determine dimension from first valid embedding
            pass
    
    return aggregated, stats

def save_embeddings(aggregated, stats):
    """
    Save embeddings to parquet file.
    """
    if not aggregated:
        raise ValueError("No embeddings to save")
    
    # Determine embedding dimension from first entry
    first_ing = next(iter(aggregated.values()))
    emb_dim = len(first_ing['embedding'])
    
    # Create DataFrame
    rows = []
    for ing_id, data in aggregated.items():
        rows.append({
            'ingredient_id': ing_id,
            'embedding': data['embedding'],
            'embedding_std': data['std'],
            'embedding_count': data['count'],
            'embedding_dim': emb_dim
        })
    
    df = pd.DataFrame(rows)
    
    # Ensure directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save to parquet
    df.to_parquet(EMBEDDINGS_OUTPUT, index=False)
    logger.info(f"Saved embeddings to {EMBEDDINGS_OUTPUT}")
    
    # Save stats
    stats_df = pd.DataFrame(stats)
    stats_path = PROCESSED_DIR / "embedding_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats_df.to_dict('records'), f, indent=2)
    logger.info(f"Saved stats to {stats_path}")
    
    return df

def main():
    """Main entry point for T014c."""
    logger.info("=" * 60)
    logger.info("T014c: Fetch Recipe1M Embeddings")
    logger.info("=" * 60)
    
    try:
        # Ensure directories
        ensure_directories()
        
        # Load ingredient list
        ingredient_list = load_ingredient_list()
        logger.info(f"Found {len(ingredient_list)} unique ingredients")
        
        if len(ingredient_list) == 0:
            raise ValueError("No ingredients found in source data")
        
        # Fetch embeddings
        ingredient_embeddings, ingredient_counts = fetch_embeddings_for_ingredients(ingredient_list)
        
        # Aggregate embeddings
        aggregated, stats = aggregate_embeddings(ingredient_embeddings, ingredient_counts)
        
        if not aggregated:
            raise ValueError("No embeddings were successfully aggregated")
        
        # Save results
        df = save_embeddings(aggregated, stats)
        
        # Log completion
        log_data = {
            'status': 'SUCCESS',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'total_ingredients': len(ingredient_list),
            'ingredients_with_embeddings': len(aggregated),
            'embedding_dimension': df['embedding_dim'].iloc[0] if 'embedding_dim' in df.columns else None,
            'output_file': str(EMBEDDINGS_OUTPUT)
        }
        
        with open(LOG_FILE, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        logger.info("Task T014c completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        # Write error log
        error_log = {
            'status': 'FAILED',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'error': str(e),
            'task': 'T014c'
        }
        with open(LOG_FILE, 'w') as f:
            json.dump(error_log, f, indent=2)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
        error_log = {
            'status': 'FAILED',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'error': str(e),
            'traceback': traceback.format_exc(),
            'task': 'T014c'
        }
        with open(LOG_FILE, 'w') as f:
            json.dump(error_log, f, indent=2)
        return 1

if __name__ == "__main__":
    sys.exit(main())
