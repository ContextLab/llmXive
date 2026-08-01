"""
LLM Inference Engine for llmXive pipeline.

Runs frozen LLM inference (Mistral-7B primary, TinyLlama fallback)
with retry logic, n-gram normalization, and OOM handling.
"""
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import torch
import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
import kenlm
import numpy as np

from config import get_project_root, load_environment, get_config
from utils.logging import get_logger, OOMError, TimeoutError, PipelineError, retry_on_transient_errors
from utils.timeout import enforce_timeout
from data.ngram import load_code_chunks

# Configure logging
logger = get_logger(__name__)

# Constants
PRIMARY_MODEL_NAME = "mistralai/Mistral-7B-v0.1"
FALLBACK_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
MAX_RETRIES = 3
BACKOFF_FACTOR = 2
CHUNK_TIMEOUT_SECONDS = 300  # Per-chunk timeout
MAX_MEMORY_GB = 6.0

@dataclass
class InferenceResult:
    chunk_id: str
    language: str
    token_loss: float
    entropy: float
    normalized_loss: float
    status: str
    error_message: Optional[str] = None

def load_model(model_name: str, device: str = "cpu") -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load a frozen LLM model with memory constraints.
    
    Args:
        model_name: HuggingFace model identifier
        device: Device to load model to (cpu only)
        
    Returns:
        Tuple of (model, tokenizer)
        
    Raises:
        OOMError: If model fails to load due to memory issues
        PipelineError: If model fails to load for other reasons
    """
    logger.info(f"Loading model: {model_name} on {device}")
    
    try:
        # Set CPU-specific optimizations
        torch.set_num_threads(4)
        torch.set_num_interop_threads(1)
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            pad_token='<pad>',
            padding_side='left'
        )
        
        # Ensure pad token exists
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model with memory-efficient settings
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,  # Use float32 for CPU stability
            device_map="cpu",
            low_cpu_mem_usage=True,
            trust_remote_code=True,
            use_safetensors=True
        )
        
        # Freeze all parameters
        for param in model.parameters():
            param.requires_grad = False
        
        model.eval()
        
        logger.info(f"Successfully loaded {model_name}")
        return model, tokenizer
        
    except RuntimeError as e:
        if "CUDA" in str(e) or "out of memory" in str(e).lower():
            raise OOMError(f"OOM while loading {model_name}: {e}")
        raise PipelineError(f"Failed to load model {model_name}: {e}")
    except Exception as e:
        raise PipelineError(f"Unexpected error loading {model_name}: {e}")

def compute_token_loss(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    text: str,
    chunk_timeout: int = CHUNK_TIMEOUT_SECONDS
) -> Tuple[float, float, List[float]]:
    """
    Compute token-level loss for a given text.
    
    Args:
        model: Loaded LLM model
        tokenizer: Loaded tokenizer
        text: Input text to evaluate
        chunk_timeout: Timeout in seconds for this computation
        
    Returns:
        Tuple of (mean_loss, entropy, list of per-token losses)
    """
    def _compute():
        with torch.no_grad():
            # Tokenize
            inputs = tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=2048
            )
            
            # Move to device (CPU)
            inputs = {k: v for k, v in inputs.items()}
            
            # Forward pass
            outputs = model(**inputs)
            
            # Compute loss per token
            logits = outputs.logits
            labels = inputs['input_ids']
            
            # Shift for next-token prediction
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            
            # Compute log probabilities
            log_probs = torch.nn.functional.log_softmax(shift_logits, dim=-1)
            
            # Get loss for each token (negative log likelihood)
            token_log_probs = log_probs.gather(2, shift_labels.unsqueeze(-1)).squeeze(-1)
            token_losses = -token_log_probs  # Convert to positive loss
            
            # Compute entropy
            probs = torch.softmax(shift_logits, dim=-1)
            entropy = -(probs * log_probs).sum(dim=-1)
            
            # Calculate mean loss and entropy
            valid_mask = shift_labels != tokenizer.pad_token_id
            if valid_mask.sum() > 0:
                mean_loss = token_losses[valid_mask].mean().item()
                mean_entropy = entropy[valid_mask].mean().item()
                token_loss_list = token_losses[valid_mask].tolist()
            else:
                mean_loss = 0.0
                mean_entropy = 0.0
                token_loss_list = []
            
            return mean_loss, mean_entropy, token_loss_list
    
    # Apply timeout
    try:
        return enforce_timeout(_compute, timeout_seconds=chunk_timeout)
    except TimeoutError:
        raise TimeoutError(f"Token computation timed out after {chunk_timeout}s")

def load_kenlm_model(model_path: Path) -> Optional[kenlm.Model]:
    """
    Load a KenLM n-gram model.
    
    Args:
        model_path: Path to .arpa file
        
    Returns:
        Loaded KenLM model or None if not found
    """
    if not model_path.exists():
        logger.warning(f"KenLM model not found: {model_path}")
        return None
    
    try:
        model = kenlm.Model(str(model_path))
        logger.info(f"Loaded KenLM model: {model_path}")
        return model
    except Exception as e:
        logger.error(f"Failed to load KenLM model {model_path}: {e}")
        return None

def compute_ngram_log_prob(kenlm_model: kenlm.Model, text: str) -> float:
    """
    Compute log probability of text using KenLM model.
    
    Args:
        kenlm_model: Loaded KenLM model
        text: Input text
        
    Returns:
        Log probability in nats
    """
    # KenLM returns log probability in log10 by default
    log_prob_log10 = kenlm_model.score(text)
    
    # Convert from log10 to natural log (nats)
    # log_e(x) = log_10(x) * ln(10)
    log_prob_nats = log_prob_log10 * np.log(10)
    
    return log_prob_nats

def normalize_loss(token_loss: float, ngram_log_prob: float) -> float:
    """
    Normalize token loss by subtracting n-gram log probability.
    
    Both values should be in nats.
    
    Args:
        token_loss: Token-level loss from LLM (positive, in nats)
        ngram_log_prob: N-gram log probability (negative, in nats)
        
    Returns:
        Normalized loss
    """
    # token_loss is positive (NLL), ngram_log_prob is negative
    # normalized_loss = token_loss - ngram_log_prob
    return token_loss - ngram_log_prob

@retry_on_transient_errors(max_retries=MAX_RETRIES, backoff_factor=BACKOFF_FACTOR)
def process_chunk(
    chunk: Dict[str, Any],
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    kenlm_model: Optional[kenlm.Model],
    language: str
) -> InferenceResult:
    """
    Process a single code chunk through the inference pipeline.
    
    Args:
        chunk: Code chunk data
        model: Loaded LLM model
        tokenizer: Loaded tokenizer
        kenlm_model: KenLM model for normalization (language-specific)
        language: Programming language of the chunk
        
    Returns:
        InferenceResult with computed metrics
    """
    chunk_id = chunk.get('chunk_id', 'unknown')
    code_text = chunk.get('code', '')
    
    if not code_text.strip():
        return InferenceResult(
            chunk_id=chunk_id,
            language=language,
            token_loss=0.0,
            entropy=0.0,
            normalized_loss=0.0,
            status='skipped',
            error_message='Empty code'
        )
    
    try:
        # Compute token loss with timeout
        token_loss, entropy, _ = compute_token_loss(
            model, tokenizer, code_text, chunk_timeout=CHUNK_TIMEOUT_SECONDS
        )
        
        # Compute n-gram normalization if model available
        normalized_loss = token_loss
        if kenlm_model is not None:
            try:
                ngram_log_prob = compute_ngram_log_prob(kenlm_model, code_text)
                normalized_loss = normalize_loss(token_loss, ngram_log_prob)
            except Exception as e:
                logger.warning(f"KenLM normalization failed for {chunk_id}: {e}")
        
        return InferenceResult(
            chunk_id=chunk_id,
            language=language,
            token_loss=token_loss,
            entropy=entropy,
            normalized_loss=normalized_loss,
            status='success'
        )
        
    except TimeoutError as e:
        logger.error(f"Timeout processing chunk {chunk_id}: {e}")
        return InferenceResult(
            chunk_id=chunk_id,
            language=language,
            token_loss=0.0,
            entropy=0.0,
            normalized_loss=0.0,
            status='timeout',
            error_message=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing chunk {chunk_id}: {e}")
        return InferenceResult(
            chunk_id=chunk_id,
            language=language,
            token_loss=0.0,
            entropy=0.0,
            normalized_loss=0.0,
            status='error',
            error_message=str(e)
        )

def run_inference_pipeline(
    python_chunks_path: Path,
    java_chunks_path: Optional[Path],
    kenlm_python_path: Path,
    kenlm_java_path: Path,
    output_python_path: Path,
    output_java_path: Path,
    use_fallback: bool = True
) -> None:
    """
    Run the complete inference pipeline for Python and Java chunks.
    
    Args:
        python_chunks_path: Path to Python annotated chunks
        java_chunks_path: Path to Java annotated chunks (optional)
        kenlm_python_path: Path to Python KenLM model
        kenlm_java_path: Path to Java KenLM model
        output_python_path: Output path for Python results
        output_java_path: Output path for Java results
        use_fallback: Whether to try fallback model on failure
    """
    # Load KenLM models
    kenlm_python = load_kenlm_model(kenlm_python_path)
    kenlm_java = load_kenlm_model(kenlm_java_path) if java_chunks_path else None
    
    # Try primary model first
    model_name = PRIMARY_MODEL_NAME
    model = None
    tokenizer = None
    
    try:
        model, tokenizer = load_model(model_name)
        logger.info(f"Using primary model: {model_name}")
    except (OOMError, PipelineError) as e:
        logger.warning(f"Primary model failed: {e}")
        if use_fallback:
            logger.info("Attempting fallback model...")
            try:
                model, tokenizer = load_model(FALLBACK_MODEL_NAME)
                model_name = FALLBACK_MODEL_NAME
                logger.info(f"Using fallback model: {model_name}")
                
                # Generate scope reduction report
                scope_report_path = Path("data/results/scope_reduction_report.md")
                with open(scope_report_path, 'w') as f:
                    f.write(f"# Scope Reduction Report\n\n")
                    f.write(f"## Primary Model Failure\n\n")
                    f.write(f"Primary model `{PRIMARY_MODEL_NAME}` failed to load.\n\n")
                    f.write(f"Error: {str(e)}\n\n")
                    f.write(f"## Fallback Activated\n\n")
                    f.write(f"Fallback model `{FALLBACK_MODEL_NAME}` loaded successfully.\n\n")
                    f.write(f"Results may differ from primary model due to architecture differences.\n")
                logger.info(f"Scope reduction report written to {scope_report_path}")
            except Exception as fallback_error:
                logger.error(f"Fallback model also failed: {fallback_error}")
                raise PipelineError("Both primary and fallback models failed to load")
        else:
            raise
    
    if model is None or tokenizer is None:
        raise PipelineError("No model could be loaded")
    
    # Process Python chunks
    if python_chunks_path.exists():
        logger.info(f"Processing Python chunks from {python_chunks_path}")
        python_results = []
        python_chunks = load_code_chunks(python_chunks_path)
        
        for chunk in python_chunks:
            result = process_chunk(
                chunk, model, tokenizer, kenlm_python, "python"
            )
            python_results.append(asdict(result))
        
        # Write Python results
        output_python_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_python_path, 'w') as f:
            for result in python_results:
                f.write(json.dumps(result) + '\n')
        
        logger.info(f"Wrote {len(python_results)} Python results to {output_python_path}")
    else:
        logger.warning(f"Python chunks not found: {python_chunks_path}")
    
    # Process Java chunks if available
    if java_chunks_path and java_chunks_path.exists():
        logger.info(f"Processing Java chunks from {java_chunks_path}")
        java_results = []
        java_chunks = load_code_chunks(java_chunks_path)
        
        for chunk in java_chunks:
            result = process_chunk(
                chunk, model, tokenizer, kenlm_java, "java"
            )
            java_results.append(asdict(result))
        
        # Write Java results
        output_java_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_java_path, 'w') as f:
            for result in java_results:
                f.write(json.dumps(result) + '\n')
        
        logger.info(f"Wrote {len(java_results)} Java results to {output_java_path}")
    else:
        logger.info("No Java chunks to process")

def main():
    """Main entry point for inference engine."""
    load_environment()
    config = get_config()
    project_root = get_project_root()
    
    # Define paths
    python_chunks_path = project_root / "data/processed/annotated_python.jsonl"
    java_chunks_path = project_root / "data/processed/annotated_java.jsonl"
    kenlm_python_path = project_root / "data/processed/kenlm_model_python.arpa"
    kenlm_java_path = project_root / "data/processed/kenlm_model_java.arpa"
    output_python_path = project_root / "data/processed/inference_results_python.jsonl"
    output_java_path = project_root / "data/processed/inference_results_java.jsonl"
    
    logger.info("Starting inference pipeline...")
    logger.info(f"Project root: {project_root}")
    
    try:
        run_inference_pipeline(
            python_chunks_path=python_chunks_path,
            java_chunks_path=java_chunks_path,
            kenlm_python_path=kenlm_python_path,
            kenlm_java_path=kenlm_java_path,
            output_python_path=output_python_path,
            output_java_path=output_java_path,
            use_fallback=True
        )
        logger.info("Inference pipeline completed successfully")
    except Exception as e:
        logger.error(f"Inference pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()