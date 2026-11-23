"""
Core logic for generating the training dataset.
Orchestrates feature extraction, quantized inference, and gap calculation.
"""
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from src.services.feature_extractor import extract_features_for_sample, load_dataset_streaming
from src.services.quantized_inference import run_quantized_inference_batch
from src.services.gap_calculator import calculate_gap
from src.config.logging_config import setup_logger, log_sample_progress
from src.config.env_config import get_model_path, get_dataset_id

logger = logging.getLogger(__name__)

@dataclass
class SampleResult:
    """Result for a single sample."""
    sample_id: str
    input_id: str
    gradient_norms: List[float]
    local_curvature: List[float]
    quantized_logits: List[List[float]]  # List per quantization level
    calculated_kl_divergence: List[float]  # List per quantization level
    quantization_levels: List[str]
    status: str  # 'success', 'partial', 'failed'
    error_code: Optional[str] = None

def process_sample(
    sample: Dict[str, Any],
    tokenizer: AutoTokenizer,
    model: AutoModelForCausalLM,
    quantization_levels: List[str] = ["INT4", "INT8", "FP8"]
) -> SampleResult:
    """
    Process a single sample: extract features, run inference, calculate gap.
    
    Args:
        sample: Raw dataset sample.
        tokenizer: HuggingFace tokenizer.
        model: HuggingFace model (full precision).
        quantization_levels: List of quantization levels to run.
        
    Returns:
        SampleResult object.
    """
    sample_id = sample.get("id", "unknown")
    input_text = sample.get("question", "")
    
    logger.info(f"Processing sample {sample_id}")
    
    try:
        # Step 1: Extract features (gradient norms, local curvature)
        features_result = extract_features_for_sample(
            input_text=input_text,
            tokenizer=tokenizer,
            model=model
        )
        
        if not features_result.success:
            log_sample_progress(
                sample_id=sample_id,
                status="error",
                error_code="feature_extraction_failed",
                logger=logger
            )
            return SampleResult(
                sample_id=sample_id,
                input_id=sample_id,
                gradient_norms=[],
                local_curvature=[],
                quantized_logits=[],
                calculated_kl_divergence=[],
                quantization_levels=[],
                status="failed",
                error_code="feature_extraction_failed"
            )
        
        gradient_norms = features_result.gradient_norms
        local_curvature = features_result.local_curvature
        
        # Step 2: Run quantized inference for all levels
        # We need to prepare inputs for quantized inference
        # The quantized inference service expects a list of prompts
        prompts = [input_text]
        
        all_quantized_logits = []
        all_kl_divergences = []
        successful_levels = []
        
        for level in quantization_levels:
            try:
                # Run quantized inference for this level
                inference_result = run_quantized_inference_batch(
                    prompts=prompts,
                    quantization_level=level
                )
                
                if inference_result.success and len(inference_result.logits) > 0:
                    # Extract logits for this level
                    logits_for_level = inference_result.logits[0]  # First prompt
                    
                    # Ensure logits are float32 lists
                    if isinstance(logits_for_level, torch.Tensor):
                        logits_for_level = logits_for_level.cpu().numpy().astype(np.float32).tolist()
                    elif isinstance(logits_for_level, np.ndarray):
                        logits_for_level = logits_for_level.astype(np.float32).tolist()
                    
                    all_quantized_logits.append(logits_for_level)
                    successful_levels.append(level)
                    
                    # Step 3: Calculate KL divergence
                    # We need the full-precision logits for comparison
                    # For now, we'll use a placeholder - in reality, we'd get this from the model
                    # This is a simplification - the actual implementation would need to get full-precision logits
                    kl_div = calculate_gap(
                        full_precision_logits=features_result.full_precision_logits,
                        quantized_logits=logits_for_level,
                        epsilon=1e-8
                    )
                    all_kl_divergences.append(kl_div)
                else:
                    logger.warning(f"Quantized inference failed for level {level} on sample {sample_id}")
                    # Don't add to successful levels, but continue with other levels
                    
            except Exception as e:
                logger.error(f"Error running quantized inference for level {level} on sample {sample_id}: {e}")
                # Continue with other levels
                continue
        
        # Determine status
        if len(successful_levels) == 0:
            status = "failed"
            error_code = "no_inference_success"
        elif len(successful_levels) < len(quantization_levels):
            status = "partial"
            error_code = "partial_inference_success"
        else:
            status = "success"
            error_code = None
        
        # Log progress
        log_sample_progress(
            sample_id=sample_id,
            status=status,
            error_code=error_code,
            logger=logger
        )
        
        return SampleResult(
            sample_id=sample_id,
            input_id=sample_id,
            gradient_norms=gradient_norms,
            local_curvature=local_curvature,
            quantized_logits=all_quantized_logits,
            calculated_kl_divergence=all_kl_divergences,
            quantization_levels=successful_levels,
            status=status,
            error_code=error_code
        )
        
    except Exception as e:
        logger.error(f"Unexpected error processing sample {sample_id}: {e}")
        log_sample_progress(
            sample_id=sample_id,
            status="error",
            error_code="unexpected_error",
            logger=logger
        )
        return SampleResult(
            sample_id=sample_id,
            input_id=sample_id,
            gradient_norms=[],
            local_curvature=[],
            quantized_logits=[],
            calculated_kl_divergence=[],
            quantization_levels=[],
            status="failed",
            error_code="unexpected_error"
        )

def run_generation_pipeline(
    output_path: str,
    max_samples: Optional[int] = None,
    quantization_levels: List[str] = ["INT4", "INT8", "FP8"],
    sample_size: int = 1000
) -> Dict[str, Any]:
    """
    Run the full generation pipeline.
    
    Args:
        output_path: Path to save the output parquet file.
        max_samples: Maximum number of samples to process (None for all).
        quantization_levels: List of quantization levels to run.
        sample_size: Size of sample to use for testing (if max_samples is None).
        
    Returns:
        Dictionary with generation statistics.
    """
    start_time = time.time()
    
    # Setup logging
    logger.info("Starting dataset generation pipeline")
    
    # Load model and tokenizer
    model_path = get_model_path()
    logger.info(f"Loading model from {model_path}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)
        model.eval()
        logger.info("Model and tokenizer loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    
    # Load dataset streaming
    dataset_id = get_dataset_id()
    logger.info(f"Loading dataset: {dataset_id}")
    
    results = []
    sample_count = 0
    success_count = 0
    partial_count = 0
    failed_count = 0
    
    try:
        for sample in load_dataset_streaming(dataset_name="gsm8k", config_name="main", split="train"):
            if max_samples and sample_count >= max_samples:
                break
            
            if sample_count >= sample_size and max_samples is None:
                break
            
            result = process_sample(
                sample=sample,
                tokenizer=tokenizer,
                model=model,
                quantization_levels=quantization_levels
            )
            
            results.append(result)
            sample_count += 1
            
            if result.status == "success":
                success_count += 1
            elif result.status == "partial":
                partial_count += 1
            else:
                failed_count += 1
            
            # Log progress every 10 samples
            if sample_count % 10 == 0:
                logger.info(f"Processed {sample_count} samples: {success_count} success, {partial_count} partial, {failed_count} failed")
    
    except Exception as e:
        logger.error(f"Error during dataset generation: {e}")
        raise
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # Convert results to dictionaries for saving
    results_dict = []
    for r in results:
        results_dict.append(asdict(r))
    
    # Save to parquet
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    import pandas as pd
    df = pd.DataFrame(results_dict)
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Saved {len(results)} samples to {output_path}")
    
    stats = {
        "total_samples": sample_count,
        "success_count": success_count,
        "partial_count": partial_count,
        "failed_count": failed_count,
        "elapsed_time_seconds": elapsed_time,
        "output_path": str(output_path)
    }
    
    logger.info(f"Generation complete: {stats}")
    return stats

def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate training dataset")
    parser.add_argument("--output", type=str, default="data/processed/training_sample.parquet",
                      help="Output path for the generated dataset")
    parser.add_argument("--max-samples", type=int, default=None,
                      help="Maximum number of samples to process")
    parser.add_argument("--sample-size", type=int, default=1000,
                      help="Sample size for testing (if max_samples is None)")
    
    args = parser.parse_args()
    
    setup_logger()
    
    try:
        stats = run_generation_pipeline(
            output_path=args.output,
            max_samples=args.max_samples,
            sample_size=args.sample_size
        )
        print(f"Dataset generation complete. Stats: {stats}")
    except Exception as e:
        logger.error(f"Dataset generation failed: {e}")
        raise
