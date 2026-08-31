import os
import json
import logging
import gc
import time
from typing import List, Dict, Any, Optional, Tuple

from sentence_transformers import SentenceTransformer
from llama_cpp import Llama

from config import get_processed_path, get_data_path, get_results_path, setup_logging
from monitoring import get_ram_usage_mb, get_cpu_utilization, capture_snapshot, record_batch_metrics, save_metrics_to_file, get_peak_ram_for_batch

logger = setup_logging(__name__)

# --- Model Loading ---

def load_embeddings_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """Load the sentence-transformers model for embeddings."""
    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    logger.info("Embedding model loaded successfully.")
    return model

def load_llama_model(
    model_path: str,
    n_ctx: int = 4096,
    n_threads: int = 4,
    n_batch: int = 512,
    use_mlock: bool = True
) -> Llama:
    """
    Load the Llama model with optimized settings for RAM usage.
    
    Optimization Strategy for T032a:
    1. n_ctx: Fixed to 4096 to prevent context window over-allocation.
    2. n_batch: Reduced to 512 to limit peak RAM during prompt processing.
    3. use_mlock: Enabled to prevent swapping to disk (reducing page faults).
    4. n_threads: Configurable to balance CPU load vs memory bandwidth.
    """
    logger.info(f"Loading Llama model from: {model_path}")
    if not os.path.exists(model_path):
        # Fallback to HF hub download if path is a repo_id, though spec implies local path
        # For this implementation, we assume the path is valid as per T014 setup
        raise FileNotFoundError(f"Model file not found at {model_path}. Ensure T014 completed.")
    
    model = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=n_threads,
        n_batch=n_batch,
        use_mlock=use_mlock,
        verbose=False
    )
    logger.info("Llama model loaded successfully.")
    return model

# --- Data Loading ---

def load_baseline_data(csv_path: str) -> List[Dict[str, Any]]:
    """Load the static baseline CSV data."""
    import pandas as pd
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Baseline data not found at {csv_path}. Run T011a first.")
    
    logger.info(f"Loading baseline data from {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Ensure we have the required columns
    required_cols = ['code', 'loc', 'cyclomatic_complexity', 'static_smell_labels']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in {csv_path}")
    
    # Convert to list of dicts for batch processing
    data = df.to_dict(orient='records')
    logger.info(f"Loaded {len(data)} functions from baseline.")
    return data

# --- Pre-processing ---

def compute_embeddings(
    model: SentenceTransformer,
    texts: List[str],
    batch_size: int = 32
) -> List[List[float]]:
    """Compute embeddings for a list of texts in batches."""
    logger.info(f"Computing embeddings for {len(texts)} texts (batch_size={batch_size})")
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True, convert_to_numpy=True)
    return embeddings.tolist()

def check_context_window(text: str, max_tokens: int = 4096) -> bool:
    """Estimate if text exceeds context window (rough char/token heuristic)."""
    # Rough estimate: 4 chars per token for Python code
    estimated_tokens = len(text) / 4
    return estimated_tokens <= max_tokens

def truncate_text(text: str, max_chars: int = 16000) -> str:
    """Truncate text to fit roughly within context window."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."

# --- Inference ---

def run_llm_inference(
    model: Llama,
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.2
) -> str:
    """Run inference on the Llama model."""
    output = model(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        stop=["</s>", "```"],
        echo=False
    )
    return output['choices'][0]['text']

def parse_llm_output(output_text: str) -> List[str]:
    """Parse the JSON list of smells from LLM output."""
    import json
    try:
        # Clean up potential markdown or extra text
        start_idx = output_text.find('[')
        end_idx = output_text.rfind(']')
        if start_idx == -1 or end_idx == -1:
            return []
        
        json_str = output_text[start_idx:end_idx+1]
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse LLM output: {e}")
        return []

# --- Main Pipeline with RAM Optimization ---

def run_semantic_analysis(
    baseline_path: Optional[str] = None,
    output_path: Optional[str] = None,
    embedding_model_name: str = "all-MiniLM-L6-v2",
    llm_model_path: Optional[str] = None,
    batch_size: int = 10,
    llm_batch_size: int = 1
) -> Dict[str, Any]:
    """
    Execute the full semantic analysis pipeline with RAM optimization.
    
    Optimization Strategy (T032a):
    1. Batch Loading: Process data in small batches (default 10) to keep memory footprint low.
    2. Explicit GC: Force garbage collection between batches to reclaim RAM.
    3. Peak RAM Tracking: Monitor and record peak RAM usage per batch.
    4. Context Management: Ensure model outputs are released immediately.
    """
    if baseline_path is None:
        baseline_path = get_data_path("static_baseline.csv")
    if output_path is None:
        output_path = get_processed_path("semantic_results.json")
    
    logger.info("Starting Semantic Analysis Pipeline with RAM Optimization")
    
    # Load Models
    embed_model = load_embeddings_model(embedding_model_name)
    
    if llm_model_path is None:
        # Default path based on project structure, adjust if needed
        llm_model_path = "models/codellama-7b-instruct.Q4_K_M.gguf" 
        if not os.path.exists(llm_model_path):
            # Fallback to common HF path if local not found (for testing purposes)
            # In production, this should be a valid path from T014
            logger.warning(f"LLM model not found at {llm_model_path}. Check T014 configuration.")
            raise FileNotFoundError("LLM Model path invalid. Ensure T014 downloaded the model.")
    
    llm_model = load_llama_model(llm_model_path)
    
    # Load Data
    data = load_baseline_data(baseline_path)
    
    # Load Prompt
    prompt_path = "contracts/llm_prompt.txt"
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found at {prompt_path}. Ensure T015a completed.")
    
    with open(prompt_path, 'r') as f:
        prompt_template = f.read()
    
    results = []
    batch_metrics = []
    
    # Process in batches
    total_batches = (len(data) + batch_size - 1) // batch_size
    
    for i in range(0, len(data), batch_size):
        batch_data = data[i:i+batch_size]
        batch_num = i // batch_size + 1
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_data)} items)")
        
        # Capture start metrics
        start_ram = get_ram_usage_mb()
        start_time = time.time()
        
        batch_results = []
        
        for item in batch_data:
            code = item['code']
            loc = item['loc']
            cc = item['cyclomatic_complexity']
            static_labels = item['static_smell_labels']
            
            # Check context window
            if not check_context_window(code):
                code = truncate_text(code)
                logger.debug(f"Truncated code for function at LOC {loc}")
            
            # Compute Embedding
            embedding = compute_embeddings(embed_model, [code])[0]
            
            # Construct Prompt
            prompt = prompt_template.replace("{code}", code)
            
            # Run LLM Inference
            llm_output = run_llm_inference(llm_model, prompt)
            detected_smells = parse_llm_output(llm_output)
            
            batch_results.append({
                "code": code,
                "loc": loc,
                "cyclomatic_complexity": cc,
                "static_smell_labels": static_labels,
                "embedding": embedding,
                "llm_detected_smells": detected_smells,
                "llm_raw_output": llm_output
            })
            
            # Force GC after every item in batch to minimize peak RAM
            gc.collect()
        
        # Capture end metrics
        end_ram = get_ram_usage_mb()
        end_time = time.time()
        
        batch_time = end_time - start_time
        batch_peak_ram = max(start_ram, end_ram)
        
        # Record batch metrics
        metrics = {
            "batch_id": batch_num,
            "items_processed": len(batch_data),
            "time_seconds": batch_time,
            "peak_ram_mb": batch_peak_ram,
            "cpu_utilization": get_cpu_utilization()
        }
        batch_metrics.append(metrics)
        
        logger.info(f"Batch {batch_num} complete. Time: {batch_time:.2f}s, Peak RAM: {batch_peak_ram:.2f}MB")
        
        results.extend(batch_results)
        
        # Explicit GC after batch completion
        gc.collect()
    
    # Save Results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save Metrics
    metrics_path = get_results_path("resource_metrics.json")
    save_metrics_to_file(batch_metrics, metrics_path)
    
    logger.info(f"Semantic analysis complete. Results saved to {output_path}")
    logger.info(f"Metrics saved to {metrics_path}")
    
    return {
        "results_path": output_path,
        "metrics_path": metrics_path,
        "total_items": len(results),
        "batches_processed": len(batch_metrics)
    }

def main():
    """Entry point for the script."""
    try:
        result = run_semantic_analysis()
        print(f"Pipeline completed successfully. Processed {result['total_items']} items.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()