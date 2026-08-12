"""
Integration tests for HumanEval data exclusion from the corpus.

Verifies that no HumanEval benchmark data is present in the training corpus.
"""
import json
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Set

# Ensure imports work
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.logging import get_logger, info, error, warning
from datasets import load_dataset


def load_human_eval_samples() -> List[Dict[str, Any]]:
    """
    Load HumanEval benchmark samples from HuggingFace.
    
    Returns:
        List of HumanEval sample dictionaries
    """
    try:
        dataset = load_dataset("openai_humaneval", split="test")
        samples = []
        for item in dataset:
            samples.append({
                "task_id": item["task_id"],
                "prompt": item["prompt"],
                "canonical_solution": item["canonical_solution"],
                "test": item["test"],
                "entry_point": item["entry_point"]
            })
        return samples
    except Exception as e:
        error(f"Failed to load HumanEval dataset: {e}")
        raise


def compute_text_fingerprint(text: str) -> str:
    """
    Compute a SHA-256 fingerprint of text content.
    
    Args:
        text: Input text string
        
    Returns:
        Hexadecimal SHA-256 hash of the text
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_corpus_samples(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load corpus samples from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file
        
    Returns:
        List of corpus sample dictionaries
    """
    samples = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))
    return samples


def check_exclusion(humaneval_samples: List[Dict], corpus_samples: List[Dict]) -> bool:
    """
    Check that no HumanEval samples are present in the corpus.
    
    Args:
        humaneval_samples: List of HumanEval samples
        corpus_samples: List of corpus samples
        
    Returns:
        True if no overlap detected, False otherwise
    """
    # Create fingerprints for HumanEval prompts
    humaneval_fingerprints = set()
    for sample in humaneval_samples:
        prompt = sample.get("prompt", "")
        if prompt:
          fingerprint = compute_text_fingerprint(prompt.strip())
          humaneval_fingerprints.add(fingerprint)
    
    # Check corpus samples
    for sample in corpus_samples:
        text = sample.get("text", "")
        if text:
            fingerprint = compute_text_fingerprint(text.strip())
            if fingerprint in humaneval_fingerprints:
                error(f"HumanEval sample found in corpus: {sample.get('id', 'unknown')}")
                return False
                
    return True


def run_test(processed_file: Path = None) -> bool:
    """
    Run the HumanEval exclusion test.
    
    Args:
        processed_file: Path to the processed corpus file (optional)
        
    Returns:
        True if test passes, False otherwise
    """
    from utils.config import get_processed_dir
    
    if processed_file is None:
        processed_dir = get_processed_dir()
        processed_file = processed_dir / "micro_corpus_full.jsonl"
        
    if not processed_file.exists():
        error(f"Processed corpus file not found: {processed_file}")
        return False
    
    info("Loading HumanEval samples...")
    humaneval_samples = load_human_eval_samples()
    info(f"Loaded {len(humaneval_samples)} HumanEval samples")
    
    info("Loading corpus samples...")
    corpus_samples = load_corpus_samples(processed_file)
    info(f"Loaded {len(corpus_samples)} corpus samples")
    
    info("Checking for HumanEval exclusion...")
    is_excluded = check_exclusion(humaneval_samples, corpus_samples)
    
    if is_excluded:
        info("✓ HumanEval exclusion test passed: No HumanEval data found in corpus")
    else:
        error("✗ HumanEval exclusion test failed: HumanEval data detected in corpus")
        
    return is_excluded


def main():
    """Main entry point for the test."""
    success = run_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
