import os
import json
import logging
import gc
import time
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from llama_cpp import Llama

from config import get_path, get_data_path, get_processed_path, get_results_path, setup_logging
from monitoring import get_ram_usage_mb, get_cpu_utilization, capture_snapshot, record_batch_metrics, save_metrics_to_file, get_peak_ram_for_batch

# Configure logging
logger = logging.getLogger(__name__)

def load_embeddings_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> SentenceTransformer:
    """Load the sentence transformer model for embeddings."""
    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    logger.info("Embedding model loaded successfully")
    return model

def load_baseline_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load the static baseline CSV data."""
    if filepath is None:
        filepath = get_data_path("static_baseline.csv")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline data not found at {filepath}")
    
    logger.info(f"Loading baseline data from {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} functions from baseline")
    return df

def compute_embeddings(model: SentenceTransformer, texts: List[str], batch_size: int = 16) -> np.ndarray:
    """Compute embeddings for a list of texts."""
    logger.info(f"Computing embeddings for {len(texts)} texts")
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True)
    logger.info("Embeddings computed successfully")
    return embeddings

def save_embeddings_to_csv(embeddings: np.ndarray, baseline_df: pd.DataFrame, output_path: str):
    """Save embeddings and baseline data to a CSV file."""
    logger.info(f"Saving embeddings to {output_path}")
    output_df = baseline_df.copy()
    output_df['embedding'] = list(embeddings)
    output_df.to_csv(output_path, index=False)
    logger.info("Embeddings saved successfully")

def load_llama_model(model_path: str, n_ctx: int = 4096, n_threads: int = 4, n_gpu_layers: int = 0) -> Llama:
    """Load the LLaMA model for inference."""
    logger.info(f"Loading LLaMA model from {model_path}")
    model = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=n_threads,
        n_gpu_layers=n_gpu_layers,
        verbose=False
    )
    logger.info("LLaMA model loaded successfully")
    return model

def check_context_window(text: str, max_tokens: int = 4096) -> bool:
    """Check if text fits within the context window (approximate token count)."""
    # Approximate token count: 1 token ≈ 4 characters for English text
    estimated_tokens = len(text) // 4
    return estimated_tokens <= max_tokens

def truncate_text(text: str, max_tokens: int = 4096) -> str:
    """Truncate text to fit within the context window."""
    # Approximate token count: 1 token ≈ 4 characters
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    logger.warning(f"Truncating text from {len(text)} to {max_chars} characters")
    return text[:max_chars]

def run_llm_inference(model: Llama, prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> str:
    """Run inference with the LLaMA model."""
    response = model(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        stop=["</s>", "```"],
        echo=False
    )
    return response['choices'][0]['text'].strip()

def parse_llm_output(output: str) -> List[str]:
    """Parse the LLM output to extract smell labels."""
    try:
        # Try to parse as JSON first
        if output.startswith('[') or output.startswith('{'):
            return json.loads(output)
        
        # Otherwise, try to extract list-like content
        if '[' in output and ']' in output:
            start = output.find('[')
            end = output.rfind(']') + 1
            list_str = output[start:end]
            return json.loads(list_str)
        
        # Fallback: split by common delimiters
        return [s.strip().strip(',').strip('"').strip("'") for s in output.split(',') if s.strip()]
    except Exception as e:
        logger.warning(f"Failed to parse LLM output: {e}")
        return []

def run_semantic_analysis(
    baseline_path: Optional[str] = None,
    embeddings_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    llama_model_path: Optional[str] = None,
    batch_size: int = 10,
    output_path: Optional[str] = None,
    metrics_output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the complete semantic analysis pipeline:
    1. Load baseline data
    2. Compute embeddings
    3. Run LLM inference for smell detection
    4. Save results to JSON
    5. Record metrics
    """
    logger.info("Starting semantic analysis pipeline")
    
    # Load baseline data
    baseline_df = load_baseline_data(baseline_path)
    
    # Load embedding model
    embeddings_model = load_embeddings_model(embeddings_model_name)
    
    # Load LLaMA model if provided
    llama_model = None
    if llama_model_path and os.path.exists(llama_model_path):
        llama_model = load_llama_model(llama_model_path)
    
    # Prepare output path
    if output_path is None:
        output_path = get_processed_path("semantic_results.json")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    results = []
    batch_metrics = []
    
    # Process in batches
    num_batches = (len(baseline_df) + batch_size - 1) // batch_size
    
    for batch_idx in range(0, len(baseline_df), batch_size):
        batch_df = baseline_df.iloc[batch_idx:batch_idx + batch_size]
        batch_codes = batch_df['code'].tolist()
        
        # Capture start snapshot
        start_snapshot = capture_snapshot()
        batch_start_time = time.time()
        
        # Compute embeddings for this batch
        batch_embeddings = compute_embeddings(embeddings_model, batch_codes)
        
        # Run LLM inference if model is loaded
        batch_llm_labels = []
        if llama_model:
            for code in batch_codes:
                # Check context window
                if not check_context_window(code):
                    code = truncate_text(code)
                
                # Create prompt
                prompt = f"""Analyze the following code for code smells. Return a JSON list of smell categories detected.
                
                Code:
                ```python
                {code}
                ```
                
                Smell categories: Long Method, Large Class, Duplicate Code, Feature Envy, Data Clumps, Primitive Obsession, Switch Statements, Parallel Inheritance Hierarchies, Lazy Class, Speculative Generality, Temporary Field, Long Parameter List, Global Data, Mutable Data, Divergent Change, Shotgun Surgery, Refused Bequest, Inappropriate Intimacy, Middle Man, Insufficient Modularization, Broken Hierarchy, Blob, Functional Decomposition, Spaghetti Code, Data Class, Dead Code, Inefficient Loop, Unnecessary Abstraction, Speculative Generality, Temporary Field, Duplicate Code, Long Method, Large Class, Feature Envy, Data Clumps, Primitive Obsession, Switch Statements, Parallel Inheritance Hierarchies, Lazy Class, Speculative Generality, Temporary Field, Long Parameter List, Global Data, Mutable Data, Divergent Change, Shotgun Surgery, Refused Bequest, Inappropriate Intimacy, Middle Man, Insufficient Modularization, Broken Hierarchy, Blob, Functional Decomposition, Spaghetti Code, Data Class, Dead Code, Inefficient Loop, Unnecessary Abstraction.
                
                Output format: ["smell1", "smell2", ...]
                """
                
                try:
                    llm_output = run_llm_inference(llama_model, prompt)
                    labels = parse_llm_output(llm_output)
                    batch_llm_labels.append(labels)
                except Exception as e:
                    logger.warning(f"LLM inference failed: {e}")
                    batch_llm_labels.append([])
        else:
            batch_llm_labels = [[] for _ in batch_codes]
        
        # Capture end snapshot
        end_snapshot = capture_snapshot()
        batch_end_time = time.time()
        
        # Record batch metrics
        batch_metrics_dict = record_batch_metrics(
            batch_idx,
            batch_size,
            start_snapshot,
            end_snapshot,
            batch_end_time - batch_start_time
        )
        batch_metrics.append(batch_metrics_dict)
        
        # Prepare results for this batch
        for i, (row, embedding, labels) in enumerate(zip(batch_df.itertuples(), batch_embeddings, batch_llm_labels)):
            result = {
                'code': row.code,
                'loc': row.loc,
                'cyclomatic_complexity': row.cyclomatic_complexity,
                'static_smell_labels': row.static_smell_labels if hasattr(row, 'static_smell_labels') else [],
                'embedding': embedding.tolist() if isinstance(embedding, np.ndarray) else list(embedding),
                'llm_smell_labels': labels,
                'batch_index': batch_idx,
                'row_index': i
            }
            results.append(result)
        
        # Force garbage collection between batches
        gc.collect()
        
        logger.info(f"Completed batch {batch_idx // batch_size + 1}/{num_batches}")
    
    # Save results to JSON
    logger.info(f"Saving {len(results)} results to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Save metrics if path provided
    if metrics_output_path:
        save_metrics_to_file(batch_metrics, metrics_output_path)
    
    logger.info("Semantic analysis pipeline completed successfully")
    
    return {
        'total_functions': len(results),
        'output_path': output_path,
        'metrics_path': metrics_output_path,
        'batch_metrics': batch_metrics
    }

def main():
    """Main entry point for semantic analysis."""
    setup_logging()
    
    # Configuration
    baseline_path = get_data_path("static_baseline.csv")
    llama_model_path = None  # Will be set if model is available
    output_path = get_processed_path("semantic_results.json")
    metrics_path = get_results_path("resource_metrics.json")
    
    # Run semantic analysis
    try:
        result = run_semantic_analysis(
            baseline_path=baseline_path,
            llama_model_path=llama_model_path,
            output_path=output_path,
            metrics_output_path=metrics_path
        )
        
        logger.info(f"Analysis complete. Results saved to {result['output_path']}")
        logger.info(f"Metrics saved to {result['metrics_path']}")
        
    except Exception as e:
        logger.error(f"Semantic analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()