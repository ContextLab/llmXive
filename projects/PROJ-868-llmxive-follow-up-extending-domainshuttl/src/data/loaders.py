"""
WebVid-10M Data Loader for llmXive Project.

This module implements the data loading logic for User Story 1.
It fetches exactly 100 diverse subjects via stratified random sampling
from the 'webvid' dataset (a proxy for WebVid-10M accessible via HuggingFace),
ensuring uniform distribution across the top 10 categories.
"""

import os
import logging
from typing import List, Dict, Any, Optional

import pandas as pd
from datasets import load_dataset, Dataset

from src.config.settings import DATA_PATHS, SEEDS
from src.utils.io import ensure_dir

logger = logging.getLogger(__name__)


def _get_top_n_categories(df: pd.DataFrame, n: int = 10) -> List[str]:
    """
    Identifies the top N most frequent categories in the dataset.
    If the dataset has fewer than N categories, it returns all available.
    """
    category_counts = df['category'].value_counts()
    top_categories = category_counts.head(n).index.tolist()
    logger.info(f"Selected top {len(top_categories)} categories: {top_categories}")
    return top_categories


def load_webvid_subjects(
    num_subjects: int = 100,
    seed: int = 42,
    category_column: str = 'category',
    id_column: str = 'videoid'
) -> Dict[str, Any]:
    """
    Loads a curated subset of 100 diverse subjects from the WebVid dataset.

    Strategy:
    1. Load the 'webvid' dataset (streaming or full depending on memory, here we assume
       a manageable subset or the specific HuggingFace mirror used for WebVid).
    2. Identify the top 10 categories.
    3. Perform stratified sampling to ensure uniform distribution across these categories.
    4. Return the resulting DataFrame and the list of sampled IDs.

    Args:
        num_subjects: Total number of subjects to fetch (default 100).
        seed: Random seed for reproducibility.
        category_column: Name of the column containing category labels.
        id_column: Name of the column containing unique video IDs.

    Returns:
        A dictionary containing:
            - 'subjects_df': DataFrame with the sampled subjects.
            - 'subject_ids': List of unique video IDs.
            - 'categories_used': List of categories sampled from.

    Raises:
        ValueError: If the dataset cannot be loaded or does not contain the required columns.
        RuntimeError: If stratified sampling fails to produce the requested number of subjects.
    """
    # Ensure deterministic behavior
    import random
    random.seed(seed)

    logger.info(f"Initializing WebVid-10M loader for {num_subjects} subjects (seed={seed})...")

    # Load dataset
    # Note: 'webvid' on HuggingFace is a common proxy for WebVid-10M.
    # We load it fully to perform stratified sampling on the metadata.
    # If the dataset is too large for memory, a streaming approach with pre-filtered shards
    # would be required, but for metadata sampling of 100 items, we load the metadata.
    try:
        # Using the specific 'webvid' dataset which contains the necessary metadata
        dataset = load_dataset("maximelb/webvid-10m", split="train")
    except Exception as e:
        raise RuntimeError(f"Failed to load WebVid-10M dataset: {e}")

    if category_column not in dataset.column_names or id_column not in dataset.column_names:
        raise ValueError(f"Dataset must contain columns '{category_column}' and '{id_column}'. "
                         f"Found columns: {dataset.column_names}")

    df = dataset.to_pandas()

    # Determine top 10 categories
    # We assume the dataset has a 'category' column. If not, we might need to map it.
    # The 'webvid' dataset typically has 'page_data' JSON, but the cleaned version
    # often exposes 'category' directly.
    if category_column not in df.columns:
        # Fallback: try to extract from page_data if it exists and is JSON
        if 'page_data' in df.columns:
            # Attempt to parse JSON if needed, otherwise assume structure
            # This is a heuristic for the specific dataset version
            logger.warning(f"Column '{category_column}' not found. Attempting to derive from 'page_data'.")
            # For this implementation, we assume the dataset is the cleaned version
            # where 'category' is already a column. If not, we raise an error to fail loudly.
            raise ValueError(f"Could not find '{category_column}' column. The dataset version loaded "
                             f"does not match the expected schema.")
        else:
            raise ValueError(f"Column '{category_column}' not found in dataset.")

    top_categories = _get_top_n_categories(df, n=10)

    # Calculate sample size per category for uniform distribution
    # We want exactly num_subjects total, distributed evenly across top 10 categories.
    # If num_subjects is not divisible by 10, we round or adjust.
    samples_per_category = num_subjects // len(top_categories)
    remainder = num_subjects % len(top_categories)

    sampled_dfs = []
    for i, cat in enumerate(top_categories):
        # Distribute remainder to the first 'remainder' categories
        n_samples = samples_per_category + (1 if i < remainder else 0)
        
        cat_df = df[df[category_column] == cat]
        
        if len(cat_df) < n_samples:
            logger.warning(f"Category '{cat}' has only {len(cat_df)} items, requested {n_samples}. "
                           f"Taking all available.")
            n_samples = len(cat_df)
        
        # Stratified random sample
        sample_df = cat_df.sample(n=n_samples, random_state=seed)
        sampled_dfs.append(sample_df)
    
    final_df = pd.concat(sampled_dfs, ignore_index=True)

    # Final shuffle to mix categories
    final_df = final_df.sample(frac=1, random_state=seed).reset_index(drop=True)

    if len(final_df) < num_subjects:
        raise RuntimeError(
            f"Stratified sampling failed to produce {num_subjects} subjects. "
            f"Only retrieved {len(final_df)}. The dataset may be too small or imbalanced."
        )

    # Truncate if we got more than requested (e.g. due to rounding up in all categories)
    final_df = final_df.head(num_subjects)

    subject_ids = final_df[id_column].tolist()
    
    logger.info(f"Successfully loaded {len(final_df)} subjects from {len(top_categories)} categories.")
    logger.info(f"Subject IDs (first 5): {subject_ids[:5]}")

    return {
        "subjects_df": final_df,
        "subject_ids": subject_ids,
        "categories_used": top_categories
    }


def save_subject_metadata(output_dir: str, data: Dict[str, Any]) -> str:
    """
    Saves the loaded subject metadata to a CSV file.

    Args:
        output_dir: Directory to save the CSV.
        data: Dictionary returned by load_webvid_subjects.

    Returns:
        Path to the saved CSV file.
    """
    ensure_dir(output_dir)
    csv_path = os.path.join(output_dir, "webvid_subjects.csv")
    
    data["subjects_df"].to_csv(csv_path, index=False)
    logger.info(f"Saved subject metadata to {csv_path}")
    return csv_path
