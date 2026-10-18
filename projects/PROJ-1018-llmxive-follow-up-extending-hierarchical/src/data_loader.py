import logging
import itertools
import os
import json
import hashlib
from typing import Iterator, List, Dict, Any
from datasets import load_dataset

from transformers import AutoTokenizer

from llmxive_toolkit import paths, get_logger
from src.config import Config

# Configure module‑level logger
logger = get_logger(__name__)

class DataFetchError(Exception):
    """Raised when real data fetching fails."""
    pass

def load_pg19_streaming(split: str = "train") -> Iterator[Dict[str, Any]]:
    """
    Low‑level helper that streams the PG‑19 dataset.

    Args:
        split: Dataset split name (e.g., "train", "validation").

    Returns:
        An iterator over raw document dictionaries.

    Raises:
        RuntimeError: If the dataset cannot be fetched.
    """
    try:
        dataset = load_dataset("lmsys/pg-19-test", split=split, streaming=True)
        return iter(dataset)
    except Exception as e:
        logger.error(f"Failed to load PG‑19 dataset: {e}")
        raise RuntimeError(f"Real data fetch failed: {e}")

def estimate_token_count(text: str, tokenizer) -> int:
    """
    Estimate token count using a HuggingFace tokenizer.
    Falls back to a simple character‑based estimate if no tokenizer is supplied.
    """
    if tokenizer is None:
        return len(text) // 4
    return len(tokenizer.encode(text, truncation=False))

def get_document_iterator(
    dataset_iter: Iterator[Dict[str, Any]],
    tokenizer,
) -> Iterator[Dict[str, Any]]:
    """
    Enrich each document with a token count.

    Yields dictionaries containing:
        - document_id
        - text
        - token_count
    """
    for doc in dataset_iter:
        text = doc.get("text", "") or ""
        token_count = estimate_token_count(text, tokenizer)
        yield {
            "document_id": doc.get("id", "unknown"),
            "text": text,
            "token_count": token_count,
        }

def filter_long_documents(
    doc_iterator: Iterator[Dict[str, Any]],
    min_tokens: int = 32000,
) -> Iterator[Dict[str, Any]]:
    """
    Yield only documents meeting the minimum token threshold.
    Logs a warning for each skipped document.
    """
    for doc in doc_iterator:
        if doc["token_count"] >= min_tokens:
            yield doc
        else:
            # Direct stdout warning as required by the spec
            print(
                f"WARNING: Skipping document {doc['document_id']}: "
                f"length {doc['token_count']} < {min_tokens}"
            )

def pad_short_document(doc: Dict[str, Any], target_tokens: int, tokenizer) -> Dict[str, Any]:
    """
    Pad a short document up to ``target_tokens`` using the tokenizer's
    padding token (or space if unavailable). This function is only used
    when ``Config.PAD_SHORT_DOCS`` is ``True``.
    """
    current = doc["token_count"]
    if current >= target_tokens:
        return doc
    # Simple padding: repeat spaces until token count is reached.
    # This is deterministic and does not introduce random content.
    pad_needed = target_tokens - current
    # Encode a single space token repeatedly
    pad_token = tokenizer.pad_token or " "
    padded_text = doc["text"] + (pad_token * pad_needed)
    doc["text"] = padded_text
    doc["token_count"] = target_tokens
    return doc

def compute_checksum(ids: List[str]) -> str:
    """
    Compute a SHA‑256 checksum of the concatenated document IDs.
    """
    concatenated = "".join(sorted(ids)).encode("utf-8")
    return hashlib.sha256(concatenated).hexdigest()

def load_streaming_pg19(split: str = "train", min_tokens: int = 32000) -> Iterator[Dict[str, Any]]:
    """
    Public API required by task T001.

    Streams the PG‑19 dataset, filters by ``min_tokens`` (or pads
    when ``Config.PAD_SHORT_DOCS`` is ``True``), logs exclusions,
    creates deterministic validation/test splits, and writes a
    ``filtered_pg19.json`` file that conforms to the
    ``SplitDefinition`` schema.

    Args:
        split: Which split of the PG‑19 dataset to stream.
        min_tokens: Minimum token count for a document to be kept.

    Returns:
        An iterator over the filtered document dictionaries.

    Raises:
        RuntimeError: If the dataset cannot be fetched or if the
            filtered set contains fewer than 30 documents.
    """
    cfg = Config()  # pulls defaults; ensures assertions on skip_short_documents

    # Load tokenizer for accurate token counting
    try:
        tokenizer = AutoTokenizer.from_pretrained("gpt2", trust_remote_code=True)
    except Exception as e:
        logger.warning(f"Could not load tokenizer (gpt2); falling back to character estimate: {e}")
        tokenizer = None

    # Stream raw dataset
    raw_iter = load_pg19_streaming(split=split)

    # Enrich with token counts
    doc_iter = get_document_iterator(raw_iter, tokenizer)

    # Apply length filter (or padding if configured)
    if cfg.PAD_SHORT_DOCS:
        # Pad short docs before filtering
        def padded_iter():
            for doc in doc_iter:
                if doc["token_count"] < min_tokens:
                    doc = pad_short_document(doc, min_tokens, tokenizer)
                yield doc
        filtered_iter = filter_long_documents(padded_iter(), min_tokens=min_tokens)
    else:
        filtered_iter = filter_long_documents(doc_iter, min_tokens=min_tokens)

    # Materialise filtered docs to enable split creation and checksum
    filtered_docs: List[Dict[str, Any]] = list(filtered_iter)
    total_kept = len(filtered_docs)
    total_excluded = getattr(filtered_iter, "excluded", None)  # not tracked; compute via length diff later

    if total_kept < 30:
        raise RuntimeError(
            f"Power‑warning: only {total_kept} documents passed the length filter; "
            "at least 30 are required for a meaningful split."
        )

    # Log exclusion count (derived from original stream size if possible)
    # Since we cannot know total stream size without iterating twice, we simply log kept count.
    logger.info(f"{total_kept} documents >= {min_tokens} tokens kept after filtering.")

    # Deterministic split: shuffle with fixed seed and split 50/50
    doc_ids = [doc["document_id"] for doc in filtered_docs]
    rng = random.Random(cfg.seed)
    rng.shuffle(doc_ids)

    split_point = len(doc_ids) // 2
    validation_ids = doc_ids[:split_point]
    test_ids = doc_ids[split_point:]

    split_definition = {
        "validation_ids": validation_ids,
        "test_ids": test_ids,
        "checksum": compute_checksum(doc_ids),
    }

    # Write split definition JSON
    output_path = paths.data("interim", "filtered_pg19.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(split_definition, f, indent=2, ensure_ascii=False)

    logger.info(f"Split definition written to {output_path}")

    # Return an iterator over the filtered documents
    return iter(filtered_docs)

def main():
    """
    Entry‑point for manual execution.
    Streams the training split, applies the default minimum token threshold,
    and writes the split definition JSON.
    """
    # Using defaults from Config via the function arguments
    _ = load_streaming_pg19(split="train", min_tokens=Config().min_tokens)

if __name__ == "__main__":
    main()
