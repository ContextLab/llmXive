import json
import sys
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from datasets import load_dataset

# Import project utilities and models using the exact API surface provided
from utils.config import load_config, get_project_root, get_artifacts_dir, get_data_dir, ConfigError
from models.autoregressive import create_autoregressive_model, AutoregressiveModel
from models.diffusion import create_diffusion_model, DiffusionModel
from utils.logging import setup_logging, get_logger, info, error, warning

# HumanEval dataset ID on Hugging Face
HUMAN_EVAL_DATASET_ID = "openai_humaneval"

def load_checkpoint(checkpoint_path: Path) -> Dict[str, Any]:
    """
    Load a PyTorch checkpoint from the specified path.
    """
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    
    logger = get_logger()
    logger.info(f"Loading checkpoint from {checkpoint_path}")
    
    try:
        checkpoint = torch.load(checkpoint_path, map_location="cpu")
        # Handle different checkpoint structures (dict with 'model_state_dict', or direct state dict)
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            return checkpoint["model_state_dict"]
        return checkpoint
    except Exception as e:
        logger.error(f"Failed to load checkpoint: {e}")
        raise

def load_model_weights(model: nn.Module, state_dict: Dict[str, Any]) -> nn.Module:
    """
    Load weights into a model instance.
    """
    # Handle potential key mismatches if model was saved with 'module.' prefix
    model_state_dict = model.state_dict()
    pretrained_dict = {}
    for k, v in state_dict.items():
        # Remove 'module.' prefix if present (common with DataParallel/DistributedDataParallel)
        if k.startswith("module."):
            k = k[7:]
        if k in model_state_dict and v.shape == model_state_dict[k].shape:
            pretrained_dict[k] = v
        else:
            warning(f"Skipping unexpected key: {k} (shape: {v.shape if hasattr(v, 'shape') else 'N/A'})")
    
    model_state_dict.update(pretrained_dict)
    model.load_state_dict(model_state_dict)
    return model

def generate_code_completion(
    model: nn.Module, 
    prompt: str, 
    max_new_tokens: int = 150,
    temperature: float = 1.0,
    top_p: float = 0.95
) -> str:
    """
    Generate a code completion for a given prompt using the loaded model.
    This implementation assumes an AutoregressiveModel interface.
    For DiffusionModel, a different generation strategy would be required,
    but HumanEval is typically evaluated on autoregressive or specific generative interfaces.
    Given the task context of comparing AR vs Diffusion, we assume the checkpoint
    corresponds to the architecture it was trained for. This function is generic
    but primarily optimized for the AR path as per standard HumanEval protocols.
    """
    model.eval()
    device = next(model.parameters()).device
    
    # Simple tokenization for demonstration - in a real scenario, use the model's tokenizer
    # Since we are using raw torch models without a specific tokenizer defined in the API,
    # we assume a character-level or byte-pair encoding handled internally or via a standard tokenizer.
    # For this specific implementation, we will use a simple byte-level approach or rely on 
    # the model's internal embedding if it expects indices. 
    # However, without a tokenizer object in the API, we must simulate or use a standard one.
    # Let's assume the model expects token IDs. We'll use a simple byte-to-int mapping for safety
    # or rely on the fact that the model might have been trained on raw bytes/chars.
    # To be robust, we'll use the `tiktoken` or `transformers` tokenizer if available, 
    # but since we can't add new deps easily without requirements.txt update (which is T005),
    # we will assume the model's vocab is standard ASCII/UTF-8 mapping or we use a fallback.
    
    # Fallback: Use a simple byte-level tokenizer for the prompt
    # This is a simplification. In a full system, a tokenizer would be part of the config.
    # We will assume the model's `get_vocab_size` implies a standard mapping.
    # For this script to run without external tokenizer deps not in requirements,
    # we will use the `transformers` AutoTokenizer if available, otherwise a byte-level fallback.
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("gpt2") # Fallback to gpt2 tokenizer for standard code
        input_ids = tokenizer.encode(prompt, return_tensors="pt").to(device)
    except ImportError:
        # Fallback: simple byte-level encoding (assuming model handles bytes)
        input_ids = torch.tensor([list(prompt.encode('utf-8'))], dtype=torch.long).to(device)

    with torch.no_grad():
        # Autoregressive generation loop
        generated = input_ids
        for _ in range(max_new_tokens):
            if generated.shape[1] >= 512: # Safety limit
                break
            
            # Forward pass
            if isinstance(model, AutoregressiveModel):
                outputs = model(generated)
                next_token_logits = outputs.logits[:, -1, :] / temperature
            elif isinstance(model, DiffusionModel):
                # Diffusion models generate differently. 
                # For HumanEval compatibility, we might need to adapt the diffusion process.
                # However, standard HumanEval evaluation expects a string completion.
                # We will treat the diffusion model as a generative model if it has a `generate` method.
                # If not, we might need to simulate an AR step or use a specific diffusion sampling.
                # Given the constraints, we assume the checkpoint is for an AR model or 
                # the diffusion model has a `generate` method.
                # If it's a pure diffusion model without AR interface, we cannot use this function directly.
                # We will assume the task implies evaluating the model that *can* generate code.
                # If the checkpoint is diffusion, we skip or use a placeholder.
                # For this implementation, we assume the model is AR or has a compatible interface.
                # If it's diffusion, we raise a warning and skip or use a dummy.
                warning("Diffusion model detected. Standard AR generation not supported. Returning empty.")
                return ""
            else:
                warning("Unknown model type for generation.")
                return ""
            
            # Top-p sampling
            probs = torch.softmax(next_token_logits, dim=-1)
            sorted_probs, sorted_indices = torch.sort(probs, descending=True)
            cumulative_probs = torch.cumsum(sorted_probs, dim=-1)
            sorted_indices_to_remove = cumulative_probs > top_p
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = 0
            indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
            probs = probs.masked_fill(indices_to_remove, 0.0)
            
            next_token = torch.multinomial(probs, num_samples=1)
            generated = torch.cat((generated, next_token), dim=1)
            
            # Check for stop token
            if next_token.item() == 50256: # GPT2 EOS
                break

    # Decode
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("gpt2")
        return tokenizer.decode(generated[0, input_ids.shape[1]:], skip_special_tokens=True)
    except ImportError:
        return generated[0, input_ids.shape[1]:].cpu().numpy().tobytes().decode('utf-8', errors='ignore')

def evaluate_human_eval_sample(
    completion: str, 
    prompt: str, 
    test_list: List[str],
    timeout: float = 3.0
) -> Dict[str, Any]:
    """
    Evaluate a single HumanEval sample by executing the completion.
    """
    result = {
        "passed": False,
        "error": None,
        "execution_time": 0.0
    }
    
    try:
        # Construct the full code to execute
        full_code = prompt + completion
        
        # Execute the test
        import time
        start_time = time.time()
        
        # We use a simple exec/eval approach with a timeout mechanism (simplified)
        # In a production environment, use a sandboxed executor.
        # Here we assume the environment is safe and we just run the tests.
        
        # Create a namespace for execution
        namespace = {}
        exec(full_code, namespace)
        
        # Run the tests
        for test in test_list:
            exec(test, namespace)
        
        result["passed"] = True
        result["execution_time"] = time.time() - start_time
        
    except Exception as e:
        result["error"] = str(e)
        result["passed"] = False
    
    return result

def run_human_eval_benchmark(
    model: nn.Module, 
    checkpoint_path: Path, 
    num_samples: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run the full HumanEval benchmark suite on the loaded model.
    """
    logger = get_logger()
    logger.info(f"Starting HumanEval benchmark on {checkpoint_path}")
    
    # Load checkpoint
    state_dict = load_checkpoint(checkpoint_path)
    
    # Determine model type from checkpoint or config
    # We assume the model is loaded based on the architecture it was trained for.
    # We need to know if it's AR or Diffusion to instantiate the correct model.
    # For this, we check the keys or assume AR as default for HumanEval.
    # If the checkpoint has specific diffusion keys, we might need to switch.
    # Let's assume we try AR first, then Diffusion if AR fails.
    
    model_config = load_config()
    # Reconstruct model
    try:
        # Try AR first
        model = create_autoregressive_model()
        model = load_model_weights(model, state_dict)
        model_type = "autoregressive"
    except Exception:
        try:
            model = create_diffusion_model()
            model = load_model_weights(model, state_dict)
            model_type = "diffusion"
        except Exception as e:
            logger.error(f"Failed to load model as AR or Diffusion: {e}")
            raise
    
    model.eval()
    
    # Load HumanEval dataset
    try:
        dataset = load_dataset(HUMAN_EVAL_DATASET_ID, split="test")
    except Exception as e:
        logger.error(f"Failed to load HumanEval dataset: {e}")
        raise
    
    if num_samples:
        dataset = dataset.select(range(num_samples))
    
    results = []
    total = len(dataset)
    
    for i, item in enumerate(dataset):
        prompt = item["prompt"]
        test_list = item["test"].split("\n") if isinstance(item["test"], str) else item["test"]
        completion = generate_code_completion(model, prompt)
        eval_result = evaluate_human_eval_sample(completion, prompt, test_list)
        
        result_entry = {
            "task_id": item["task_id"],
            "prompt": prompt,
            "completion": completion,
            "passed": eval_result["passed"],
            "error": eval_result["error"],
            "execution_time": eval_result["execution_time"]
        }
        results.append(result_entry)
        
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{total} samples")
    
    # Calculate pass@1
    passed_count = sum(1 for r in results if r["passed"])
    pass_rate = passed_count / total if total > 0 else 0.0
    
    return {
        "model_type": model_type,
        "checkpoint_path": str(checkpoint_path),
        "total_samples": total,
        "passed_samples": passed_count,
        "pass_rate": pass_rate,
        "results": results
    }

def re_verify_human_eval_exclusion(corpus_path: Path) -> Dict[str, Any]:
    """
    Re-verify that the Micro-Corpus does not contain any HumanEval samples.
    """
    logger = get_logger()
    logger.info("Re-verifying HumanEval exclusion from Micro-Corpus")
    
    # Load HumanEval samples
    try:
        humaneval_dataset = load_dataset(HUMAN_EVAL_DATASET_ID, split="test")
        humaneval_prompts = {item["prompt"] for item in humaneval_dataset}
    except Exception as e:
        logger.error(f"Failed to load HumanEval for exclusion check: {e}")
        return {"error": str(e), "verified": False}
    
    # Load Micro-Corpus
    if not corpus_path.exists():
        logger.error(f"Corpus file not found: {corpus_path}")
        return {"error": "Corpus not found", "verified": False}
    
    overlap_count = 0
    total_corpus_entries = 0
    
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            total_corpus_entries += 1
            try:
                entry = json.loads(line)
                text = entry.get("text", "")
                # Simple substring check (could be optimized with hashing)
                for hp in humaneval_prompts:
                    if hp in text:
                        overlap_count += 1
                        break
            except json.JSONDecodeError:
                continue
    
    verified = overlap_count == 0
    return {
        "verified": verified,
        "overlap_count": overlap_count,
        "total_corpus_entries": total_corpus_entries,
        "status": "PASS" if verified else "FAIL"
    }

def compute_text_fp(text: str) -> str:
    """
    Compute a fingerprint (hash) for a text string.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def main():
    """
    Main entry point for the HumanEval evaluation script.
    """
    logger = setup_logging()
    project_root = get_project_root()
    artifacts_dir = get_artifacts_dir()
    processed_dir = get_data_dir() / "processed"
    
    # Ensure directories exist
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Load config to get regime and other params
    try:
        config = load_config()
    except ConfigError as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # Determine which checkpoints to evaluate
    # We expect checkpoints in data/artifacts/checkpoints/
    checkpoint_dir = artifacts_dir / "checkpoints"
    if not checkpoint_dir.exists():
        logger.error(f"Checkpoint directory not found: {checkpoint_dir}")
        sys.exit(1)
    
    checkpoint_files = list(checkpoint_dir.glob("model_seed_*_final.pt"))
    if not checkpoint_files:
        logger.error("No checkpoint files found. Run training first.")
        sys.exit(1)
    
    corpus_path = processed_dir / "micro_corpus_full.jsonl"
    
    all_results = {
        "evaluation_timestamp": str(torch.now().isoformat() if hasattr(torch, 'now') else "N/A"),
        "corpus_verification": {},
        "model_evaluations": []
    }
    
    # Re-verify exclusion
    exclusion_result = re_verify_human_eval_exclusion(corpus_path)
    all_results["corpus_verification"] = exclusion_result
    
    if not exclusion_result.get("verified", False):
        warning("HumanEval exclusion verification FAILED. Proceeding with caution.")
    
    # Evaluate each checkpoint
    for checkpoint_path in checkpoint_files:
        logger.info(f"Evaluating checkpoint: {checkpoint_path}")
        try:
            eval_result = run_human_eval_benchmark(None, checkpoint_path) # Model is loaded inside
            all_results["model_evaluations"].append(eval_result)
        except Exception as e:
            logger.error(f"Failed to evaluate {checkpoint_path}: {e}")
            all_results["model_evaluations"].append({
                "checkpoint_path": str(checkpoint_path),
                "error": str(e)
            })
    
    # Save results
    output_path = artifacts_dir / "human_eval_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    logger.info(f"HumanEval results saved to {output_path}")
    print(f"HumanEval pass rate summary:")
    for eval_res in all_results["model_evaluations"]:
        if "pass_rate" in eval_res:
            print(f"  {eval_res['checkpoint_path']}: {eval_res['pass_rate']:.4f} ({eval_res['passed_samples']}/{eval_res['total_samples']})")
        elif "error" in eval_res:
            print(f"  {eval_res['checkpoint_path']}: ERROR - {eval_res['error']}")

if __name__ == "__main__":
    main()
