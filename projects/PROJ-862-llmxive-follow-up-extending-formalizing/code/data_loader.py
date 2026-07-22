import json
import logging
from typing import Dict, Any, Optional, Iterator, List
from datasets import load_dataset
from config import DataConfig, PipelineConfig
from streaming_utils import stream_dataset

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when configuration or data requirements are not met."""
    pass

def load_reasoning_dataset(dataset_name: str, split: str = "train") -> Iterator[Dict[str, Any]]:
    """
    Load the reasoning dataset from HuggingFace.
    Returns an iterator over the dataset rows.
    """
    logger.info(f"Loading dataset: {dataset_name}, split: {split}")
    try:
        # Use streaming to handle large datasets
        ds = load_dataset(dataset_name, split=split, streaming=True)
        return iter(ds)
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        raise

def validate_expected_answer_column(batch: List[Dict[str, Any]]) -> None:
    """
    Validates that the 'expected_answer' column exists in the dataset.
    Raises ConfigurationError if missing.
    """
    if not batch:
        raise ConfigurationError("Dataset batch is empty, cannot validate columns.")
    
    first_item = batch[0]
    if 'expected_answer' not in first_item:
        raise ConfigurationError(
            "Dataset missing required column 'expected_answer'. "
            "This is a hard failure; no synthetic fallback is permitted."
        )
    logger.info("Validation passed: 'expected_answer' column exists.")

def get_pairing_data(dataset_iter: Iterator[Dict[str, Any]], config: DataConfig) -> List[Dict[str, Any]]:
    """
    Groups questions by task type and returns a list of pairs.
    This is a simplified implementation assuming the dataset has a 'task_type' field.
    In a real scenario, this logic would be more complex to handle specific pairing rules.
    """
    # For the purpose of T013 implementation, we collect items into groups
    # Note: In a true streaming scenario with infinite data, we would process in chunks.
    # Here we assume the dataset is finite enough for this step or we limit the scope.
    groups = {}
    count = 0
    max_items = 1000 # Limit for this demo implementation to prevent OOM in pairing logic
    
    for item in dataset_iter:
        if count >= max_items:
            break
        
        task_type = item.get('task_type', 'unknown')
        if task_type not in groups:
            groups[task_type] = []
        groups[task_type].append(item)
        count += 1
    
    # Pair items within groups
    pairs = []
    pair_id = 0
    for task_type, items in groups.items():
        # Simple pairing: consecutive items
        for i in range(0, len(items) - 1, 2):
            pair_id += 1
            pairs.append({
                'PairID': pair_id,
                'TaskType': task_type,
                'Item1': items[i],
                'Item2': items[i+1]
            })
    
    return pairs

def pair_questions_by_task_type(dataset_iter: Iterator[Dict[str, Any]], config: DataConfig) -> List[Dict[str, Any]]:
    """
    Wrapper to pair questions by task type.
    Returns a list of dictionaries containing PairID, TaskType, and necessary fields for extraction.
    """
    # We need to extract specific fields for model_utils.extract_thought_vector
    # Assuming the dataset has 'input_ids' and 'thought_token_pos'
    
    raw_pairs = get_pairing_data(dataset_iter, config)
    
    processed_pairs = []
    for pair in raw_pairs:
        # Flatten the pair structure for easier consumption by the extraction loop
        # We assume we pair Item1 and Item2, but for baseline extraction we might just process one?
        # The task says "pair questions", so we output the pair.
        # However, extract_thought_vector expects input_ids.
        # Let's assume we process Item1 for baseline, or both.
        # For T017, we just need to ensure the structure exists.
        
        # Let's assume we create a pair where both items are processed or we pick one.
        # The requirement says "pair questions by task type and assign unique PairIDs".
        # We will output a structure that the main loop can iterate.
        
        # For simplicity in this implementation, we assume the pair logic is:
        # PairID -> [Item1, Item2]
        # But the extraction loop needs input_ids.
        # Let's create a flat list of items that belong to a pair, or just return the raw pairs
        # and let the extraction logic handle it.
        
        # Revised: The main loop expects an iterator of items to process, each with a PairID.
        # So we will flatten the pairs back into items, tagging them with the PairID.
        
        item1 = pair['Item1']
        item2 = pair['Item2']
        
        # Ensure required fields exist
        if 'input_ids' not in item1 or 'thought_token_pos' not in item1:
            logger.warning(f"Skipping pair {pair['PairID']}: Missing required fields in Item1.")
            continue
        
        processed_pairs.append({
            'PairID': pair['PairID'],
            'TaskType': pair['TaskType'],
            'input_ids': item1['input_ids'],
            'thought_token_pos': item1['thought_token_pos']
        })
        
        if 'input_ids' in item2 and 'thought_token_pos' in item2:
            processed_pairs.append({
                'PairID': pair['PairID'],
                'TaskType': pair['TaskType'],
                'input_ids': item2['input_ids'],
                'thought_token_pos': item2['thought_token_pos']
            })
        
    return processed_pairs
