"""
Download Micro-Corpus from Project Gutenberg and The Stack.

This script fetches data streams from Hugging Face datasets, tokenizes them
using the GPT-2 tokenizer, and stops immediately after reaching the 1,000,000
token threshold. No synthetic fallbacks are used; the script fails loudly
on download errors.

Plan-Authorized Deviation: Implements scope reduction from Spec FR-001 (10M) to 1M tokens.
"""

import json
import os
import sys
import hashlib
import time
from pathlib import Path
from typing import Iterator, List, Dict, Any, Optional, Tuple

from datasets import load_dataset
from transformers import GPT2Tokenizer
from utils.logging import get_logger, info, error, warning, setup_logging

# Constants
TARGET_TOKEN_COUNT = 1_000_000
MAX_TOKEN_COUNT = 1_010_000  # Allow slight overshoot for last document
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "micro_corpus_raw.jsonl"
GUTENBERG_DATASET = "gutenberg"
THE_STACK_DATASET = "bigcode/the-stack-smart"
THE_STACK_SUBSET = "data/python"  # Focus on Python code for relevance

logger = get_logger(__name__)


def setup_logging() -> None:
    """Initialize logging for the data download process."""
    setup_logging()
    logger.info("Logging initialized for corpus download.")


def fetch_gutenberg_samples(tokenizer: GPT2Tokenizer) -> Iterator[Dict[str, Any]]:
    """
    Fetch samples from Project Gutenberg dataset using streaming.

    Args:
        tokenizer: The GPT-2 tokenizer to use for token counting.

    Yields:
        Dictionaries containing text and metadata.
    """
    logger.info(f"Fetching from {GUTENBERG_DATASET} dataset (streaming)...")
    try:
        dataset = load_dataset(GUTENBERG_DATASET, streaming=True, split="train")
        count = 0
        for item in dataset:
            # Gutenberg items usually have 'text' and 'title'
            text = item.get("text", "")
            if not text or len(text.strip()) == 0:
                continue

            # Tokenize to check length
            tokens = tokenizer.encode(text, add_special_tokens=False)
            if len(tokens) == 0:
                continue

            yield {
                "source": "gutenberg",
                "text": text,
                "title": item.get("title", "unknown"),
                "token_count": len(tokens)
            }
            count += 1
            if count % 1000 == 0:
                logger.debug(f"Processed {count} Gutenberg documents so far...")
    except Exception as e:
        error(f"Failed to fetch or stream from Gutenberg: {e}")
        raise RuntimeError(f"Data fetch error (Gutenberg): {e}")


def fetch_the_stack_samples(tokenizer: GPT2Tokenizer) -> Iterator[Dict[str, Any]]:
    """
    Fetch samples from The Stack dataset using streaming.

    Args:
        tokenizer: The GPT-2 tokenizer to use for token counting.

    Yields:
        Dictionaries containing text and metadata.
    """
    logger.info(f"Fetching from {THE_STACK_DATASET} dataset (streaming, subset={THE_STACK_SUBSET})...")
    try:
        # Using streaming to avoid downloading the full dataset
        dataset = load_dataset(
            THE_STACK_DATASET,
            name=THE_STACK_SUBSET,
            streaming=True,
            split="train"
        )
        count = 0
        for item in dataset:
            # The Stack items usually have 'content' and 'language'
            text = item.get("content", "")
            if not text or len(text.strip()) == 0:
                continue

            tokens = tokenizer.encode(text, add_special_tokens=False)
            if len(tokens) == 0:
                continue

            yield {
                "source": "the_stack",
                "text": text,
                "language": item.get("language", "unknown"),
                "token_count": len(tokens)
            }
            count += 1
            if count % 1000 == 0:
                logger.debug(f"Processed {count} The Stack documents so far...")
    except Exception as e:
        error(f"Failed to fetch or stream from The Stack: {e}")
        raise RuntimeError(f"Data fetch error (The Stack): {e}")


def count_tokens(text: str, tokenizer: GPT2Tokenizer) -> int:
    """Count tokens in a string using the GPT-2 tokenizer."""
    return len(tokenizer.encode(text, add_special_tokens=False))


def count_lines(file_path: Path) -> int:
    """Count lines in a file efficiently."""
    with open(file_path, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def save_samples_to_jsonl(
    samples: Iterator[Dict[str, Any]],
    output_path: Path,
    target_tokens: int,
    tokenizer: GPT2Tokenizer
) -> Tuple[int, int]:
    """
    Save samples to a JSONL file until the target token count is reached.

    Args:
        samples: Iterator of sample dictionaries.
        output_path: Path to the output JSONL file.
        target_tokens: The target token count to stop at.
        tokenizer: The tokenizer to use for counting.

    Returns:
        Tuple of (total_tokens, total_documents).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_tokens = 0
    total_docs = 0
    start_time = time.time()

    with open(output_path, "w", encoding="utf-8") as f:
        for sample in samples:
            text = sample["text"]
            doc_tokens = sample.get("token_count") or count_tokens(text, tokenizer)

            # Check if adding this document would exceed the target
            if total_tokens + doc_tokens > target_tokens:
                # Truncate the last document to hit the target exactly
                remaining_tokens = target_tokens - total_tokens
                if remaining_tokens > 0:
                    encoded = tokenizer.encode(text, add_special_tokens=False)
                    truncated_text = tokenizer.decode(encoded[:remaining_tokens], skip_special_tokens=True)
                    final_doc = {
                        "source": sample["source"],
                        "text": truncated_text,
                        "title": sample.get("title", "unknown"),
                        "token_count": remaining_tokens
                    }
                    f.write(json.dumps(final_doc) + "\n")
                    total_tokens += remaining_tokens
                    total_docs += 1
                logger.info(f"Target token count ({target_tokens}) reached. Stopping.")
                break
            else:
                # Write the full document
                f.write(json.dumps(sample) + "\n")
                total_tokens += doc_tokens
                total_docs += 1

            # Log progress every 100k tokens
            if total_tokens % 100_000 == 0 and total_tokens > 0:
                elapsed = time.time() - start_time
                rate = total_tokens / elapsed if elapsed > 0 else 0
                info(f"Progress: {total_tokens:,} tokens ({total_docs:,} docs) in {elapsed:.1f}s ({rate:.0f} tok/s)")

    return total_tokens, total_docs


def combine_and_save_corpus() -> None:
    """
    Main function to fetch, tokenize, and save the micro-corpus.

    This function orchestrates the download of data from both Gutenberg
    and The Stack, tokenizing and combining them until the 1M token
    threshold is reached.
    """
    setup_logging()
    info("Starting micro-corpus download and tokenization.")

    # Initialize tokenizer
    logger.info("Loading GPT-2 tokenizer...")
    try:
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
    except Exception as e:
        error(f"Failed to load GPT-2 tokenizer: {e}")
        raise RuntimeError(f"Tokenizer initialization failed: {e}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create a combined iterator
    def combined_iterator():
        # Prioritize Gutenberg for natural language, then The Stack for code
        # We interleave them to get a diverse corpus
        gutenberg_iter = fetch_gutenberg_samples(tokenizer)
        stack_iter = fetch_the_stack_samples(tokenizer)

        # Interleave: take one from Gutenberg, one from Stack, repeat
        while True:
            try:
                gutenberg_item = next(gutenberg_iter)
                yield gutenberg_item
            except StopIteration:
                break

            try:
                stack_item = next(stack_iter)
                yield stack_item
            except StopIteration:
                # If Stack runs out, continue with Gutenberg
                pass

    # Save the combined corpus
    info(f"Starting download with target of {TARGET_TOKEN_COUNT:,} tokens...")
    total_tokens, total_docs = save_samples_to_jsonl(
        combined_iterator(),
        OUTPUT_FILE,
        TARGET_TOKEN_COUNT,
        tokenizer
    )

    elapsed_time = time.time() - start_time if 'start_time' in locals() else 0
    info(f"Download complete. Saved {total_docs:,} documents with {total_tokens:,} tokens to {OUTPUT_FILE}")
    info(f"Total time: {elapsed_time:.1f} seconds")

    # Verify bounds
    if total_tokens < TARGET_TOKEN_COUNT:
        warning(f"Warning: Only {total_tokens:,} tokens collected, below target of {TARGET_TOKEN_COUNT:,}")
    elif total_tokens > MAX_TOKEN_COUNT:
        error(f"Error: Collected {total_tokens:,} tokens, exceeding max of {MAX_TOKEN_COUNT:,}")
        raise RuntimeError(f"Token count {total_tokens} exceeds maximum allowed {MAX_TOKEN_COUNT}")
    else:
        info(f"Success: Token count {total_tokens:,} is within bounds [{TARGET_TOKEN_COUNT:,}, {MAX_TOKEN_COUNT:,}]")


def main() -> None:
    """Entry point for the script."""
    try:
        combine_and_save_corpus()
        logger.info("Micro-corpus download completed successfully.")
    except KeyboardInterrupt:
        error("Download interrupted by user.")
        sys.exit(1)
    except Exception as e:
        error(f"Fatal error during corpus download: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()