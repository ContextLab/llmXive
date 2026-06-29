"""
Model metrics computation for code duplication analysis.

This module handles loading quantized LLM models and computing perplexity scores
for code segments. It implements 8-bit quantization via bitsandbytes for memory
efficiency while maintaining numerical stability.

Per Constitution Principle III (Data Hygiene): Validates all perplexity values
for NaN/inf and logs parse failures appropriately.
"""

import logging
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from bitsandbytes.nn import Int8Params

# Import from project config
from config import (
    get_model_name,
    get_quantization_bits,
    get_random_seed,
    get_memory_limit_mb,
)

# Import logging utilities
from parse_failure_logger import log_parse_failure, get_parse_failures_path

# Set random seed for reproducibility
torch.manual_seed(get_random_seed())
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(get_random_seed())

# Configure logging
logger = logging.getLogger(__name__)

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Configure logging for model metrics computation.
    
    Args:
        log_file: Optional path to log file. If None, logs to stderr.
    
    Returns:
        Configured logger instance.
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    if log_file:
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[logging.StreamHandler(sys.stdout)]
        )
    
    return logger

def load_model_and_tokenizer(
    model_name: Optional[str] = None,
    quantization_bits: int = 8,
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
) -> Tuple[Any, Any]:
    """
    Load model and tokenizer for perplexity computation.
    
    Args:
        model_name: Name of the HuggingFace model to load. Defaults to config.
        quantization_bits: Bits for quantization (8 for 8-bit quantization).
        device: Device to load model on.
    
    Returns:
        Tuple of (model, tokenizer).
    
    Raises:
        ValueError: If model loading fails.
    """
    if model_name is None:
        model_name = get_model_name()
    
    logger.info(f"Loading model: {model_name}")
    logger.info(f"Quantization: {quantization_bits}-bit")
    logger.info(f"Device: {device}")
    
    try:
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            padding_side='left'
        )
        
        # Set pad token if not set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model with 8-bit quantization
        if quantization_bits == 8 and device == "cuda":
            try:
                from transformers import BitsAndBytesConfig
                
                bnb_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    llm_int8_threshold=6.0,
                    llm_int8_skip_modules=["lm_head"],
                    llm_int8_enable_fp32_cpu_offload=False,
                )
                
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    quantization_config=bnb_config,
                    device_map="auto",
                    trust_remote_code=True,
                    torch_dtype=torch.float16,
                )
            except ImportError as e:
                logger.warning(f"bitsandbytes not available, falling back to standard loading: {e}")
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    device_map="auto",
                    trust_remote_code=True,
                    torch_dtype=torch.float16,
                )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto" if device == "cuda" else None,
                trust_remote_code=True,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            )
        
        model.eval()
        logger.info(f"Model loaded successfully: {model_name}")
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise ValueError(f"Model loading failed: {e}")

def load_model_8bit(
    model_name: Optional[str] = None,
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
) -> Any:
    """
    Convenience wrapper to load model in 8-bit quantization.
    
    Args:
        model_name: Model name from config if None.
        device: Device to load on.
    
    Returns:
        Loaded model in 8-bit quantization.
    """
    model, _ = load_model_and_tokenizer(
        model_name=model_name,
        quantization_bits=8,
        device=device
    )
    return model

def validate_perplexity(perplexity: float) -> bool:
    """
    Validate that perplexity value is valid (not NaN or infinite).
    
    Per Constitution Principle III (Data Hygiene): All metrics must be validated.
    
    Args:
        perplexity: Perplexity value to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    if math.isnan(perplexity) or math.isinf(perplexity):
        return False
    if perplexity < 0:
        return False
    return True

def compute_perplexity(
    model: Any,
    tokenizer: Any,
    text: str,
    max_length: int = 512,
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
) -> float:
    """
    Compute perplexity for a single text segment.
    
    Args:
        model: Loaded transformer model.
        tokenizer: Corresponding tokenizer.
        text: Text/code segment to compute perplexity for.
        max_length: Maximum sequence length.
        device: Device to use for computation.
    
    Returns:
        Perplexity score (exp of cross-entropy loss).
    """
    try:
        # Tokenize input
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
            padding=True
        )
        
        # Move to device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Compute loss
        with torch.no_grad():
            outputs = model(**inputs, labels=inputs["input_ids"])
            loss = outputs.loss
            
        # Convert loss to perplexity
        perplexity = math.exp(loss.item())
        
        # Validate result
        if not validate_perplexity(perplexity):
            logger.warning(f"Invalid perplexity computed: {perplexity}")
            return float('inf')
        
        return perplexity
        
    except Exception as e:
        logger.error(f"Perplexity computation failed: {e}")
        log_parse_failure(
            file_path="model_inference",
            error_type="perplexity_computation_error",
            error_message=str(e),
            context={"text_length": len(text)}
        )
        return float('inf')

def compute_perplexity_batch(
    model: Any,
    tokenizer: Any,
    texts: List[str],
    max_length: int = 512,
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
) -> List[float]:
    """
    Compute perplexity for multiple text segments.
    
    Args:
        model: Loaded transformer model.
        tokenizer: Corresponding tokenizer.
        texts: List of text/code segments.
        max_length: Maximum sequence length per segment.
        device: Device to use for computation.
    
    Returns:
        List of perplexity scores.
    """
    perplexities = []
    
    for i, text in enumerate(texts):
        if not text or len(text.strip()) == 0:
            perplexities.append(float('inf'))
            continue
        
        perplexity = compute_perplexity(
            model, tokenizer, text, max_length, device
        )
        perplexities.append(perplexity)
        
        if i % 10 == 0:
            logger.info(f"Processed {i+1}/{len(texts)} segments")
    
    return perplexities

def save_perplexity_scores(
    scores: List[Dict[str, Any]],
    output_path: Path,
    checksum_manifest_path: Optional[Path] = None
) -> None:
    """
    Save perplexity scores to CSV file.
    
    Args:
        scores: List of dicts with 'file_id', 'segment_id', 'perplexity' keys.
        output_path: Path to output CSV file.
        checksum_manifest_path: Optional path to manifest for checksum recording.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.DataFrame(scores)
    
    # Ensure required columns exist
    required_cols = ['file_id', 'segment_id', 'perplexity']
    for col in required_cols:
        if col not in df.columns:
            df[col] = ''
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(scores)} perplexity scores to {output_path}")
    
    # Record checksum if manifest path provided
    if checksum_manifest_path:
        from checksum_manifest import record_artifact_checksums
        try:
            record_artifact_checksums(
                artifact_path=str(output_path),
                manifest_path=checksum_manifest_path,
                artifact_type="perplexity_scores"
            )
        except Exception as e:
            logger.warning(f"Failed to record checksum: {e}")

def load_input_data(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load input data from CSV file (clone metrics or raw code).
    
    Args:
        input_path: Path to input CSV file.
    
    Returns:
        List of dicts with code segment data.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Handle different input formats
    if 'code' in df.columns:
        # Raw code format
        return df.to_dict('records')
    elif 'clone_density' in df.columns and 'file_id' in df.columns:
        # Clone metrics format - need to load code separately
        return df.to_dict('records')
    else:
        # Try to infer format
        logger.warning(f"Unknown input format, attempting generic load")
        return df.to_dict('records')

def main():
    """
    Main entry point for perplexity computation.
    
    Expected command-line usage:
        python model_metrics.py --input <input_csv> --output <output_csv> [--model <model_name>]
    
    Reads code segments from input CSV, computes perplexity, writes to output CSV.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Compute perplexity scores for code segments"
    )
    parser.add_argument(
        '--input',
        required=True,
        type=Path,
        help='Path to input CSV file with code segments'
    )
    parser.add_argument(
        '--output',
        required=True,
        type=Path,
        help='Path to output CSV file for perplexity scores'
    )
    parser.add_argument(
        '--model',
        default=None,
        type=str,
        help='Model name (overrides config)'
    )
    parser.add_argument(
        '--max-length',
        default=512,
        type=int,
        help='Maximum sequence length for tokenization'
    )
    parser.add_argument(
        '--device',
        default='cuda' if torch.cuda.is_available() else 'cpu',
        type=str,
        help='Device to use for computation'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("Starting perplexity computation (T020)")
    logger.info("=" * 60)
    
    try:
        # Load input data
        logger.info(f"Loading input from: {args.input}")
        input_data = load_input_data(args.input)
        logger.info(f"Loaded {len(input_data)} records")
        
        if len(input_data) == 0:
            logger.warning("No input data found, creating empty output")
            save_perplexity_scores([], args.output)
            return
        
        # Extract code segments
        code_segments = []
        segment_ids = []
        file_ids = []
        
        for record in input_data:
            # Handle different input formats
            if 'code' in record and record['code']:
                code_segments.append(record['code'])
                segment_ids.append(record.get('segment_id', f'seg_{len(segment_ids)}'))
                file_ids.append(record.get('file_id', f'file_{len(file_ids)}'))
            elif 'text' in record and record['text']:
                code_segments.append(record['text'])
                segment_ids.append(record.get('segment_id', f'seg_{len(segment_ids)}'))
                file_ids.append(record.get('file_id', f'file_{len(file_ids)}'))
            else:
                # Try to find any text field
                for key in ['code', 'text', 'content', 'source_code']:
                    if key in record and record[key]:
                        code_segments.append(record[key])
                        segment_ids.append(record.get('segment_id', f'seg_{len(segment_ids)}'))
                        file_ids.append(record.get('file_id', f'file_{len(file_ids)}'))
                        break
        
        if len(code_segments) == 0:
            logger.warning("No code segments found in input data")
            save_perplexity_scores([], args.output)
            return
        
        logger.info(f"Processing {len(code_segments)} code segments")
        
        # Load model and tokenizer
        model, tokenizer = load_model_and_tokenizer(
            model_name=args.model,
            device=args.device
        )
        
        # Compute perplexity for each segment
        perplexities = compute_perplexity_batch(
            model, tokenizer, code_segments,
            max_length=args.max_length,
            device=args.device
        )
        
        # Build output records
        scores = []
        valid_count = 0
        invalid_count = 0
        
        for i, (file_id, seg_id, perplexity) in enumerate(zip(file_ids, segment_ids, perplexities)):
            is_valid = validate_perplexity(perplexity)
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                logger.warning(f"Invalid perplexity for {file_id}/{seg_id}: {perplexity}")
            
            scores.append({
                'file_id': file_id,
                'segment_id': seg_id,
                'perplexity': perplexity,
                'timestamp': datetime.now().isoformat(),
                'model': args.model or get_model_name()
            })
        
        # Save results
        save_perplexity_scores(scores, args.output)
        
        logger.info("=" * 60)
        logger.info(f"Perplexity computation complete")
        logger.info(f"  Total segments: {len(scores)}")
        logger.info(f"  Valid perplexities: {valid_count}")
        logger.info(f"  Invalid perplexities: {invalid_count}")
        logger.info(f"  Output saved to: {args.output}")
        logger.info("=" * 60)
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Perplexity computation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
