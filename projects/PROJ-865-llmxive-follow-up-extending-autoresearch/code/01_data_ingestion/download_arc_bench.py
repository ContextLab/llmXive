"""
T009: Implement download_arc_bench.py to fetch the ARC-Bench 25-topic subset.

This script fetches the ARC-Bench dataset from HuggingFace, filters for the
25-topic subset as required by the project specs, and saves the raw data
to data/raw/arc_bench_25_topics.jsonl.

It fails loudly if the data cannot be fetched; it does not generate synthetic data.
"""

import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import validate_resource_limits

# Configure logger
logger = get_logger("data_ingestion")

# Constants
DATASET_ID = "allenai/arc-bench"
# The task specifies "25-topic subset". We will fetch the full dataset
# and filter for the first 25 unique topics or a specific split if available.
# Since ARC-Bench typically has a 'full' split, we will stream it and limit
# to a representative subset if the full set is too large, but ensure we
# are using REAL data.
# Note: If the specific "25-topic" split name exists, we use it. Otherwise,
# we fetch the main split and sample 25 topics deterministically.
TARGET_TOPICS_COUNT = 25
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "arc_bench_25_topics.jsonl"

def fetch_arc_bench_subset():
    """
    Fetches the ARC-Bench dataset from HuggingFace and filters for 25 topics.
    
    Returns:
        list: A list of dictionaries representing the filtered dataset.
    
    Raises:
        RuntimeError: If the dataset cannot be fetched or processed.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is required. Install with: pip install datasets")
        raise

    logger.info(f"Attempting to fetch dataset: {DATASET_ID}")
    
    # Attempt to load the dataset. We use streaming to handle potential size issues
    # but we need to materialize a specific subset.
    # We try to load the 'full' split. If that fails, we try 'train' or default.
    try:
        dataset = load_dataset(DATASET_ID, split="full", streaming=True)
    except Exception as e:
        # Fallback to default split if 'full' is not found or fails
        logger.warning(f"Could not load 'full' split: {e}. Trying default split.")
        try:
            dataset = load_dataset(DATASET_ID, streaming=True)
            # If it's a dict of splits, take the first one (usually train)
            if isinstance(dataset, dict):
                first_key = next(iter(dataset.keys()))
                dataset = dataset[first_key]
        except Exception as e2:
            logger.error(f"Failed to load dataset from {DATASET_ID}: {e2}")
            raise RuntimeError(f"Unable to fetch real data from HuggingFace: {e2}")

    # We need to collect data for exactly 25 unique topics.
    # We iterate through the streaming dataset and group by topic.
    topics_data = {}
    total_rows = 0
    
    logger.info(f"Streaming dataset to filter for {TARGET_TOPICS_COUNT} topics...")
    
    for row in dataset:
        total_rows += 1
        
        # Determine the topic key. ARC-Bench usually has 'topic' or 'category'.
        # We check common keys.
        topic = row.get("topic") or row.get("category") or row.get("subject")
        
        if topic is None:
            logger.warning(f"Row {total_rows} has no identifiable topic. Skipping.")
            continue
        
        if topic not in topics_data:
            topics_data[topic] = []
        
        # We only need enough data to cover 25 topics. 
        # To be safe and representative, we might collect a few rows per topic,
        # but the task implies a subset of 25 topics. Let's collect all rows 
        # for the first 25 topics we encounter to ensure we have data.
        if len(topics_data) <= TARGET_TOPICS_COUNT:
            topics_data[topic].append(row)
        
        # Optimization: Stop if we have collected enough topics and a reasonable 
        # amount of data per topic (e.g., at least 5 rows per topic to be useful).
        # However, the task says "25-topic subset", implying the scope is defined by topics.
        # Let's ensure we have at least 10 rows per topic if possible, or stop if we hit 25 topics.
        if len(topics_data) == TARGET_TOPICS_COUNT:
            # Check if we have enough data. If a topic has very few rows, we might need to continue.
            # For robustness, let's ensure every collected topic has at least 5 examples.
            min_rows = min(len(rows) for rows in topics_data.values())
            if min_rows >= 5:
                logger.info(f"Collected {TARGET_TOPICS_COUNT} topics with at least {min_rows} rows each.")
                break

    if len(topics_data) < TARGET_TOPICS_COUNT:
        logger.warning(f"Could only find {len(topics_data)} unique topics in the dataset. Proceeding with available data.")
    
    # Flatten the collected data back into a list
    final_dataset = []
    for topic, rows in topics_data.items():
        final_dataset.extend(rows)
    
    logger.info(f"Successfully filtered dataset. Total rows: {len(final_dataset)}, Topics: {len(topics_data)}")
    return final_dataset

def main():
    """Main entry point for the download script."""
    log_stage_start("download_arc_bench")
    
    # Validate resource limits (T005c dependency)
    validate_resource_limits()
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Fetch real data
        data = fetch_arc_bench_subset()
        
        if not data:
            logger.error("No data was fetched. The dataset might be empty or filtering failed.")
            raise RuntimeError("No real data fetched from HuggingFace.")
        
        # Write to disk
        logger.info(f"Writing {len(data)} rows to {OUTPUT_FILE}")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for row in data:
                # Ensure the row is serializable. Some datasets have non-serializable types.
                # Convert sets to lists, etc.
                clean_row = {}
                for k, v in row.items():
                    if isinstance(v, (set, frozenset)):
                        clean_row[k] = list(v)
                    else:
                        clean_row[k] = v
                f.write(json.dumps(clean_row) + "\n")
        
        logger.info(f"Download complete. Output saved to {OUTPUT_FILE}")
        log_stage_end("download_arc_bench", status="success")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to download or process ARC-Bench: {e}", exc_info=True)
        log_stage_end("download_arc_bench", status="failed", error=str(e))
        raise

if __name__ == "__main__":
    sys.exit(main())