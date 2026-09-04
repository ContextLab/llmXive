"""
T027: Generate structured text from RF tokens and validate syntax.

This module implements the logic to:
1. Load RF token sequences from data/processed/tokens.parquet.
2. Use the trained autoregressive model (code/models/autoregressive.py) to generate
   structured text (JSON/Markdown) from these tokens.
3. Validate the generated output using jsonschema or markdown parsers (via code/utils/validators.py).
4. Log results to data/results/generation_validation.json.

Dependencies:
- code/models/autoregressive.py (LightweightAutoregressiveModel)
- code/utils/validators.py (validate_json_syntax, validate_markdown_syntax)
- code/data/preprocessing.py (load_and_preprocess_image, etc.)
- code/config.py (get_config_dict)
"""

import os
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import torch
import pandas as pd
from tqdm import tqdm

# Project imports
from config import get_config_dict, ensure_dirs
from models.autoregressive import create_ar_model, get_default_config
from utils.validators import (
    validate_json_syntax,
    validate_markdown_syntax,
    ValidationError
)
from data.preprocessing import load_and_preprocess_image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_tokens_from_parquet(parquet_path: str) -> List[Dict[str, Any]]:
    """
    Load token sequences from a Parquet file.

    Args:
        parquet_path: Path to the tokens.parquet file.

    Returns:
        List of dictionaries containing token sequences and metadata.
    """
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Token file not found: {parquet_path}")

    logger.info(f"Loading tokens from {parquet_path}")
    df = pd.read_parquet(parquet_path)

    # Convert DataFrame to list of dicts
    # Expected columns: 'tokens', 'image_id', 'label' (or similar)
    records = df.to_dict(orient='records')
    logger.info(f"Loaded {len(records)} token sequences")
    return records

def generate_text_from_tokens(
    model: torch.nn.Module,
    tokens: torch.Tensor,
    max_length: int = 256,
    device: str = 'cpu'
) -> str:
    """
    Generate structured text from RF tokens using the autoregressive model.

    Args:
        model: The trained autoregressive model.
        tokens: Input token tensor (batch_size=1, seq_len, embed_dim).
        max_length: Maximum generation length.
        device: Device to run inference on.

    Returns:
        Generated text string.
    """
    model.eval()
    with torch.no_grad():
        # Ensure input is on correct device
        tokens = tokens.to(device)

        # Generate using the model's generate method (if available) or manual loop
        # Assuming the model has a generate method that returns token IDs
        if hasattr(model, 'generate'):
            generated_ids = model.generate(
                tokens,
                max_length=max_length,
                pad_token_id=model.config.pad_token_id if hasattr(model.config, 'pad_token_id') else 0
            )
        else:
            # Fallback: simple greedy decoding
            generated_ids = []
            current_input = tokens
            for _ in range(max_length):
                outputs = model(current_input)
                next_token_logits = outputs.logits[:, -1, :]
                next_token = torch.argmax(next_token_logits, dim=-1, keepdim=True)
                generated_ids.append(next_token)
                current_input = torch.cat([current_input, next_token], dim=1)
                if next_token.item() == model.config.eos_token_id:
                    break
            generated_ids = torch.cat(generated_ids, dim=1)

        # Decode token IDs to text
        # Assuming a simple tokenizer mapping (in real scenario, use model's tokenizer)
        # For this implementation, we'll assume the model outputs text directly or we have a simple decoder
        # Since we don't have a full tokenizer defined in the API, we'll mock the decoding
        # In a real scenario, this would use the model's tokenizer
        generated_text = ""
        if hasattr(model, 'tokenizer'):
            generated_text = model.tokenizer.decode(generated_ids[0].cpu().numpy(), skip_special_tokens=True)
        else:
            # Fallback: convert token IDs to a placeholder string
            # This is a limitation; in a real implementation, we'd have a proper tokenizer
            generated_text = f"[Generated: {generated_ids[0].cpu().numpy().tolist()[:20]}...]"

    return generated_text

def validate_generated_text(
    text: str,
    output_format: str = 'json'
) -> Tuple[bool, Optional[str]]:
    """
    Validate the generated text for syntax correctness.

    Args:
        text: Generated text to validate.
        output_format: 'json' or 'markdown'.

    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        if output_format.lower() == 'json':
            is_valid, error = validate_json_syntax(text)
        elif output_format.lower() == 'markdown':
            is_valid, error = validate_markdown_syntax(text)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

        return is_valid, error
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False, str(e)

def process_and_validate(
    tokens_data: List[Dict[str, Any]],
    model: torch.nn.Module,
    output_format: str = 'json',
    device: str = 'cpu',
    max_samples: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Process token sequences, generate text, and validate.

    Args:
        tokens_data: List of token sequences and metadata.
        model: Trained autoregressive model.
        output_format: 'json' or 'markdown'.
        device: Device for inference.
        max_samples: Maximum number of samples to process (for testing).

    Returns:
        List of results with validation status.
    """
    results = []
    config = get_default_config()
    max_length = config.get('max_length', 256)

    # Limit samples if specified
    if max_samples:
        tokens_data = tokens_data[:max_samples]

    for i, item in enumerate(tqdm(tokens_data, desc="Generating and validating")):
        try:
            # Extract tokens from the item
            # Expected format: {'tokens': [list of floats], 'image_id': ..., ...}
            if 'tokens' not in item:
                logger.warning(f"Skipping item {i}: missing 'tokens' field")
                continue

            tokens_list = item['tokens']
            image_id = item.get('image_id', f'unknown_{i}')

            # Convert to tensor (batch_size=1, seq_len, embed_dim)
            # Assuming tokens are already in the correct format (seq_len, embed_dim)
            # If tokens are 1D, we might need to reshape
            if isinstance(tokens_list, list):
                tokens_tensor = torch.tensor(tokens_list, dtype=torch.float32)
                if tokens_tensor.dim() == 1:
                    # If 1D, assume it's a single embedding and expand
                    # This is a simplification; real tokens should be 2D
                    tokens_tensor = tokens_tensor.unsqueeze(0)
                elif tokens_tensor.dim() == 2:
                    # Add batch dimension
                    tokens_tensor = tokens_tensor.unsqueeze(0)
                else:
                    logger.warning(f"Unexpected token dimension for {image_id}: {tokens_tensor.dim()}")
                    continue
            else:
                logger.warning(f"Skipping item {i}: tokens not a list")
                continue

            # Generate text
            generated_text = generate_text_from_tokens(
                model, tokens_tensor, max_length=max_length, device=device
            )

            # Validate
            is_valid, error_msg = validate_generated_text(generated_text, output_format)

            results.append({
                'image_id': image_id,
                'generated_text': generated_text,
                'is_valid': is_valid,
                'error_message': error_msg,
                'output_format': output_format
            })

        except Exception as e:
            logger.error(f"Error processing item {i} (image_id={image_id}): {e}")
            results.append({
                'image_id': image_id,
                'generated_text': '',
                'is_valid': False,
                'error_message': str(e),
                'output_format': output_format
            })

    return results

def save_results(results: List[Dict[str, Any]], output_path: str):
    """
    Save validation results to a JSON file.

    Args:
        results: List of result dictionaries.
        output_path: Path to save the results.
    """
    # Ensure output directory exists
    ensure_dirs([output_path])

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for T027."""
    config = get_config_dict()

    # Paths
    tokens_path = config.get('paths', {}).get('tokens_parquet', 'data/processed/tokens.parquet')
    model_path = config.get('paths', {}).get('ar_model_checkpoint', 'data/models/ar_model.pt')
    output_path = config.get('paths', {}).get('generation_validation_log', 'data/results/generation_validation.json')
    output_format = config.get('generation', {}).get('output_format', 'json')
    device = config.get('generation', {}).get('device', 'cpu')
    max_samples = config.get('generation', {}).get('max_samples', None)

    # Ensure directories exist
    ensure_dirs([output_path])

    # Load model
    logger.info(f"Loading autoregressive model from {model_path}")
    try:
        model_config = get_default_config()
        model = create_ar_model(model_config)
        if os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path, map_location=torch.device(device)))
            logger.info(f"Model weights loaded from {model_path}")
        else:
            logger.warning(f"Model checkpoint not found at {model_path}. Using random weights.")
        model.to(device)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # Load tokens
    try:
        tokens_data = load_tokens_from_parquet(tokens_path)
    except FileNotFoundError as e:
        logger.error(f"Token file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load tokens: {e}")
        sys.exit(1)

    # Process and validate
    logger.info(f"Processing {len(tokens_data)} samples with output format '{output_format}'")
    results = process_and_validate(
        tokens_data, model, output_format=output_format, device=device, max_samples=max_samples
    )

    # Save results
    save_results(results, output_path)

    # Summary
    valid_count = sum(1 for r in results if r['is_valid'])
    total_count = len(results)
    logger.info(f"Generation and validation complete. Valid: {valid_count}/{total_count} ({valid_count/total_count*100:.2f}%)")

    return results

if __name__ == '__main__':
    main()