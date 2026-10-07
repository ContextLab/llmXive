"""
Entropy extraction module for llmXive.
Handles entropy calculation from model samples with robust error handling.
"""
import ast
import hashlib
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import torch
import numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer
import pandas as pd

from src.config import load_config, get_config_value
from src.utils import set_global_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_model(model_name: str, device: str = "cuda", model_temp: float = 0.7, model_top_p: float = 0.95):
    """Load the transformer model and tokenizer."""
    logger.info(f"Loading model: {model_name} on {device}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        # Handle models without pad_token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True
        )
        if device == "cpu":
            model = model.to(torch.float32)
        model.eval()
        logger.info("Model loaded successfully")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def normalize_ast(code_str: str) -> Optional[str]:
    """
    Normalize code by parsing to AST and converting back to string.
    Returns None if parsing fails (malformed code).
    """
    try:
        tree = ast.parse(code_str)
        # Normalize by converting back to string
        # ast.unparse is available in Python 3.9+
        normalized = ast.unparse(tree)
        return normalized
    except SyntaxError as e:
        # Malformed code that cannot be parsed
        logger.debug(f"SyntaxError in normalize_ast: {e}")
        return None
    except Exception as e:
        # Other AST parsing errors
        logger.debug(f"AST error in normalize_ast: {e}")
        return None

def generate_samples(model, tokenizer, prompt: str, n_samples: int = 10, 
                    temperature: float = 0.7, top_p: float = 0.95, 
                    max_new_tokens: int = 512) -> List[str]:
    """Generate multiple samples from the model for a given prompt."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    samples = []
    
    for _ in range(n_samples):
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        # Decode and extract the generated text
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract just the new part (after the prompt)
        if prompt in generated:
            generated = generated.split(prompt, 1)[1]
        samples.append(generated.strip())
    
    return samples

def cluster_samples(samples: List[str]) -> Dict[str, int]:
    """
    Cluster samples by their normalized AST hash.
    Returns a dictionary of hash -> count.
    """
    clusters = {}
    for sample in samples:
        normalized = normalize_ast(sample)
        if normalized is None:
            # Skip malformed code, do not crash
            continue
        
        # Compute hash of normalized code
        code_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
        clusters[code_hash] = clusters.get(code_hash, 0) + 1
    
    return clusters

def compute_shannon_entropy(cluster_counts: Dict[str, int]) -> float:
    """Compute Shannon entropy from cluster counts."""
    if not cluster_counts:
        # No valid samples -> minimal entropy
        return 1e-9
    
    total = sum(cluster_counts.values())
    if total == 0:
        return 1e-9
    
    entropy = 0.0
    for count in cluster_counts.values():
        if count > 0:
            p = count / total
            entropy -= p * np.log2(p)
    
    return entropy

def load_reference_set(path: str) -> pd.DataFrame:
    """Load the reference validation set."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Reference set not found at {path}")
    return pd.read_csv(path)

def process_entropy_for_dataset(
    dataset_path: str,
    output_path: str,
    reference_path: str,
    model_name: str,
    device: str = "cuda",
    n_samples: int = 10,
    seed: int = 42,
    sample_size: Optional[int] = None
) -> None:
    """
    Process a dataset to compute entropy for each problem.
    
    Args:
        dataset_path: Path to the input dataset (JSON/CSV with task_id and prompt)
        output_path: Path to save entropy results CSV
        reference_path: Path to the unseen validation set for reference
        model_name: HuggingFace model name
        device: Device to run inference on
        n_samples: Number of samples to generate per problem
        seed: Random seed
        sample_size: Optional limit on number of problems to process
    """
    set_global_seed(seed)
    
    # Load config
    config = load_config()
    model_temp = get_config_value(config, "MODEL_TEMP", 0.7)
    model_top_p = get_config_value(config, "MODEL_TOP_P", 0.95)
    
    # Load model
    model, tokenizer = load_model(model_name, device, model_temp, model_top_p)
    
    # Load dataset
    if dataset_path.endswith('.json'):
        with open(dataset_path, 'r') as f:
            data = json.load(f)
    elif dataset_path.endswith('.csv'):
        data = pd.read_csv(dataset_path).to_dict('records')
    else:
        raise ValueError(f"Unsupported dataset format: {dataset_path}")
    
    # Limit sample size if specified
    if sample_size is not None:
        data = data[:sample_size]
    
    # Load reference set (for validation, not used in clustering directly)
    try:
        reference_df = load_reference_set(reference_path)
        logger.info(f"Loaded reference set with {len(reference_df)} entries")
    except FileNotFoundError as e:
        logger.warning(f"Reference set not found: {e}. Proceeding without reference validation.")
        reference_df = None
    
    results = []
    exclusion_log = []
    
    # Process each problem
    for idx, problem in enumerate(data):
        task_id = problem.get('task_id', f'unknown_{idx}')
        prompt = problem.get('prompt', '')
        
        if not prompt:
            exclusion_log.append({
                'task_id': task_id,
                'reason': 'Empty prompt',
                'error': 'No prompt content found'
            })
            continue
        
        try:
            # Generate samples
            samples = generate_samples(
                model, tokenizer, prompt, 
                n_samples=n_samples,
                temperature=model_temp,
                top_p=model_top_p
            )
            
            # Filter out empty samples
            valid_samples = [s for s in samples if s.strip()]
            
            if not valid_samples:
                exclusion_log.append({
                    'task_id': task_id,
                    'reason': 'No valid samples generated',
                    'error': 'All samples were empty'
                })
                continue
            
            # Cluster samples
            clusters = cluster_samples(valid_samples)
            
            if not clusters:
                # All samples were malformed
                exclusion_log.append({
                    'task_id': task_id,
                    'reason': 'All samples malformed',
                    'error': 'No samples could be normalized to AST'
                })
                # Assign minimal entropy
                results.append({
                    'task_id': task_id,
                    'entropy': 1e-9,
                    'exclusion_reason': 'all_samples_malformed'
                })
                continue
            
            # Compute entropy
            entropy = compute_shannon_entropy(clusters)
            
            results.append({
                'task_id': task_id,
                'entropy': entropy,
                'exclusion_reason': None
            })
            
        except Exception as e:
            # Log the error and continue with next problem
            error_msg = str(e)
            exclusion_log.append({
                'task_id': task_id,
                'reason': 'Processing error',
                'error': error_msg
            })
            logger.error(f"Error processing task {task_id}: {error_msg}")
            # Still record the result with minimal entropy to maintain continuity
            results.append({
                'task_id': task_id,
                'entropy': 1e-9,
                'exclusion_reason': f'processing_error: {error_msg[:100]}'
            })
        
        if (idx + 1) % 10 == 0:
            logger.info(f"Processed {idx + 1}/{len(data)} problems")
    
    # Save results
    output_df = pd.DataFrame(results)
    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved entropy results to {output_path}")
    
    # Save exclusion log
    exclusion_path = str(Path(output_path).parent / 'exclusion_log.json')
    with open(exclusion_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    logger.info(f"Saved exclusion log to {exclusion_path}")

def main():
    """Main entry point for entropy extraction."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute entropy for code generation samples")
    parser.add_argument("--input", type=str, required=True, help="Input dataset path")
    parser.add_argument("--output", type=str, required=True, help="Output CSV path")
    parser.add_argument("--reference", type=str, default=None, help="Reference validation set path")
    parser.add_argument("--model", type=str, default="codellama/CodeLlama-7b-Instruct-hf", help="Model name")
    parser.add_argument("--device", type=str, default="cuda", help="Device (cuda/cpu)")
    parser.add_argument("--n-samples", type=int, default=10, help="Number of samples per problem")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--sample-size", type=int, default=None, help="Limit number of problems to process")
    
    args = parser.parse_args()
    
    # Use reference from args or config
    reference_path = args.reference
    if reference_path is None:
        # Try to find default reference
        default_ref = "data/processed/unseen_validation_set.csv"
        if os.path.exists(default_ref):
            reference_path = default_ref
        else:
            logger.warning("No reference set specified and default not found. Continuing without reference validation.")
    
    process_entropy_for_dataset(
        dataset_path=args.input,
        output_path=args.output,
        reference_path=reference_path,
        model_name=args.model,
        device=args.device,
        n_samples=args.n_samples,
        seed=args.seed,
        sample_size=args.sample_size
    )

if __name__ == "__main__":
    main()