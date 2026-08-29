"""
Semantic analysis module for LLM-based code smell detection.

This module handles:
1. Loading semantic embeddings models (sentence-transformers)
2. Loading quantized LLM models (llama-cpp-python)
3. Computing embeddings for code functions
4. Running LLM inference with standardized prompts
5. Parsing and validating LLM outputs
6. Resource monitoring integration for batch processing
"""
import os
import json
import logging
import gc
import time
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
from llama_cpp import Llama

from config import get_processed_path, get_results_path, setup_logging
from monitoring import (
    capture_snapshot,
    track_inference_time,
    record_batch_metrics,
    save_metrics_to_file,
    get_ram_usage_mb,
    get_cpu_utilization
)

# Configure logging
logger = setup_logging(__name__)

# Constants
BATCH_SIZE = 10
MAX_CONTEXT_TOKENS = 4096  # CodeLlama-7B context window
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
LLAMA_MODEL_PATH = "models/CodeLlama-7B-Instruct-GGUF/q4_k_m.gguf"
OUTPUT_EMBEDDINGS_PATH = "data/processed/semantic_results.json"
OUTPUT_METRICS_PATH = "results/resource_metrics.json"


def load_embeddings_model(model_name: str = EMBEDDING_MODEL_NAME) -> SentenceTransformer:
    """
    Load the sentence-transformers model for computing embeddings.

    Args:
        model_name: Name of the model to load from HuggingFace Hub.

    Returns:
        SentenceTransformer: Loaded embedding model.
    """
    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    logger.info(f"Embedding model loaded successfully: {model_name}")
    return model


def load_llama_model(model_path: str = LLAMA_MODEL_PATH, n_ctx: int = MAX_CONTEXT_TOKENS) -> Llama:
    """
    Load the quantized CodeLlama model using llama-cpp-python.

    Args:
        model_path: Path to the GGUF model file.
        n_ctx: Context window size in tokens.

    Returns:
        Llama: Loaded LLM instance.
    """
    logger.info(f"Loading LLM model from: {model_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"LLM model file not found at: {model_path}")

    model = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=4,
        n_batch=512,
        verbose=False
    )
    logger.info("LLM model loaded successfully")
    return model


def load_baseline_data(baseline_path: str = "data/static_baseline.csv") -> List[Dict[str, Any]]:
    """
    Load the static baseline CSV containing code functions and metrics.

    Args:
        baseline_path: Path to the static baseline CSV file.

    Returns:
        List of dictionaries, each representing a function with its code and metrics.
    """
    import pandas as pd

    logger.info(f"Loading baseline data from: {baseline_path}")
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline file not found at: {baseline_path}")

    df = pd.read_csv(baseline_path)
    data = df.to_dict(orient='records')
    logger.info(f"Loaded {len(data)} functions from baseline")
    return data


def compute_embeddings(model: SentenceTransformer, code_texts: List[str]) -> List[List[float]]:
    """
    Compute semantic embeddings for a list of code texts.

    Args:
        model: The loaded SentenceTransformer model.
        code_texts: List of code strings to embed.

    Returns:
        List of embedding vectors (each as a list of floats).
    """
    logger.info(f"Computing embeddings for {len(code_texts)} functions")
    embeddings = model.encode(code_texts, convert_to_numpy=True, show_progress_bar=True)
    return embeddings.tolist()


def check_context_window(text: str, max_tokens: int = MAX_CONTEXT_TOKENS) -> bool:
    """
    Check if text fits within the model's context window.

    Args:
        text: The text to check.
        max_tokens: Maximum allowed tokens.

    Returns:
        bool: True if text fits, False otherwise.
    """
    # Rough estimate: 1 token ≈ 4 characters for code
    estimated_tokens = len(text) // 4
    return estimated_tokens <= max_tokens


def truncate_text(text: str, max_tokens: int = MAX_CONTEXT_TOKENS) -> str:
    """
    Truncate text to fit within the context window.

    Args:
        text: The text to truncate.
        max_tokens: Maximum allowed tokens.

    Returns:
        Truncated text string.
    """
    # Rough estimate: 1 token ≈ 4 characters
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def run_llm_inference(
    model: Llama,
    code_text: str,
    temperature: float = 0.1,
    max_tokens: int = 512
) -> str:
    """
    Run LLM inference on a single code snippet.

    Args:
        model: The loaded Llama model.
        code_text: The code snippet to analyze.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens to generate.

    Returns:
        str: The raw LLM response.
    """
    prompt = (
        "You are a code quality expert. Analyze the following Python code for code smells. "
        "Return your answer as a JSON list of smell categories. "
        "Available smell categories: LongMethod, LargeClass, DuplicateCode, LongParameterList, "
        "FeatureEnvy, DataClass, GodClass, ShotgunSurgery, DivergentChange, ParallelInheritance. "
        "If no smells are detected, return an empty list [].\n\n"
        f"Code:\n{code_text}\n\n"
        "Smells (JSON list):"
    )

    response = model(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        stop=["\n\n", "```"],
        echo=False,
        verbose=False
    )

    return response['choices'][0]['text'].strip()


def parse_llm_output(raw_output: str) -> List[str]:
    """
    Parse the LLM's raw output into a list of smell categories.

    Args:
        raw_output: Raw string output from the LLM.

    Returns:
        List of smell category strings, or empty list if parsing fails.
    """
    valid_smells = [
        "LongMethod", "LargeClass", "DuplicateCode", "LongParameterList",
        "FeatureEnvy", "DataClass", "GodClass", "ShotgunSurgery",
        "DivergentChange", "ParallelInheritance"
    ]

    try:
        # Try to extract JSON from the output
        import re
        json_match = re.search(r'\[.*\]', raw_output, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            smells = json.loads(json_str)
            if isinstance(smells, list):
                # Filter to only valid smells
                return [s for s in smells if s in valid_smells]
    except (json.JSONDecodeError, AttributeError):
        logger.warning(f"Failed to parse LLM output: {raw_output[:200]}")
        return []

    return []


def run_semantic_analysis(
    baseline_path: str = "data/static_baseline.csv",
    output_path: str = OUTPUT_EMBEDDINGS_PATH,
    metrics_path: str = OUTPUT_METRICS_PATH,
    batch_size: int = BATCH_SIZE
) -> Dict[str, Any]:
    """
    Run the full semantic analysis pipeline with resource monitoring.

    This function:
    1. Loads the baseline data
    2. Computes embeddings for all functions
    3. Runs LLM inference in batches with monitoring
    4. Saves results and resource metrics

    Args:
        baseline_path: Path to the static baseline CSV.
        output_path: Path to save semantic results.
        metrics_path: Path to save resource metrics.
        batch_size: Number of functions to process per batch.

    Returns:
        Dictionary containing summary statistics.
    """
    logger.info("Starting semantic analysis pipeline")

    # Load models
    embedding_model = load_embeddings_model()
    llama_model = load_llama_model()

    # Load data
    baseline_data = load_baseline_data(baseline_path)
    total_functions = len(baseline_data)
    logger.info(f"Processing {total_functions} functions in batches of {batch_size}")

    # Prepare results storage
    all_results = []
    all_metrics = []
    skipped_count = 0
    unparseable_count = 0

    # Process in batches
    for batch_start in range(0, total_functions, batch_size):
        batch_end = min(batch_start + batch_size, total_functions)
        batch_id = batch_start // batch_size
        batch_data = baseline_data[batch_start:batch_end]

        logger.info(f"Processing batch {batch_id} (functions {batch_start} to {batch_end-1})")

        # Capture metrics for this batch
        with track_inference_time() as batch_metrics:
            batch_results = []

            for idx, item in enumerate(batch_data):
                code = item.get('code', '')
                if not code:
                    continue

                # Check context window
                if not check_context_window(code):
                    logger.warning(f"Function at index {batch_start + idx} exceeds context window, skipping")
                    skipped_count += 1
                    continue

                # Truncate if necessary
                truncated_code = truncate_text(code)

                # Compute embedding
                embedding = compute_embeddings(embedding_model, [truncated_code])[0]

                # Run LLM inference
                try:
                    raw_output = run_llm_inference(llama_model, truncated_code)
                    smells = parse_llm_output(raw_output)
                    if not smells:
                        unparseable_count += 1
                except Exception as e:
                    logger.error(f"Error during LLM inference: {e}")
                    smells = []
                    unparseable_count += 1

                result_item = {
                    'function_id': item.get('function_id', f"{batch_start + idx}"),
                    'code': truncated_code,
                    'embedding': embedding,
                    'llm_smells': smells,
                    'static_smells': item.get('static_smell_labels', []),
                    'radon_metrics': {
                        'loc': item.get('loc', 0),
                        'cyclomatic_complexity': item.get('cyclomatic_complexity', 0)
                    }
                }
                batch_results.append(result_item)

            # Record batch metrics
            batch_metrics['batch_id'] = batch_id
            batch_metrics['functions_processed'] = len(batch_results)
            batch_metrics['functions_skipped'] = skipped_count
            all_metrics.append(record_batch_metrics(batch_id, batch_metrics))

            all_results.extend(batch_results)

            # Force garbage collection between batches
            gc.collect()

        logger.info(f"Batch {batch_id} completed. Processed: {len(batch_results)}, Skipped: {skipped_count}")

    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    logger.info(f"Saved semantic results to {output_path}")

    # Save metrics
    save_metrics_to_file(all_metrics, metrics_path)
    logger.info(f"Saved resource metrics to {metrics_path}")

    summary = {
        'total_functions': total_functions,
        'processed': len(all_results),
        'skipped_context_window': skipped_count,
        'unparseable_outputs': unparseable_count,
        'batches_processed': len(all_metrics),
        'output_path': output_path,
        'metrics_path': metrics_path
    }

    logger.info(f"Semantic analysis completed. Summary: {summary}")
    return summary


def main():
    """Main entry point for semantic analysis."""
    setup_logging()
    run_semantic_analysis()


if __name__ == "__main__":
    main()
