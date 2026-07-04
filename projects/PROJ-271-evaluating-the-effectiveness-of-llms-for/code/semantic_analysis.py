"""
Semantic analysis module for LLM-based code smell detection.

This module handles loading embeddings models, computing semantic vectors,
loading and running LLM inference for code smell detection, and managing
resource monitoring during batch processing.
"""
import os
import json
import logging
import gc
import time
from typing import List, Dict, Any, Optional, Tuple

from sentence_transformers import SentenceTransformer
from llama_cpp import Llama
import pandas as pd

from config import get_path, get_data_path, get_processed_path, get_results_path, setup_logging
from monitoring import (
    capture_snapshot,
    track_inference_time,
    record_batch_metrics,
    save_metrics_to_file,
    get_peak_ram_for_batch
)

# Initialize logger
logger = logging.getLogger(__name__)

# Constants
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
LLAMA_MODEL_PATH = "models/CodeLlama-7B-Instruct-GGUF/q4_k_m.gguf"
BATCH_SIZE = 10
CONTEXT_WINDOW_LIMIT = 4096  # tokens approximation

# Standardized prompt for code smell detection
CODE_SMELL_PROMPT = """You are an expert code reviewer. Analyze the following Python function for code smells.
Return a JSON list of smell categories found. If no smells are found, return an empty list.
Valid smell categories: "Long Method", "Large Class", "Duplicate Code", "Complex Conditional", "Magic Number", "Dead Code", "Feature Envy", "Data Clumps", "Primitive Obsession", "Switch Statements".

Function code:
{code}

JSON output:
"""


def load_embeddings_model() -> SentenceTransformer:
    """
    Load the sentence-transformers model for computing embeddings.

    Returns:
        SentenceTransformer: The loaded model.
    """
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    logger.info("Embedding model loaded successfully")
    return model


def load_baseline_data() -> pd.DataFrame:
    """
    Load the static baseline data from the CSV file.

    Returns:
        pd.DataFrame: The loaded baseline data.
    """
    input_path = get_data_path("static_baseline.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Baseline data not found at {input_path}. Run data_pipeline.py first.")
    
    logger.info(f"Loading baseline data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} functions from baseline")
    return df


def compute_embeddings(model: SentenceTransformer, code_texts: List[str]) -> List[List[float]]:
    """
    Compute embeddings for a list of code texts.

    Args:
        model: The loaded sentence-transformers model.
        code_texts: List of code strings to embed.

    Returns:
        List[List[float]]: List of embedding vectors.
    """
    logger.info(f"Computing embeddings for {len(code_texts)} functions")
    embeddings = model.encode(code_texts, convert_to_numpy=True, show_progress_bar=True)
    return embeddings.tolist()


def save_embeddings_to_csv(embeddings: List[List[float]], df: pd.DataFrame) -> None:
    """
    Save embeddings to a CSV file alongside original data.

    Args:
        embeddings: List of embedding vectors.
        df: Original dataframe containing code and metadata.
    """
    output_path = get_processed_path("embeddings.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df_with_embeddings = df.copy()
    df_with_embeddings['embedding'] = embeddings
    
    # Flatten embeddings for CSV storage (store as string representation)
    df_with_embeddings['embedding_str'] = df_with_embeddings['embedding'].apply(lambda x: json.dumps(x))
    df_with_embeddings = df_with_embeddings.drop(columns=['embedding'])
    
    df_with_embeddings.to_csv(output_path, index=False)
    logger.info(f"Saved embeddings to {output_path}")


def load_llama_model() -> Llama:
    """
    Load the quantized CodeLlama model using llama-cpp-python.

    Returns:
        Llama: The loaded LLM model.
    """
    logger.info(f"Loading LLM model from {LLAMA_MODEL_PATH}")
    if not os.path.exists(LLAMA_MODEL_PATH):
        # Fallback to HuggingFace download if GGUF not found
        logger.warning(f"GGUF model not found at {LLAMA_MODEL_PATH}. Attempting to download...")
        # In a real scenario, this would trigger a download script
        raise FileNotFoundError(f"Model file not found: {LLAMA_MODEL_PATH}. Please ensure the model is downloaded.")
    
    model = Llama(
        model_path=LLAMA_MODEL_PATH,
        n_ctx=CONTEXT_WINDOW_LIMIT,
        n_threads=4,
        n_batch=512
    )
    logger.info("LLM model loaded successfully")
    return model


def check_context_window(text: str, max_tokens: int = CONTEXT_WINDOW_LIMIT) -> bool:
    """
    Check if text fits within the model's context window.
    
    Note: This is an approximation using character count / 4 as a rough token estimate.
    
    Args:
        text: The text to check.
        max_tokens: Maximum allowed tokens.
        
    Returns:
        bool: True if text fits, False otherwise.
    """
    estimated_tokens = len(text) // 4
    return estimated_tokens <= max_tokens


def truncate_text(text: str, max_tokens: int = CONTEXT_WINDOW_LIMIT) -> str:
    """
    Truncate text to fit within the context window.
    
    Args:
        text: The text to truncate.
        max_tokens: Maximum allowed tokens.
        
    Returns:
        str: Truncated text.
    """
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    
    # Truncate at a reasonable point (end of last complete line)
    truncated = text[:max_chars]
    last_newline = truncated.rfind('\n')
    if last_newline > 0:
        truncated = truncated[:last_newline]
    
    return truncated + "\n... [truncated]"


def run_llm_inference(model: Llama, code: str) -> Optional[List[str]]:
    """
    Run LLM inference on a single code snippet to detect smells.
    
    Args:
        model: The loaded LLM model.
        code: The code snippet to analyze.
        
    Returns:
        Optional[List[str]]: List of detected smell categories, or None if parsing fails.
    """
    # Check context window
    if not check_context_window(code):
        logger.warning(f"Code too long, truncating. Length: {len(code)}")
        code = truncate_text(code)
    
    prompt = CODE_SMELL_PROMPT.format(code=code)
    
    try:
        output = model(
            prompt,
            max_tokens=256,
            temperature=0.2,
            stop=["\n\n"],
            echo=False
        )
        
        response_text = output['choices'][0]['text'].strip()
        
        # Parse JSON response
        try:
            # Extract JSON block if present
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                json_str = response_text[start:end].strip()
            elif response_text.startswith('[') or response_text.startswith('{'):
                json_str = response_text
            else:
                # Try to find JSON in the text
                import re
                match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if match:
                    json_str = match.group(0)
                else:
                    json_str = response_text
            
            smells = json.loads(json_str)
            if isinstance(smells, list):
                return smells
            else:
                logger.warning(f"Unexpected response format: {type(smells)}")
                return None
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}. Raw response: {response_text}")
            return None
            
    except Exception as e:
        logger.error(f"LLM inference failed: {e}")
        return None


def run_semantic_analysis() -> Dict[str, Any]:
    """
    Run the complete semantic analysis pipeline.
    
    Returns:
        Dict[str, Any]: Summary statistics of the analysis.
    """
    logger.info("Starting semantic analysis pipeline")
    
    # Load models
    embedding_model = load_embeddings_model()
    llama_model = load_llama_model()
    
    # Load data
    df = load_baseline_data()
    code_texts = df['code'].tolist()
    
    # Compute embeddings
    embeddings = compute_embeddings(embedding_model, code_texts)
    
    # Run LLM inference in batches with monitoring
    llm_results = []
    metric_records = []
    
    for i in range(0, len(code_texts), BATCH_SIZE):
        batch_idx = i // BATCH_SIZE
        batch_codes = code_texts[i:i+BATCH_SIZE]
        batch_indices = list(range(i, min(i+BATCH_SIZE, len(code_texts))))
        
        logger.info(f"Processing batch {batch_idx}: {len(batch_codes)} functions")
        
        # Capture batch start metrics
        batch_start_snapshot = capture_snapshot()
        batch_start_time = time.time()
        batch_peak_ram = batch_start_snapshot['process_ram_mb']
        
        batch_results = []
        
        for code in batch_codes:
            with track_inference_time() as metrics:
                result = run_llm_inference(llama_model, code)
                batch_results.append(result)
                
                # Track peak RAM during this inference
                if metrics['end_process_ram_mb'] > batch_peak_ram:
                    batch_peak_ram = metrics['end_process_ram_mb']
            
            # Clean up to prevent memory buildup
            gc.collect()
        
        # Record batch metrics
        batch_end_time = time.time()
        batch_duration = batch_end_time - batch_start_time
        batch_end_snapshot = capture_snapshot()
        
        batch_record = record_batch_metrics(batch_idx, {
            "start_timestamp": batch_start_snapshot["timestamp"],
            "end_timestamp": batch_end_snapshot["timestamp"],
            "duration_seconds": batch_duration,
            "start_process_ram_mb": batch_start_snapshot["process_ram_mb"],
            "end_process_ram_mb": batch_end_snapshot["process_ram_mb"],
            "peak_process_ram_mb": batch_peak_ram,
            "start_process_cpu_pct": batch_start_snapshot["process_cpu_pct"],
            "end_process_cpu_pct": batch_end_snapshot["process_cpu_pct"],
            "start_system_ram_mb": batch_start_snapshot["system_ram_mb"],
            "end_system_ram_mb": batch_end_snapshot["system_ram_mb"],
            "start_system_cpu_pct": batch_start_snapshot["system_cpu_pct"],
            "end_system_cpu_pct": batch_end_snapshot["system_cpu_pct"],
            "functions_processed": len(batch_codes),
            "successful_inferences": sum(1 for r in batch_results if r is not None),
            "failed_inferences": sum(1 for r in batch_results if r is None)
        })
        metric_records.append(batch_record)
        
        # Store results with indices
        for idx, result in zip(batch_indices, batch_results):
            llm_results.append({
                "index": idx,
                "smells": result,
                "status": "success" if result is not None else "failed"
            })
        
        # Force garbage collection between batches
        gc.collect()
    
    # Save embeddings
    save_embeddings_to_csv(embeddings, df)
    
    # Save LLM results
    results_path = get_processed_path("semantic_results.json")
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    
    output_data = {
        "embeddings_file": "embeddings.csv",
        "llm_results": llm_results,
        "total_functions": len(code_texts),
        "successful_analyses": sum(1 for r in llm_results if r['status'] == 'success'),
        "failed_analyses": sum(1 for r in llm_results if r['status'] == 'failed')
    }
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    logger.info(f"Saved semantic results to {results_path}")
    
    # Save resource metrics
    metrics_path = get_results_path("resource_metrics.json")
    save_metrics_to_file(metric_records, metrics_path)
    logger.info(f"Saved resource metrics to {metrics_path}")
    
    return {
        "total_functions": len(code_texts),
        "successful": output_data["successful_analyses"],
        "failed": output_data["failed_analyses"],
        "batches_processed": len(metric_records),
        "metrics_file": metrics_path,
        "results_file": results_path
    }


def main():
    """Main entry point for the semantic analysis module."""
    setup_logging()
    
    try:
        summary = run_semantic_analysis()
        logger.info(f"Semantic analysis completed successfully")
        logger.info(f"Summary: {json.dumps(summary, indent=2)}")
    except Exception as e:
        logger.error(f"Semantic analysis failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()