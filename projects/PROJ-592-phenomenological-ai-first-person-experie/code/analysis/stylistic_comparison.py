"""
Stylistic Comparison Module (Task T035)

Implements a comparative analysis to test the "phenomenological style" hypothesis
by comparing generated phenomenological reports against a baseline of "ordinary
conversation" (using the IMDB dataset as a proxy for non-phenomenological text).

Metrics computed:
1. Marker Density: Ratio of phenomenological markers (sensory, temporal, intentional)
   to total tokens.
2. Structural Coherence: Average sentence length variance and sentence count per
   report (proxy for narrative structure).

Output: data/processed/stylistic_comparison.csv
"""
import os
import json
import logging
import re
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from datasets import load_dataset

# Import shared utilities and config
from utils.logging import get_logger, setup_logging
from utils.io import safe_write_csv, load_json, ensure_dir
from config import get_marker_keywords

logger = get_logger(__name__)

# --- Constants ---
DATASET_NAME = "imdb"
SAMPLE_SIZE_BASELINE = 200  # Number of IMDB reviews to sample for baseline
PHENOMENAL_DATA_PATH = "data/raw/generation_corpus.json"
OUTPUT_PATH = "data/processed/stylistic_comparison.csv"
OUTPUT_DIR = "data/processed"

# --- Helper Functions ---

def load_baseline_dataset(n_samples: int) -> List[str]:
    """
    Loads a subset of the IMDB dataset to serve as the 'ordinary conversation'
    or non-phenomenological baseline.
    """
    logger.info(f"Loading baseline dataset: {DATASET_NAME} (n={n_samples})")
    try:
        dataset = load_dataset(DATASET_NAME, split="train", trust_remote_code=True)
        # Shuffle and sample
        sampled_indices = np.random.choice(len(dataset), size=min(n_samples, len(dataset)), replace=False)
        texts = [dataset[int(i)]["text"] for i in sampled_indices]
        # Clean text (IMDB text often contains HTML tags)
        cleaned_texts = [re.sub(r'<br\s*/?>', ' ', text) for text in texts]
        cleaned_texts = [re.sub(r'<[^>]+>', '', text) for text in cleaned_texts]
        logger.info(f"Loaded and cleaned {len(cleaned_texts)} baseline samples.")
        return cleaned_texts
    except Exception as e:
        logger.error(f"Failed to load baseline dataset: {e}")
        raise RuntimeError(f"Could not load {DATASET_NAME} dataset. Ensure 'datasets' is installed.") from e

def load_phenomenological_reports() -> List[Dict[str, Any]]:
    """
    Loads the generated phenomenological reports from the raw generation corpus.
    """
    logger.info(f"Loading phenomenological reports from {PHENOMENAL_DATA_PATH}")
    try:
        data = load_json(Path(PHENOMENAL_DATA_PATH))
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "samples" in data:
            return data["samples"]
        else:
            logger.warning("Unexpected format in generation corpus. Attempting to treat as list.")
            return [data] if data else []
    except FileNotFoundError:
        logger.error(f"Phenomenological data file not found: {PHENOMENAL_DATA_PATH}")
        raise
    except Exception as e:
        logger.error(f"Error loading phenomenological reports: {e}")
        raise

def count_markers(text: str, markers: Dict[str, List[str]]) -> int:
    """
    Counts the total number of phenomenological markers in a text.
    """
    count = 0
    text_lower = text.lower()
    for category, words in markers.items():
        for word in words:
            # Simple word boundary check to avoid partial matches
            pattern = r'\b' + re.escape(word.lower()) + r'\b'
            count += len(re.findall(pattern, text_lower))
    return count

def compute_marker_density(text: str, markers: Dict[str, List[str]]) -> float:
    """
    Computes the ratio of markers to total words.
    """
    words = text.split()
    total_words = len(words)
    if total_words == 0:
        return 0.0
    marker_count = count_markers(text, markers)
    return marker_count / total_words

def compute_structural_coherence(text: str) -> Dict[str, float]:
    """
    Computes structural metrics:
    - avg_sentence_length: Mean words per sentence
    - sentence_count: Total sentences
    - length_variance: Variance in sentence lengths (proxy for structural variety)
    """
    # Split by punctuation
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return {
            "avg_sentence_length": 0.0,
            "sentence_count": 0.0,
            "length_variance": 0.0
        }

    lengths = [len(s.split()) for s in sentences]
    avg_len = np.mean(lengths)
    variance = np.var(lengths)

    return {
        "avg_sentence_length": float(avg_len),
        "sentence_count": float(len(sentences)),
        "length_variance": float(variance)
    }

def analyze_corpus(
    texts: List[str],
    source_label: str,
    markers: Dict[str, List[str]]
) -> List[Dict[str, Any]]:
    """
    Analyzes a list of texts for marker density and structural coherence.
    """
    results = []
    for i, text in enumerate(texts):
        if not text or not isinstance(text, str):
            continue

        density = compute_marker_density(text, markers)
        structure = compute_structural_coherence(text)

        results.append({
            "source": source_label,
            "sample_id": i,
            "marker_density": density,
            "avg_sentence_length": structure["avg_sentence_length"],
            "sentence_count": structure["sentence_count"],
            "length_variance": structure["length_variance"]
        })
    return results

def run_stylistic_comparison(
    phen_text: Optional[List[str]] = None,
    baseline_text: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Orchestrates the full stylistic comparison pipeline.
    """
    logger.info("Starting Stylistic Comparison Analysis (Task T035)")

    # 1. Load Data
    markers = get_marker_keywords()

    # Load Phenomenological Reports
    if phen_text is None:
        reports = load_phenomenological_reports()
        phen_texts = [r.get("text", "") for r in reports if "text" in r]
    else:
        phen_texts = phen_text

    if not phen_texts:
        raise ValueError("No phenomenological texts found to analyze.")
    logger.info(f"Found {len(phen_texts)} phenomenological samples.")

    # Load Baseline
    if baseline_text is None:
        baseline_texts = load_baseline_dataset(SAMPLE_SIZE_BASELINE)
    else:
        baseline_texts = baseline_text

    if not baseline_texts:
        raise ValueError("No baseline texts found to analyze.")
    logger.info(f"Found {len(baseline_texts)} baseline samples.")

    # 2. Analyze
    phen_results = analyze_corpus(phen_texts, "phenomenological", markers)
    baseline_results = analyze_corpus(baseline_texts, "ordinary", markers)

    all_results = phen_results + baseline_results

    # 3. Compute Aggregate Statistics
    phen_df = [r for r in all_results if r["source"] == "phenomenological"]
    base_df = [r for r in all_results if r["source"] == "ordinary"]

    stats = {
        "phenomenological": {
            "count": len(phen_df),
            "avg_marker_density": float(np.mean([r["marker_density"] for r in phen_df])),
            "std_marker_density": float(np.std([r["marker_density"] for r in phen_df])),
            "avg_sentence_length": float(np.mean([r["avg_sentence_length"] for r in phen_df])),
            "avg_length_variance": float(np.mean([r["length_variance"] for r in phen_df]))
        },
        "ordinary": {
            "count": len(base_df),
            "avg_marker_density": float(np.mean([r["marker_density"] for r in base_df])),
            "std_marker_density": float(np.std([r["marker_density"] for r in base_df])),
            "avg_sentence_length": float(np.mean([r["avg_sentence_length"] for r in base_df])),
            "avg_length_variance": float(np.mean([r["length_variance"] for r in base_df]))
        }
    }

    # 4. Write Output
    ensure_dir(Path(OUTPUT_PATH))
    safe_write_csv(Path(OUTPUT_PATH), all_results)
    logger.info(f"Individual sample results written to {OUTPUT_PATH}")

    # Write summary stats to a JSON file for easy reading
    stats_path = Path(OUTPUT_DIR) / "stylistic_comparison_summary.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Aggregate statistics written to {stats_path}")

    # 5. Log Key Findings (Review-DavidKrakauer context)
    phen_density = stats["phenomenological"]["avg_marker_density"]
    base_density = stats["ordinary"]["avg_marker_density"]
    logger.info(f"Phenomenological Avg Marker Density: {phen_density:.4f}")
    logger.info(f"Ordinary Avg Marker Density: {base_density:.4f}")
    logger.info(f"Difference: {phen_density - base_density:.4f}")

    return {
        "status": "success",
        "summary": stats,
        "output_file": str(Path(OUTPUT_PATH).resolve())
    }

def main():
    """Entry point for CLI execution."""
    setup_logging()
    try:
        result = run_stylistic_comparison()
        logger.info("Stylistic Comparison completed successfully.")
        print(json.dumps(result["summary"], indent=2))
    except Exception as e:
        logger.critical(f"Stylistic Comparison failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
