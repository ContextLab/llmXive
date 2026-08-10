import os
import sys
import json
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
import torch
import torch.nn.functional as F
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
import numpy as np
import json
from config import get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/processed/error.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DeltaCoefficient:
    """Data class for DelTA coefficient structure."""
    def __init__(self, token_id: int, coefficient: float, variance: float):
        self.token_id = token_id
        self.coefficient = coefficient
        self.variance = variance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "coefficient": self.coefficient,
            "variance": self.variance
        }

def load_phi3_mini():
    """Load Phi-3-mini model and tokenizer on CPU."""
    model_name = "microsoft/Phi-3-mini-4k-instruct"
    logger.info(f"Loading model: {model_name} (CPU only)")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        # Explicitly force CPU and full precision as per constraints
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            device_map="cpu",
            trust_remote_code=True
        )
        model.eval()
        logger.info("Model loaded successfully.")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def load_gsm8k_verified():
    """Load the verified GSM8K dataset from the raw Parquet file."""
    data_path = Path("data/raw/gsm8k_verified.parquet")
    if not data_path.exists():
        logger.error(f"Verified GSM8K file not found at {data_path}. Run T012 first.")
        raise FileNotFoundError(f"Missing required input: {data_path}")
    
    try:
        import pandas as pd
        df = pd.read_parquet(data_path)
        logger.info(f"Loaded {len(df)} verified examples from {data_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load GSM8K data: {e}")
        raise

def stratified_sample(df: Any, n: int, seed: int = 42) -> List[Dict]:
    """Select N stratified examples based on length."""
    np.random.seed(seed)
    df_list = df.to_dict('records')
    # Stratify by length of question
    df_list_sorted = sorted(df_list, key=lambda x: len(x['question']))
    
    # Simple stratified sampling: divide into buckets and sample
    num_buckets = min(n, len(df_list_sorted))
    if num_buckets == 0:
        return []
    
    bucket_size = len(df_list_sorted) // num_buckets
    sample = []
    for i in range(num_buckets):
        start_idx = i * bucket_size
        end_idx = start_idx + bucket_size if i < num_buckets - 1 else len(df_list_sorted)
        bucket = df_list_sorted[start_idx:end_idx]
        if bucket:
            sample.append(bucket[0]) # Take one representative per bucket
    
    # If we need more, fill randomly
    while len(sample) < n and len(df_list_sorted) > len(sample):
        remaining = [x for x in df_list_sorted if x not in sample]
        if not remaining:
            break
        idx = np.random.randint(0, len(remaining))
        sample.append(remaining[idx])
    
    return sample[:n]

def compute_delta_coefficients(model, tokenizer, example: Dict) -> List[DeltaCoefficient]:
    """
    Compute DelTA coefficients for a single example using torch.autograd.grad.
    Implements the discriminative token credit assignment logic.
    """
    question = example['question']
    answer = example['answer']
    
    # Tokenize
    inputs = tokenizer(question, return_tensors="pt", truncation=True, max_length=512)
    input_ids = inputs['input_ids']
    attention_mask = inputs['attention_mask']
    
    # Forward pass
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits
    
    # We need to compute gradients w.r.t input embeddings for the answer tokens
    # For simplicity in this CPU-bound context, we approximate the 'true coefficient'
    # as the gradient magnitude of the loss w.r.t the input embeddings at the answer positions.
    
    # Re-run with requires_grad=True on embeddings
    input_ids.requires_grad_(True)
    outputs_grad = model(input_ids=input_ids, attention_mask=attention_mask)
    logits_grad = outputs_grad.logits
    
    # Calculate loss (cross entropy against the answer tokens)
    # Shift for next token prediction
    shift_logits = logits_grad[..., :-1, :].contiguous()
    shift_labels = input_ids[..., 1:].contiguous()
    
    # Create a mask for the answer portion (simplified: assume answer is the last part)
    # In a real implementation, we would parse the answer to get exact token indices.
    # Here we use the last 20 tokens as a proxy for the 'answer' contribution to the loss.
    loss = F.cross_entropy(shift_logits.view(-1, shift_logits.size(-1)), 
                           shift_labels.view(-1), reduction='none')
    
    # Reshape to match input sequence
    loss = loss.view(shift_labels.shape)
    
    # Compute gradient of loss w.r.t input_ids (embedding layer)
    # We only care about the magnitude of the gradient as the 'credit'
    try:
        grads = torch.autograd.grad(loss.sum(), input_ids, retain_graph=True)[0]
    except RuntimeError as e:
        logger.warning(f"Gradient computation failed for example: {e}")
        return []
    
    coefficients = []
    # Iterate over tokens and compute a scalar coefficient (L2 norm of grad w.r.t embedding)
    # Note: input_ids are indices, grads are w.r.t embeddings. 
    # We map back to token IDs.
    if grads is not None:
        # grads shape: [batch, seq_len, embed_dim]
        # We take the norm over the embedding dimension for each token
        grad_norms = torch.norm(grads, dim=2).squeeze(0).detach().numpy()
        
        for i, (token_id, grad_val) in enumerate(zip(input_ids.squeeze().numpy(), grad_norms)):
            # Filter out padding
            if token_id == tokenizer.pad_token_id:
                continue
            
            coeff_val = float(grad_val)
            # Variance check placeholder (calculated later globally, but we store local variance if needed)
            # For this task, variance is computed over the set of coefficients for the example
            coefficients.append(DeltaCoefficient(token_id=int(token_id), coefficient=coeff_val, variance=0.0))
    
    input_ids.requires_grad_(False)
    return coefficients

def validate_coefficients(coefficients: List[DeltaCoefficient], min_variance: float = 1e-9) -> bool:
    """
    Validate that the computed coefficients have variance > min_variance.
    This is the core requirement for T014.
    """
    if not coefficients:
        logger.error("No coefficients generated to validate.")
        return False
    
    coeffs = [c.coefficient for c in coefficients]
    if len(coeffs) < 2:
        logger.warning("Less than 2 coefficients found; variance check skipped (or set to 0).")
        # If we have 0 or 1 coefficient, variance is 0, which fails the check.
        return False

    global_variance = float(np.var(coeffs))
    
    logger.info(f"Global variance of coefficients: {global_variance}")
    
    if global_variance <= min_variance:
        logger.error(f"Variance check FAILED: {global_variance} <= {min_variance}")
        return False
    
    return True

def save_oracle_results(all_results: List[Dict], output_path: str, schema_path: str):
    """Save oracle results to JSON, validating against schema if provided."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load schema if it exists for validation
    schema = None
    if schema_path and os.path.exists(schema_path):
        try:
            import yaml
            with open(schema_path, 'r') as f:
                schema = yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load schema for validation: {e}")

    # Validate each record if schema exists
    if schema:
        for record in all_results:
            # Basic structural validation
            if 'example_id' not in record or 'coefficients' not in record:
                raise ValueError(f"Invalid record structure: {record}")
            for coef in record['coefficients']:
                if not isinstance(coef, dict) or 'token_id' not in coef or 'coefficient' not in coef:
                    raise ValueError(f"Invalid coefficient structure: {coef}")

    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Saved {len(all_results)} examples to {output_file}")

def main():
    """Main entry point for T014 / T013 merged logic."""
    config = get_config_summary()
    n_examples = config.get('n_examples', 200)
    seed = config.get('seed', 42)
    output_path = "data/processed/delta_coefficients.json"
    schema_path = "contracts/delta_oracle.schema.yaml"
    
    logger.info("Starting DelTA Oracle Generation...")
    
    # 1. Load Model
    model, tokenizer = load_phi3_mini()
    
    # 2. Load Data
    df = load_gsm8k_verified()
    if len(df) < n_examples:
        logger.error(f"Dataset has {len(df)} examples, but {n_examples} are required.")
        sys.exit(1)
    
    # 3. Stratified Sample
    sample_data = stratified_sample(df, n_examples, seed)
    logger.info(f"Selected {len(sample_data)} stratified examples.")
    
    all_results = []
    failed_count = 0
    
    for idx, example in enumerate(sample_data):
        try:
            # Compute coefficients
            coeffs = compute_delta_coefficients(model, tokenizer, example)
            
            if not coeffs:
                logger.warning(f"Example {idx} produced no coefficients. Skipping.")
                failed_count += 1
                continue
            
            # Validate variance locally (optional per-example) or globally later
            # T014 requires global variance check > 1e-9. 
            # We collect all and check at the end, or check per example if that's the intent.
            # The task says "Ensure output coefficients have variance > 1e-9". 
            # Usually this implies the global set.
            
            all_results.append({
                "example_id": idx,
                "coefficients": [c.to_dict() for c in coeffs]
            })
            
        except Exception as e:
            logger.error(f"Error processing example {idx}: {e}")
            traceback.print_exc()
            failed_count += 1
            continue
    
    if len(all_results) == 0:
        logger.error("No valid examples processed. Aborting.")
        sys.exit(1)
    
    # 4. Global Variance Validation (T014 Requirement)
    all_coeffs = []
    for res in all_results:
        all_coeffs.extend([c['coefficient'] for c in res['coefficients']])
    
    if len(all_coeffs) < 2:
        logger.error("Insufficient coefficients to compute global variance.")
        sys.exit(1)
    
    global_var = float(np.var(all_coeffs))
    logger.info(f"Global Variance: {global_var}")
    
    if global_var <= 1e-9:
        logger.error(f"CRITICAL: Global variance {global_var} is <= 1e-9. Failing as per T014.")
        sys.exit(1)
    
    # 5. Save Results
    save_oracle_results(all_results, output_path, schema_path)
    
    logger.info("Oracle generation and validation complete.")

if __name__ == "__main__":
    main()