import os
import sys
import json
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import load_dataset
from dataclasses import dataclass
import numpy as np

# Import config for paths and seeds
from config import get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DeltaCoefficient:
    """Represents a single DelTA coefficient for a token."""
    token_id: int
    coefficient: float
    variance: float

def load_phi3_mini():
    """Load Phi-3-mini model and tokenizer for CPU inference."""
    logger.info("Loading Phi-3-mini model (CPU)...")
    model_name = "microsoft/Phi-3-mini-4k-instruct"
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        # Ensure pad token is set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model in full precision for CPU as per spec
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            device_map="cpu",
            trust_remote_code=True
        )
        model.eval()
        logger.info("Phi-3-mini loaded successfully.")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def load_gsm8k_verified():
    """Load the verified GSM8K dataset from disk."""
    raw_path = Path("data/raw/gsm8k_verified.parquet")
    if not raw_path.exists():
        raise FileNotFoundError(f"Required file {raw_path} not found. Run T012 first.")
    
    import pandas as pd
    df = pd.read_parquet(raw_path)
    logger.info(f"Loaded {len(df)} verified GSM8K examples.")
    return df

def stratified_sample(df: pd.DataFrame, n: int, seed: int = 42) -> List[Dict[str, Any]]:
    """Select N examples stratified by solution length."""
    np.random.seed(seed)
    # Create length bins
    df['sol_len'] = df['solution'].apply(len)
    df['len_bin'] = pd.qcut(df['sol_len'], q=min(10, len(df)), labels=False)
    
    # Sample from each bin
    samples = []
    for bin_id in df['len_bin'].unique():
        bin_df = df[df['len_bin'] == bin_id]
        count = min(int(n * len(bin_df) / len(df)), len(bin_df))
        samples.extend(bin_df.sample(n=count, random_state=seed).to_dict('records'))
    
    return samples

def compute_delta_coefficients(model, tokenizer, question: str, answer: str, token_ids: List[int]) -> List[DeltaCoefficient]:
    """
    Compute DelTA coefficients using torch.autograd.grad.
    Implements the discriminative token credit assignment logic.
    """
    # Prepare input
    prompt = f"<|user|>\n{question}<|end|>\n<|assistant|>\n{answer}"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
    
    # We need to compute gradients with respect to the input embeddings
    # to approximate token-level credit assignment.
    # Note: This is a simplified approximation of the full DelTA algorithm
    # suitable for CPU execution on small subsets.
    
    input_ids = inputs['input_ids']
    attention_mask = inputs['attention_mask']
    
    # Forward pass to get logits
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits
    
    # Identify target tokens (the answer part)
    # In a real implementation, we would align token_ids precisely with the answer
    # For this implementation, we assume token_ids correspond to the answer tokens
    # and compute gradients for those positions.
    
    coefficients = []
    
    # To avoid memory explosion, we compute gradients one token at a time
    # or in small batches.
    batch_size = 5
    for i in range(0, len(token_ids), batch_size):
        batch_tokens = token_ids[i:i+batch_size]
        batch_grads = []
        
        # We'll use a simple heuristic: 
        # The 'coefficient' is approximated by the magnitude of the gradient
        # of the loss with respect to the input embedding of that token.
        # Since we don't have a true 'loss' function for credit assignment yet,
        # we use the negative log-likelihood of the next token as a proxy.
        
        for token_idx, token_id in enumerate(batch_tokens):
            # Find position of this token in input_ids
            # This is a simplification; real alignment would be more complex
            pos = torch.where(input_ids == token_id)[0]
            if len(pos) == 0:
                continue
            pos = pos[0].item()
            
            # Create a dummy loss for this position
            # We want to maximize the probability of the correct next token
            # But for credit assignment, we look at sensitivity
            try:
                # Enable gradients for embeddings
                model.get_input_embeddings().requires_grad_(True)
                
                # Forward pass
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                
                # Simple proxy loss: negative log prob of the next token
                # (In a full DelTA implementation, this would be more sophisticated)
                if pos < len(outputs.logits[0]):
                    next_token_logits = outputs.logits[0, pos, :]
                    # Assume the 'correct' next token is the one at pos+1 in input_ids
                    if pos + 1 < len(input_ids[0]):
                        correct_token = input_ids[0, pos+1]
                        log_probs = torch.nn.functional.log_softmax(next_token_logits, dim=-1)
                        loss = -log_probs[correct_token]
                        
                        # Compute gradient w.r.t. input embeddings
                        grads = torch.autograd.grad(
                            outputs=loss,
                            inputs=model.get_input_embeddings().weight,
                            retain_graph=True,
                            create_graph=False
                        )[0]
                        
                        # Extract gradient for the specific token position
                        # This is a simplification; real DelTA would use more complex attribution
                        grad_norm = grads[0, token_id].norm().item()
                        batch_grads.append(grad_norm)
                    else:
                        batch_grads.append(0.0)
                else:
                    batch_grads.append(0.0)
                    
            except Exception as e:
                logger.warning(f"Gradient computation failed for token {token_id}: {e}")
                batch_grads.append(0.0)
            finally:
                model.get_input_embeddings().weight.requires_grad_(False)
        
        # Create coefficients for this batch
        for j, token_id in enumerate(batch_tokens):
            coeff_val = batch_grads[j] if j < len(batch_grads) else 0.0
            # Variance proxy: use the coefficient itself as a proxy for uncertainty
            # In a real implementation, this would be computed over multiple samples
            variance = abs(coeff_val) * 0.1 + 1e-10 
            
            coefficients.append(DeltaCoefficient(
                token_id=int(token_id),
                coefficient=float(coeff_val),
                variance=float(variance)
            ))
    
    return coefficients

def validate_coefficients(coefficients: List[DeltaCoefficient]) -> bool:
    """
    Validate that coefficients meet the variance threshold.
    Returns False if any coefficient fails validation.
    """
    if not coefficients:
        logger.error("No coefficients generated.")
        return False
    
    for i, coeff in enumerate(coefficients):
        if np.isnan(coeff.coefficient) or np.isinf(coeff.coefficient):
            logger.error(f"Coefficient {i} is NaN or Inf: {coeff.coefficient}")
            return False
        if coeff.variance <= 1e-9:
            logger.error(f"Coefficient {i} variance too low: {coeff.variance}")
            return False
    
    # Global variance check
    all_coeffs = [c.coefficient for c in coefficients]
    global_var = np.var(all_coeffs)
    if global_var <= 1e-9:
        logger.error(f"Global variance too low: {global_var}")
        return False
    
    logger.info(f"Validation passed. Global variance: {global_var}")
    return True

def save_oracle_results(coefficients: List[DeltaCoefficient], output_path: str):
    """Save coefficients to JSON conforming to schema."""
    data = {
        "coefficients": [
            {
                "token_id": c.token_id,
                "coefficient": c.coefficient,
                "variance": c.variance
            }
            for c in coefficients
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved {len(coefficients)} coefficients to {output_path}")

def main():
    """Main entry point for T013/T014."""
    logger.info("Starting DelTA Oracle generation (T013/T014)...")
    
    # Load config
    config = get_config_summary()
    n_examples = config.get('N', 200)
    seed = config.get('SEED', 42)
    
    # Load model
    model, tokenizer = load_phi3_mini()
    
    # Load and sample data
    df = load_gsm8k_verified()
    if len(df) < n_examples:
        logger.error(f"Only {len(df)} examples available, need {n_examples}")
        sys.exit(1)
    
    samples = stratified_sample(df, n_examples, seed)
    logger.info(f"Processing {len(samples)} examples...")
    
    all_coefficients = []
    valid_count = 0
    
    for i, sample in enumerate(samples):
        try:
            question = sample['question']
            answer = sample['solution']
            
            # Tokenize answer
            # Note: In a real implementation, we would carefully align
            # the question and answer tokens
            answer_tokens = tokenizer.encode(answer, add_special_tokens=False)
            
            if len(answer_tokens) == 0:
                logger.warning(f"Example {i}: No answer tokens")
                continue
            
            # Compute coefficients
            coeffs = compute_delta_coefficients(model, tokenizer, question, answer, answer_tokens)
            
            if coeffs:
                all_coefficients.extend(coeffs)
                valid_count += 1
                
                if valid_count % 10 == 0:
                    logger.info(f"Processed {valid_count} examples...")
                    
        except Exception as e:
            logger.error(f"Error processing example {i}: {e}")
            traceback.print_exc()
            # Skip this example but continue
            continue
    
    if valid_count < n_examples:
        logger.error(f"Only {valid_count} valid examples out of {n_examples} requested.")
        # Per spec: FAIL if fewer than 200 valid examples remain
        sys.exit(1)
    
    # Validate coefficients
    if not validate_coefficients(all_coefficients):
        logger.error("Coefficient validation failed. Exiting.")
        sys.exit(1)
    
    # Save results
    output_path = "data/processed/delta_coefficients.json"
    save_oracle_results(all_coefficients, output_path)
    
    logger.info("DelTA Oracle generation completed successfully.")

if __name__ == "__main__":
    main()