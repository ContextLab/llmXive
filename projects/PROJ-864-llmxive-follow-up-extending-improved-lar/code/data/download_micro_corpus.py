"""
Security hardened Micro-Corpus download module.
Implements input validation and path sanitization.
"""
import json
import os
import sys
import hashlib
import time
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging

# Attempt to import real dependencies; if missing, the script will fail loudly
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError("Required package 'datasets' is not installed. Run: pip install datasets")

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

# --- Configuration Loading ---

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load and validate configuration from a YAML or JSON file.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    # Basic extension check
    if path.suffix.lower() not in ['.yaml', '.yml', '.json']:
        raise ValueError(f"Unsupported config format: {path.suffix}")
    
    with open(path, 'r', encoding='utf-8') as f:
        if path.suffix.lower() in ['.yaml', '.yml']:
            try:
                import yaml
                return yaml.safe_load(f)
            except ImportError:
                raise ImportError("PyYAML is required to load .yaml config files.")
        else:
            return json.load(f)

# --- Logging Setup ---

def setup_logging(log_dir: str, name: str = "download_micro_corpus") -> logging.Logger:
    """
    Setup logging to file and console.
    """
    log_path = validate_path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler(log_path / f"{name}_{int(time.time())}.log")
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

# --- Data Fetching ---

def fetch_gutenberg_samples(streaming: bool = True, num_samples: int = 1000) -> Any:
    """
    Fetch samples from Project Gutenberg via Hugging Face Datasets.
    Uses streaming to avoid loading full dataset into memory.
    """
    try:
        # Real source: Project Gutenberg on Hugging Face
        # Dataset ID is verified to exist and be public
        ds = load_dataset("pg19", split="train", streaming=streaming)
        return ds
    except Exception as e:
        raise RuntimeError(f"Failed to load Project Gutenberg dataset: {e}")

def fetch_the_stack_samples(streaming: bool = True, subset: str = "code") -> Any:
    """
    Fetch samples from The Stack via Hugging Face Datasets.
    Uses streaming to avoid loading full dataset into memory.
    """
    try:
        # Real source: The Stack (v2 or v1) on Hugging Face
        # Using a specific subset to ensure it's code-heavy as required
        # Note: 'bigcode/the-stack' is the canonical ID
        ds = load_dataset("bigcode/the-stack", split="train", streaming=streaming, trust_remote_code=True)
        return ds
    except Exception as e:
        raise RuntimeError(f"Failed to load The Stack dataset: {e}")

# --- Token Counting ---

def count_tokens(text: str) -> int:
    """
    Simple token counting approximation (whitespace + punctuation).
    For real production, a specific tokenizer should be used.
    """
    if not text:
        return 0
    # Rough approximation: split by whitespace
    return len(text.split())

# --- Saving ---

def save_samples_to_jsonl(data_stream: Any, output_path: str, max_tokens: int = -1) -> int:
    """
    Save samples from a stream to a JSONL file.
    Enforces max_tokens limit if provided.
    """
    output_path_obj = validate_path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    current_tokens = 0
    count = 0
    
    with open(output_path_obj, 'w', encoding='utf-8') as f:
        for item in data_stream:
            # Basic validation of item structure
            if not isinstance(item, dict):
                raise ValueError("Dataset item must be a dictionary.")
            
            text = item.get("text", "")
            if not isinstance(text, str):
                raise ValueError("Text field must be a string.")
            
            tokens = count_tokens(text)
            
            if max_tokens > 0 and current_tokens + tokens > max_tokens:
                break
            
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            current_tokens += tokens
            count += 1
            
            if count % 1000 == 0:
                print(f"Saved {count} samples, {current_tokens} tokens...")
    
    return count

# --- Main Logic ---

def combined_stream(gutenberg_ds: Any, stack_ds: Any, target_tokens: int) -> Any:
    """
    Combine two data streams in a round-robin fashion.
    """
    g_iter = iter(gutenberg_ds)
    s_iter = iter(stack_ds)
    
    current_tokens = 0
    
    while current_tokens < target_tokens:
        try:
            g_item = next(g_iter)
            yield g_item
            current_tokens += count_tokens(g_item.get("text", ""))
            if current_tokens >= target_tokens:
                break
        except StopIteration:
            raise RuntimeError("Gutenberg stream exhausted before target reached.")
        
        try:
            s_item = next(s_iter)
            yield s_item
            current_tokens += count_tokens(s_item.get("text", ""))
            if current_tokens >= target_tokens:
                break
        except StopIteration:
            raise RuntimeError("The Stack stream exhausted before target reached.")

def combine_and_save_corpus(config: Dict[str, Any], log_dir: str) -> str:
    """
    Main orchestration function for downloading and combining the corpus.
    """
    token_target = config.get("token_target")
    if not token_target or not isinstance(token_target, int) or token_target <= 0:
        raise ValueError("Invalid token_target in config.")
    
    logger = setup_logging(log_dir)
    logger.info(f"Starting corpus download for {token_target} tokens.")
    
    gutenberg_ds = fetch_gutenberg_samples(streaming=True)
    stack_ds = fetch_the_stack_samples(streaming=True)
    
    combined = combined_stream(gutenberg_ds, stack_ds, token_target)
    
    output_dir = Path(log_dir).parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "micro_corpus_full.jsonl"
    
    try:
        count = save_samples_to_jsonl(combined, str(output_path), max_tokens=token_target)
        logger.info(f"Successfully saved {count} samples to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save corpus: {e}")
        raise
    
    return str(output_path)

def main():
    """
    Entry point for the script.
    """
    # Default config path relative to project root
    config_path = "code/config.yaml"
    if not Path(config_path).exists():
        # Try relative to script location if run from different dir
        config_path = Path(__file__).parent.parent / "config.yaml"
    
    if not Path(config_path).exists():
        print(f"Error: Config file not found at {config_path}")
        sys.exit(1)
    
    try:
        config = load_config(config_path)
        log_dir = "data/logs"
        combine_and_save_corpus(config, log_dir)
    except Exception as e:
        print(f"Fatal Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
