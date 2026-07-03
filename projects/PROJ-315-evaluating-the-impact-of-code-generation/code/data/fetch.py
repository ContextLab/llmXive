"""
Dataset fetching module for llmXive research pipeline.

Handles downloading the GitHub PR dataset from HuggingFace.
"""
from pathlib import Path
from typing import Optional

from datasets import load_dataset
import pandas as pd

from code.utils.config import set_global_seed
from code.utils.logger import get_logger

logger = get_logger(__name__)


def fetch_dataset(
    dataset_name: str = "codeparliament/github-code-search",
    split: str = "train",
    streaming: bool = True,
    max_records: Optional[int] = None,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Fetch the GitHub PR dataset from HuggingFace.
    
    Args:
        dataset_name: HuggingFace dataset identifier
        split: Dataset split to load
        streaming: Whether to use streaming mode
        max_records: Maximum number of records to load (None for all)
        output_path: Optional path to save the dataset
        
    Returns:
        DataFrame with the dataset
    """
    set_global_seed(42)
    logger.info(f"Fetching dataset: {dataset_name} ({split})")
    
    try:
        dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=streaming,
            trust_remote_code=True
        )
        
        # Convert to pandas
        df_list = []
        count = 0
        for item in dataset:
            df_list.append(item)
            count += 1
            if max_records and count >= max_records:
                break
        
        df = pd.DataFrame(df_list)
        logger.info(f"Loaded {len(df)} records from {dataset_name}")
        
        # Save if output path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_path, index=False)
            logger.info(f"Saved dataset to {output_path}")
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        raise