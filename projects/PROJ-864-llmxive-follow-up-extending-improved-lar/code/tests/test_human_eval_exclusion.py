"""
Integration test for HumanEval exclusion in the Micro-Corpus.

This test verifies that the constructed micro-corpus does not contain
any samples that match the HumanEval benchmark dataset.

It performs the following checks:
1. Loads the HumanEval dataset from Hugging Face.
2. Computes a cryptographic fingerprint (SHA-256) for the text of each HumanEval sample.
3. Loads the constructed micro-corpus (data/processed/micro_corpus.jsonl).
4. Computes fingerprints for the corpus samples.
5. Asserts that the intersection of fingerprints is empty.
"""

import json
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Set

# Add parent directory to path for imports if running directly
if "code" not in sys.path:
    code_root = Path(__file__).resolve().parent.parent
    if code_root.name == "code":
        sys.path.insert(0, str(code_root))

from utils.logging import get_logger, info, error
from utils.config import get_processed_dir, get_config, ConfigError

# Initialize logger
logger = get_logger(__name__)

def load_human_eval_samples() -> List[Dict[str, Any]]:
    """
    Loads the HumanEval dataset from Hugging Face.
    Returns a list of dictionaries containing 'prompt' and 'canonical_solution'.
    """
    try:
        from datasets import load_dataset
        logger.info("Loading HumanEval dataset from Hugging Face...")
        dataset = load_dataset("openai_humaneval", split="test")
        samples = []
        for item in dataset:
            samples.append({
                "prompt": item["prompt"],
                "canonical_solution": item["canonical_solution"]
            })
        logger.info(f"Loaded {len(samples)} HumanEval samples.")
        return samples
    except Exception as e:
        logger.error(f"Failed to load HumanEval dataset: {e}")
        raise

def compute_text_fingerprint(text: str) -> str:
    """
    Computes a SHA-256 fingerprint of the text.
    Normalizes whitespace to ensure robust comparison.
    """
    if not isinstance(text, str):
        text = str(text)
    # Normalize whitespace: replace multiple spaces/newlines with a single space
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def load_corpus_samples() -> List[Dict[str, Any]]:
    """
    Loads the micro-corpus from the processed directory.
    Expects data/processed/micro_corpus.jsonl.
    """
    processed_dir = get_processed_dir()
    corpus_path = processed_dir / "micro_corpus.jsonl"

    if not corpus_path.exists():
        raise FileNotFoundError(
            f"Corpus file not found at {corpus_path}. "
            "Please run the data construction pipeline first."
        )

    samples = []
    logger.info(f"Loading corpus samples from {corpus_path}...")
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                # The corpus items typically have a 'text' field
                samples.append(data)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
    
    logger.info(f"Loaded {len(samples)} corpus samples.")
    return samples

def check_exclusion(human_eval_fingerprints: Set[str], corpus_fingerprints: Set[str]) -> bool:
    """
    Checks if there is any overlap between HumanEval and corpus fingerprints.
    Returns True if NO overlap is found (exclusion successful).
    """
    intersection = human_eval_fingerprints.intersection(corpus_fingerprints)
    if intersection:
        logger.error(f"OVERLAP DETECTED: {len(intersection)} samples match HumanEval!")
        logger.error("First 5 matching fingerprints:")
        for fp in list(intersection)[:5]:
            logger.error(f"  - {fp}")
        return False
    return True

def run_test() -> bool:
    """
    Runs the full exclusion test.
    Returns True if the test passes, False otherwise.
    """
    logger.info("Starting HumanEval Exclusion Test (T012)...")

    # 1. Load HumanEval
    try:
        human_eval_samples = load_human_eval_samples()
    except Exception as e:
        logger.error(f"Test failed due to HumanEval loading error: {e}")
        return False

    # 2. Compute HumanEval Fingerprints
    logger.info("Computing HumanEval fingerprints...")
    human_eval_fingerprints = set()
    for sample in human_eval_samples:
        # We check the prompt primarily, as that's the input context
        # We also check the solution to be thorough
        fp_prompt = compute_text_fingerprint(sample["prompt"])
        fp_solution = compute_text_fingerprint(sample["canonical_solution"])
        human_eval_fingerprints.add(fp_prompt)
        human_eval_fingerprints.add(fp_solution)
    
    logger.info(f"Computed {len(human_eval_fingerprints)} unique HumanEval fingerprints.")

    # 3. Load Corpus
    try:
        corpus_samples = load_corpus_samples()
    except FileNotFoundError as e:
        logger.error(f"Test failed: {e}")
        return False

    # 4. Compute Corpus Fingerprints
    logger.info("Computing corpus fingerprints...")
    corpus_fingerprints = set()
    for sample in corpus_samples:
        text = sample.get("text", "")
        if not text:
            continue
        fp = compute_text_fingerprint(text)
        corpus_fingerprints.add(fp)
    
    logger.info(f"Computed {len(corpus_fingerprints)} unique corpus fingerprints.")

    # 5. Check Exclusion
    logger.info("Checking for overlaps...")
    is_excluded = check_exclusion(human_eval_fingerprints, corpus_fingerprints)

    if is_excluded:
        logger.info("SUCCESS: No overlap found between Micro-Corpus and HumanEval.")
        return True
    else:
        logger.error("FAILURE: Overlap detected between Micro-Corpus and HumanEval.")
        return False

def main():
    """Entry point for the test script."""
    success = run_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()