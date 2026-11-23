"""
Security hardened data splitting module.
Implements input validation and path sanitization.
"""
import json
import os
import random
import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# --- Input Validation Helpers ---

def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be used as a filename.
    Removes or replaces characters that are invalid or dangerous on most filesystems.
    """
    if not name:
        raise ValueError("Filename cannot be empty.")
    
    # Remove control characters and null bytes
    name = re.sub(r'[\x00-\x1f\x7f]', '', name)
    
    # Replace path separators and dangerous characters
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    
    # Remove leading/trailing dots or spaces (Windows specific issues)
    name = name.strip('. ')
    
    # Limit length to prevent filesystem limits
    if len(name) > 255:
        name = name[:255]
    
    if not name:
        raise ValueError("Filename became empty after sanitization.")
    
    return name

def validate_path(path: str, base_dir: Optional[Path] = None) -> Path:
    """
    Validate a path to ensure it does not escape the base directory (Path Traversal prevention).
    """
    if not path:
        raise ValueError("Path cannot be empty.")
    
    # Sanitize the input string first
    safe_name = sanitize_filename(path)
    
    target = Path(base_dir) / safe_name if base_dir else Path(safe_name)
    
    # Resolve to absolute path to check for .. traversal
    try:
        resolved = target.resolve()
    except Exception as e:
        raise ValueError(f"Invalid path resolution: {e}")
    
    if base_dir:
        base_resolved = base_dir.resolve()
        # Ensure the resolved path is within the base directory
        try:
            resolved.relative_to(base_resolved)
        except ValueError:
            raise ValueError(f"Path traversal detected: {path} resolves outside {base_dir}")
    
    return resolved

# --- Data Loading/Saving ---

def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """
    Load a JSONL file into a list of dictionaries.
    """
    path = validate_path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_num} in {file_path}: {e}")
    return data

def save_jsonl(data: List[Dict[str, Any]], file_path: str) -> None:
    """
    Save a list of dictionaries to a JSONL file.
    """
    path = validate_path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Data must be a list of dictionaries.")
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

# --- Splitting Logic ---

def split_data(input_file: str, train_ratio: float = 0.8, seed: int = 42) -> Tuple[str, str]:
    """
    Split the input JSONL file into train and test sets.
    Returns the paths to the new files.
    """
    # Validate inputs
    if not isinstance(train_ratio, (int, float)) or not (0.0 < train_ratio < 1.0):
        raise ValueError("train_ratio must be a float between 0 and 1.")
    
    if not isinstance(seed, int):
        raise ValueError("seed must be an integer.")
    
    random.seed(seed)
    
    data = load_jsonl(input_file)
    
    if not data:
        raise ValueError("Input file is empty.")
    
    # Shuffle data
    random.shuffle(data)
    
    split_idx = int(len(data) * train_ratio)
    train_data = data[:split_idx]
    test_data = data[split_idx:]
    
    # Construct output paths safely
    input_path = validate_path(input_file)
    base_name = input_path.stem
    parent_dir = input_path.parent
    
    train_output = validate_path(f"{base_name}_train.jsonl", base_dir=parent_dir)
    test_output = validate_path(f"{base_name}_test.jsonl", base_dir=parent_dir)
    
    save_jsonl(train_data, str(train_output))
    save_jsonl(test_data, str(test_output))
    
    return str(train_output), str(test_output)

def main():
    """
    Entry point for the script.
    """
    # Default paths
    input_file = "data/processed/micro_corpus_full.jsonl"
    
    if not Path(input_file).exists():
        print(f"Error: Input file not found at {input_file}")
        sys.exit(1)
    
    try:
        train_path, test_path = split_data(input_file, train_ratio=0.8, seed=42)
        print(f"Split complete. Train: {train_path}, Test: {test_path}")
    except Exception as e:
        print(f"Fatal Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()