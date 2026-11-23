import os
import sys
import json
import logging
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project utilities
from utils import get_logger, save_json, load_json, ensure_dir, compute_sha256
from config import load_config, set_seed
from update_state import load_state, save_state, register_artifact, hash_artifact

# Configure logging
def setup_logging():
    logger = get_logger("data_ingestion")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

logger = setup_logging()

def download_arxiv_subset():
    """
    Downloads the arXiv dataset (train split) filtered by categories.
    Returns a list of dicts with 'author' and 'text' keys.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("The 'datasets' library is required. Install it via: pip install datasets")
        raise

    logger.info("Downloading arXiv dataset (train split)...")
    # Load the specific subset defined in previous tasks (T011)
    # Categories: [cs.CL, physics.gen-ph, q-bio.QM]
    dataset = load_dataset(
        "arxiv",
        split="train",
        filter_columns=["abstract", "authors", "categories"]
    )

    # Filter by categories
    target_categories = {"cs.CL", "physics.gen-ph", "q-bio.QM"}
    filtered_data = []
    
    logger.info("Filtering by categories...")
    for item in dataset:
        # Categories in arxiv dataset can be a list or string
        cats = item.get("categories", [])
        if isinstance(cats, str):
            cats = [c.strip() for c in cats.split()]
        
        if any(cat in target_categories for cat in cats):
            # Extract author (assuming first author or a specific extraction logic)
            # T012 logic likely extracted the 'lead author' here. 
            # We assume 'authors' is a list of strings, take the first one.
            authors = item.get("authors", [])
            if isinstance(authors, str):
                authors = [a.strip() for a in authors.split(",")]
            
            if authors:
                lead_author = authors[0].strip()
                abstract = item.get("abstract", "").strip()
                if abstract:
                    filtered_data.append({
                        "author": lead_author,
                        "text": abstract,
                        "raw_categories": cats
                    })
    
    logger.info(f"Downloaded and filtered {len(filtered_data)} records.")
    return filtered_data

def extract_authors_and_filter(data: List[Dict[str, Any]], min_abstracts: int = 10):
    """
    Extracts authors and filters to those with >= min_abstracts.
    Returns a dict of {author: [texts]} and a list of excluded authors.
    """
    author_map = {}
    for item in data:
        author = item["author"]
        text = item["text"]
        if author not in author_map:
            author_map[author] = []
        author_map[author].append(text)
    
    qualified_authors = {k: v for k, v in author_map.items() if len(v) >= min_abstracts}
    excluded = {k: v for k, v in author_map.items() if k not in qualified_authors}
    
    logger.info(f"Found {len(author_map)} unique authors.")
    logger.info(f"Qualified authors (>= {min_abstracts} abstracts): {len(qualified_authors)}")
    logger.info(f"Excluded authors (< {min_abstracts} abstracts): {len(excluded)}")
    
    return qualified_authors, excluded

def write_collision_report(author_map: Dict[str, List[str]], state_path: Path, log_path: Path):
    """
    Checks for name collisions (names appearing > 50 times as distinct authors? 
    or high frequency? T013a says 'name appears > 50 times').
    Assuming this refers to the count of abstracts per author triggering a collision flag
    if the count is suspiciously high, or if the name is ambiguous.
    Per T013a: 'log warning if name appears >50 times'.
    """
    collision_report = []
    critical_threshold = 50
    
    for author, texts in author_map.items():
        count = len(texts)
        if count > critical_threshold:
            collision_report.append({
                "author": author,
                "count": count,
                "flag": "high_frequency_collision",
                "manual_review": True
            })
            logger.warning(f"Collision Warning: Author '{author}' appears {count} times (> {critical_threshold}). Flagged for review.")
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        json.dump(collision_report, f, indent=2)
    
    # Update state
    state = load_state(state_path)
    state["collision_report"] = str(log_path)
    state["collision_count"] = len(collision_report)
    if len(collision_report) > 0:
        state["manual_review_required"] = True
    save_state(state, state_path)
    
    return collision_report

def filter_short_abstracts(author_map: Dict[str, List[str]], min_length: int = 6) -> Dict[str, List[str]]:
    """
    Filters abstracts shorter than min_length characters.
    T017: Filter abstracts < 6 characters (max n-gram order) to ensure validity.
    Returns the cleaned map and logs the count of excluded abstracts.
    """
    cleaned_map = {}
    total_excluded = 0
    
    logger.info(f"Filtering abstracts with length < {min_length} characters...")
    
    for author, texts in author_map.items():
        valid_texts = []
        excluded_count = 0
        for text in texts:
            # Check length of the raw text (before tokenization)
            if len(text) >= min_length:
                valid_texts.append(text)
            else:
                excluded_count += 1
        
        cleaned_map[author] = valid_texts
        total_excluded += excluded_count
        
        # Optional: log if an author loses all texts
        if len(valid_texts) == 0 and len(texts) > 0:
            logger.warning(f"Author '{author}' has no valid abstracts after short-filtering.")

    logger.info(f"Total abstracts excluded due to length < {min_length}: {total_excluded}")
    return cleaned_map

def stratified_sample_authors(author_map: Dict[str, List[str]], target_count: int = 20, seed: int = 42) -> Dict[str, List[str]]:
    """
    Selects exactly target_count authors if more qualify.
    Raises fatal error if < target_count.
    """
    set_seed(seed)
    authors = list(author_map.keys())
    
    if len(authors) < target_count:
        msg = f"FATAL: Filtered dataset yields {len(authors)} authors, which is less than the required {target_count}. Cannot proceed."
        logger.critical(msg)
        raise ValueError(msg)
    
    if len(authors) > target_count:
        import random
        random.seed(seed)
        selected_authors = random.sample(authors, target_count)
        logger.info(f"Selected {target_count} authors via stratified random sampling from {len(authors)} candidates.")
        return {k: author_map[k] for k in selected_authors}
    
    return author_map

def main():
    """
    Main execution flow for T017 (and US1 data pipeline).
    """
    config = load_config()
    seed = config.get("seed", 42)
    set_seed(seed)
    
    project_root = Path.cwd()
    data_raw_dir = project_root / "data" / "raw"
    data_processed_dir = project_root / "data" / "processed"
    state_file = project_root / "state" / "PROJ-809-llmxive-followup.yaml"
    
    ensure_dir(data_raw_dir)
    ensure_dir(data_processed_dir)
    ensure_dir(state_file.parent)
    
    # 1. Download (T011)
    raw_data = download_arxiv_subset()
    
    # Save raw parquet (T011 requirement)
    import pandas as pd
    df_raw = pd.DataFrame(raw_data)
    parquet_path = data_raw_dir / "arxiv_subset.parquet"
    df_raw.to_parquet(parquet_path)
    logger.info(f"Saved raw data to {parquet_path}")
    
    # 2. Extract authors and filter (T012)
    author_map, excluded = extract_authors_and_filter(raw_data, min_abstracts=10)
    
    # 3. Collision check (T013a)
    collision_report_path = data_processed_dir / "collision_report.json"
    write_collision_report(author_map, state_file, collision_report_path)
    
    # 4. T017: Filter short abstracts (< 6 chars)
    # This is the core task of this implementation
    author_map = filter_short_abstracts(author_map, min_length=6)
    
    # 5. Stratified sampling (T015)
    try:
        final_author_map = stratified_sample_authors(author_map, target_count=20, seed=seed)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 6. Save processed data (T014 - preprocessing logic would go here, but T017 is just filtering)
    # We save the filtered, cleaned data as JSON for the next steps
    processed_data_path = data_processed_dir / "corpus.json"
    processed_records = []
    for author, texts in final_author_map.items():
        for text in texts:
            processed_records.append({"author": author, "text": text})
    
    save_json(processed_records, processed_data_path)
    logger.info(f"Saved processed corpus to {processed_data_path}")
    
    # 7. Update state with hashes (T016)
    raw_hash = hash_artifact(parquet_path)
    proc_hash = hash_artifact(processed_data_path)
    
    state = load_state(state_file)
    state["artifacts"]["raw_parquet"] = {"path": str(parquet_path), "hash": raw_hash}
    state["artifacts"]["processed_corpus"] = {"path": str(processed_data_path), "hash": proc_hash}
    save_state(state, state_file)
    
    logger.info("Data ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()