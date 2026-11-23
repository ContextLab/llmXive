"""
Data loading and splitting utilities for the llmXive ProRL pipeline.

This module provides loaders for Amazon Books, Last.fm, and MovieLens datasets
using the HuggingFace datasets library with streaming enabled. It also implements
time-based splitting logic to generate held-out test sets for cold-start evaluation.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

from datasets import load_dataset
import pandas as pd

from src.config import get_config
from src.exceptions import DataFetchError, DataSplitError
from src.utils.io import write_json, read_json


def load_amazon_books(streaming: bool = True) -> Any:
    """
    Load the Amazon Books dataset.

    Args:
        streaming: If True, stream the dataset; otherwise download fully.

    Returns:
        HuggingFace Dataset object.

    Raises:
        DataFetchError: If the dataset cannot be fetched.
    """
    try:
        dataset = load_dataset('amazon_books', split='train', streaming=streaming)
        return dataset
    except Exception as e:
        raise DataFetchError(f"Failed to load Amazon Books dataset: {e}")


def load_lastfm(streaming: bool = True) -> Any:
    """
    Load the Last.fm dataset.

    Args:
        streaming: If True, stream the dataset; otherwise download fully.

    Returns:
        HuggingFace Dataset object.

    Raises:
        DataFetchError: If the dataset cannot be fetched.
    """
    try:
        dataset = load_dataset('lastfm', split='train', streaming=streaming)
        return dataset
    except Exception as e:
        raise DataFetchError(f"Failed to load Last.fm dataset: {e}")


def load_movielens(streaming: bool = True) -> Any:
    """
    Load the MovieLens latest-small dataset.

    Args:
        streaming: If True, stream the dataset; otherwise download fully.

    Returns:
        HuggingFace Dataset object.

    Raises:
        DataFetchError: If the dataset cannot be fetched.
    """
    try:
        dataset = load_dataset('ml-latest-small', split='train', streaming=streaming)
        return dataset
    except Exception as e:
        raise DataFetchError(f"Failed to load MovieLens dataset: {e}")


def _parse_timestamp(value: Any, dataset_name: str) -> Optional[float]:
    """
    Parse a timestamp value from various formats.

    Args:
        value: The raw timestamp value.
        dataset_name: Name of the dataset for format context.

    Returns:
        Float timestamp or None if parsing fails.
    """
    if value is None:
        return None

    # If already numeric (epoch seconds or milliseconds)
    if isinstance(value, (int, float)):
        # Assume seconds if < 1e12, milliseconds otherwise
        if value > 1e12:
            return value / 1000.0
        return float(value)

    # String parsing
    if isinstance(value, str):
        # Try common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%m-%d-%Y',
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                return dt.timestamp()
            except ValueError:
                continue

        # Try ISO format
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.timestamp()
        except (ValueError, AttributeError):
            pass

    # Last.fm specific: try parsing 'date' string
    if dataset_name == 'lastfm' and isinstance(value, str):
        # Format: "2010-01-01" or similar
        try:
            dt = datetime.strptime(value, '%Y-%m-%d')
            return dt.timestamp()
        except ValueError:
            pass

    return None


def split_dataset_by_time(
    dataset: Any,
    dataset_name: str,
    timestamp_column: str,
    user_column: str,
    item_column: str,
    test_ratio: float = 0.2,
    output_dir: str = 'data/processed',
    streaming: bool = True
) -> Tuple[str, str]:
    """
    Split dataset into train and test sets using a time-based split per user.

    For each user, sort their interactions by timestamp and assign the most recent
    interactions (test_ratio proportion) to the test set. This ensures the test set
    represents future interactions for cold-start evaluation.

    Args:
        dataset: HuggingFace Dataset object.
        dataset_name: Name of the dataset ('amazon_books', 'lastfm', 'movielens').
        timestamp_column: Column name containing timestamps.
        user_column: Column name containing user IDs.
        item_column: Column name containing item IDs.
        test_ratio: Proportion of recent interactions to use as test set (0.0-1.0).
        output_dir: Directory to save the split datasets.
        streaming: Whether the dataset is being streamed.

    Returns:
        Tuple of (train_path, test_path) where paths are to saved JSON/Parquet files.

    Raises:
        DataSplitError: If timestamp column is missing or parsing fails.
    """
    # Validate test_ratio
    if not 0.0 < test_ratio < 1.0:
        raise DataSplitError(f"test_ratio must be between 0 and 1, got {test_ratio}")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Determine timestamp column based on dataset
    if dataset_name == 'amazon_books':
        ts_col = timestamp_column if timestamp_column else 'reviewTime'
    elif dataset_name == 'lastfm':
        ts_col = timestamp_column if timestamp_column else 'date'
    elif dataset_name == 'movielens':
        ts_col = timestamp_column if timestamp_column else 'timestamp'
    else:
        ts_col = timestamp_column

    # Check if column exists
    if streaming:
        # For streaming, we need to materialize to check columns
        try:
            sample = next(iter(dataset))
            if ts_col not in sample:
                raise DataSplitError(
                    f"Timestamp column '{ts_col}' not found in dataset. "
                    f"Available columns: {list(sample.keys())}"
                )
        except StopIteration:
            raise DataSplitError("Dataset is empty")
    else:
        if ts_col not in dataset.column_names:
            raise DataSplitError(
                f"Timestamp column '{ts_col}' not found in dataset. "
                f"Available columns: {dataset.column_names}"
            )

    # Collect all interactions with parsed timestamps
    user_interactions = defaultdict(list)
    processed_count = 0

    # Convert to list for sorting (may be memory intensive for large datasets)
    # For very large datasets, consider chunked processing
    if streaming:
        interactions_list = list(dataset)
    else:
        interactions_list = dataset.to_list()

    for idx, interaction in enumerate(interactions_list):
        user_id = interaction.get(user_column)
        item_id = interaction.get(item_column)
        ts_raw = interaction.get(ts_col)

        if user_id is None or item_id is None:
            continue

        ts_parsed = _parse_timestamp(ts_raw, dataset_name)
        if ts_parsed is None:
            # Log warning but continue
            continue

        user_interactions[user_id].append({
            'user_id': user_id,
            'item_id': item_id,
            'timestamp': ts_parsed,
            'original_interaction': interaction
        })

        processed_count += 1
        if processed_count % 100000 == 0:
            print(f"Processed {processed_count} interactions...")

    if not user_interactions:
        raise DataSplitError("No valid interactions found after parsing timestamps")

    # Split by time for each user
    train_data = []
    test_data = []

    for user_id, interactions in user_interactions.items():
        if len(interactions) < 2:
            # Not enough interactions to split, put all in train
            train_data.extend(interactions)
            continue

        # Sort by timestamp
        interactions.sort(key=lambda x: x['timestamp'])

        # Calculate split index
        n_test = max(1, int(len(interactions) * test_ratio))
        n_train = len(interactions) - n_test

        # Ensure at least one interaction in train
        if n_train == 0:
            n_train = 1
            n_test = len(interactions) - 1

        train_data.extend(interactions[:n_train])
        test_data.extend(interactions[n_train:])

    print(f"Train set: {len(train_data)} interactions")
    print(f"Test set: {len(test_data)} interactions")

    # Prepare output data (flatten to simple format)
    def prepare_output(data_list, filename):
        output = []
        for item in data_list:
            record = {
                'user_id': item['user_id'],
                'item_id': item['item_id'],
                'timestamp': item['timestamp'],
                'dataset': dataset_name
            }
            # Add any additional fields from original interaction
            orig = item['original_interaction']
            for key, value in orig.items():
                if key not in record and key not in ['user_id', 'item_id', ts_col]:
                    record[key] = value
            output.append(record)
        return output

    train_output = prepare_output(train_data, 'train')
    test_output = prepare_output(test_data, 'test')

    # Save to files
    train_path = os.path.join(output_dir, f'{dataset_name}_train.json')
    test_path = os.path.join(output_dir, f'{dataset_name}_test.json')

    write_json(train_path, train_output)
    write_json(test_path, test_output)

    print(f"Train data saved to: {train_path}")
    print(f"Test data saved to: {test_path}")

    return train_path, test_path


def load_and_split_dataset(
    dataset_name: str,
    test_ratio: float = 0.2,
    output_dir: str = 'data/processed'
) -> Tuple[str, str]:
    """
    Main function to load a dataset and perform time-based splitting.

    Args:
        dataset_name: One of 'amazon_books', 'lastfm', 'movielens'.
        test_ratio: Proportion of recent interactions for test set.
        output_dir: Directory to save split datasets.

    Returns:
        Tuple of (train_path, test_path).

    Raises:
        ValueError: If dataset_name is not recognized.
        DataFetchError: If dataset cannot be loaded.
        DataSplitError: If splitting fails.
    """
    # Map dataset names to their configurations
    configs = {
        'amazon_books': {
            'loader': load_amazon_books,
            'user_col': 'user_id',
            'item_col': 'asin',
            'ts_col': 'reviewTime'
        },
        'lastfm': {
            'loader': load_lastfm,
            'user_col': 'user',
            'item_col': 'artist',
            'ts_col': 'date'
        },
        'movielens': {
            'loader': load_movielens,
            'user_col': 'userId',
            'item_col': 'movieId',
            'ts_col': 'timestamp'
        }
    }

    if dataset_name not in configs:
        raise ValueError(f"Unknown dataset: {dataset_name}. "
                       f"Choose from: {list(configs.keys())}")

    config = configs[dataset_name]

    # Load dataset
    print(f"Loading {dataset_name} dataset...")
    dataset = config['loader'](streaming=True)

    # Split dataset
    print(f"Splitting {dataset_name} dataset with time-based split...")
    train_path, test_path = split_dataset_by_time(
        dataset=dataset,
        dataset_name=dataset_name,
        timestamp_column=config['ts_col'],
        user_column=config['user_col'],
        item_column=config['item_col'],
        test_ratio=test_ratio,
        output_dir=output_dir,
        streaming=True
    )

    return train_path, test_path


if __name__ == '__main__':
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python data_loader.py <dataset_name> [test_ratio]")
        print("Available datasets: amazon_books, lastfm, movielens")
        sys.exit(1)

    dataset_name = sys.argv[1]
    test_ratio = float(sys.argv[2]) if len(sys.argv) > 2 else 0.2

    train_path, test_path = load_and_split_dataset(dataset_name, test_ratio)
    print(f"Completed. Train: {train_path}, Test: {test_path}")
