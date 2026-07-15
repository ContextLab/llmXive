"""
Synthetic data generator for Bloom Filter benchmarks.

Generates log-normal distributed text samples mimicking Enron/Google distributions.
Supports generating specific dataset sizes (10k, 50k, 100k, 500k, 1M) and
prepares query sets (10x dataset size).
"""
import os
import json
import csv
import math
import random
from typing import Tuple, Dict, Any, List, Generator
from scipy import stats
import numpy as np

# Constants for dataset sizes
DATASET_SIZES = [10_000, 50_000, 100_000, 500_000, 1_000_000]
QUERY_MULTIPLIER = 10
MIN_QUERY_COUNT = 10_000

# Log-normal distribution parameters (mimicking word length/complexity)
# mu and sigma for log-normal distribution
LOG_NORMAL_MU = 2.5
LOG_NORMAL_SIGMA = 1.2

# Vocabulary for synthetic text generation
COMMON_WORDS = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "I",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
    "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
    "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
    "system", "project", "data", "result", "analysis", "performance", "benchmark", "filter",
    "memory", "latency", "query", "insert", "set", "element", "bit", "hash",
    "function", "distribution", "log-normal", "synthetic", "corpus", "sample", "random",
    "test", "validation", "verification", "integrity", "consistency", "reproducibility"
]

# Technical terms for domain simulation
TECHNICAL_WORDS = [
    "bloom", "filter", "hash", "bit", "array", "vector", "bitset", "memory",
    "cache", "latency", "throughput", "bandwidth", "algorithm", "complexity", "o1",
    "on", "o2", "log", "n", "constant", "linear", "quadratic", "exponential",
    "polynomial", "recursion", "iteration", "parallel", "concurrent", "async", "sync",
    "buffer", "queue", "stack", "heap", "tree", "graph", "node", "edge",
    "vertex", "path", "cycle", "search", "sort", "merge", "split", "join",
    "index", "key", "value", "map", "dict", "list", "set", "tuple",
    "string", "int", "float", "bool", "null", "none", "true", "false"
]

def _generate_log_normal_length() -> int:
    """Generate a string length following a log-normal distribution."""
    return max(1, int(np.random.lognormal(LOG_NORMAL_MU, LOG_NORMAL_SIGMA)))

def _generate_random_string(length: int) -> str:
    """Generate a random string of specified length using common and technical words."""
    words = []
    current_length = 0
    while current_length < length:
        # Mix common and technical words
        if random.random() < 0.7:
            word = random.choice(COMMON_WORDS)
        else:
            word = random.choice(TECHNICAL_WORDS)
        
        # Add punctuation occasionally
        if random.random() < 0.1:
            word += random.choice([",", ".", "!", "?", ";", ":"])
        
        words.append(word)
        current_length += len(word) + 1  # +1 for space
    
    return " ".join(words)[:length]

def generate_synthetic_corpus(
    n_elements: int,
    seed: int = 42,
    output_path: str = None
) -> List[str]:
    """
    Generate a synthetic corpus of n_elements strings following log-normal distribution.
    
    Args:
        n_elements: Number of elements to generate
        seed: Random seed for reproducibility
        output_path: Optional path to save the generated corpus as CSV
    
    Returns:
        List of generated strings
    """
    np.random.seed(seed)
    random.seed(seed)
    
    corpus = []
    for i in range(n_elements):
        length = _generate_log_normal_length()
        text = _generate_random_string(length)
        corpus.append(text)
        
        # Progress indicator for large datasets
        if (i + 1) % 100000 == 0:
            print(f"Generated {i + 1}/{n_elements} elements")
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'text'])
            for idx, text in enumerate(corpus):
                writer.writerow([idx, text])
        print(f"Corpus saved to {output_path}")
    
    return corpus

def generate_query_set(
    corpus: List[str],
    query_count: int,
    seed: int = 42,
    include_positives: float = 0.5
) -> List[str]:
    """
    Generate a query set for benchmarking.
    
    Args:
        corpus: Source corpus to sample from
        query_count: Number of queries to generate
        seed: Random seed
        include_positives: Fraction of queries that are actual corpus members (0.0-1.0)
    
    Returns:
        List of query strings
    """
    np.random.seed(seed)
    random.seed(seed)
    
    query_set = []
    n_positives = int(query_count * include_positives)
    n_negatives = query_count - n_positives
    
    # Positive queries: sample from corpus
    if n_positives > 0:
        positive_indices = np.random.choice(len(corpus), size=min(n_positives, len(corpus)), replace=False)
        query_set.extend([corpus[i] for i in positive_indices])
    
    # Negative queries: generate new strings not in corpus
    if n_negatives > 0:
        for _ in range(n_negatives):
            length = _generate_log_normal_length()
            # Generate until we get something not in corpus (simple approach)
            while True:
                text = _generate_random_string(length)
                if text not in corpus:
                    query_set.append(text)
                    break
    
    # Shuffle the query set
    random.shuffle(query_set)
    return query_set

def get_config_for_size(n_elements: int) -> Dict[str, Any]:
    """
    Get benchmark configuration for a specific dataset size.
    
    Args:
        n_elements: Target dataset size
    
    Returns:
        Dictionary with dataset_size, query_count, and other config
    """
    if n_elements not in DATASET_SIZES:
        # Find closest supported size
        closest = min(DATASET_SIZES, key=lambda x: abs(x - n_elements))
        print(f"Warning: {n_elements} not in standard sizes, using {closest}")
        n_elements = closest
    
    query_count = max(n_elements * QUERY_MULTIPLIER, MIN_QUERY_COUNT)
    
    return {
        "dataset_size": n_elements,
        "query_count": query_count,
        "repetitions": 5,
        "fpr_targets": [0.01, 0.05, 0.10],
        "implementations": ["array", "vector", "bitset"]
    }

def validate_distribution(corpus: List[str]) -> Dict[str, float]:
    """
    Validate that the generated corpus follows a log-normal distribution.
    
    Args:
        corpus: List of strings to validate
    
    Returns:
        Dictionary with KS-test statistics
    """
    lengths = [len(s) for s in corpus]
    
    # Fit log-normal distribution
    params = stats.lognorm.fit(lengths, floc=0)
    
    # KS-test
    ks_stat, p_value = stats.kstest(lengths, 'lognorm', args=params)
    
    return {
        "ks_statistic": ks_stat,
        "p_value": p_value,
        "is_log_normal": p_value > 0.05,
        "fitted_params": {
            "s": params[0],
            "loc": params[1],
            "scale": params[2]
        }
    }

def main():
    """
    Main entry point for generating benchmark datasets.
    
    Generates datasets for all standard sizes and validates their distributions.
    """
    print("Starting synthetic corpus generation...")
    
    # Ensure output directories exist
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("results/benchmarks", exist_ok=True)
    
    all_configs = []
    
    for size in DATASET_SIZES:
        print(f"\nGenerating dataset for size: {size:,}")
        
        # Generate corpus
        corpus = generate_synthetic_corpus(
            n_elements=size,
            seed=42,
            output_path=f"data/processed/corpus_{size:,}.csv"
        )
        
        # Validate distribution
        validation = validate_distribution(corpus)
        print(f"  Distribution validation: {'PASS' if validation['is_log_normal'] else 'FAIL'} (p={validation['p_value']:.4f})")
        
        # Generate query set
        query_count = max(size * QUERY_MULTIPLIER, MIN_QUERY_COUNT)
        queries = generate_query_set(
            corpus=corpus,
            query_count=query_count,
            seed=42,
            include_positives=0.5
        )
        
        # Save query set
        query_path = f"data/processed/queries_{size:,}.csv"
        with open(query_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'text'])
            for idx, q in enumerate(queries):
                writer.writerow([idx, q])
        
        print(f"  Query set saved: {query_path} ({len(queries):,} queries)")
        
        # Save configuration
        config = get_config_for_size(size)
        config["validation"] = validation
        config["query_file"] = query_path
        config["corpus_file"] = f"data/processed/corpus_{size:,}.csv"
        all_configs.append(config)
        
        # Save config to JSON
        config_path = f"results/benchmarks/config_{size:,}.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"  Config saved: {config_path}")
    
    # Save summary
    summary_path = "results/benchmarks/generation_summary.json"
    with open(summary_path, 'w') as f:
        json.dump({
            "total_sizes": len(all_configs),
            "sizes": DATASET_SIZES,
            "configs": all_configs
        }, f, indent=2)
    print(f"\nGeneration complete. Summary saved to {summary_path}")

if __name__ == "__main__":
    main()