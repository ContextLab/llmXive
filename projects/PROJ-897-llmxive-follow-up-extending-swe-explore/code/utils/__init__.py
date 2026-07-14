"""
Utilities package for llmXive.
Exports memory management and validation utilities.
"""
from .hash_artifacts import compute_sha256, hash_directory, generate_manifest, verify_manifest
from .validation import validate_field_type, validate_record_against_schema
from .memory_manager import (
    MemoryMonitor,
    MemoryExhaustedError,
    memory_limited,
    LRUContextCache,
    get_global_monitor,
    optimize_gc_for_large_graphs,
    get_memory_profile,
    batch_process_with_memory_control,
    clean_up_large_objects
)

__all__ = [
    # Hash artifacts
    'compute_sha256', 'hash_directory', 'generate_manifest', 'verify_manifest',
    # Validation
    'validate_field_type', 'validate_record_against_schema',
    # Memory management
    'MemoryMonitor', 'MemoryExhaustedError', 'memory_limited', 'LRUContextCache',
    'get_global_monitor', 'optimize_gc_for_large_graphs', 'get_memory_profile',
    'batch_process_with_memory_control', 'clean_up_large_objects'
]
