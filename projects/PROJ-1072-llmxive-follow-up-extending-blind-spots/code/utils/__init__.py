"""
Utilities package for llmXive pipeline.
"""
from .hashing_utils import (
    compute_file_hash,
    compute_string_hash,
    compute_bytes_hash,
    compute_dict_hash,
    hash_artifact,
    verify_file_hash
)
from .logging_config import (
    JsonFormatter,
    get_logger,
    log_event,
    setup_root_logger
)
from .dataset_integrity import (
    IntegrityError,
    validate_record_fields,
    validate_dataset_records,
    generate_integrity_report,
    load_and_validate_jsonl,
    verify_record_hash
)
from .semantic_matcher import (
    encode_texts,
    compute_cosine_similarity,
    is_paraphrase,
    batch_is_paraphrase,
    find_best_match,
    DEFAULT_THRESHOLD
)

__all__ = [
    # Hashing
    "compute_file_hash",
    "compute_string_hash",
    "compute_bytes_hash",
    "compute_dict_hash",
    "hash_artifact",
    "verify_file_hash",
    # Logging
    "JsonFormatter",
    "get_logger",
    "log_event",
    "setup_root_logger",
    # Integrity
    "IntegrityError",
    "validate_record_fields",
    "validate_dataset_records",
    "generate_integrity_report",
    "load_and_validate_jsonl",
    "verify_record_hash",
    # Semantic Matching
    "encode_texts",
    "compute_cosine_similarity",
    "is_paraphrase",
    "batch_is_paraphrase",
    "find_best_match",
    "DEFAULT_THRESHOLD"
]