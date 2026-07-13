"""
Pilot evaluation script for User Story 1 (T018a).
Runs the text-only pipeline on a small subset (10%) of the held-out test set
to measure per-query runtime and verify system stability before full execution.
"""
import os
import json
import time
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports
from main import load_test_set
from retriever import TextRetriever, load_processed_data
from reasoning import load_phi3_model, build_prompt, generate_response, parse_model_response
from config import get_config_dict
from logging_utils import setup_query_logger, get_memory_usage_mb, profile_and_log_query

# Configure logging
logger = setup_query_logger("pilot_eval")

def run_pilot_evaluation(
    test_set: List[Dict[str, Any]],
    retriever: TextRetriever,
    model,
    tokenizer,
    subset_fraction: float = 0.1,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run the pipeline on a subset of the test set to measure runtime.

    Args:
        test_set: Full list of test queries.
        retriever: Initialized TextRetriever.
        model: Loaded Phi-3 model.
        tokenizer: Loaded Phi-3 tokenizer.
        subset_fraction: Fraction of data to process (default 10%).
        seed: Random seed for reproducibility.

    Returns:
        Dictionary containing pilot results (timings, memory, subset stats).
    """
    random.seed(seed)
    total_queries = len(test_set)
    pilot_size = max(1, int(total_queries * subset_fraction))
    pilot_queries = random.sample(test_set, pilot_size)

    logger.info(f"Starting pilot evaluation on {pilot_size} queries (subset of {total_queries}).")

    timings = []
    memory_samples = []
    results = []

    for idx, query in enumerate(pilot_queries):
        query_id = query.get("query_id", f"unknown_{idx}")
        query_text = query.get("query", "")
        ground_truth = query.get("ground_truth", {})

        start_time = time.perf_counter()
        initial_memory = get_memory_usage_mb()

        try:
            # 1. Retrieval
            retrieved_chunks = retriever.retrieve(query_text, top_k=3)
            
            # 2. Reasoning
            prompt = build_prompt(query_text, retrieved_chunks)
            response_text = generate_response(model, tokenizer, prompt)
            answer, predicted_chunk_id = parse_model_response(response_text)

            end_time = time.perf_counter()
            current_memory = get_memory_usage_mb()

            latency = end_time - start_time
            memory_delta = current_memory - initial_memory

            timings.append(latency)
            memory_samples.append(memory_delta)

            results.append({
                "query_id": query_id,
                "latency_sec": latency,
                "memory_delta_mb": memory_delta,
                "answer": answer,
                "predicted_chunk_id": predicted_chunk_id,
                "status": "success"
            })

            logger.info(f"Pilot [{idx+1}/{pilot_size}] {query_id}: {latency:.2f}s")

        except Exception as e:
            end_time = time.perf_counter()
            latency = end_time - start_time
            logger.error(f"Pilot [{idx+1}/{pilot_size}] {query_id} FAILED: {str(e)}")
            results.append({
                "query_id": query_id,
                "latency_sec": latency,
                "memory_delta_mb": 0.0,
                "answer": None,
                "predicted_chunk_id": None,
                "status": "error",
                "error": str(e)
            })

    # Aggregate stats
    avg_latency = sum(timings) / len(timings) if timings else 0.0
    max_latency = max(timings) if timings else 0.0
    avg_memory = sum(memory_samples) / len(memory_samples) if memory_samples else 0.0

    pilot_stats = {
        "total_pilot_queries": pilot_size,
        "total_full_queries": total_queries,
        "subset_fraction": subset_fraction,
        "avg_latency_sec": avg_latency,
        "max_latency_sec": max_latency,
        "avg_memory_delta_mb": avg_memory,
        "success_count": sum(1 for r in results if r["status"] == "success"),
        "error_count": sum(1 for r in results if r["status"] == "error"),
        "details": results
    }

    return pilot_stats

def main():
    """Entry point for pilot evaluation."""
    config = get_config_dict()
    data_dir = Path(config["data_dir"])
    results_dir = Path(config["results_dir"])
    
    # Ensure directories exist
    results_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    logger.info("Loading test set...")
    test_set = load_test_set()
    if not test_set:
        logger.error("Test set is empty. Cannot run pilot.")
        return

    logger.info("Loading processed data for retriever...")
    processed_data = load_processed_data()
    
    logger.info("Initializing retriever...")
    retriever = TextRetriever(processed_data)

    logger.info("Loading model...")
    model, tokenizer = load_phi3_model()

    logger.info("Running pilot evaluation...")
    pilot_results = run_pilot_evaluation(
        test_set=test_set,
        retriever=retriever,
        model=model,
        tokenizer=tokenizer,
        subset_fraction=0.1
    )

    # Save results
    output_path = results_dir / "pilot_evaluation_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pilot_results, f, indent=2, default=str)

    logger.info(f"Pilot results saved to {output_path}")
    logger.info(f"Average latency: {pilot_results['avg_latency_sec']:.2f}s")
    logger.info(f"Estimated full run time (approx): {pilot_results['avg_latency_sec'] * pilot_results['total_full_queries']:.1f}s")

if __name__ == "__main__":
    main()