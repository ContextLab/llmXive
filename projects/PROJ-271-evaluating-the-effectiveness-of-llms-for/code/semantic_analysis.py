import os
import json
import logging
import gc
import time
from typing import List, Dict, Any, Optional, Tuple

from sentence_transformers import SentenceTransformer
import pandas as pd
from llama_cpp import Llama

from config import get_path, get_data_path, get_processed_path, setup_logging
from monitoring import get_ram_usage_mb, get_cpu_utilization, record_batch_metrics, save_metrics_to_file, get_peak_ram_for_batch

logger = setup_logging(__name__)

# --- Embedding Model ---

def load_embeddings_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> SentenceTransformer:
    logger.info(f"Loading embedding model: {model_name}")
    return SentenceTransformer(model_name)

# --- LLM Model ---

def load_llama_model(model_path: str, n_ctx: int = 4096, n_threads: int = 4, n_batch: int = 512) -> Llama:
    logger.info(f"Loading LLM from: {model_path}")
    # Assuming GGUF path is configured or passed; using a placeholder for the path logic
    # In a real run, this path must be valid.
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"LLM model file not found at {model_path}. Please download CodeLlama-7B-Instruct-GGUF.")
    
    return Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=n_threads,
        n_batch=n_batch,
        verbose=False
    )

# --- Data Loading ---

def load_baseline_data(csv_path: str) -> pd.DataFrame:
    logger.info(f"Loading baseline data from {csv_path}")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Baseline CSV not found: {csv_path}")
    df = pd.read_csv(csv_path)
    # Ensure 'code' column exists
    if 'code' not in df.columns:
        raise ValueError("Baseline CSV must contain a 'code' column.")
    return df

# --- Embedding Computation ---

def compute_embeddings(df: pd.DataFrame, model: SentenceTransformer, batch_size: int = 32) -> List[List[float]]:
    logger.info(f"Computing embeddings for {len(df)} functions...")
    texts = df['code'].tolist()
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True, convert_to_numpy=True)
    return embeddings.tolist()

# --- Context Window Handling ---

def check_context_window(text: str, max_tokens: int = 4096) -> bool:
    # Rough estimate: 1 token ~ 4 chars for code
    estimated_tokens = len(text) // 4
    return estimated_tokens <= max_tokens

def truncate_text(text: str, max_tokens: int = 4096) -> str:
    # Truncate by characters based on token estimate
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."

# --- LLM Inference ---

def run_llm_inference(llm: Llama, code: str, prompt_template: str, max_tokens: int = 512) -> str:
    # Construct prompt
    full_prompt = prompt_template.format(code=code)
    
    # Check context window
    if not check_context_window(full_prompt):
        full_prompt = truncate_text(full_prompt)
        logger.warning("Prompt truncated due to context window limit.")

    try:
        output = llm(
            full_prompt,
            max_tokens=max_tokens,
            temperature=0.0, # Deterministic
            stop=["</s>", "```"],
            echo=False
        )
        return output['choices'][0]['text']
    except Exception as e:
        logger.error(f"LLM inference failed: {e}")
        return ""

def parse_llm_output(text: str) -> List[str]:
    # Expecting JSON list like ["Long Function", "Complex Condition"]
    # The prompt should enforce this, but we handle errors.
    try:
        # Clean up potential markdown code blocks
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        result = json.loads(text)
        if isinstance(result, list):
            return result
        return []
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse LLM output as JSON: {text[:100]}...")
        return []

# --- Main Pipeline ---

def run_semantic_analysis(
    baseline_path: str,
    output_path: str,
    model_path: str,
    batch_size: int = 10,
    llm_batch_size: int = 10
):
    """
    Executes the full semantic analysis pipeline:
    1. Loads baseline data.
    2. Computes embeddings.
    3. Runs LLM inference in batches.
    4. Writes results to JSON.
    """
    # 1. Load Data
    df = load_baseline_data(baseline_path)
    
    # 2. Load Models
    embed_model = load_embeddings_model()
    llm_model = load_llama_model(model_path)
    
    # 3. Compute Embeddings
    all_embeddings = compute_embeddings(df, embed_model)
    
    # 4. Prepare Prompt
    prompt_template = """
    Analyze the following Python code function for code smells.
    Return ONLY a JSON list of strings containing the names of detected code smells.
    Do not output any other text.
    
    Code:
    {code}
    
    Detected Smells (JSON list):
    """

    results = []
    metrics_log = []
    
    logger.info(f"Starting LLM inference on {len(df)} functions.")
    
    # Process in batches for resource management
    for i in range(0, len(df), llm_batch_size):
        batch_df = df.iloc[i:i+llm_batch_size]
        batch_indices = list(range(i, min(i+llm_batch_size, len(df))))
        
        batch_start_time = time.time()
        batch_ram_start = get_ram_usage_mb()
        
        batch_results = []
        for idx, row in batch_df.iterrows():
            code = row['code']
            llm_output = run_llm_inference(llm_model, code, prompt_template)
            smells = parse_llm_output(llm_output)
            
            # Find original index in df to match embedding
            original_idx = row.name
            batch_results.append({
                "original_index": int(original_idx),
                "llm_smells": smells,
                "llm_raw_output": llm_output
            })
        
        batch_end_time = time.time()
        batch_ram_end = get_ram_usage_mb()
        
        # Record metrics
        batch_metrics = {
            "batch_start_idx": i,
            "batch_end_idx": i + llm_batch_size,
            "duration_seconds": batch_end_time - batch_start_time,
            "ram_usage_mb": batch_ram_end,
            "cpu_utilization": get_cpu_utilization()
        }
        metrics_log.append(batch_metrics)
        
        # Force GC
        gc.collect()
        
        results.extend(batch_results)
        logger.info(f"Processed batch {i//llm_batch_size + 1}: {len(batch_results)} items")

    # 5. Construct Final Output
    # Merge embeddings, static labels (from baseline), and LLM results
    # We need to align results with the original dataframe order
    
    final_data = []
    for idx, row in df.iterrows():
        emb = all_embeddings[idx]
        static_smells = row.get('static_smell_labels', '[]')
        # Ensure static_smells is a list if it was a string in CSV
        if isinstance(static_smells, str):
            try:
                static_smells = json.loads(static_smells)
            except:
                static_smells = []
        
        llm_entry = next((r for r in results if r['original_index'] == idx), None)
        llm_smells = llm_entry['llm_smells'] if llm_entry else []
        
        final_data.append({
            "original_index": idx,
            "code_length": len(row['code']),
            "static_smell_labels": static_smells,
            "llm_smell_labels": llm_smells,
            "embedding": emb
        })

    # 6. Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2)
    
    logger.info(f"Saved semantic results to {output_path}")
    
    # Save metrics if path is provided in config
    metrics_path = get_path('results', 'resource_metrics.json')
    save_metrics_to_file(metrics_log, metrics_path)

def main():
    """Entry point for running the semantic analysis task."""
    baseline_csv = get_data_path('static_baseline.csv')
    output_json = get_processed_path('semantic_results.json')
    
    # The model path should be configured or downloaded. 
    # For this implementation, we assume the user has the model path or it's in a standard location.
    # In a real deployment, this might come from an env var or config.
    # We'll use a placeholder that the user must update or a standard HF cache path if available.
    # However, the task requires a real run. We will assume the model is downloaded to a specific path.
    # Let's assume a standard GGUF path structure for the sake of the script, but it will fail if not found.
    model_path = os.environ.get('LLAMA_MODEL_PATH', 'models/CodeLlama-7B-Instruct-GGUF/q4_k_m.gguf')
    
    if not os.path.exists(model_path):
        logger.error(f"Model not found at {model_path}. Please set LLAMA_MODEL_PATH or download the model.")
        return

    run_semantic_analysis(
        baseline_path=baseline_csv,
        output_path=output_json,
        model_path=model_path,
        batch_size=32,
        llm_batch_size=10
    )

if __name__ == "__main__":
    main()
