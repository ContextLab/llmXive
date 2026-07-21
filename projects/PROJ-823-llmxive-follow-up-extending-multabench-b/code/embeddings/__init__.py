"""
Embeddings module for generating and validating frozen embeddings.

This module provides functionality for:
- Generating embeddings using CLIP and Sentence-BERT
- Validating that gradient tracking is disabled during inference
- Serializing and deserializing embeddings to/from Parquet files
- Preprocessing datasets for embedding generation
"""

from .generator import EmbeddingGenerator
from .validator import (
    validate_no_gradient_tracking,
    assert_no_grad_context,
    validate_embedding_generator,
    run_validation_suite
)
from .serializer import (
    generate_run_id,
    serialize_embeddings_to_parquet,
    load_embeddings_from_parquet
)
from .preprocessing import (
    detect_zero_variance_columns,
    detect_missing_fields,
    handle_zero_variance_columns,
    handle_missing_fields,
    validate_dataset_fields,
    preprocess_dataset_for_embedding
)
from .utils import batch_process_embeddings

__all__ = [
    # Generator
    'EmbeddingGenerator',
    
    # Validator
    'validate_no_gradient_tracking',
    'assert_no_grad_context',
    'validate_embedding_generator',
    'run_validation_suite',
    
    # Serializer
    'generate_run_id',
    'serialize_embeddings_to_parquet',
    'load_embeddings_from_parquet',
    
    # Preprocessing
    'detect_zero_variance_columns',
    'detect_missing_fields',
    'handle_zero_variance_columns',
    'handle_missing_fields',
    'validate_dataset_fields',
    'preprocess_dataset_for_embedding',
    
    # Utilities
    'batch_process_embeddings',
]
