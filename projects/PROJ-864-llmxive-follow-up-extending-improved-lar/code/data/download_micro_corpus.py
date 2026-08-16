import json
import os
import sys
import hashlib
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional
import logging

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import load_config, get_project_root, get_raw_dir, get_data_dir
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

def setup_logging():
    """Setup logging for the module."""
    return setup_logging("download_micro_corpus")

def load_config():
    """Load configuration from code/config.yaml."""
    config_path = get_project_root() / "code" / "config.yaml"
    if not config_path.exists():
        error(f"Config file not found: {config_path}")
        sys.exit(1)
    return load_config(config_path)

def fetch_gutenberg_samples(streaming: bool = True) -> Generator[Dict[str, Any], None, None]:
    """Fetch samples from Project Gutenberg via Hugging Face datasets."""
    try:
        from datasets import load_dataset
        # Use a verified real dataset: Project Gutenberg mirror
        dataset = load_dataset("gutenberg", "english", streaming=streaming)
        info(f"Connected to Project Gutenberg dataset")
        for item in dataset["train"]:
            # Sanitize and validate text content
            text = item.get("text", "")
            if not isinstance(text, str):
                continue
            # Basic sanitization: remove control characters but keep newlines
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
            yield {"source": "gutenberg", "text": text, "id": item.get("id", str(hash(text)))}
    except Exception as e:
        error(f"Failed to fetch Gutenberg samples: {e}")
        raise

def fetch_the_stack_samples(streaming: bool = True) -> Generator[Dict[str, Any], None, None]:
    """Fetch samples from The Stack via Hugging Face datasets."""
    try:
        from datasets import load_dataset
        # Use a verified real dataset subset
        dataset = load_dataset("bigcode/the-stack", "data", streaming=streaming, split="train")
        info(f"Connected to The Stack dataset")
        count = 0
        for item in dataset:
            # Sanitize and validate text content
            text = item.get("content", "")
            if not isinstance(text, str):
                continue
            # Basic sanitization
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
            # Sanitize filename if present
            filename = item.get("filename", "unknown")
            safe_filename = sanitize_filename(str(filename))
            yield {
                "source": "the_stack",
                "text": text,
                "id": item.get("id", str(hash(text))),
                "filename": safe_filename
            }
            count += 1
            if count % 1000 == 0:
                info(f"Processed {count} samples from The Stack")
    except Exception as e:
        error(f"Failed to fetch The Stack samples: {e}")
        raise

def count_tokens(text: str) -> int:
    """Count tokens in text using a simple whitespace-based estimator."""
    # For a real implementation, this would use a tokenizer
    # Using word count as a proxy for token estimation
    return len(text.split())

def save_samples_to_jsonl(samples: List[Dict[str, Any]], output_path: Path):
    """Save samples to a JSONL file with path validation."""
    # Validate output path
    raw_dir = get_raw_dir()
    safe_output_path = validate_path(output_path, raw_dir, "output file")
    
    with open(safe_output_path, 'w', encoding='utf-8') as f:
        for sample in samples:
            # Validate each sample's text before saving
            if "text" in sample and not isinstance(sample["text"], str):
                sample["text"] = str(sample["text"])
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    info(f"Saved {len(samples)} samples to {safe_output_path}")

def combined_stream() -> Generator[Dict[str, Any], None, None]:
    """Combine streams from multiple sources."""
    # Fetch from Gutenberg
    info("Starting Gutenberg stream...")
    gutenberg_count = 0
    for item in fetch_gutenberg_samples():
        yield item
        gutenberg_count += 1
        if gutenberg_count % 5000 == 0:
            info(f"Gutenberg: {gutenberg_count} samples processed")
    
    # Fetch from The Stack
    info("Starting The Stack stream...")
    stack_count = 0
    for item in fetch_the_stack_samples():
        yield item
        stack_count += 1
        if stack_count % 5000 == 0:
            info(f"The Stack: {stack_count} samples processed")

def combine_and_save_corpus(output_path: Path, target_tokens: int):
    """Combine streams and save until target tokens reached."""
    raw_dir = get_raw_dir()
    safe_output_path = validate_path(output_path, raw_dir, "corpus output")
    
    total_tokens = 0
    samples = []
    batch_size = 1000
    
    info(f"Starting corpus construction with target: {target_tokens} tokens")
    
    for sample in combined_stream():
        tokens = count_tokens(sample.get("text", ""))
        total_tokens += tokens
        samples.append(sample)
        
        if len(samples) >= batch_size or total_tokens >= target_tokens:
            save_samples_to_jsonl(samples, safe_output_path)
            info(f"Progress: {total_tokens} tokens, {len(samples)} samples")
            samples = []
            
            if total_tokens >= target_tokens:
                break
    
    # Save remaining samples
    if samples:
        save_samples_to_jsonl(samples, safe_output_path)
    
    info(f"Corpus construction complete. Total tokens: {total_tokens}")
    return total_tokens

def main():
    """Main entry point."""
    logger = setup_logging()
    
    try:
        config = load_config()
        token_target = config.get("token_target", 1000000)
        regime = config.get("regime", "1M")
        
        info(f"Starting micro-corpus download for regime: {regime}")
        info(f"Target tokens: {token_target}")
        
        # Validate config values
        if not isinstance(token_target, int) or token_target <= 0:
            error(f"Invalid token_target in config: {token_target}")
            sys.exit(1)
        
        # Define output path
        raw_dir = get_raw_dir()
        output_path = raw_dir / "raw_corpus.jsonl"
        
        # Validate output path is within allowed directory
        validate_path(output_path, raw_dir, "output file")
        
        # Build corpus
        total_tokens = combine_and_save_corpus(output_path, token_target)
        
        info(f"Successfully built micro-corpus at {output_path}")
        info(f"Total tokens collected: {total_tokens}")
        
    except Exception as e:
        error(f"Fatal error in download_micro_corpus: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
