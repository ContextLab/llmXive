"""
T013a: Stream & Validate Recipe1M Dataset.

Streams the Recipe1M dataset from HuggingFace, enforces sample size limits
based on pilot power analysis, validates schema, and saves to Parquet.
"""
import os
import sys
import json
import logging
import itertools
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
from datasets import load_dataset

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.memory_monitor import check_memory_limit, get_memory_usage_gb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / "data" / "logs" / "stream_recipe1m.log")
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure output directories exist."""
    output_dir = project_root / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "logs").mkdir(parents=True, exist_ok=True)

def load_sample_size_requirement():
    """Read sample_size_required from T013b output."""
    pilot_stats_path = project_root / "data" / "pilot_stats.json"
    if not pilot_stats_path.exists():
        logger.error(f"Pilot stats file not found: {pilot_stats_path}. Run T013b first.")
        raise FileNotFoundError(f"Pilot stats file not found: {pilot_stats_path}. Run T013b first.")

    with open(pilot_stats_path, "r") as f:
        data = json.load(f)

    if "sample_size_required" not in data:
        logger.error("sample_size_required key missing from pilot_stats.json")
        raise KeyError("sample_size_required key missing from pilot_stats.json")

    return int(data["sample_size_required"])

def load_amendment_log():
    """Check if we are in proxy mode (though T013a is Recipe1M specific)."""
    amendment_path = project_root / "data" / "amendment_log.json"
    if not amendment_path.exists():
        logger.warning("Amendment log not found. Proceeding assuming full causal path.")
        return {"status": "PENDING", "methodology": "Causal Independence"}
    
    with open(amendment_path, "r") as f:
        return json.load(f)

def stream_and_process_dataset(sample_limit: int):
    """
    Stream Recipe1M dataset, enforce sample limit, validate schema, and save.
    """
    logger.info("Starting Recipe1M streaming...")
    
    # Verify ratification gate
    amendment = load_amendment_log()
    if amendment.get("status") != "RATIFIED":
        logger.error("Ratification gate not passed. Amendment log status is not RATIFIED.")
        raise RuntimeError("Ratification gate not passed. Cannot proceed.")

    # Load dataset with streaming
    # Using the verified Recipe1M source from HuggingFace
    try:
        dataset = load_dataset(
            "recipe1m", 
            split="train", 
            streaming=True,
            trust_remote_code=True
        )
    except Exception as e:
        logger.error(f"Failed to load Recipe1M dataset: {e}")
        raise

    logger.info(f"Dataset loaded. Streaming {sample_limit} samples...")
    
    # Enforce sample limit using itertools.islice
    limited_iterator = itertools.islice(dataset, sample_limit)
    
    # Convert to list of dicts for DataFrame creation
    # We process in chunks to manage memory if sample_limit is large
    chunk_size = 5000
    chunks = []
    processed_count = 0
    
    logger.info("Processing chunks...")
    for i, batch in enumerate(limited_iterator):
        chunks.append(batch)
        processed_count += 1
        
        if processed_count % chunk_size == 0:
            logger.info(f"Processed {processed_count} samples so far...")
            # Check memory
            mem_gb = get_memory_usage_gb()
            if mem_gb > 6.0:  # Alert if > 6GB
                logger.warning(f"High memory usage: {mem_gb:.2f} GB")
                # Optional: trigger downsampling logic if needed, but we rely on sample_limit
        
        if processed_count >= sample_limit:
            break

    if not chunks:
        logger.error("No data retrieved from stream.")
        raise ValueError("No data retrieved from stream.")

    logger.info(f"Collected {processed_count} samples. Converting to DataFrame...")
    
    # Flatten and create DataFrame
    # Recipe1M structure: {recipes: [{ingredients: [...], instructions: [...], ...}]}
    # We need to normalize this to a flat table for analysis
    records = []
    for item in chunks:
        # Handle the structure: usually 'recipes' key or direct fields
        if isinstance(item, dict):
            if 'recipes' in item:
                for recipe in item['recipes']:
                    records.append(flatten_recipe(recipe))
            else:
                records.append(flatten_recipe(item))
    
    df = pd.DataFrame(records)
    
    if df.empty:
        logger.error("Resulting DataFrame is empty.")
        raise ValueError("Resulting DataFrame is empty.")

    # Schema Validation (T007b)
    logger.info("Validating schema...")
    required_cols = ['recipe_id', 'ingredients', 'instructions', 'rating']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        # Attempt to map common variations
        logger.warning(f"Missing expected columns: {missing_cols}. Attempting schema mapping...")
        # Recipe1M often has 'title', 'ingredients', 'instructions', 'rating'
        # If 'recipe_id' is missing, generate one
        if 'recipe_id' not in df.columns:
            if 'id' in df.columns:
                df['recipe_id'] = df['id']
            else:
                df['recipe_id'] = range(len(df))
        
        if 'ingredients' not in df.columns:
            logger.error("Critical column 'ingredients' missing after mapping.")
            raise ValueError("Critical column 'ingredients' missing.")
        
        if 'rating' not in df.columns:
            # If rating is missing, we might need to handle it, but T019 handles label derivation
            # For now, we ensure the structure exists
            logger.warning("Rating column missing. Will be handled in T019.")
            df['rating'] = None

    # Final check
    if 'recipe_id' not in df.columns or 'ingredients' not in df.columns:
        logger.error("Schema validation failed after mapping.")
        raise ValueError("Schema validation failed.")

    # Save to Parquet
    output_path = project_root / "data" / "raw" / "recipe1m_processed.parquet"
    logger.info(f"Saving to {output_path}...")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        df.to_parquet(output_path, index=False, compression='snappy')
    except Exception as e:
        logger.error(f"Failed to save Parquet file: {e}")
        raise

    logger.info(f"Successfully saved {len(df)} records to {output_path}")
    
    # Log completion
    log_path = project_root / "data" / "stream_recipe1m_status.json"
    with open(log_path, "w") as f:
        json.dump({
            "status": "SUCCESS",
            "timestamp": datetime.now().isoformat(),
            "records_processed": len(df),
            "sample_limit": sample_limit,
            "output_file": str(output_path)
        }, f, indent=2)

    return len(df)

def flatten_recipe(recipe_dict):
    """Flatten a recipe dictionary into a single record."""
    record = {}
    
    # Extract ID
    if 'id' in recipe_dict:
        record['recipe_id'] = recipe_dict['id']
    elif 'recipe_id' in recipe_dict:
        record['recipe_id'] = recipe_dict['recipe_id']
    else:
        record['recipe_id'] = None

    # Extract Title
    record['title'] = recipe_dict.get('title', '')
    
    # Extract Ingredients
    # Recipe1M ingredients can be list of strings or list of dicts
    ingredients = recipe_dict.get('ingredients', [])
    if isinstance(ingredients, list):
        # Convert to list of strings if needed
        if ingredients and isinstance(ingredients[0], dict):
            # Extract 'ingredient' key if present
            record['ingredients'] = [i.get('ingredient', str(i)) for i in ingredients]
        else:
            record['ingredients'] = [str(i) for i in ingredients]
    else:
        record['ingredients'] = []

    # Extract Instructions
    instructions = recipe_dict.get('instructions', [])
    if isinstance(instructions, list):
        record['instructions'] = instructions
    else:
        record['instructions'] = []

    # Extract Rating
    record['rating'] = recipe_dict.get('rating', None)
    
    # Extract other metadata if present
    record['url'] = recipe_dict.get('url', '')
    record['source'] = recipe_dict.get('source', '')
    
    return record

def main():
    """Main entry point for T013a."""
    logger.info("Starting T013a: Stream & Validate Recipe1M")
    ensure_directories()
    
    try:
        sample_limit = load_sample_size_requirement()
        logger.info(f"Sample size limit from pilot: {sample_limit}")
        
        count = stream_and_process_dataset(sample_limit)
        logger.info(f"T013a completed successfully. Processed {count} records.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except KeyError as e:
        logger.error(f"Key error in pilot stats: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
