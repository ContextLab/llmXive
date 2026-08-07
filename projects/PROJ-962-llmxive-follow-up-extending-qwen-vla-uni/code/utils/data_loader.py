"""
Hardened Data Loader for llmXive pipeline.

This module provides a robust data loading interface that strictly enforces
the "Fail Loudly" principle. It removes any silent fallback mechanisms (try/except
blocks that generate synthetic data) and ensures that any failure to fetch
real data from the source raises a specific, descriptive exception.
"""

import os
import sys
from typing import Dict, Any, Optional, Union, List
from datasets import load_dataset, Dataset, DatasetDict

class DataFetchError(Exception):
    """
    Custom exception raised when data fetching from a real source fails.
    This ensures the pipeline halts immediately rather than proceeding with
    missing or synthetic data.
    """
    def __init__(self, message: str, source_id: Optional[str] = None, url: Optional[str] = None):
        super().__init__(message)
        self.source_id = source_id
        self.url = url
        self.message = message

    def __str__(self) -> str:
        base_msg = f"DataFetchError: {self.message}"
        if self.source_id:
            base_msg += f" (Source ID: {self.source_id})"
        if self.url:
            base_msg += f" (URL: {self.url})"
        return base_msg


def load_qwen_vla_dataset(
    dataset_id: str = "Qwen-VLA/Hy-Embodied",
    streaming: bool = True,
    split: Optional[str] = None,
    **kwargs
) -> Union[Dataset, DatasetDict]:
    """
    Loads the Qwen-VLA Hy-Embodied dataset from HuggingFace.

    This function implements a "Hardened Data Fetch" strategy:
    1. It attempts to load the dataset from the specified real source.
    2. It does NOT catch exceptions to fall back to synthetic data.
    3. If the load fails (network error, missing repo, auth error), it raises
       a specific DataFetchError with details about the failed source.

    Args:
        dataset_id (str): The HuggingFace dataset identifier.
        streaming (bool): If True, streams the dataset to handle large sizes (>7GB).
        split (str, optional): Specific split to load (e.g., 'train', 'test').
        **kwargs: Additional arguments passed to `datasets.load_dataset`.

    Returns:
        Union[Dataset, DatasetDict]: The loaded dataset object.

    Raises:
        DataFetchError: If the dataset cannot be fetched from the source.
    """
    # Validate input
    if not dataset_id or not isinstance(dataset_id, str):
        raise DataFetchError(
            "Invalid dataset_id provided.",
            source_id=dataset_id
        )

    try:
        # Attempt real data fetch
        # We do NOT wrap this in a try/except that swallows errors or returns synthetic data.
        # Any exception raised by `load_dataset` will bubble up, but we catch it here
        # to wrap it in our specific DataFetchError with context.
        dataset = load_dataset(
            dataset_id,
            split=split,
            streaming=streaming,
            **kwargs
        )
        
        # Basic validation that we got something
        if dataset is None:
            raise DataFetchError(
                f"Dataset loaded but returned None.",
                source_id=dataset_id
            )

        return dataset

    except Exception as e:
        # Re-raise as a specific DataFetchError to halt the pipeline
        # This prevents silent failures where the pipeline might proceed with empty data.
        raise DataFetchError(
            f"Failed to fetch dataset from HuggingFace: {str(e)}",
            source_id=dataset_id,
            url=f"https://huggingface.co/datasets/{dataset_id}"
        ) from e


def validate_dataset_structure(
    dataset: Union[Dataset, DatasetDict],
    required_columns: List[str]
) -> bool:
    """
    Validates that the loaded dataset contains the required columns.

    Args:
        dataset: The loaded dataset object.
        required_columns: List of column names that must be present.

    Returns:
        bool: True if valid.

    Raises:
        DataFetchError: If required columns are missing (indicating a data integrity issue).
    """
    if isinstance(dataset, DatasetDict):
        # Check the first split for structure
        first_split_name = next(iter(dataset.keys()))
        features = dataset[first_split_name].features
    else:
        features = dataset.features

    missing_cols = [col for col in required_columns if col not in features]

    if missing_cols:
        raise DataFetchError(
            f"Dataset is missing required columns: {missing_cols}. "
            "The data source may be corrupted or incompatible.",
            source_id="Unknown" # Source ID already known at load time
        )

    return True
