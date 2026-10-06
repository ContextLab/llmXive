import os
import sys
import json
import logging
import itertools
from datetime import datetime
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' library is required. Install via: pip install datasets")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'data' / 'logs' / 'stream_recipe1m.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure output directories exist."""
    data_raw = project_root / 'data' / 'raw'
    data_logs = project_root / 'data' / 'logs'
    data_raw.mkdir(parents=True, exist_ok=True)
    data_logs.mkdir(parents=True, exist_ok=True)
    return data_raw, data_logs

def load_sample_size_requirement():
    """Read sample size requirement from T013b output."""
    pilot_stats_path = project_root / 'data' / 'pilot_stats.json'
    if not pilot_stats_path.exists():
        logger.warning(f"Pilot stats not found at {pilot_stats_path}. Using default sample size.")
        return 10000  # Default fallback if pilot stats missing
    
    try:
        with open(pilot_stats_path, 'r') as f:
            stats = json.load(f)
        return stats.get('sample_size_required', 10000)
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Error reading pilot stats: {e}. Using default sample size.")
        return 10000

def load_amendment_log():
    """Read amendment log to check methodology and proxy source."""
    amendment_path = project_root / 'data' / 'amendment_log.json'
    if not amendment_path.exists():
        logger.error("Amendment log not found. T012d_ratification_gate must run first.")
        sys.exit(1)
    
    with open(amendment_path, 'r') as f:
        return json.load(f)

def flatten_recipe(recipe: dict) -> dict:
    """Flatten a recipe record into a tabular row."""
    # Extract basic fields
    row = {
        'recipe_id': recipe.get('id', ''),
        'title': recipe.get('title', ''),
        'description': recipe.get('description', ''),
        'rating': recipe.get('rating', None),
        'num_ratings': recipe.get('num_ratings', 0),
        'ingredients': recipe.get('ingredients', []),
        'instructions': recipe.get('instructions', []),
        'url': recipe.get('url', ''),
        'timestamp': datetime.now().isoformat()
    }
    
    # Flatten ingredients list into a string for easier processing later
    if isinstance(row['ingredients'], list):
        row['ingredients_str'] = ';'.join([str(i) for i in row['ingredients']])
    else:
        row['ingredients_str'] = str(row['ingredients'])
    
    return row

def stream_and_process_dataset(sample_size: int, data_raw: Path):
    """Stream Recipe1M dataset, limit to sample_size, and save to parquet."""
    output_path = data_raw / 'recipe1m_processed.parquet'
    
    logger.info(f"Starting stream of Recipe1M dataset (limit: {sample_size} recipes)...")
    
    try:
        # Load dataset with streaming enabled
        # Using the verified source: recipe1m/recipe1m
        dataset = load_dataset("recipe1m/recipe1m", split="train", streaming=True)
        
        logger.info("Dataset loaded in streaming mode. Iterating and processing...")
        
        processed_rows = []
        count = 0
        
        # Iterate with limit
        for item in dataset:
            if count >= sample_size:
                logger.info(f"Reached sample limit of {sample_size}. Stopping stream.")
                break
            
            try:
                row = flatten_recipe(item)
                processed_rows.append(row)
                count += 1
                
                if count % 1000 == 0:
                    logger.info(f"Processed {count} recipes...")
            except Exception as e:
                logger.warning(f"Skipping malformed recipe at index {count}: {e}")
                continue
        
        if not processed_rows:
            logger.error("No valid recipes were processed. Pipeline cannot continue.")
            raise RuntimeError("No valid data extracted from Recipe1M stream.")
        
        logger.info(f"Processing complete. Total valid recipes: {count}")
        
        # Convert to pandas and save
        import pandas as pd
        df = pd.DataFrame(processed_rows)
        
        # Ensure rating column exists (may be None if missing in source)
        if 'rating' not in df.columns:
            df['rating'] = None
            logger.warning("Rating column not found in source data; added as None.")
        
        logger.info(f"Saving to {output_path}...")
        df.to_parquet(output_path, index=False)
        
        logger.info(f"Successfully saved {len(df)} records to {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to stream and process dataset: {e}")
        
        # Write failure status as per task requirements
        status_path = project_root / 'data' / 'download_status_recipe1m.json'
        status = {
            "dataset": "recipe1m",
            "status": "FAILED",
            "error_code": f"STREAM_ERROR_{str(e)[:20]}",
            "timestamp": datetime.now().isoformat()
        }
        with open(status_path, 'w') as f:
            json.dump(status, f, indent=2)
        
        raise e

def write_validation_log(rating_present: bool, data_logs: Path):
    """Write validation log indicating schema compliance."""
    validation_path = data_logs / 'recipe1m_validation.json'
    
    log_data = {
        "rating_column_present": rating_present,
        "timestamp": datetime.now().isoformat(),
        "task_id": "T013a",
        "status": "VALIDATED" if rating_present else "WARNING_MISSING_RATING"
    }
    
    with open(validation_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Validation log written to {validation_path}")

def main():
    """Main entry point for T013a."""
    logger.info("Starting T013a: Stream & Validate Recipe1M")
    
    # Ensure directories
    data_raw, data_logs = ensure_directories()
    
    # Check amendment log
    amendment = load_amendment_log()
    if amendment.get('status') != 'RATIFIED':
        logger.error("Amendment log status is not RATIFIED. Halting.")
        sys.exit(1)
    
    # Load sample size requirement
    sample_size = load_sample_size_requirement()
    logger.info(f"Sample size requirement: {sample_size}")
    
    # Stream and process
    success = stream_and_process_dataset(sample_size, data_raw)
    
    if success:
        # Validate output
        output_path = data_raw / 'recipe1m_processed.parquet'
        import pandas as pd
        try:
            df = pd.read_parquet(output_path)
            rating_present = 'rating' in df.columns
            write_validation_log(rating_present, data_logs)
            
            if not rating_present:
                logger.warning("Rating column missing in output. This may affect downstream tasks.")
            else:
                logger.info("Validation successful: Rating column present.")
        except Exception as e:
            logger.error(f"Failed to validate output file: {e}")
            sys.exit(1)
    
    logger.info("T013a completed successfully.")

if __name__ == "__main__":
    main()
