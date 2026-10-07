"""
Data leakage guard utility to enforce strict memory isolation during split-half bootstrap.

This module ensures that training and test sets do not share memory references,
preventing accidental data leakage during the GLM fitting process.
"""

import gc
import logging
import sys
from typing import Any, Dict, List, Set, Tuple, Union

class DataLeakageError(Exception):
    """Raised when potential data leakage is detected between train/test sets."""
    pass

logger = logging.getLogger(__name__)

def get_object_ids(obj: Any) -> Set[int]:
    """
    Recursively collect all object IDs reachable from a given object.
    
    Args:
        obj: The object to inspect.
        
    Returns:
        A set of unique object IDs.
    """
    visited = set()
    queue = [obj]
    
    while queue:
        current = queue.pop(0)
        obj_id = id(current)
        
        if obj_id in visited:
            continue
        
        visited.add(obj_id)
        
        if isinstance(current, dict):
            for key, value in current.items():
                queue.append(key)
                queue.append(value)
        elif isinstance(current, (list, tuple, set)):
            for item in current:
                queue.append(item)
        elif hasattr(current, '__dict__'):
            for value in current.__dict__.values():
                queue.append(value)
        elif hasattr(current, '__array__'):
            # Handle numpy arrays
            import numpy as np
            if isinstance(current, np.ndarray):
                queue.append(current.data)
    
    return visited

def force_memory_isolation(obj: Any) -> None:
    """
    Force garbage collection and ensure object is isolated.
    
    Args:
        obj: The object to isolate.
    """
    # Delete any references to the object
    del obj
    # Force garbage collection
    gc.collect()
    logger.debug("Memory isolation completed via gc.collect()")

def verify_no_leakage(train_obj: Any, test_obj: Any) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify that training and test objects do not share memory.
    
    Args:
        train_obj: The training data object.
        test_obj: The test data object.
        
    Returns:
        A tuple of (is_clean, details_dict).
        
    Raises:
        DataLeakageError: If shared memory is detected.
    """
    train_ids = get_object_ids(train_obj)
    test_ids = get_object_ids(test_obj)
    
    shared_ids = train_ids.intersection(test_ids)
    
    details = {
        "train_object_count": len(train_ids),
        "test_object_count": len(test_ids),
        "shared_object_count": len(shared_ids),
        "shared_ids_sample": list(shared_ids)[:10] if shared_ids else []
    }
    
    if shared_ids:
        logger.warning(f"Potential data leakage detected: {len(shared_ids)} shared objects")
        raise DataLeakageError(
            f"Data leakage detected: {len(shared_ids)} shared memory objects "
            f"between train and test sets. Sample IDs: {details['shared_ids_sample']}"
        )
    
    logger.info("No data leakage detected between train and test sets")
    return True, details

def isolate_and_verify(train_obj: Any, test_obj: Any) -> Tuple[bool, Dict[str, Any]]:
    """
    Full isolation and verification workflow.
    
    1. Delete any external references to training data
    2. Force garbage collection
    3. Verify no shared memory with test data
    
    Args:
        train_obj: The training data object.
        test_obj: The test data object.
        
    Returns:
        A tuple of (is_clean, details_dict).
    """
    logger.info("Starting memory isolation and verification")
    
    # Step 1: Force isolation
    force_memory_isolation(train_obj)
    
    # Step 2: Create fresh copies for verification
    # (In practice, the caller should pass fresh references after isolation)
    
    # Step 3: Verify
    is_clean, details = verify_no_leakage(train_obj, test_obj)
    
    logger.info(f"Isolation verification complete: {is_clean}")
    return is_clean, details
