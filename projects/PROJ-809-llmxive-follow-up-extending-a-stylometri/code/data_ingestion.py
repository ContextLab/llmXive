import os
import sys
import json
import logging
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import project utilities
from utils import get_logger, load_json, save_json, ensure_dir
from update_state import load_state, save_state, hash_artifact, register_artifact
from config import load_config

# Constants
MIN_ABSTRACT_LENGTH = 6  # Minimum characters to support max n-gram order (n=6)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STATE_FILE = PROJECT_ROOT / "state" / "PROJ-809-llmxive-followup.yaml"

logger = get_logger(__name__)

def filter_short_abstracts(corpus_path: Path) -> Tuple[Path, int, int]:
    """
    Filters the processed corpus JSON to remove abstracts shorter than MIN_ABSTRACT_LENGTH.
    
    Args:
        corpus_path: Path to the processed corpus JSON file (e.g., data/processed/corpus.json)
        
    Returns:
        Tuple of (output_path, original_count, filtered_count)
    """
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus file not found: {corpus_path}")

    logger.info(f"Loading corpus from {corpus_path}")
    corpus_data = load_json(corpus_path)
    
    original_count = len(corpus_data)
    logger.info(f"Original corpus size: {original_count} abstracts")

    # Filter abstracts
    filtered_corpus = []
    excluded_count = 0
    
    for author_id, entries in corpus_data.items():
        valid_entries = []
        for entry in entries:
            text = entry.get("text", "")
            if len(text) >= MIN_ABSTRACT_LENGTH:
                valid_entries.append(entry)
            else:
                excluded_count += 1
        filtered_corpus.append({author_id: valid_entries})

    # Reconstruct the dictionary structure if needed, or keep as list of dicts
    # Assuming corpus_data was a dict of author_id -> list of entries
    # If the input was a list of single-key dicts, we reconstruct the dict
    if isinstance(corpus_data, list):
        final_corpus = {}
        for item in corpus_data:
            for k, v in item.items():
                if k not in final_corpus:
                    final_corpus[k] = []
                # We need to re-filter this list if we didn't process it correctly above
                # Let's assume the input structure is a dict {author_id: [entries]}
                pass
        # Re-logic for safety:
        final_corpus = {}
        for author_id, entries in corpus_data.items() if isinstance(corpus_data, dict) else []:
             valid_entries = []
             for entry in entries:
                  if len(entry.get("text", "")) >= MIN_ABSTRACT_LENGTH:
                      valid_entries.append(entry)
             final_corpus[author_id] = valid_entries
    else:
        final_corpus = {}
        for author_id, entries in corpus_data.items():
            valid_entries = []
            for entry in entries:
                if len(entry.get("text", "")) >= MIN_ABSTRACT_LENGTH:
                    valid_entries.append(entry)
            final_corpus[author_id] = valid_entries

    filtered_count = sum(len(v) for v in final_corpus.values())
    
    output_path = DATA_PROCESSED_DIR / "corpus_filtered.json"
    ensure_dir(output_path)
    save_json(final_corpus, output_path)
    
    logger.info(f"Filtered corpus saved to {output_path}")
    logger.info(f"Excluded {excluded_count} abstracts (< {MIN_ABSTRACT_LENGTH} chars)")
    logger.info(f"Final corpus size: {filtered_count} abstracts")
    
    return output_path, original_count, filtered_count

def log_exclusion_stats(original_count: int, filtered_count: int, excluded_count: int):
    """Logs the exclusion statistics to the console and a log file."""
    logger.info("=" * 50)
    logger.info("ABSTRACT FILTERING SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Original abstracts: {original_count}")
    logger.info(f"Excluded abstracts (< {MIN_ABSTRACT_LENGTH} chars): {excluded_count}")
    logger.info(f"Final valid abstracts: {filtered_count}")
    if original_count > 0:
        exclusion_rate = (excluded_count / original_count) * 100
        logger.info(f"Exclusion rate: {exclusion_rate:.2f}%")
    logger.info("=" * 50)

def main():
    """
    Main entry point for T017: Filter abstracts < 6 characters.
    This task ensures validity for n=4, 5, 6 models.
    """
    logger.info("Starting T017: Filtering short abstracts...")
    
    # Load configuration if needed
    config = load_config()
    
    # Determine input path based on previous tasks (T014/T015 output)
    # Assuming T014/T015 saved to corpus.json or similar in data/processed
    input_corpus = DATA_PROCESSED_DIR / "corpus.json"
    
    # Fallback if the previous task named it differently (e.g., corpus_cleaned.json)
    if not input_corpus.exists():
        candidates = list(DATA_PROCESSED_DIR.glob("corpus*.json"))
        if candidates:
            input_corpus = sorted(candidates)[-1] # Pick the most recent
        else:
            raise FileNotFoundError(
                "No processed corpus found in data/processed/. "
                "Ensure T014/T015 have completed successfully."
            )

    try:
        output_path, original, filtered = filter_short_abstracts(input_corpus)
        excluded = original - filtered
        log_exclusion_stats(original, filtered, excluded)
        
        # Update state with artifact hash
        if STATE_FILE.exists():
            state = load_state(STATE_FILE)
            register_artifact(state, "corpus_filtered", str(output_path))
            save_state(state, STATE_FILE)
            logger.info("State updated with filtered corpus hash.")
        else:
            logger.warning(f"State file not found at {STATE_FILE}. Skipping state update.")

    except Exception as e:
        logger.error(f"Failed to filter abstracts: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("T017 completed successfully.")

if __name__ == "__main__":
    main()
