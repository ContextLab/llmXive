import os
import json
import logging
import gc
import time
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from llama_cpp import Llama

from config import get_data_path, get_processed_path, get_results_path, setup_logging
from monitoring import record_batch_metrics, save_metrics_to_file


def load_embeddings_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> SentenceTransformer:
    """Load the sentence transformer model for embeddings."""
    logger = setup_logging(__name__)
    logger.info(f"Loading embedding model: {model_name}...")
    model = SentenceTransformer(model_name)
    logger.info("Embedding model loaded.")
    return model


def load_llama_model(model_path: str, n_ctx: int = 4096) -> Llama:
    """Load the quantized CodeLlama model."""
    logger = setup_logging(__name__)
    logger.info(f"Loading LLM from {model_path}...")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=4,
        verbose=False
    )

    # Verify quantization (basic check: file name or internal property)
    if "q4" not in model_path.lower() and "Q4" not in model_path:
        logger.warning("Model may not be 4-bit quantized. Proceeding with caution.")
    else:
        logger.info("Model is 4-bit quantized (verified from path).")

    return model


def load_baseline_data(csv_path: str) -> pd.DataFrame:
    """Load the static baseline CSV."""
    logger = setup_logging(__name__)
    logger.info(f"Loading baseline data from {csv_path}...")
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} records.")
    return df


def compute_embeddings(model: SentenceTransformer, codes: List[str], batch_size: int = 16) -> np.ndarray:
    """Compute embeddings for a list of code snippets."""
    logger = setup_logging(__name__)
    embeddings = []

    for i in range(0, len(codes), batch_size):
        batch = codes[i:i + batch_size]
        batch_embeddings = model.encode(batch, convert_to_numpy=True)
        embeddings.append(batch_embeddings)
        gc.collect()

    return np.vstack(embeddings)


def check_context_window(text: str, max_tokens: int = 4096) -> bool:
    """Check if text fits within the context window (approximate token count)."""
    # Simple approximation: 1 token ~ 4 characters
    estimated_tokens = len(text) // 4
    return estimated_tokens <= max_tokens


def truncate_text(text: str, max_tokens: int = 4096) -> str:
    """Truncate text from the start to fit context window, preserving the end."""
    # Simple approximation
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def run_llm_inference(model: Llama, code: str, prompt: str) -> str:
    """Run LLM inference on a single code snippet."""
    full_prompt = prompt.replace("{code}", code)
    response = model(
        full_prompt,
        max_tokens=512,
        temperature=0.2,
        stop=["\n\n"],
        echo=False
    )
    return response["choices"][0]["text"].strip()


def parse_llm_output(output: str) -> List[str]:
    """Parse LLM output into a list of smell categories."""
    try:
        # Expect JSON list
        smells = json.loads(output)
        if isinstance(smells, list):
            return smells
        else:
            return []
    except json.JSONDecodeError:
        logging.getLogger(__name__).warning(f"Unparseable LLM output: {output}")
        return []


def run_semantic_analysis(
    baseline_path: str,
    embedding_model: SentenceTransformer,
    llama_model: Llama,
    prompt_path: str,
    batch_size: int = 10
) -> Dict[str, Any]:
    """
    Run semantic analysis: compute embeddings and LLM labels.
    """
    logger = setup_logging(__name__)
    df = load_baseline_data(baseline_path)

    # Load prompt
    with open(prompt_path, "r") as f:
        prompt_template = f.read()

    results = []
    metrics = []

    for i in range(0, len(df), batch_size):
        batch_df = df.iloc[i:i + batch_size]
        batch_start = time.time()

        batch_results = []
        for _, row in batch_df.iterrows():
            code = row["code"]

            # Truncate if necessary
            if not check_context_window(code):
                code = truncate_text(code)
                if not check_context_window(code):
                    logger.warning("Code too long even after truncation. Skipping.")
                    continue

            # Compute embedding
            embedding = embedding_model.encode([code], convert_to_numpy=True)[0]

            # Run LLM inference
            llm_output = run_llm_inference(llama_model, code, prompt_template)
            smells = parse_llm_output(llm_output)

            batch_results.append({
                "code": code,
                "embedding": embedding.tolist(),
                "llm_smell_labels": ",".join(smells)
            })

        batch_end = time.time()
        batch_time = batch_end - batch_start

        # Record metrics
        batch_metrics = record_batch_metrics(
            batch_id=i // batch_size,
            time_seconds=batch_time,
            items=len(batch_results)
        )
        metrics.append(batch_metrics)

        results.extend(batch_results)
        gc.collect()

    # Save metrics
    save_metrics_to_file(metrics, os.path.join(get_results_path(), "resource_metrics.json"))

    return results


def main():
    """Main entry point for semantic analysis."""
    logger = setup_logging(__name__)

    # Paths
    baseline_path = os.path.join(get_data_path(), "static_baseline.csv")
    prompt_path = os.path.join("contracts", "llm_prompt.txt")
    model_path = "models/CodeLlama-7B-Instruct-GGUF/Q4_K_M.gguf"  # Adjust as needed
    output_path = os.path.join(get_processed_path(), "semantic_results.json")

    try:
        # Load models
        embedding_model = load_embeddings_model()
        llama_model = load_llama_model(model_path)

        # Run analysis
        results = run_semantic_analysis(
            baseline_path=baseline_path,
            embedding_model=embedding_model,
            llama_model=llama_model,
            prompt_path=prompt_path,
            batch_size=10
        )

        # Save results
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Semantic analysis complete. Results saved to {output_path}")

    except Exception as e:
        logger.error(f"Semantic analysis failed: {e}")
        raise
