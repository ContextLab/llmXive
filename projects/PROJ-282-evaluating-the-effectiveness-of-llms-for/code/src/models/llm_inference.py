import os
import sys
import time
import gc
import json
import re
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

# Import local project modules based on API surface
from src.utils.config import get_config, get_runtime_limits, InferenceConfig
from src.utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_failure
from src.models.code_snippet import CodeSnippet
from src.models.prediction_result import PredictionResult, create_prediction_result
from src.utils.memory_monitor import MemoryMonitor

# Configure logger for this module
logger = get_logger(__name__)

# Constants for response mapping
UNCERTAIN_PATTERNS = [
    r"\bmaybe\b", r"\bunclear\b", r"\bpossibly\b", r"\blikely\b",
    r"\bunknown error\b", r"\berror\b", r"\bnot sure\b", r"\binconclusive\b"
]
UNCERTAIN_REGEX = re.compile("|".join(UNCERTAIN_PATTERNS), re.IGNORECASE)

VULNERABILITY_MAPPINGS = {
    r"\bsql injection\b": "SQLi",
    r"\bsqli\b": "SQLi",
    r"\bbuffer overflow\b": "Buffer Overflow",
    r"\boverflow\b": "Buffer Overflow",
    r"\brace condition\b": "Race Condition",
    r"\bxss\b": "XSS",
    r"\bcommand injection\b": "Command Injection",
    r"\bpath traversal\b": "Path Traversal",
    r"\bnone\b": "none",
    r"\bno vulnerability\b": "none",
    r"\bno\s*vuln\b": "none"
}

# Combined regex for efficient matching
VULNERABILITY_REGEX = re.compile("|".join(VULNERABILITY_MAPPINGS.keys()), re.IGNORECASE)

class InferenceConfig:
    """Configuration for LLM inference parameters."""
    def __init__(self, model_name: str, max_context_tokens: int, batch_size: int):
        self.model_name = model_name
        self.max_context_tokens = max_context_tokens
        self.batch_size = batch_size

def get_available_ram_gb() -> float:
    """Estimate available RAM in GB (simplified implementation)."""
    # In a real implementation, this would use psutil or /proc/meminfo
    # For now, return a safe default
    return 16.0

def check_memory_constraint(required_gb: float) -> bool:
    """Check if system has enough memory."""
    available = get_available_ram_gb()
    if available < required_gb:
        logger.warning(f"Memory constraint check failed: Required {required_gb}GB, Available {available}GB")
        return False
    return True

def load_model_4bit_cpu(model_name: str):
    """Load model in 4-bit quantization on CPU."""
    logger.info(f"Loading model {model_name} in 4-bit quantization on CPU")
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        import torch

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True
        )

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=quantization_config,
            device_map="cpu",
            torch_dtype=torch.float16
        )
        logger.info(f"Model {model_name} loaded successfully")
        return model, tokenizer
    except ImportError as e:
        logger.error(f"Failed to import required libraries: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def parse_llm_response(response_text: str) -> Tuple[str, float]:
    """
    Parse LLM free-text response into structured label and confidence.
    Maps ambiguous responses to 'uncertain'.
    Handles context window truncation events.
    
    Args:
        response_text: Raw text from LLM response
        
    Returns:
        Tuple of (mapped_label, confidence_score)
    """
    response_text = response_text.strip()
    
    # Check for truncation event indicators
    if "truncated" in response_text.lower() or "context window" in response_text.lower():
        logger.warning("Detected context window truncation event in response")
        return "uncertain", 0.0

    # Check for uncertain patterns first
    if UNCERTAIN_REGEX.search(response_text):
        logger.debug(f"Mapped ambiguous response to 'uncertain': {response_text[:50]}...")
        return "uncertain", 0.0

    # Try to map to known vulnerability categories
    match = VULNERABILITY_REGEX.search(response_text)
    if match:
        matched_text = match.group(0)
        for pattern, label in VULNERABILITY_MAPPINGS.items():
            if re.match(pattern, matched_text, re.IGNORECASE):
                logger.debug(f"Mapped response to {label}")
                return label, 0.8  # Default confidence for mapped responses

    # If no match found, treat as uncertain
    logger.debug(f"Could not map response, defaulting to 'uncertain': {response_text[:50]}...")
    return "uncertain", 0.0

def handle_context_truncation(code_snippet: str, max_tokens: int) -> Tuple[str, bool]:
    """
    Truncate code snippet if it exceeds context window and log the event.
    
    Args:
        code_snippet: Original code
        max_tokens: Maximum allowed tokens
        
    Returns:
        Tuple of (truncated_code, was_truncated)
    """
    # Simple token estimation: 1 token ≈ 4 characters for code
    estimated_tokens = len(code_snippet) // 4
    
    if estimated_tokens > max_tokens:
        logger.warning(f"Context window truncation triggered: {estimated_tokens} tokens > {max_tokens} limit")
        # Truncate from the end (preserving beginning which often has context)
        max_chars = max_tokens * 4
        truncated_code = code_snippet[:max_chars] + "\n... [TRUNCATED]"
        return truncated_code, True
    
    return code_snippet, False

def run_inference_batch(
    model,
    tokenizer,
    snippets: List[CodeSnippet],
    config: InferenceConfig,
    memory_monitor: Optional[MemoryMonitor] = None
) -> List[PredictionResult]:
    """
    Run zero-shot inference on a batch of code snippets.
    Implements context window truncation and ambiguous response handling.
    
    Args:
        model: Loaded LLM model
        tokenizer: Model tokenizer
        snippets: List of CodeSnippet objects
        config: Inference configuration
        memory_monitor: Optional memory monitor for dynamic batch adjustment
        
    Returns:
        List of PredictionResult objects
    """
    results = []
    prompt_template = "Identify any security vulnerability in the following code: {code}"
    
    for i, snippet in enumerate(snippets):
        start_time = time.time()
        
        # Check memory constraints if monitor is provided
        if memory_monitor:
            mem_usage = memory_monitor.get_memory_usage_gb()
            if mem_usage > 0.9 * get_runtime_limits().ram_limit_gb:
                logger.warning(f"Memory usage high ({mem_usage}GB). Reducing batch size or pausing.")
                # In a real implementation, we would adjust batch size here
                gc.collect()
        
        # Handle context window truncation
        processed_code, was_truncated = handle_context_truncation(
            snippet.code, 
            config.max_context_tokens
        )
        
        if was_truncated:
            # Log truncation event as required by task
            truncation_event = {
                "snippet_id": snippet.snippet_id,
                "original_length": len(snippet.code),
                "truncated_length": len(processed_code),
                "timestamp": datetime.now().isoformat(),
                "reason": "context_window_exceeded"
            }
            logger.info(f"Truncation event logged: {json.dumps(truncation_event)}")
        
        # Construct prompt
        prompt = prompt_template.format(code=processed_code)
        
        # Generate response (simplified - in reality would use model.generate)
        try:
            inputs = tokenizer(prompt, return_tensors="pt")
            # Limit generation length to prevent excessive output
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                temperature=0.1,
                do_sample=False
            )
            response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the generated part (after the prompt)
            if prompt in response_text:
                response_text = response_text.split(prompt, 1)[1].strip()
            
        except Exception as e:
            logger.error(f"Inference failed for snippet {snippet.snippet_id}: {e}")
            response_text = "unknown error"
        
        # Parse response with robust handling
        predicted_label, confidence = parse_llm_response(response_text)
        
        # Calculate inference time
        inference_time = time.time() - start_time
        logger.debug(f"Inference time for snippet {snippet.snippet_id}: {inference_time:.2f}s")
        
        # Create prediction result
        result = create_prediction_result(
            snippet_id=snippet.snippet_id,
            predicted_label=predicted_label,
            confidence=confidence,
            inference_time=inference_time,
            is_correct=None  # Will be determined later against ground truth
        )
        
        results.append(result)
        
        # Log progress
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(snippets)} snippets")
    
    return results

def process_snippets_zero_shot(
    snippets: List[CodeSnippet],
    model_name: str,
    max_context_tokens: int = 2048,
    batch_size: int = 1
) -> List[PredictionResult]:
    """
    Main entry point for zero-shot vulnerability detection.
    Orchestrates model loading, batch processing, and result collection.
    
    Args:
        snippets: List of code snippets to analyze
        model_name: HuggingFace model identifier
        max_context_tokens: Maximum tokens for context window
        batch_size: Number of snippets to process in parallel
        
    Returns:
        List of PredictionResult objects
    """
    log_stage_start("Zero-Shot LLM Inference")
    
    try:
        # Load model
        model, tokenizer = load_model_4bit_cpu(model_name)
        
        # Initialize memory monitor
        memory_monitor = MemoryMonitor()
        
        # Create inference config
        config = InferenceConfig(
            model_name=model_name,
            max_context_tokens=max_context_tokens,
            batch_size=batch_size
        )
        
        # Process in batches
        all_results = []
        for i in range(0, len(snippets), batch_size):
            batch = snippets[i:i + batch_size]
            batch_results = run_inference_batch(model, tokenizer, batch, config, memory_monitor)
            all_results.extend(batch_results)
            
            # Force garbage collection between batches
            gc.collect()
        
        log_stage_complete("Zero-Shot LLM Inference", len(all_results))
        return all_results
        
    except Exception as e:
        log_stage_failure("Zero-Shot LLM Inference", str(e))
        raise

def main():
    """Main entry point for standalone execution."""
    logger.info("Starting LLM Inference Module")
    
    # Load configuration
    config = get_config()
    inference_config = get_inference_params()
    
    # Example usage (would be replaced by actual data loading in pipeline)
    # snippets = load_snippets_from_csv("data/processed/snippets.csv")
    # results = process_snippets_zero_shot(
    #     snippets,
    #     model_name=inference_config.model_name,
    #     max_context_tokens=inference_config.max_context_tokens
    # )
    
    logger.info("LLM Inference Module ready for integration")

if __name__ == "__main__":
    main()
