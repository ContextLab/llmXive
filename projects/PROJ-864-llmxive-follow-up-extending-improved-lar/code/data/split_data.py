import json
import os
import random
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import hashlib

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import load_config, get_project_root, get_processed_dir, get_data_dir
from utils.logging import setup_logging, get_logger, info, error, warning

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and invalid characters."""
    # Remove path separators and control characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Prevent path traversal
    filename = filename.replace('..', '')
    # Limit length
    if len(filename) > 255:
        base, ext = os.path.splitext(filename)
        filename = base[:255-len(ext)] + ext
    return filename

def validate_path(path: Path, base_dir: Path, description: str = "path") -> Path:
    """Validate that a path is within the allowed base directory."""
    try:
        resolved = path.resolve()
        base_resolved = base_dir.resolve()
        if not str(resolved).startswith(str(base_resolved)):
            raise ValueError(f"Security Error: {description} path '{path}' is outside allowed directory '{base_dir}'")
        return resolved
    except (ValueError, OSError) as e:
        error(f"Path validation failed for {description}: {e}")
        raise

def load_jsonl(input_path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file with path validation and content sanitization."""
    processed_dir = get_processed_dir()
    safe_input_path = validate_path(input_path, processed_dir, "input file")
    
    if not safe_input_path.exists():
        error(f"Input file not found: {safe_input_path}")
        raise FileNotFoundError(f"Input file not found: {safe_input_path}")
    
    data = []
    with open(safe_input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                # Sanitize text content
                if "text" in entry and isinstance(entry["text"], str):
                    entry["text"] = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', entry["text"])
                # Sanitize any filename fields
                if "filename" in entry:
                    entry["filename"] = sanitize_filename(str(entry["filename"]))
                data.append(entry)
            except json.JSONDecodeError as e:
                warning(f"Skipping invalid JSON at line {line_num}: {e}")
                continue
    
    info(f"Loaded {len(data)} entries from {safe_input_path}")
    return data

def save_jsonl(data: List[Dict[str, Any]], output_path: Path):
    """Save data to a JSONL file with path validation."""
    processed_dir = get_processed_dir()
    safe_output_path = validate_path(output_path, processed_dir, "output file")
    
    # Ensure parent directory exists
    safe_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(safe_output_path, 'w', encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    info(f"Saved {len(data)} entries to {safe_output_path}")

def split_data(input_path: Path, train_ratio: float = 0.8, seed: int = 42) -> Tuple[Path, Path]:
    """Split JSONL data into train and test sets with path validation."""
    # Validate input path
    processed_dir = get_processed_dir()
    safe_input_path = validate_path(input_path, processed_dir, "input file")
    
    if not safe_input_path.exists():
        error(f"Input file not found: {safe_input_path}")
        raise FileNotFoundError(f"Input file not found: {safe_input_path}")
    
    # Load data
    data = load_jsonl(safe_input_path)
    
    if len(data) == 0:
        error("No data to split")
        raise ValueError("No data to split")
    
    # Set seed for reproducibility
    random.seed(seed)
    
    # Shuffle data
    random.shuffle(data)
    
    # Calculate split index
    split_idx = int(len(data) * train_ratio)
    
    train_data = data[:split_idx]
    test_data = data[split_idx:]
    
    # Define output paths
    train_path = processed_dir / "micro_corpus_train.jsonl"
    test_path = processed_dir / "micro_corpus_test.jsonl"
    
    # Validate output paths
    train_path = validate_path(train_path, processed_dir, "train output")
    test_path = validate_path(test_path, processed_dir, "test output")
    
    # Save splits
    save_jsonl(train_data, train_path)
    save_jsonl(test_data, test_path)
    
    info(f"Split complete: Train={len(train_data)}, Test={len(test_data)}")
    info(f"Train ratio: {len(train_data)/len(data):.2%}, Test ratio: {len(test_data)/len(data):.2%}")
    
    return train_path, test_path

def main():
    """Main entry point for data splitting."""
    logger = setup_logging()
    
    try:
        config = load_config()
        train_ratio = config.get("train_split_ratio", 0.8)
        
        # Validate config
        if not isinstance(train_ratio, (int, float)) or not 0 < train_ratio < 1:
            error(f"Invalid train_split_ratio in config: {train_ratio}")
            sys.exit(1)
        
        input_path = get_processed_dir() / "micro_corpus_full.jsonl"
        
        info(f"Starting data split with train ratio: {train_ratio}")
        train_path, test_path = split_data(input_path, train_ratio)
        
        info(f"Data split completed successfully")
        info(f"Train file: {train_path}")
        info(f"Test file: {test_path}")
        
    except Exception as e:
        error(f"Fatal error in split_data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()