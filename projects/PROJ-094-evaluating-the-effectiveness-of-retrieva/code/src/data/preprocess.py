"""
Preprocessing module for CodeSearchNet data.

This module handles loading raw data, stripping non-ASCII characters,
truncating text to a fixed token count, and saving the processed data
to JSONL and CSV formats.
"""

import os
import json
import csv
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from local project modules
from src.data.download import load_dataset_subset
from src.data.checksum import register_file, calculate_sha256
from src.data.models import CodeSnippet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tokenization configuration
MAX_TOKENS = 256
# Simple whitespace-based tokenizer for counting (approximate)
# In a real scenario, we might use a specific tokenizer from transformers
# but for this task, we assume whitespace splitting as a proxy for tokenization
# unless a specific tokenizer is mandated by the spec.
# Given the constraint to use existing APIs, we implement a robust whitespace splitter.

def strip_non_ascii(text: str) -> str:
    """
    Remove non-ASCII characters from the input text.

    Args:
        text: The input string.

    Returns:
        A string containing only ASCII characters.
    """
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    # Replace non-ASCII characters with empty string
    return text.encode('ascii', 'ignore').decode('ascii')

def tokenize_and_truncate(text: str, max_tokens: int = MAX_TOKENS) -> str:
    """
    Tokenize text by splitting on whitespace and truncate to max_tokens.

    Args:
        text: The input string.
        max_tokens: Maximum number of tokens to keep.

    Returns:
        The truncated string.
    """
    if not text:
        return ""

    # Split by whitespace to simulate tokenization
    tokens = text.split()

    if len(tokens) <= max_tokens:
        return text

    # Truncate
    truncated_tokens = tokens[:max_tokens]
    return " ".join(truncated_tokens)

def process_snippet(raw_item: Dict[str, Any]) -> CodeSnippet:
    """
    Process a raw data item into a CodeSnippet object.

    Args:
        raw_item: A dictionary containing raw data fields (e.g., from ir_datasets).

    Returns:
        A CodeSnippet object with processed fields.
    """
    # Extract fields based on typical CodeSearchNet structure
    # Adjust keys if the dataset structure differs, but this matches the spec's expectation
    code = raw_item.get('code', '')
    code_language = raw_item.get('language', 'unknown')
    docstring = raw_item.get('docstring', '')
    repo = raw_item.get('repo', '')
    function_name = raw_item.get('function_name', '')

    # Preprocessing steps
    clean_code = strip_non_ascii(code)
    clean_docstring = strip_non_ascii(docstring)

    truncated_code = tokenize_and_truncate(clean_code)
    truncated_docstring = tokenize_and_truncate(clean_docstring)

    return CodeSnippet(
        code=truncated_code,
        language=code_language,
        docstring=truncated_docstring,
        repo=repo,
        function_name=function_name,
        raw_id=raw_item.get('id', 'unknown')
    )

def load_and_process_subset(
    language: str = 'python',
    split: str = 'train',
    limit: Optional[int] = None
) -> List[CodeSnippet]:
    """
    Load a subset of the dataset, process it, and return a list of CodeSnippets.

    Args:
        language: The programming language subset (e., 'python', 'java').
        split: The dataset split (e.g., 'train', 'test').
        limit: Optional limit on the number of items to process.

    Returns:
        A list of processed CodeSnippet objects.
    """
    logger.info(f"Loading and processing {language}/{split} subset...")

    # Use the download module to fetch data
    # The download module handles the actual fetching from ir_datasets
    raw_data = load_dataset_subset(language, split, limit)

    processed_snippets = []
    for item in raw_data:
        try:
            snippet = process_snippet(item)
            processed_snippets.append(snippet)
        except Exception as e:
            logger.warning(f"Failed to process item: {e}")
            continue

    logger.info(f"Processed {len(processed_snippets)} snippets.")
    return processed_snippets

def save_to_jsonl(snippets: List[CodeSnippet], output_path: str) -> None:
    """
    Save a list of CodeSnippets to a JSONL file.

    Args:
        snippets: List of CodeSnippet objects.
        output_path: Path to the output file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        for snippet in snippets:
            # Convert dataclass to dict for JSON serialization
            # Assuming CodeSnippet has a to_dict method or we use vars/fields
            # Since CodeSnippet is a dataclass, we can use dataclasses.asdict
            import dataclasses
            record = dataclasses.asdict(snippet)
            f.write(json.dumps(record) + '\n')

    logger.info(f"Saved {len(snippets)} snippets to {output_path}")

    # Register file for checksum tracking
    register_file(output_path)

def save_to_csv(snippets: List[CodeSnippet], output_path: str) -> None:
    """
    Save a list of CodeSnippets to a CSV file.

    Args:
        snippets: List of CodeSnippet objects.
        output_path: Path to the output file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not snippets:
        logger.warning("No snippets to save to CSV.")
        return

    # Get field names from the first snippet (assuming all are same type)
    import dataclasses
    field_names = [f.name for f in dataclasses.fields(snippets[0])]

    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        for snippet in snippets:
            writer.writerow(dataclasses.asdict(snippet))

    logger.info(f"Saved {len(snippets)} snippets to {output_path}")

    # Register file for checksum tracking
    register_file(output_path)

def main():
    """
    Main entry point for the preprocessing pipeline.
    Loads raw data, processes it, and saves to data/processed/.
    """
    # Configuration
    DATA_LANG = 'python'  # Default language
    DATA_SPLIT = 'train'  # Default split
    OUTPUT_DIR = Path('data/processed')
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting preprocessing for {DATA_LANG}/{DATA_SPLIT}...")

    # Load and process
    snippets = load_and_process_subset(language=DATA_LANG, split=DATA_SPLIT)

    if not snippets:
        logger.error("No data processed. Exiting.")
        return

    # Save outputs
    jsonl_path = OUTPUT_DIR / f"{DATA_LANG}_{DATA_SPLIT}_processed.jsonl"
    csv_path = OUTPUT_DIR / f"{DATA_LANG}_{DATA_SPLIT}_processed.csv"

    save_to_jsonl(snippets, str(jsonl_path))
    save_to_csv(snippets, str(csv_path))

    logger.info("Preprocessing complete.")

if __name__ == '__main__':
    main()
