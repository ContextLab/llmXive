"""
Integration test for HumanEval exclusion in the Micro-Corpus.

This test verifies that the processed corpus (data/processed/micro_corpus.jsonl)
does not contain any samples that match the HumanEval benchmark suite.
It ensures strict separation between training data and the evaluation benchmark.
"""
import json
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Set
from utils.config import get_config, get_processed_dir, get_artifacts_dir, ConfigError
from utils.logging import get_logger, info, error, warning

# Configure logger
logger = get_logger(__name__)

# Constants
HUMAN_EVAL_DATASET_ID = "openai_humaneval"
# We will load the HumanEval dataset and compute a "fingerprint" of each sample
# to compare against the corpus.

def load_human_eval_samples() -> List[Dict[str, Any]]:
    """
    Loads the HumanEval benchmark dataset from HuggingFace.
    
    Returns:
        List of dictionaries containing 'prompt' and 'canonical_solution'.
    
    Raises:
        RuntimeError: If the dataset cannot be loaded.
    """
    try:
        from datasets import load_dataset
        info(f"Loading HumanEval dataset: {HUMAN_EVAL_DATASET_ID}")
        dataset = load_dataset(HUMAN_EVAL_DATASET_ID, split="test")
        samples = []
        for item in dataset:
            samples.append({
                "prompt": item.get("prompt", ""),
                "task_id": item.get("task_id", ""),
                "canonical_solution": item.get("canonical_solution", "")
            })
        info(f"Loaded {len(samples)} HumanEval samples")
        return samples
    except Exception as e:
        error(f"Failed to load HumanEval dataset: {e}")
        raise RuntimeError(f"Could not load HumanEval benchmark data: {e}")

def compute_text_fingerprint(text: str) -> str:
    """
    Computes a normalized SHA-256 fingerprint of a text string.
    
    Normalization steps:
    1. Strip leading/trailing whitespace.
    2. Normalize line endings (CRLF -> LF).
    3. Collapse multiple spaces into single spaces.
    
    Args:
        text: The input text.
        
    Returns:
        Hex digest of the SHA-256 hash.
    """
    if not text:
        return ""
    
    normalized = text.strip()
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse multiple spaces
    import re
    normalized = re.sub(r' +', ' ', normalized)
    
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def load_corpus_samples(processed_dir: Path) -> List[Dict[str, Any]]:
    """
    Loads the processed micro-corpus from the JSONL file.
    
    Args:
        processed_dir: Path to the processed data directory.
        
    Returns:
        List of corpus items.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is malformed.
    """
    corpus_path = processed_dir / "micro_corpus.jsonl"
    if not corpus_path.exists():
        raise FileNotFoundError(f"Processed corpus not found at {corpus_path}")
    
    samples = []
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                samples.append(item)
            except json.JSONDecodeError as e:
                error(f"JSON decode error at line {line_num}: {e}")
                raise
    
    info(f"Loaded {len(samples)} samples from corpus")
    return samples

def check_exclusion(processed_dir: Path) -> Dict[str, Any]:
    """
    Checks if any HumanEval samples are present in the corpus.
    
    Strategy:
    1. Load HumanEval samples.
    2. Compute fingerprints for all HumanEval prompts.
    3. Load Corpus samples.
    4. Compute fingerprints for corpus prompts (and full text if available).
    5. Compare sets.
    
    Args:
        processed_dir: Path to the processed data directory.
        
    Returns:
        Dictionary with 'passed' (bool), 'matches' (list), and 'details'.
    """
    info("Starting HumanEval exclusion check...")
    
    # 1. Load HumanEval
    human_eval_samples = load_human_eval_samples()
    if not human_eval_samples:
        raise ValueError("HumanEval dataset is empty.")
        
    # 2. Compute HumanEval fingerprints (focusing on prompt)
    he_fingerprints = set()
    for sample in human_eval_samples:
        prompt = sample.get("prompt", "")
        if prompt:
            fp = compute_text_fingerprint(prompt)
            he_fingerprints.add(fp)
    
    info(f"Computed {len(he_fingerprints)} unique HumanEval prompt fingerprints")
    
    # 3. Load Corpus
    try:
        corpus_samples = load_corpus_samples(processed_dir)
    except FileNotFoundError as e:
        error(f"Corpus file missing: {e}")
        return {
            "passed": False,
            "matches": [],
            "details": f"Corpus file missing: {e}",
            "error": str(e)
        }
    
    # 4. Check Corpus against HumanEval fingerprints
    matches = []
    corpus_fingerprints = set()
    
    for idx, item in enumerate(corpus_samples):
        # Determine text to check. Usually 'text' or 'content' or 'prompt'.
        # Based on typical data-models, we check 'text'.
        text_candidates = []
        if "text" in item:
            text_candidates.append(item["text"])
        if "content" in item:
            text_candidates.append(item["content"])
        if "prompt" in item:
            text_candidates.append(item["prompt"])
        
        # Check each candidate text
        for text in text_candidates:
            if not text:
                continue
            fp = compute_text_fingerprint(text)
            corpus_fingerprints.add(fp)
            
            if fp in he_fingerprints:
                matches.append({
                    "corpus_index": idx,
                    "task_id": item.get("task_id", "unknown"),
                    "matched_type": "prompt",
                    "fingerprint": fp
                })
                # Log but don't break immediately to find all matches
                warning(f"Found match at corpus index {idx}: {item.get('task_id', 'unknown')}")
    
    passed = len(matches) == 0
    
    result = {
        "passed": passed,
        "matches": matches,
        "total_corpus_samples": len(corpus_samples),
        "total_human_eval_samples": len(human_eval_samples),
        "details": "Exclusion check passed." if passed else f"Found {len(matches)} overlapping samples."
    }
    
    return result

def run_test():
    """
    Entry point for the integration test.
    Returns 0 if passed, 1 if failed or error.
    """
    try:
        config = get_config()
        processed_dir = get_processed_dir()
        
        info(f"Checking exclusion in: {processed_dir}")
        
        result = check_exclusion(processed_dir)
        
        if result.get("error"):
            error(f"Test failed with error: {result['error']}")
            return 1
        
        if result["passed"]:
            info("SUCCESS: No HumanEval samples found in the corpus.")
            return 0
        else:
            error(f"FAILURE: {result['details']}")
            # Log first few matches for debugging
            if result["matches"]:
                for m in result["matches"][:5]:
                    error(f"  Match: Index={m['corpus_index']}, TaskID={m['task_id']}")
            return 1
            
    except ConfigError as e:
        error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        error(f"Unexpected error during test: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """
    Main entry point for the script.
    """
    sys.exit(run_test())

if __name__ == "__main__":
    main()