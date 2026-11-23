import os
import json
import logging
import hashlib
import gc
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from llama_cpp import Llama
import psutil

from config import (
    setup_logging,
    get_path,
    get_data_path,
    get_processed_path,
    get_results_path,
    LLM_BATCH_SIZE_MAX,
    FR008_BATCH_SIZE_LIMIT,
    RANDOM_SEED,
    STATIC_BASELINE_PATH,
    SEMANTIC_RESULTS_PATH,
    RESOURCE_METRICS_PATH
)
from monitoring import record_batch_metrics, save_metrics_to_file

logger = setup_logging("semantic_analysis")

def load_embeddings_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """Load the sentence-transformers model for embeddings."""
    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    logger.info("Embedding model loaded successfully")
    return model

def verify_model_integrity(model_path: str) -> bool:
    """Verify the integrity of the downloaded GGUF model file."""
    if not os.path.exists(model_path):
        logger.error(f"Model file not found: {model_path}")
        return False
    
    # Basic integrity check - verify file size is non-zero
    file_size = os.path.getsize(model_path)
    if file_size == 0:
        logger.error(f"Model file is empty: {model_path}")
        return False
    
    logger.info(f"Model integrity verified: {model_path} ({file_size} bytes)")
    return True

def load_llama_model(
    model_path: str,
    n_ctx: int = 4096,
    n_threads: int = 4,
    n_batch: int = LLM_BATCH_SIZE_MAX
) -> Llama:
    """Load the quantized CodeLlama model using llama-cpp-python."""
    logger.info(f"Loading LLM model from: {model_path}")
    
    # Verify model integrity before loading
    if not verify_model_integrity(model_path):
        raise ValueError(f"Model integrity check failed: {model_path}")
    
    # Check if model is 4-bit quantized
    if "q4" not in model_path.lower() and "Q4" not in model_path:
        logger.warning(f"Model may not be 4-bit quantized: {model_path}")
        # We proceed anyway but log a warning
    
    model = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=n_threads,
        n_batch=n_batch,
        verbose=False
    )
    
    logger.info("LLM model loaded successfully")
    return model

def load_baseline_data() -> pd.DataFrame:
    """Load the static baseline data from CSV."""
    logger.info(f"Loading baseline data from: {STATIC_BASELINE_PATH}")
    if not os.path.exists(STATIC_BASELINE_PATH):
        raise FileNotFoundError(f"Baseline file not found: {STATIC_BASELINE_PATH}")
    
    df = pd.read_csv(STATIC_BASELINE_PATH)
    logger.info(f"Loaded {len(df)} functions from baseline")
    return df

def compute_embeddings(
    model: SentenceTransformer,
    texts: List[str],
    batch_size: int = 32
) -> np.ndarray:
    """Compute embeddings for a list of texts."""
    logger.info(f"Computing embeddings for {len(texts)} texts")
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    logger.info("Embedding computation complete")
    return embeddings

def check_context_window(text: str, max_length: int = 4096) -> Tuple[bool, int]:
    """Check if text exceeds the model's context window."""
    # Simple token estimation: 1 token ≈ 4 characters
    estimated_tokens = len(text) // 4
    exceeds = estimated_tokens > max_length
    return exceeds, estimated_tokens

def truncate_text(text: str, max_length: int = 4096, preserve_header: bool = True) -> str:
    """Truncate text to fit within context window, preserving function header."""
    if len(text) <= max_length:
        return text
    
    if preserve_header:
        # Try to preserve the function definition line
        lines = text.split('\n')
        header_lines = []
        body_lines = []
        
        in_header = True
        for line in lines:
            if in_header and (line.strip().startswith('def ') or line.strip().startswith('async def ')):
                header_lines.append(line)
            elif in_header and line.strip() == '' or (line.strip().startswith('"""') or line.strip().startswith("'''")):
                # Continue collecting header lines (docstrings, etc.)
                header_lines.append(line)
                if line.strip().endswith('"""') or line.strip().endswith("'''"):
                    in_header = False
            else:
                in_header = False
                body_lines.append(line)
        
        # Combine header and truncated body
        header_text = '\n'.join(header_lines)
        remaining_length = max_length - len(header_text)
        
        if remaining_length > 0:
            # Truncate body while trying to keep lines intact
            truncated_body = []
            current_length = 0
            for line in body_lines:
                if current_length + len(line) + 1 <= remaining_length:
                    truncated_body.append(line)
                    current_length += len(line) + 1
                else:
                    # Truncate within the line if necessary
                    remaining = remaining_length - current_length
                    if remaining > 10:
                        truncated_body.append(line[:remaining])
                    break
            
            return header_text + '\n' + '\n'.join(truncated_body)
        else:
            return header_text[:max_length]
    else:
        return text[:max_length]

def run_llm_inference(
    model: Llama,
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.0
) -> str:
    """Run LLM inference with the given prompt."""
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
        # Try to parse as JSON
        if output.startswith('```'):
            # Remove markdown code block markers
            output = output.split('```')[1].strip()
            if output.startswith('json'):
                output = output[4:].strip()
        
        parsed = json.loads(output)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict) and 'smells' in parsed:
            return parsed['smells']
        else:
            logger.warning(f"Unexpected LLM output structure: {output[:200]}")
            return []
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM output as JSON: {e}")
        logger.warning(f"Raw output: {output[:200]}")
        return []

def load_prompt_template(prompt_path: str) -> str:
    """Load the prompt template from file."""
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def run_semantic_analysis(
    baseline_df: pd.DataFrame,
    llm_model: Llama,
    embedding_model: SentenceTransformer,
    prompt_template: str,
    batch_size: int = LLM_BATCH_SIZE_MAX
) -> Dict[str, Any]:
    """Run the full semantic analysis pipeline."""
    logger.info(f"Starting semantic analysis with batch size: {batch_size}")
    
    # Validate batch size against FR-008 constraint
    if batch_size < FR008_BATCH_SIZE_LIMIT:
        deviation_msg = f"Batch size < 50 (actual: {batch_size}) due to Plan constraint"
        logger.warning(deviation_msg)
        
        # Record this deviation in resource metrics
        metrics = {
            "batch_size": batch_size,
            "fr008_limit": FR008_BATCH_SIZE_LIMIT,
            "deviation": deviation_msg,
            "timestamp": time.time()
        }
        
        # Load existing metrics if present
        if os.path.exists(RESOURCE_METRICS_PATH):
            with open(RESOURCE_METRICS_PATH, 'r') as f:
                existing_metrics = json.load(f)
            if isinstance(existing_metrics, list):
                existing_metrics.append(metrics)
            else:
                existing_metrics = [metrics]
        else:
            existing_metrics = [metrics]
        
        save_metrics_to_file(existing_metrics, RESOURCE_METRICS_PATH)
        logger.info(f"Recorded batch size deviation to {RESOURCE_METRICS_PATH}")
    
    results = []
    total_functions = len(baseline_df)
    
    for i in range(0, total_functions, batch_size):
        batch_end = min(i + batch_size, total_functions)
        batch_df = baseline_df.iloc[i:batch_end]
        
        logger.info(f"Processing batch {i//batch_size + 1}: functions {i+1} to {batch_end}")
        
        # Record metrics for this batch
        batch_start_time = time.time()
        batch_ram_before = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        batch_results = []
        for _, row in batch_df.iterrows():
            code = row['code']
            
            # Check context window
            exceeds, token_count = check_context_window(code)
            if exceeds:
                logger.warning(f"Function exceeds context window ({token_count} tokens). Truncating...")
                code = truncate_text(code)
            
            # Compute embedding
            embedding = compute_embeddings(embedding_model, [code])[0]
            
            # Run LLM inference
            prompt = prompt_template.format(code=code)
            try:
                llm_output = run_llm_inference(llm_model, prompt)
                smells = parse_llm_output(llm_output)
            except Exception as e:
                logger.error(f"LLM inference failed: {e}")
                smells = ["Unparseable"]
            
            batch_results.append({
                "code": code,
                "embedding": embedding.tolist(),
                "llm_labels": smells,
                "static_labels": row.get('static_smell_labels', '')
            })
            
            # Garbage collection between functions
            if i % 5 == 0:  # Every 5th function in batch
                gc.collect()
        
        batch_ram_after = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        batch_time = time.time() - batch_start_time
        
        # Record batch metrics
        batch_metrics = {
            "batch_index": i // batch_size,
            "batch_size": len(batch_results),
            "ram_usage_mb": (batch_ram_before + batch_ram_after) / 2,
            "inference_time_seconds": batch_time,
            "timestamp": time.time()
        }
        save_metrics_to_file([batch_metrics], RESOURCE_METRICS_PATH, append=True)
        
        results.extend(batch_results)
        
        # Force garbage collection after each batch
        gc.collect()
    
    logger.info(f"Semantic analysis complete. Processed {len(results)} functions.")
    return {"results": results}

def main():
    """Main entry point for semantic analysis."""
    logger.info("Starting semantic analysis pipeline")
    
    # Load models
    embedding_model = load_embeddings_model()
    
    # Load LLM model (adjust path as needed)
    # Note: This path should be updated to point to the actual downloaded model
    model_path = "models/codellama-7b-instruct.Q4_K_M.gguf"
    if not os.path.exists(model_path):
        logger.error(f"Model not found at {model_path}. Please download the 4-bit quantized model first.")
        return
    
    llm_model = load_llama_model(model_path)
    
    # Load prompt template
    prompt_path = "contracts/llm_prompt.txt"
    prompt_template = load_prompt_template(prompt_path)
    
    # Load baseline data
    baseline_df = load_baseline_data()
    
    # Run semantic analysis
    analysis_results = run_semantic_analysis(
        baseline_df=baseline_df,
        llm_model=llm_model,
        embedding_model=embedding_model,
        prompt_template=prompt_template,
        batch_size=LLM_BATCH_SIZE_MAX
    )
    
    # Save results
    output_path = get_processed_path("semantic_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    logger.info("Semantic analysis pipeline complete")

if __name__ == "__main__":
    main()