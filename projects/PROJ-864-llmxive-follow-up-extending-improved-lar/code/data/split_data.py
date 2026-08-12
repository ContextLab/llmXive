import json
import os
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.logging import get_logger, info, error, warning

logger = get_logger(__name__)

def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load a JSONL file into a list of dictionaries.

    Args:
        file_path: Path to the JSONL file.

    Returns:
        List of dictionaries, each representing a line in the JSONL file.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If a line is not valid JSON.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    logger.info(f"Loading JSONL from {file_path}")
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                error(f"Invalid JSON on line {line_num} in {file_path}: {e}")
                raise
    logger.info(f"Loaded {len(data)} records from {file_path}")
    return data

def save_jsonl(data: List[Dict[str, Any]], file_path: Path) -> None:
    """
    Save a list of dictionaries to a JSONL file.

    Args:
        data: List of dictionaries to save.
        file_path: Path to the output JSONL file.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving {len(data)} records to {file_path}")
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record) + '\n')
    logger.info(f"Successfully saved to {file_path}")

def split_data(
    data: List[Dict[str, Any]],
    train_ratio: float = 0.9,
    seed: int = 42
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Split data into training and test sets.

    Args:
        data: List of data records.
        train_ratio: Proportion of data to use for training (default 0.9).
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (train_data, test_data).

    Raises:
        ValueError: If train_ratio is not between 0 and 1.
    """
    if not 0.0 < train_ratio < 1.0:
        raise ValueError(f"train_ratio must be between 0 and 1, got {train_ratio}")

    random.seed(seed)
    indices = list(range(len(data)))
    random.shuffle(indices)

    split_idx = int(len(data) * train_ratio)
    train_indices = indices[:split_idx]
    test_indices = indices[split_idx:]

    train_data = [data[i] for i in train_indices]
    test_data = [data[i] for i in test_indices]

    logger.info(f"Split complete: {len(train_data)} training, {len(test_data)} test samples")
    logger.info(f"Split ratio: {len(train_data) / len(data):.2%} train, {len(test_data) / len(data):.2%} test")

    return train_data, test_data

def main():
    """
    Main entry point for splitting the micro-corpus.

    Reads micro_corpus_full.jsonl and splits it into train and test sets.
    """
    # Determine paths relative to project root
    # Assuming script is at code/data/split_data.py
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    input_file = project_root / "data" / "processed" / "micro_corpus_full.jsonl"
    train_output = project_root / "data" / "processed" / "micro_corpus_train.jsonl"
    test_output = project_root / "data" / "processed" / "micro_corpus_test.jsonl"

    # Configuration
    train_ratio = 0.9  # 90% train, 10% test
    seed = 42

    info(f"Starting data split for {input_file}")
    info(f"Train ratio: {train_ratio}, Seed: {seed}")

    try:
        # Load the full corpus
        data = load_jsonl(input_file)

        if len(data) == 0:
            error("Input file is empty. Cannot split empty data.")
            sys.exit(1)

        # Split the data
        train_data, test_data = split_data(data, train_ratio=train_ratio, seed=seed)

        # Validate splits are non-overlapping (by index, already guaranteed by logic)
        # But we can double-check content hash if needed for strict verification
        info(f"Train set size: {len(train_data)} records")
        info(f"Test set size: {len(test_data)} records")

        # Save outputs
        save_jsonl(train_data, train_output)
        save_jsonl(test_data, test_output)

        info(f"Successfully split data into:")
        info(f"  Train: {train_output}")
        info(f"  Test:  {test_output}")

    except FileNotFoundError as e:
        error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        error(f"Unexpected error during split: {e}")
        raise

if __name__ == "__main__":
    main()