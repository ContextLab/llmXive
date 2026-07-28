"""
Preprocessing module for CodeSearchNet data.

This module handles loading raw data, stripping non-ASCII characters,
tokenizing and truncating to 256 tokens, and saving the processed
data to JSONL and CSV formats in the data/processed/ directory.
"""
import os
import json
import csv
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing modules to ensure API consistency
from src.data.download import load_dataset_subset
from src.data.checksum import register_file, save_state, calculate_sha256
from src.data.models import CodeSnippet


def strip_non_ascii(text: str) -> str:
    """
    Remove all non-ASCII characters from the input text.

    Args:
        text: Input string potentially containing non-ASCII characters.

    Returns:
        String with only ASCII characters preserved.
    """
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    return text.encode('ascii', 'ignore').decode('ascii')


def tokenize_and_truncate(text: str, max_tokens: int = 256) -> str:
    """
    Simple tokenization and truncation.

    For this implementation, we use a whitespace-based tokenization
    which is sufficient for code snippets. More sophisticated
    tokenizers can be substituted if needed.

    Args:
        text: Input text to tokenize and truncate.
        max_tokens: Maximum number of tokens to keep (default 256).

    Returns:
        Truncated text with at most max_tokens.
    """
    if not text:
        return ""

    # Simple whitespace tokenization
    tokens = text.split()

    if len(tokens) <= max_tokens:
        return text

    # Truncate to max_tokens
    truncated_tokens = tokens[:max_tokens]
    return ' '.join(truncated_tokens)


def process_snippet(snippet: Dict[str, Any]) -> CodeSnippet:
    """
    Process a single code snippet from the raw dataset.

    Args:
        snippet: Raw snippet dictionary from the dataset.

    Returns:
        Processed CodeSnippet object with cleaned and truncated fields.
    """
    # Extract fields with defaults
    code = snippet.get('code', '')
    language = snippet.get('language', 'unknown')
    repo = snippet.get('repo', 'unknown')
    path = snippet.get('path', 'unknown')
    commit_hash = snippet.get('commit_hash', 'unknown')

    # Strip non-ASCII
    code = strip_non_ascii(code)

    # Tokenize and truncate
    code = tokenize_and_truncate(code, max_tokens=256)

    # Create CodeSnippet object
    return CodeSnippet(
        code=code,
        language=language,
        repo=repo,
        path=path,
        commit_hash=commit_hash,
        original_length=len(code.split()),
        processed_length=len(code.split())
    )


def load_and_process_subset(
    language: str = 'python',
    split: str = 'test',
    max_samples: Optional[int] = None
) -> List[CodeSnippet]:
    """
    Load a subset of the dataset and process all snippets.

    Args:
        language: Language subset to load ('python', 'java', etc.).
        split: Dataset split to use ('train', 'test', 'validation').
        max_samples: Maximum number of samples to process (None for all).

    Returns:
        List of processed CodeSnippet objects.
    """
    # Load raw data using the download module
    raw_data = load_dataset_subset(language, split)

    processed_snippets = []

    for i, item in enumerate(raw_data):
        if max_samples is not None and i >= max_samples:
            break

        try:
            snippet = process_snippet(item)
            processed_snippets.append(snippet)
        except Exception as e:
            # Log error but continue processing
            print(f"Warning: Failed to process item {i}: {e}")
            continue

    return processed_snippets


def save_to_jsonl(snippets: List[CodeSnippet], output_path: Path) -> None:
    """
    Save processed snippets to a JSONL file.

    Args:
        snippets: List of CodeSnippet objects to save.
        output_path: Path to the output JSONL file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for snippet in snippets:
            # Convert dataclass to dict
            data = {
                'code': snippet.code,
                'language': snippet.language,
                'repo': snippet.repo,
                'path': snippet.path,
                'commit_hash': snippet.commit_hash,
                'original_length': snippet.original_length,
                'processed_length': snippet.processed_length
            }
            f.write(json.dumps(data) + '\n')


def save_to_csv(snippets: List[CodeSnippet], output_path: Path) -> None:
    """
    Save processed snippets to a CSV file.

    Args:
        snippets: List of CodeSnippet objects to save.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'code', 'language', 'repo', 'path', 'commit_hash',
        'original_length', 'processed_length'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for snippet in snippets:
            row = {
                'code': snippet.code,
                'language': snippet.language,
                'repo': snippet.repo,
                'path': snippet.path,
                'commit_hash': snippet.commit_hash,
                'original_length': snippet.original_length,
                'processed_length': snippet.processed_length
            }
            writer.writerow(row)


def main():
    """
    Main function to run the preprocessing pipeline.

    This function:
    1. Loads raw data from CodeSearchNet (Python test set by default)
    2. Strips non-ASCII characters
    3. Truncates to 256 tokens
    4. Saves to both JSONL and CSV formats in data/processed/
    5. Registers the output files for checksum verification
    """
    # Configuration
    language = 'python'
    split = 'test'
    output_dir = Path('data/processed')

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading and processing {language}/{split} subset...")
    snippets = load_and_process_subset(language, split)

    if not snippets:
        print("Warning: No snippets were processed. Check if the dataset is available.")
        return

    print(f"Processed {len(snippets)} snippets.")

    # Define output paths
    jsonl_path = output_dir / f"{language}_{split}_processed.jsonl"
    csv_path = output_dir / f"{language}_{split}_processed.csv"

    # Save to JSONL
    print(f"Saving to JSONL: {jsonl_path}")
    save_to_jsonl(snippets, jsonl_path)

    # Save to CSV
    print(f"Saving to CSV: {csv_path}")
    save_to_csv(snippets, csv_path)

    # Register output files for checksum verification
    register_file(jsonl_path)
    register_file(csv_path)

    print("Preprocessing complete!")
    print(f"  - JSONL: {jsonl_path}")
    print(f"  - CSV: {csv_path}")


if __name__ == '__main__':
    main()
