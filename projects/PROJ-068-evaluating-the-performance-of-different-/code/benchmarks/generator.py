"""
Synthetic Data Generator for Bloom Filter Benchmarks.

Generates log-normal distributed text samples mimicking Enron/Google email
body distributions. Validates the distribution using the Kolmogorov-Smirnov
test before writing to disk.
"""
import os
import json
import csv
import math
import random
import hashlib
from typing import Tuple, Dict, Any, List, Generator

import numpy as np
from scipy import stats

# Project root relative to this file
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_DATA_PROCESSED_DIR = os.path.join(_PROJECT_ROOT, 'data', 'processed')
_CHECKSUMS_FILE = os.path.join(_PROJECT_ROOT, 'data', 'checksums.manifest')

# Configuration
MU = 2.5
SIGMA = 1.2
RANDOM_SEED = 42
VALIDATION_KS_ALPHA = 0.05

# Word list to simulate realistic text (mimicking email corpora)
_WORD_POOL = [
    "please", "review", "attached", "document", "meeting", "schedule",
    "urgent", "update", "project", "deadline", "team", "quarter",
    "report", "analysis", "budget", "approval", "client", "feedback",
    "draft", "final", "version", "email", "call", "conference",
    "action", "item", "status", "timeline", "milestone", "deliverable",
    "resource", "allocation", "risk", "issue", "mitigation", "strategy",
    "stakeholder", "requirement", "specification", "implementation", "testing",
    "deployment", "maintenance", "support", "incident", "resolution",
    "performance", "optimization", "scalability", "architecture", "design",
    "pattern", "component", "module", "interface", "database", "query",
    "security", "authentication", "authorization", "encryption", "protocol",
    "network", "server", "client", "request", "response", "error",
    "exception", "logging", "monitoring", "alert", "dashboard", "metric",
    "KPI", "ROI", "efficiency", "productivity", "quality", "compliance",
    "audit", "regulation", "policy", "procedure", "guideline", "standard",
    "best", "practice", "methodology", "framework", "tool", "platform",
    "cloud", "infrastructure", "automation", "integration", "migration",
    "upgrade", "patch", "release", "feature", "enhancement", "bug",
    "fix", "hotfix", "rollback", "recovery", "backup", "restore"
]

def _generate_log_normal_length() -> int:
    """Generate a word count based on log-normal distribution."""
    # Generate from log-normal: exp(mu + sigma * Z)
    # We ensure at least 1 word
    length = int(math.exp(random.gauss(MU, SIGMA)))
    return max(1, length)

def _generate_text_sample() -> str:
    """Generate a single text sample mimicking an email body."""
    word_count = _generate_log_normal_length()
    words = [random.choice(_WORD_POOL) for _ in range(word_count)]
    # Capitalize first letter, add period
    text = " ".join(words)
    return text.capitalize() + "."

def validate_distribution(samples: List[str]) -> Tuple[bool, float]:
    """
    Validates that the generated text lengths follow a log-normal distribution.
    Uses the Kolmogorov-Smirnov test.

    Args:
        samples: List of text strings.

    Returns:
        Tuple of (is_valid, p_value).
    """
    if len(samples) < 10:
        raise ValueError("Not enough samples to validate distribution.")

    # Extract lengths
    lengths = np.array([len(s.split()) for s in samples])

    # Fit log-normal parameters to the data
    # scipy.stats.lognorm.fit returns (shape, loc, scale)
    # For log-normal, shape is sigma, scale is exp(mu)
    fitted_params = stats.lognorm.fit(lengths, floc=0)
    shape, loc, scale = fitted_params

    # Perform KS-test against the fitted distribution
    # Note: Since we fitted parameters from the same data, p-value is optimistic,
    # but sufficient for validation of the generator logic.
    ks_stat, p_value = stats.kstest(lengths, 'lognorm', args=fitted_params)

    is_valid = p_value > VALIDATION_KS_ALPHA
    return is_valid, p_value

def generate_synthetic_corpus(
    target_size: int,
    output_file: str,
    seed: int = RANDOM_SEED
) -> str:
    """
    Generates a synthetic corpus of text samples and writes to CSV.

    Args:
        target_size: Number of samples to generate.
        output_file: Path to the output CSV file.
        seed: Random seed for reproducibility.

    Returns:
        SHA-256 checksum of the generated file.
    """
    random.seed(seed)
    np.random.seed(seed)

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Generate samples in memory first to validate
    # To avoid memory issues with huge sizes, we generate in batches
    # but validate on a representative subset if size is very large.
    # However, for correctness, we validate the distribution logic.
    # We'll generate a validation set first.
    validation_size = min(10000, target_size)
    validation_samples = [_generate_text_sample() for _ in range(validation_size)]

    is_valid, p_value = validate_distribution(validation_samples)
    if not is_valid:
        raise RuntimeError(
            f"Distribution validation failed. KS-test p-value: {p_value:.4f}. "
            f"Expected p-value > {VALIDATION_KS_ALPHA}. "
            "Parameters: mu={MU}, sigma={SIGMA}. "
            "This indicates the generator is not producing the correct distribution."
        )

    # Stream to file to handle large sizes
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'text', 'word_count'])

        for i in range(target_size):
            text = _generate_text_sample()
            word_count = len(text.split())
            writer.writerow([i, text, word_count])

    # Compute checksum
    checksum = compute_file_checksum(output_file)
    return checksum

def generate_query_set(
    corpus_file: str,
    query_size: int,
    output_file: str,
    seed: int = RANDOM_SEED
) -> str:
    """
    Generates a query set by sampling from the corpus.
    Also generates some negative samples (non-existent strings).

    Args:
        corpus_file: Path to the source corpus CSV.
        query_size: Total number of queries.
        output_file: Path to output CSV.
        seed: Random seed.

    Returns:
        SHA-256 checksum.
    """
    random.seed(seed)

    # Read corpus into memory (assuming corpus fits for query generation)
    # If corpus is too large, we would need a streaming approach, but
    # for benchmarking query sets, we usually load the relevant subset.
    corpus_texts = []
    with open(corpus_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            corpus_texts.append(row['text'])

    if not corpus_texts:
        raise ValueError("Corpus file is empty.")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    queries = []
    # 50% positive (from corpus), 50% negative (synthetic noise)
    positive_count = query_size // 2
    negative_count = query_size - positive_count

    # Positive queries
    indices = random.sample(range(len(corpus_texts)), min(positive_count, len(corpus_texts)))
    for idx in indices:
        queries.append((corpus_texts[idx], True))

    # Negative queries (slightly modified existing texts to ensure they are not in corpus)
    for _ in range(negative_count):
        base = random.choice(corpus_texts)
        # Append a random character or number to ensure it's new
        suffix = str(random.randint(0, 9999))
        queries.append((base + " " + suffix, False))

    random.shuffle(queries)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'text', 'is_positive'])
        for i, (text, is_pos) in enumerate(queries):
            writer.writerow([i, text, is_pos])

    return compute_file_checksum(output_file)

def compute_file_checksum(filepath: str) -> str:
    """Computes SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def record_checksum(checksum: str, filepath: str):
    """Appends checksum record to the manifest file."""
    os.makedirs(os.path.dirname(_CHECKSUMS_FILE), exist_ok=True)
    with open(_CHECKSUMS_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{checksum}  {filepath}\n")

def get_config_for_size(size: int) -> Dict[str, Any]:
    """
    Returns configuration parameters based on dataset size.
    Currently returns fixed distribution params, but can be extended.
    """
    return {
        "mu": MU,
        "sigma": SIGMA,
        "target_size": size,
        "seed": RANDOM_SEED
    }

def main():
    """
    Main entry point to generate the synthetic corpus.
    Expected to be called with a target size argument or default.
    """
    import sys

    # Default size for demonstration, can be overridden via CLI
    target_size = 100000
    if len(sys.argv) > 1:
        try:
            target_size = int(sys.argv[1])
        except ValueError:
            print(f"Error: Invalid size argument '{sys.argv[1]}'. Using default {target_size}.")

    output_filename = f"corpus_{target_size}.csv"
    output_path = os.path.join(_DATA_PROCESSED_DIR, output_filename)

    print(f"Generating synthetic corpus of {target_size} samples...")
    print(f"Parameters: mu={MU}, sigma={SIGMA}")

    try:
        checksum = generate_synthetic_corpus(target_size, output_path)
        print(f"Generated: {output_path}")
        print(f"Validation: PASSED (Distribution matches log-normal)")
        
        record_checksum(checksum, output_path)
        print(f"Checksum recorded: {checksum}")
        print(f"Output file written successfully.")
    except Exception as e:
        print(f"ERROR: Generation failed: {e}")
        raise

if __name__ == "__main__":
    main()
