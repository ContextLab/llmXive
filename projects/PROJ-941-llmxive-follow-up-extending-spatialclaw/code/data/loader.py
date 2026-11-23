"""
code/data/loader.py

Implements the loader for the Synthetic SpatialClaw Proxy data.
This module strictly adheres to the "fail loudly" constraint:
- It attempts to load data from the expected path.
- If the file is missing or invalid, it raises a FileNotFoundError or ValueError.
- It explicitly DOES NOT contain any synthetic data generation fallbacks.

This implementation includes memory-aware streaming (T035) to handle large datasets
on CPU-first constrained environments (SC-004).
"""
import json
import os
import sys
import gc
from typing import Any, Dict, List, Iterator, Optional

# Constants matching the generator output
DATA_DIR = "data/raw"
DATASET_FILENAME = "synthetic_spatialclaw_v1.json"
FULL_PATH = os.path.join(DATA_DIR, DATASET_FILENAME)

# Memory safety thresholds (SC-004)
# Warn if usage exceeds 80% of available memory
MEMORY_WARN_THRESHOLD = 0.80
# Force garbage collection if usage exceeds 90%
MEMORY_GC_THRESHOLD = 0.90


class DataLoadError(Exception):
    """Custom exception for data loading failures."""
    pass


def _get_memory_usage_ratio() -> float:
    """
    Returns the current memory usage ratio (0.0 to 1.0).
    Uses psutil if available, otherwise returns 0.0 (safe fallback).
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        total_mem = psutil.virtual_memory().total
        if total_mem == 0:
            return 0.0
        return mem_info.rss / total_mem
    except ImportError:
        # psutil not installed, cannot monitor memory
        return 0.0
    except Exception:
        # Any other error, assume safe
        return 0.0


def _check_memory_and_gc() -> None:
    """
    Checks memory usage and triggers garbage collection if necessary.
    Logs warnings if memory usage is high.
    """
    ratio = _get_memory_usage_ratio()
    if ratio > MEMORY_GC_THRESHOLD:
        import logging
        logging.warning(f"High memory usage detected ({ratio:.2%}). Triggering garbage collection.")
        gc.collect()
    elif ratio > MEMORY_WARN_THRESHOLD:
        import logging
        logging.warning(f"Memory usage approaching limit ({ratio:.2%}).")


def load_dataset_stream(chunk_size: int = 1000) -> Iterator[Dict[str, Any]]:
    """
    Streams the dataset in chunks to prevent OOM errors on large files.
    
    Args:
        chunk_size: Number of items to yield at once.
        
    Yields:
        Dict[str, Any]: A single task instance.
        
    Raises:
        FileNotFoundError: If the dataset file does not exist.
        DataLoadError: If JSON parsing fails or schema is invalid.
    """
    if not os.path.exists(FULL_PATH):
        raise FileNotFoundError(
            f"Data file not found: {FULL_PATH}. "
            "Please ensure T006 (generator) has been run successfully to create the dataset."
        )

    try:
        with open(FULL_PATH, 'r', encoding='utf-8') as f:
            # Read the opening bracket
            char = f.read(1)
            if char != '[':
                raise DataLoadError(f"Invalid JSON structure: Expected '[' at start, got '{char}'")
            
            buffer = []
            current_item = ""
            depth = 0
            in_string = False
            escape_next = False
            item_start_found = False

            while True:
                char = f.read(1)
                if not char:
                    break

                if escape_next:
                    current_item += char
                    escape_next = False
                    continue

                if char == '\\':
                    current_item += char
                    escape_next = True
                    continue

                if char == '"' and not escape_next:
                    in_string = not in_string
                    current_item += char
                    continue

                if not in_string:
                    if char == '{':
                        depth += 1
                        item_start_found = True
                        current_item += char
                    elif char == '}':
                        depth -= 1
                        current_item += char
                        if depth == 0 and item_start_found:
                            # End of an object
                            try:
                                obj = json.loads(current_item.strip())
                                buffer.append(obj)
                                _check_memory_and_gc()
                                if len(buffer) >= chunk_size:
                                    yield buffer
                                    buffer = []
                            except json.JSONDecodeError as e:
                                raise DataLoadError(f"Failed to parse JSON object: {e}")
                            current_item = ""
                            item_start_found = False
                    elif char == ',':
                        if depth == 0:
                            # End of list item separator
                            pass
                        else:
                            current_item += char
                    elif char == ']':
                        # End of list
                        if current_item.strip():
                            try:
                                obj = json.loads(current_item.strip())
                                buffer.append(obj)
                            except json.JSONDecodeError as e:
                                raise DataLoadError(f"Failed to parse final JSON object: {e}")
                        break
                    else:
                        current_item += char
                else:
                    current_item += char

            # Yield remaining items
            if buffer:
                yield buffer

    except json.JSONDecodeError as e:
        raise DataLoadError(f"Failed to parse JSON in {FULL_PATH}: {e}")


def load_dataset() -> List[Dict[str, Any]]:
    """
    Loads the Synthetic SpatialClaw Proxy dataset from disk.
    For very large datasets, consider using load_dataset_stream() instead.
    
    Returns:
        List[Dict[str, Any]]: A list of task instances and metadata.
        
    Raises:
        FileNotFoundError: If the dataset file does not exist at the expected path.
        DataLoadError: If the file exists but contains invalid JSON or schema.
        ValueError: If the dataset is empty.
        
    Note:
        This function explicitly does NOT generate synthetic data on failure.
        It fails loudly to ensure the pipeline only runs on verified real data.
    """
    # Check memory before loading
    _check_memory_and_gc()
    
    if not os.path.exists(FULL_PATH):
        raise FileNotFoundError(
            f"Data file not found: {FULL_PATH}. "
            "Please ensure T006 (generator) has been run successfully to create the dataset."
        )

    try:
        with open(FULL_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DataLoadError(f"Failed to parse JSON in {FULL_PATH}: {e}")

    if not isinstance(data, list):
        raise DataLoadError(
            f"Invalid dataset structure in {FULL_PATH}: Expected a list of task instances, got {type(data)}."
        )

    if len(data) == 0:
        raise ValueError(f"Dataset at {FULL_PATH} is empty. Cannot proceed with analysis.")

    # Basic schema validation (checking for required keys mentioned in T006)
    required_keys = {"task_id", "ground_truth_3d_params", "task_type", "scene_id"}
    if data:
        first_item = data[0]
        missing_keys = required_keys - set(first_item.keys())
        if missing_keys:
            raise DataLoadError(
                f"Dataset schema mismatch in {FULL_PATH}: Missing required keys {missing_keys}."
            )

    return data


def main():
    """
    Entry point for testing the loader independently.
    Attempts to load the dataset and prints summary statistics.
    Includes memory usage reporting.
    """
    print(f"Attempting to load dataset from: {FULL_PATH}")
    try:
        # Demonstrate streaming capability if file is large
        file_size = os.path.getsize(FULL_PATH)
        print(f"File size: {file_size / (1024*1024):.2f} MB")
        
        if file_size > 100 * 1024 * 1024:  # > 100MB
            print("File is large. Testing streaming loader...")
            total_items = 0
            for chunk in load_dataset_stream(chunk_size=500):
                total_items += len(chunk)
                print(f"  Loaded chunk of {len(chunk)} items (Total: {total_items})")
            print(f"Streaming complete. Total items: {total_items}")
        else:
            print("File is small. Testing standard loader...")
            dataset = load_dataset()
            print(f"Success! Loaded {len(dataset)} task instances.")

            # Print a sample of task types found
            task_types = set(item.get("task_type") for item in dataset)
            print(f"Task types found: {task_types}")

        # Final memory check
        ratio = _get_memory_usage_ratio()
        print(f"Final memory usage ratio: {ratio:.2%}")
        
        return dataset if file_size <= 100 * 1024 * 1024 else None
    except FileNotFoundError as e:
        print(f"CRITICAL ERROR: {e}")
        raise
    except DataLoadError as e:
        print(f"DATA ERROR: {e}")
        raise
    except ValueError as e:
        print(f"VALUE ERROR: {e}")
        raise


if __name__ == "__main__":
    main()