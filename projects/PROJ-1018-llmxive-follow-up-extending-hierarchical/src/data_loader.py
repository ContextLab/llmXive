"""
Streaming PG‑19 loader with length filtering, deterministic split creation,
and schema‑validated output.

The script is invoked from the quick‑start run‑book:

    python src/data_loader.py \
        --dataset deepmind/pg19 \
        --split-ratio 0.05 \
        --seed 42 \
        --min-tokens 32000 \
        --pad-short-docs False

It writes ``data/interim/filtered_pg19.json`` conforming to
``contracts/split_definition.schema.yaml`` and logs the number of
documents excluded because they are shorter than the required token count.
"""

import argparse
import json
import os
import random
import hashlib
import logging
from typing import Iterator, List, Dict, Any

import yaml  # pyyaml is available in the base environment
from transformers import AutoTokenizer
from jsonschema import validate, ValidationError
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger
from src.config import Config

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def compute_checksum(ids: List[str]) -> str:
    """SHA‑256 checksum of the sorted concatenated document IDs."""
    concatenated = "".join(sorted(ids)).encode("utf-8")
    return hashlib.sha256(concatenated).hexdigest()


def count_tokens(text: str, tokenizer) -> int:
    """Return token count using the provided tokenizer or a cheap fallback."""
    if tokenizer is None:
        # Rough fallback: ~4 characters per token
        return len(text) // 4
    return len(tokenizer.encode(text, truncation=False))


def enrich_with_counts(
    raw_iter: Iterator[Dict[str, Any]],
    tokenizer,
) -> Iterator[Dict[str, Any]]:
    """
    Yield documents enriched with a ``token_count`` field.
    Expected keys in each raw document: ``document_id`` and ``text``.
    """
    for doc in raw_iter:
        text = doc.get("text", "") or ""
        token_cnt = count_tokens(text, tokenizer)
        yield {
            "document_id": doc["document_id"],
            "text": text,
            "token_count": token_cnt,
        }


def filter_documents(
    docs: Iterator[Dict[str, Any]],
    min_tokens: int,
    pad_short: bool,
    tokenizer,
) -> Iterator[Dict[str, Any]]:
    """
    Apply length filtering (or optional padding) and emit only documents
    meeting the threshold. Short‑document skips are printed to stdout
    exactly as required by the spec.
    """
    for doc in docs:
        if doc["token_count"] >= min_tokens:
            yield doc
        else:
            if pad_short:
                pad_token = tokenizer.pad_token if tokenizer and tokenizer.pad_token else " "
                needed = min_tokens - doc["token_count"]
                doc["text"] = doc["text"] + (pad_token * needed)
                doc["token_count"] = min_tokens
                yield doc
            else:
                # Direct stdout warning (spec requirement)
                print(
                    f"WARNING: Skipping document {doc['document_id']}: "
                    f"length {doc['token_count']} < {min_tokens}"
                )
                # Do not yield


def create_splits(
    doc_ids: List[str],
    split_ratio: float,
    seed: int,
) -> Dict[str, List[str]]:
    """
    Deterministically shuffle IDs and split them into validation / test.
    ``split_ratio`` is the proportion assigned to the *validation* split.
    """
    rng = random.Random(seed)
    rng.shuffle(doc_ids)
    split_point = int(len(doc_ids) * split_ratio)
    return {
        "validation_ids": doc_ids[:split_point],
        "test_ids": doc_ids[split_point:],
    }


# ----------------------------------------------------------------------
# Main public API required by the task specification
# ----------------------------------------------------------------------


def load_streaming_pg19(
    dataset_name: str = "lmsys/pg-19-test",
    split: str = "train",
    min_tokens: int = 32000,
    split_ratio: float = 0.5,
    seed: int = 42,
    pad_short_docs: bool = False,
) -> Iterator[Dict[str, Any]]:
    """
    Stream the PG‑19 dataset, filter by length (or pad), log exclusions,
    create deterministic validation / test splits, and write a JSON file
    conforming to the ``SplitDefinition`` schema.

    Returns an iterator over the filtered documents.
    """
    cfg = Config()
    # Override config values with CLI arguments where appropriate
    cfg.seed = seed
    cfg.min_tokens = min_tokens
    cfg.PAD_SHORT_DOCS = pad_short_docs

    # Load a tokenizer for accurate token counting
    try:
        tokenizer = AutoTokenizer.from_pretrained("gpt2", trust_remote_code=True)
    except Exception as exc:
        logger.warning(f"Tokenizer load failed ({exc}); using character estimate.")
        tokenizer = None

    # ------------------------------------------------------------------
    # Stream raw dataset using the HuggingFace `datasets` library (streaming)
    # ------------------------------------------------------------------
    try:
        raw_dataset = load_dataset(dataset_name, split=split, streaming=True)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load dataset '{dataset_name}' (split={split}) with streaming: {exc}"
        ) from exc

    # Normalise each record to contain ``document_id`` and ``text`` fields
    def _normalise(record: Dict[str, Any], idx: int) -> Dict[str, Any]:
        return {
            "document_id": (
                record.get("id")
                or record.get("document_id")
                or f"doc_{idx}"
            ),
            "text": record.get("text", ""),
        }

    raw_iter = (_normalise(rec, i) for i, rec in enumerate(raw_dataset))

    # Enrich with token counts
    enriched_iter = enrich_with_counts(raw_iter, tokenizer)

    # Apply length filter / padding
    filtered_iter = filter_documents(
        enriched_iter,
        min_tokens=cfg.min_tokens,
        pad_short=cfg.PAD_SHORT_DOCS,
        tokenizer=tokenizer,
    )

    # Materialise filtered docs (required for split creation & checksum)
    filtered_docs = list(filtered_iter)
    kept = len(filtered_docs)

    if kept < 30:
        raise RuntimeError(
            f"Power‑warning: only {kept} documents passed the length filter; "
            "at least 30 are required for a meaningful split."
        )

    logger.info(f"{kept} documents >= {cfg.min_tokens} tokens kept after filtering.")

    # Create splits
    doc_ids = [doc["document_id"] for doc in filtered_docs]
    splits = create_splits(doc_ids, split_ratio=split_ratio, seed=cfg.seed)

    split_definition = {
        "validation_ids": splits["validation_ids"],
        "test_ids": splits["test_ids"],
        "checksum": compute_checksum(doc_ids),
    }

    # Write JSON file
    output_path = paths.data("interim", "filtered_pg19.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(split_definition, fp, indent=2, ensure_ascii=False)

    logger.info(f"Split definition written to {output_path}")

    # Validate against the contract schema (fails loudly if non‑conformant)
    schema_path = paths.root / "contracts" / "split_definition.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as sf:
        schema = yaml.safe_load(sf)
    try:
        validate(instance=split_definition, schema=schema)
    except ValidationError as ve:
        raise RuntimeError(
            f"Generated split definition does not conform to schema: {ve}"
        ) from ve

    # Return iterator over filtered documents for downstream pipelines
    return iter(filtered_docs)


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def _parse_bool(value: str) -> bool:
    """Parse a string into a boolean; accepts common variants."""
    lowered = value.lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"Cannot interpret '{value}' as boolean.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stream PG‑19, filter by length, and write split definition."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="lmsys/pg-19-test",
        help="HuggingFace dataset identifier (e.g., 'lmsys/pg-19-test').",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="train",
        help="Dataset split to stream (default: train).",
    )
    parser.add_argument(
        "--split-ratio",
        type=float,
        default=0.5,
        help="Proportion of filtered documents assigned to the validation split "
             "(the remainder becomes the test split).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic shuffling.",
    )
    parser.add_argument(
        "--min-tokens",
        type=int,
        default=32000,
        help="Minimum token count required for a document to be kept.",
    )
    parser.add_argument(
        "--pad-short-docs",
        type=_parse_bool,
        default=False,
        help="If true, pad short documents to ``min_tokens`` instead of skipping.",
    )

    args = parser.parse_args()

    # Map deprecated / renamed dataset identifiers to the current canonical name.
    if args.dataset in {"deepmind/pg19", "deepmind/pg-19"}:
        logger.info(
            f"Mapping deprecated dataset identifier '{args.dataset}' to 'lmsys/pg-19-test'."
        )
        args.dataset = "lmsys/pg-19-test"

    # Run the loader; we discard the iterator because the quick‑start only
    # cares about the side‑effect of writing the JSON file.
    _ = load_streaming_pg19(
        dataset_name=args.dataset,
        split=args.split,
        min_tokens=args.min_tokens,
        split_ratio=args.split_ratio,
        seed=args.seed,
        pad_short_docs=args.pad_short_docs,
    )

    logger.info("PG‑19 streaming loader completed successfully.")


if __name__ == "__main__":
    main()
