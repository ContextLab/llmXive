import json
import os
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path to allow imports from sibling modules if needed
# However, this script primarily uses standard library and local file I/O.
# We ensure the path is set relative to the project root.
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load a JSONL file into a list of dictionaries.
    
    Args:
        file_path: Path to the JSONL file.
        
    Returns:
        List of dictionaries representing the lines in the file.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If a line is not valid JSON.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON at line {line_num} in {file_path}: {e.msg}",
                    e.doc, e.pos
                )
    return data

def save_jsonl(data: List[Dict[str, Any]], file_path: Path) -> None:
    """
    Save a list of dictionaries to a JSONL file.
    
    Args:
        data: List of dictionaries to save.
        file_path: Path to the output JSONL file.
    """
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def split_data(
    input_file: Path, 
    train_output: Path, 
    test_output: Path, 
    test_ratio: float = 0.2, 
    seed: int = 42
) -> Tuple[int, int]:
    """
    Split the input JSONL corpus into training and test sets.
    
    This function reads the entire corpus, shuffles it deterministically,
    splits it according to the test_ratio, and writes the two parts to
    separate files. It ensures no overlap between the sets.
    
    Args:
        input_file: Path to the input JSONL file (e.g., micro_corpus_full.jsonl).
        train_output: Path for the training set output.
        test_output: Path for the test set output.
        test_ratio: Fraction of data to use for testing (default 0.2).
        seed: Random seed for reproducibility.
        
    Returns:
        A tuple (train_count, test_count).
        
    Raises:
        ValueError: If test_ratio is not between 0 and 1.
        FileNotFoundError: If input_file does not exist.
    """
    if not 0.0 <= test_ratio <= 1.0:
        raise ValueError(f"test_ratio must be between 0 and 1, got {test_ratio}")
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input corpus file not found: {input_file}")
    
    # Set random seed for reproducibility
    random.seed(seed)
    
    # Load data
    print(f"Loading data from {input_file}...")
    data = load_jsonl(input_file)
    total_count = len(data)
    
    if total_count == 0:
        raise ValueError("Input corpus is empty. Cannot split.")
    
    # Shuffle data
    random.shuffle(data)
    
    # Calculate split index
    test_count = int(total_count * test_ratio)
    train_count = total_count - test_count
    
    if test_count == 0:
        print("Warning: test_ratio resulted in 0 test samples. Adjust ratio or data size.")
    
    train_data = data[:train_count]
    test_data = data[train_count:]
    
    # Ensure no overlap (sanity check)
    assert len(set(id(x) for x in train_data)) == len(train_data), "Duplicate references in train"
    assert len(set(id(x) for x in test_data)) == len(test_data), "Duplicate references in test"
    
    # Save outputs
    print(f"Saving {train_count} samples to {train_output}...")
    save_jsonl(train_data, train_output)
    
    print(f"Saving {test_count} samples to {test_output}...")
    save_jsonl(test_data, test_output)
    
    return train_count, test_count

def main():
    """
    Main entry point for splitting the micro-corpus.
    
    Expects the input file at: data/processed/micro_corpus_full.jsonl
    Outputs to:
        data/processed/micro_corpus_train.jsonl
        data/processed/micro_corpus_test.jsonl
    """
    input_path = DATA_PROCESSED_DIR / "micro_corpus_full.jsonl"
    train_path = DATA_PROCESSED_DIR / "micro_corpus_train.jsonl"
    test_path = DATA_PROCESSED_DIR / "micro_corpus_test.jsonl"
    
    # Default split: 80% train, 20% test
    TEST_RATIO = 0.2
    SEED = 42
    
    print(f"Starting data split for project: {PROJECT_ROOT}")
    print(f"Input: {input_path}")
    print(f"Output Train: {train_path}")
    print(f"Output Test: {test_path}")
    
    try:
        train_count, test_count = split_data(
            input_file=input_path,
            train_output=train_path,
            test_output=test_path,
            test_ratio=TEST_RATIO,
            seed=SEED
        )
        print(f"Split complete.")
        print(f"  Training samples: {train_count}")
        print(f"  Test samples: {test_count}")
        print(f"  Total: {train_count + test_count}")
        
        # Verify outputs exist and are non-empty
        if not train_path.exists() or train_path.stat().st_size == 0:
            raise RuntimeError("Training file was not created or is empty.")
        if not test_path.exists() or test_path.stat().st_size == 0:
            raise RuntimeError("Test file was not created or is empty.")
            
        print("Verification passed: Output files exist and are non-empty.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Ensure that T014 (tokenize_and_stream.py) has completed successfully and generated micro_corpus_full.jsonl.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during split: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()