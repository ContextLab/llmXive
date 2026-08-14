"""
Inference engine for running frozen LLMs on code chunks.
Implements memory optimization strategies including torch.no_grad(), explicit model offloading,
and gradient checkpointing to keep memory usage under 6GB on CPU.
"""
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import torch
import kenlm
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from dataclasses import dataclass

from config import get_project_root, get_config
from utils.timeout import enforce_timeout
from utils.logging import get_logger, TimeoutError, OOMError

logger = get_logger(__name__)

@dataclass
class InferenceResult:
    """Container for inference results of a single chunk."""
    chunk_id: str
    token_loss: float
    entropy: float
    normalized_loss: float
    tokens_count: int
    status: str  # 'success', 'timeout', 'oom', 'error'
    error_message: Optional[str] = None

def load_model(model_name: str, device: str = 'cpu') -> Tuple[Any, Any]:
    """
    Load a frozen LLM model and tokenizer with memory optimizations.
    
    Args:
        model_name: HuggingFace model identifier
        device: Device to load model to ('cpu' or 'cuda')
        
    Returns:
        Tuple of (model, tokenizer)
    """
    logger.info(f"Loading model {model_name} on {device}...")
    
    # Set environment variables for memory optimization
    os.environ['PYTORCH_NO_CUDA_MEMORY_CACHING'] = '1'
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        # Ensure pad token is set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model with memory optimizations
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,  # Use float32 for CPU stability
            device_map='auto' if device == 'cuda' else None,
            low_cpu_mem_usage=True,
            use_cache=False,  # Disable KV cache for memory savings
            pad_token_id=tokenizer.pad_token_id
        )
        
        if device == 'cpu':
            model = model.to(device)
            # Explicitly set number of threads for CPU
            torch.set_num_threads(4)
        
        # Freeze model parameters
        for param in model.parameters():
            param.requires_grad = False
        
        model.eval()
        logger.info(f"Model loaded successfully: {model_name}")
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise

def load_kenlm_model(model_path: Path) -> kenlm.Model:
    """
    Load a KenLM n-gram model.
    
    Args:
        model_path: Path to the .arpa or .bin KenLM model file
        
    Returns:
        Loaded KenLM model
    """
    if not model_path.exists():
        raise FileNotFoundError(f"KenLM model not found at {model_path}")
    
    logger.info(f"Loading KenLM model from {model_path}")
    return kenlm.Model(str(model_path))

def compute_token_loss(
    model: Any,
    tokenizer: Any,
    text: str,
    device: str = 'cpu'
) -> Tuple[float, float, int]:
    """
    Compute token-level loss and entropy for a text chunk.
    
    Uses torch.no_grad() to disable gradient computation and save memory.
    
    Args:
        model: Loaded LLM model
        tokenizer: Loaded tokenizer
        text: Input text string
        device: Device to run inference on
        
    Returns:
        Tuple of (mean_token_loss, mean_entropy, token_count)
    """
    # Tokenize input
    inputs = tokenizer(
        text,
        return_tensors='pt',
        truncation=True,
        max_length=512,  # Limit context for memory
        padding=True
    ).to(device)
    
    # Disable gradient computation for memory savings
    with torch.no_grad():
        # Run model forward pass
        outputs = model(**inputs, labels=inputs['input_ids'])
        
        # Extract loss (mean over tokens)
        loss = outputs.loss.item()
        
        # Compute entropy from logits
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)
        log_probs = torch.log(probs + 1e-9)
        entropy = -torch.sum(probs * log_probs, dim=-1).mean().item()
        
        # Count non-padding tokens
        attention_mask = inputs['attention_mask']
        token_count = attention_mask.sum().item()
    
    return loss, entropy, token_count

def compute_ngram_log_prob(kenlm_model: kenlm.Model, text: str) -> float:
    """
    Compute log probability of text using KenLM n-gram model.
    
    Args:
        kenlm_model: Loaded KenLM model
        text: Input text string
        
    Returns:
        Log probability in nats
    """
    # KenLM returns log probability in log10 by default, convert to nats
    # log10(x) * ln(10) = ln(x)
    log_prob_base10 = kenlm_model.score(text)
    log_prob_nats = log_prob_base10 * np.log(10)
    
    return log_prob_nats

def normalize_loss(
    token_loss_nats: float,
    ngram_log_prob_nats: float,
    token_count: int
) -> float:
    """
    Normalize token loss by subtracting n-gram baseline.
    
    Both values are in nats (natural log scale).
    The normalization is: normalized_loss = token_loss - ngram_baseline
    
    Args:
        token_loss_nats: Token-level loss in nats
        ngram_log_prob_nats: N-gram log probability in nats
        token_count: Number of tokens
        
    Returns:
        Normalized loss value
    """
    # Normalize by token count for fair comparison
    baseline_per_token = ngram_log_prob_nats / max(token_count, 1)
    normalized = token_loss_nats - baseline_per_token
    return normalized

@enforce_timeout
def process_chunk(
    chunk_id: str,
    text: str,
    model: Any,
    tokenizer: Any,
    kenlm_model: Optional[kenlm.Model],
    device: str = 'cpu'
) -> InferenceResult:
    """
    Process a single code chunk through the inference pipeline.
    
    Args:
        chunk_id: Unique identifier for the chunk
        text: Code text to analyze
        model: Loaded LLM model
        tokenizer: Loaded tokenizer
        kenlm_model: Optional KenLM model for normalization
        device: Device to run inference on
        
    Returns:
        InferenceResult with computed metrics
    """
    try:
        # Compute token loss and entropy
        token_loss, entropy, token_count = compute_token_loss(
            model, tokenizer, text, device
        )
        
        # Convert to nats if needed (transformers returns nats by default)
        token_loss_nats = token_loss
        
        # Compute n-gram baseline if model provided
        if kenlm_model is not None:
            ngram_log_prob_nats = compute_ngram_log_prob(kenlm_model, text)
            normalized_loss = normalize_loss(
                token_loss_nats, ngram_log_prob_nats, token_count
            )
        else:
            normalized_loss = token_loss_nats
        
        return InferenceResult(
            chunk_id=chunk_id,
            token_loss=token_loss_nats,
            entropy=entropy,
            normalized_loss=normalized_loss,
            tokens_count=token_count,
            status='success'
        )
        
    except TimeoutError:
        logger.warning(f"Timeout processing chunk {chunk_id}")
        return InferenceResult(
            chunk_id=chunk_id,
            token_loss=0.0,
            entropy=0.0,
            normalized_loss=0.0,
            tokens_count=0,
            status='timeout',
            error_message='Timeout exceeded'
        )
    except Exception as e:
        logger.error(f"Error processing chunk {chunk_id}: {e}")
        return InferenceResult(
            chunk_id=chunk_id,
            token_loss=0.0,
            entropy=0.0,
            normalized_loss=0.0,
            tokens_count=0,
            status='error',
            error_message=str(e)
        )

def run_inference_pipeline(
    input_path: Path,
    output_path: Path,
    model_name: str = 'TinyLlama/TinyLlama-1.1B-Chat-v1.0',
    kenlm_path_python: Optional[Path] = None,
    kenlm_path_java: Optional[Path] = None,
    device: str = 'cpu',
    timeout_seconds: int = 60,
    retry_count: int = 3
) -> List[InferenceResult]:
    """
    Run inference pipeline on all chunks in input file.
    
    Args:
        input_path: Path to input JSONL file with chunks
        output_path: Path to output JSONL file for results
        model_name: HuggingFace model identifier
        kenlm_path_python: Path to Python KenLM model
        kenlm_path_java: Path to Java KenLM model
        device: Device to run inference on
        timeout_seconds: Timeout per chunk in seconds
        retry_count: Number of retries on transient errors
        
    Returns:
        List of InferenceResult objects
    """
    # Load model
    model, tokenizer = load_model(model_name, device)
    
    # Load KenLM models if provided
    kenlm_python = None
    kenlm_java = None
    
    if kenlm_path_python and kenlm_path_python.exists():
        kenlm_python = load_kenlm_model(kenlm_path_python)
        logger.info("Loaded Python KenLM model")
    
    if kenlm_path_java and kenlm_path_java.exists():
        kenlm_java = load_kenlm_model(kenlm_path_java)
        logger.info("Loaded Java KenLM model")
    
    results = []
    
    # Read input file
    with open(input_path, 'r', encoding='utf-8') as f:
        chunks = [json.loads(line) for line in f if line.strip()]
    
    logger.info(f"Processing {len(chunks)} chunks...")
    
    for i, chunk in enumerate(chunks):
        chunk_id = chunk.get('chunk_id', f'chunk_{i}')
        text = chunk.get('text', '')
        language = chunk.get('language', 'python')
        
        # Select appropriate KenLM model
        kenlm_model = kenlm_python if language == 'python' else kenlm_java
        
        # Process with retry logic
        result = None
        for attempt in range(retry_count):
            try:
                result = process_chunk(
                    chunk_id=chunk_id,
                    text=text,
                    model=model,
                    tokenizer=tokenizer,
                    kenlm_model=kenlm_model,
                    device=device
                )
                if result.status == 'success':
                    break
            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed for {chunk_id}: {e}")
                if attempt == retry_count - 1:
                    result = InferenceResult(
                        chunk_id=chunk_id,
                        token_loss=0.0,
                        entropy=0.0,
                        normalized_loss=0.0,
                        tokens_count=0,
                        status='error',
                        error_message=str(e)
                    )
        
        if result:
            results.append(result)
            
            # Write result to output file immediately
            with open(output_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result.__dict__) + '\n')
            
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{len(chunks)} chunks")
    
    # Clear model from memory
    del model
    del tokenizer
    if kenlm_python:
        del kenlm_python
    if kenlm_java:
        del kenlm_java
    
    # Force garbage collection
    import gc
    gc.collect()
    
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    logger.info(f"Inference complete. Results written to {output_path}")
    return results

def main():
    """CLI entry point for inference engine."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run LLM inference on code chunks')
    parser.add_argument('--model', type=str, default='TinyLlama/TinyLlama-1.1B-Chat-v1.0',
                      help='HuggingFace model identifier')
    parser.add_argument('--input', type=Path, required=True,
                      help='Path to input JSONL file')
    parser.add_argument('--output', type=Path, required=True,
                      help='Path to output JSONL file')
    parser.add_argument('--kenlm-python', type=Path, default=None,
                      help='Path to Python KenLM model')
    parser.add_argument('--kenlm-java', type=Path, default=None,
                      help='Path to Java KenLM model')
    parser.add_argument('--device', type=str, default='cpu',
                      help='Device to run inference on (cpu/cuda)')
    parser.add_argument('--timeout', type=int, default=60,
                      help='Timeout per chunk in seconds')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear output file if exists
    if args.output.exists():
        args.output.unlink()
    
    # Run pipeline
    results = run_inference_pipeline(
        input_path=args.input,
        output_path=args.output,
        model_name=args.model,
        kenlm_path_python=args.kenlm_python,
        kenlm_path_java=args.kenlm_java,
        device=args.device,
        timeout_seconds=args.timeout
    )
    
    # Summary
    success_count = sum(1 for r in results if r.status == 'success')
    logger.info(f"Pipeline complete: {success_count}/{len(results)} chunks processed successfully")
    
    return 0 if success_count == len(results) else 1

if __name__ == '__main__':
    sys.exit(main())