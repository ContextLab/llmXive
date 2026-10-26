import argparse
import json
import os
import random
import hashlib
import logging
from typing import Iterator, List, Dict, Any

import yaml
from transformers import AutoTokenizer
from jsonschema import validate, ValidationError
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger
from src.config import Config

logger = get_logger(__name__)

def compute_checksum(ids: List[str]) -> str:
    """SHA‑256 checksum of the sorted concatenated document IDs."""
    concatenated = "".join(sorted(ids)).encode("utf-8")
    return hashlib.sha256(concatenated).hexdigest()

def count_tokens(text: str, tokenizer) -> int:
    """Return token count using the provided tokenizer."""
    if tokenizer is None:
        return len(text) // 4
    return len(tokenizer.encode(text, truncation=False))

def create_splits(doc_ids: List[str], split_ratio: float, seed: int) -> Dict[str, List[str]]:
    """Deterministically shuffle IDs and split them into validation / test."""
    rng = random.Random(seed)
    shuffled = list(doc_ids)
    rng.shuffle(shuffled)
    split_point = int(len(shuffled) * split_ratio)
    return {
        "validation_ids": shuffled[:split_point],
        "test_ids": shuffled[split_point:],
    }

def load_streaming_pg19(
    dataset_name: str = "lmsys/pg-19-test",
    split: str = "train",
    min_tokens: int = 32000,
    split_ratio: float = 0.5,
    seed: int = 42,
    pad_short_docs: bool = False,
) -> Iterator[Dict[str, Any]]:
    """
    Stream PG‑19, filter by length, log exclusions, create deterministic 
    splits, and write a schema‑validated JSON split definition.
    """
    cfg = Config()
    cfg.seed = seed
    cfg.min_tokens = min_tokens
    cfg.PAD_SHORT_DOCS = pad_short_docs

    try:
        tokenizer = AutoTokenizer.from_pretrained("gpt2")
    except Exception as e:
        logger.warning(f"Tokenizer load failed: {e}. Using character estimate.")
        tokenizer = None

    try:
        raw_dataset = load_dataset(dataset_name, split=split, streaming=True)
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset {dataset_name}: {e}")

    filtered_docs = []
    exclusion_count = 0

    for i, record in enumerate(raw_dataset):
        doc_id = record.get("id") or record.get("document_id") or f"doc_{i}"
        text = record.get("text", "")
        tokens = count_tokens(text, tokenizer)

        if tokens >= min_tokens:
            filtered_docs.append({"document_id": doc_id, "text": text, "token_count": tokens})
        elif pad_short_docs:
            pad_token = tokenizer.pad_token if tokenizer and tokenizer.pad_token else " "
            needed = min_tokens - tokens
            padded_text = text + (pad_token * needed)
            filtered_docs.append({"document_id": doc_id, "text": padded_text, "token_count": min_tokens})
        else:
            print(f"WARNING: Skipping document {doc_id}: length {tokens} < {min_tokens}")
            exclusion_count += 1

    kept = len(filtered_docs)
    if kept < 30:
        raise RuntimeError(f"Power‑warning: only {kept} documents passed the length filter; at least 30 required.")

    logger.info(f"Kept {kept} documents. Excluded {exclusion_count} short documents.")

    doc_ids = [doc["document_id"] for doc in filtered_docs]
    splits = create_splits(doc_ids, split_ratio, seed)

    split_definition = {
        "validation_ids": splits["validation_ids"],
        "test_ids": splits["test_ids"],
        "checksum": compute_checksum(doc_ids),
    }

    output_path = paths.data("interim", "filtered_pg19.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(split_definition, f, indent=2)

    schema_path = paths.root / "contracts" / "split_definition.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as sf:
        schema = yaml.safe_load(sf)
    
    try:
        validate(instance=split_definition, schema=schema)
    except ValidationError as ve:
        raise RuntimeError(f"Split definition schema validation failed: {ve}")

    return iter(filtered_docs)

def _parse_bool(value: str) -> bool:
    return value.lower() in {"true", "1", "yes", "y"}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="lmsys/pg-19-test")
    parser.add_argument("--split", type=str, default="train")
    parser.add_argument("--split-ratio", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-tokens", type=int, default=32000)
    parser.add_argument("--pad-short-docs", type=_parse_bool, default=False)
    args = parser.parse_args()

    if args.dataset in {"deepmind/pg19", "deepmind/pg-19"}:
        args.dataset = "lmsys/pg-19-test"

    _ = load_streaming_pg19(
        dataset_name=args.dataset,
        split=args.split,
        min_tokens=args.min_tokens,
        split_ratio=args.split_ratio,
        seed=args.seed,
        pad_short_docs=args.pad_short_docs,
    )
    logger.info("T001: Data loading and split creation completed successfully.")

if __name__ == "__main__":
    main()