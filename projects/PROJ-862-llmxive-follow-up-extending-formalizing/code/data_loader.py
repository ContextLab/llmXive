"""
Data loading module for the llmXive noise injection pipeline.
Fetches the BigBench reasoning dataset and ensures schema validity.
"""
import json
import logging
from typing import Dict, Any, Optional, Iterator, List
from datasets import load_dataset

from config import DataConfig, PipelineConfig
from streaming_utils import stream_dataset
from memory_monitor import check_memory_limit

logger = logging.getLogger(__name__)


def load_reasoning_dataset(
    config: DataConfig,
    streaming: bool = False
) -> Any:
    """
    Loads the BigBench reasoning dataset from Hugging Face.
    
    Args:
        config: DataConfig instance containing dataset parameters.
        streaming: If True, returns a streaming dataset iterator.
    
    Returns:
        Dataset or IterableDataset depending on streaming flag.
    
    Raises:
        ConfigurationError: If the dataset cannot be fetched or lacks 'expected_answer'.
    """
    dataset_name = config.dataset_name
    subset_name = config.subset_name
    
    logger.info(f"Loading dataset: {dataset_name} (subset: {subset_name})")
    
    try:
        if streaming:
            dataset = load_dataset(
                dataset_name,
                subset_name,
                split=config.split,
                streaming=True
            )
        else:
            dataset = load_dataset(
                dataset_name,
                subset_name,
                split=config.split
            )
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}/{subset_name}: {e}")
        raise ConfigurationError(
            f"Could not fetch dataset from Hugging Face: {e}. "
            "Ensure the dataset name and subset are correct and internet is accessible."
        )
    
    return dataset


def validate_expected_answer_column(dataset: Any) -> None:
    """
    Validates that the dataset contains the 'expected_answer' column.
    
    Args:
        dataset: The loaded dataset object.
    
    Raises:
        ConfigurationError: If 'expected_answer' column is missing.
    """
    # Handle both standard Dataset and Streaming Dataset column checks
    if hasattr(dataset, 'column_names'):
        columns = dataset.column_names
    else:
        # For streaming, we might need to peek or rely on schema
        # Assuming standard HF streaming dataset structure
        columns = dataset.features.keys() if hasattr(dataset, 'features') else []
    
    if 'expected_answer' not in columns:
        available_cols = list(columns) if isinstance(columns, list) else list(columns.keys())
        logger.critical(
            f"Dataset missing required column 'expected_answer'. "
            f"Available columns: {available_cols}"
        )
        raise ConfigurationError(
            f"Dataset validation failed: Column 'expected_answer' is missing. "
            f"Found columns: {available_cols}. "
            "The pipeline requires 'expected_answer' for output validity checks (FR-006)."
        )
    
    logger.info("Dataset validation passed: 'expected_answer' column found.")


class ConfigurationError(Exception):
    """Custom exception for configuration and data validation errors."""
    pass


def get_pairing_data(
    config: DataConfig,
    pipeline_config: PipelineConfig
) -> Iterator[Dict[str, Any]]:
    """
    Streams the dataset, validates the schema, and yields rows for pairing.
    
    Args:
        config: DataConfig instance.
        pipeline_config: PipelineConfig instance (for memory limits).
    
    Yields:
        Dictionary rows from the dataset.
    
    Raises:
        ConfigurationError: If data fetch fails or schema is invalid.
    """
    dataset = load_reasoning_dataset(config, streaming=True)
    
    # Validate schema immediately
    validate_expected_answer_column(dataset)
    
    # Stream and yield rows, checking memory periodically
    for row in dataset:
        check_memory_limit(pipeline_config.memory_limit_gb)
        yield row


def pair_questions_by_task_type(
    config: DataConfig,
    pipeline_config: PipelineConfig,
    output_path: str = "data/processed/pairing_config.json"
) -> Dict[str, Any]:
    """
    Pairs questions by task type and assigns unique PairIDs.
    
    This function iterates over the dataset, groups questions by their 'task_type'
    (or inferred equivalent), and generates unique PairIDs for each group.
    It outputs a configuration JSON file mapping PairIDs to question indices/text.
    
    Args:
        config: DataConfig instance.
        pipeline_config: PipelineConfig instance.
        output_path: Path to save the pairing configuration JSON.
    
    Returns:
        A dictionary containing the pairing configuration.
    
    Raises:
        ConfigurationError: If dataset structure is invalid for pairing.
    """
    logger.info("Starting question pairing by task type...")
    
    # Ensure output directory exists
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    pairing_data: Dict[str, List[Dict[str, Any]]] = {}
    pair_id_counter = 0
    
    # We need to collect data to form pairs. Since we are streaming,
    # we accumulate by task_type in memory. If a task_type has N items,
    # we can form pairs (0,1), (2,3) etc. or a complete graph.
    # For this implementation, we will group by task_type and assign
    # a PairID to each group (or sub-group if we want pairs within groups).
    # The task says "pair questions", implying pairs of questions.
    # Strategy: Group by task_type. For each group with >= 2 items,
    # create pairs (item_i, item_j) and assign a unique PairID.
    
    # We will store a list of items per task_type temporarily.
    # Note: If a task_type is very large, this might exceed memory.
    # Given the memory constraints (T008b), we assume task_types are reasonable
    # or we process in chunks. For now, we implement a grouping strategy
    # that resets after creating pairs to save memory, or we just list all
    # indices per task_type and generate PairIDs logically.
    
    # Let's define the schema for the output:
    # {
    #   "pairing_metadata": { "total_pairs": int, "task_types_processed": [...] },
    #   "pairs": [ { "pair_id": "PAIR_0001", "task_type": "...", "indices": [i, j], "texts": ["...", "..."] } ... ]
    # }
    # However, storing all texts in memory might be heavy.
    # Better approach: Store indices and metadata.
    
    # Re-evaluating based on "assign unique PairIDs":
    # We will iterate, group by task_type, and for every 2 items in a group,
    # create a pair and assign a PairID.
    
    current_task_groups: Dict[str, List[Dict[str, Any]]] = {}
    
    for row in get_pairing_data(config, pipeline_config):
        # Identify task type. Try common column names.
        task_type = None
        if 'task_type' in row:
            task_type = row['task_type']
        elif 'type' in row:
            task_type = row['type']
        elif 'task_id' in row:
            task_type = row['task_id']
        else:
            # Fallback: use a hash of the question or a default
            task_type = "unknown"
        
        if task_type not in current_task_groups:
            current_task_groups[task_type] = []
        
        current_task_groups[task_type].append(row)
        
        # If a group has enough items to form a pair, we can emit it?
        # Or we wait until the end? To save memory, we emit pairs as soon as we have 2.
        # But we need to ensure we don't hold too many unpaired items.
        # Let's emit pairs immediately when a group reaches size 2.
        if len(current_task_groups[task_type]) >= 2:
            item1 = current_task_groups[task_type].pop(0)
            item2 = current_task_groups[task_type].pop(0)
            
            pair_id = f"PAIR_{pair_id_counter:06d}"
            pair_id_counter += 1
            
            # Determine indices. If the dataset has an 'idx' or 'id' column, use it.
            # Otherwise, we might need to track global index.
            # For now, we assume the row contains an identifier or we use a generated one.
            # Let's assume we track a global index if not present.
            idx1 = item1.get('idx', item1.get('id', f"idx_{pair_id}_1"))
            idx2 = item2.get('idx', item2.get('id', f"idx_{pair_id}_2"))
            
            # We store minimal info to keep memory low.
            # If the task requires full text, we might need to store it.
            # Assuming we store text for the config file as per "output pairing_config.json".
            text1 = item1.get('question', item1.get('input', ""))
            text2 = item2.get('question', item2.get('input', ""))
            
            pair_record = {
                "pair_id": pair_id,
                "task_type": task_type,
                "indices": [idx1, idx2],
                "texts": [text1[:500], text2[:500]] # Truncate to save space if needed
            }
            
            if "pairs" not in pairing_data:
                pairing_data["pairs"] = []
            
            pairing_data["pairs"].append(pair_record)
            
            # Check memory limit frequently
            check_memory_limit(pipeline_config.memory_limit_gb)
    
    # Handle remaining unpaired items (if any) - optionally log or discard
    remaining_count = sum(len(v) for v in current_task_groups.values())
    if remaining_count > 0:
        logger.warning(f"Found {remaining_count} unpaired items after processing. They will be discarded.")
    
    pairing_data["pairing_metadata"] = {
        "total_pairs": len(pairing_data.get("pairs", [])),
        "task_types_processed": list(current_task_groups.keys()),
        "output_file": output_path
    }
    
    # Write to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(pairing_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Pairing complete. Saved {len(pairing_data['pairs'])} pairs to {output_path}")
    return pairing_data
