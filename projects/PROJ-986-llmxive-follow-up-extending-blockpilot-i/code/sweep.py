import os
import sys
import json
import time
import logging
import signal
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import traceback

# Import from project utils and config
from utils.data_loader import load_gsm8k_streaming, load_humaneval_streaming
from utils.metrics import calculate_latency
from config import load_config, SweepConfig, get_config
from main import handle_oom_error, PipelineError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global checkpoint state
checkpoint_data = {
    "processed_samples": 0,
    "last_sample_id": None,
    "results": [],
    "status": "running"
}

def setup_signal_handlers(checkpoint_path: str):
    """Setup signal handlers for graceful shutdown and checkpointing."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}. Saving checkpoint and exiting...")
        save_checkpoint(checkpoint_path)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def save_checkpoint(path: str):
    """Save current sweep state to disk."""
    try:
        with open(path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        logger.info(f"Checkpoint saved to {path}")
    except Exception as e:
        logger.error(f"Failed to save checkpoint: {e}")

def load_checkpoint(path: str) -> Dict[str, Any]:
    """Load previous sweep state from disk."""
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded checkpoint from {path}")
            return data
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}, starting fresh.")
    return {
        "processed_samples": 0,
        "last_sample_id": None,
        "results": [],
        "status": "running"
    }

def initialize_model(model_name: str, device: str = "cpu"):
    """Initialize the transformer model for inference."""
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        logger.info(f"Loading model: {model_name} on {device}")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        model = model.to(device)
        model.eval()
        return model, tokenizer
    except Exception as e:
        raise PipelineError(f"Failed to initialize model: {e}")

def run_inference_with_block_size(
    model,
    tokenizer,
    prompt: str,
    block_size: int,
    device: str = "cpu"
) -> Tuple[float, bool, str]:
    """
    Run inference with a specific block size.
    Returns: (latency_seconds, success_flag, error_message)
    """
    try:
        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        start_time = time.time()
        with torch.no_grad():
            # Simulate block-based inference logic here
            # In a real implementation, this would use the specific block size
            # for the diffusion-based spec mechanism
            outputs = model.generate(
                **inputs,
                max_new_tokens=10,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
        end_time = time.time()
        
        latency = end_time - start_time
        return latency, True, ""
    except RuntimeError as e:
        if "CUDA out of memory" in str(e) or "OOM" in str(e):
            return 0.0, False, "OOM"
        return 0.0, False, str(e)
    except Exception as e:
        return 0.0, False, str(e)

def process_sample(
    sample: Dict[str, Any],
    model,
    tokenizer,
    block_sizes: List[int],
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Process a single sample across all block sizes.
    Implements deterministic tie-breaking: selects smallest block size on ties.
    """
    prompt = sample.get("question", sample.get("prompt", ""))
    sample_id = sample.get("id", str(time.time()))
    
    results = []
    best_block_size = None
    best_latency = float('inf')
    
    for b_size in block_sizes:
        latency, success, error = run_inference_with_block_size(
            model, tokenizer, prompt, b_size, device
        )
        
        result_entry = {
            "block_size": b_size,
            "latency": latency if success else None,
            "success": success,
            "error": error if not success else None
        }
        results.append(result_entry)
        
        # Track best latency, applying deterministic tie-breaking
        if success:
            if latency < best_latency:
                best_latency = latency
                best_block_size = b_size
            elif latency == best_latency and best_block_size is not None:
                # Tie-breaking rule: select smallest block size
                if b_size < best_block_size:
                    best_block_size = b_size
    
    return {
        "sample_id": sample_id,
        "prompt": prompt,
        "block_results": results,
        "optimal_block_size": best_block_size,
        "optimal_latency": best_latency if best_block_size is not None else None
    }

def run_sweep(
    config: SweepConfig,
    dataset_name: str = "gsm8k",
    output_path: str = "data/processed/ground_truth.jsonl",
    checkpoint_path: str = "data/processed/sweep_checkpoint.json"
):
    """
    Execute the exhaustive block-size sweep.
    """
    # Setup checkpoint path
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Load or initialize checkpoint
    global checkpoint_data
    checkpoint_data = load_checkpoint(checkpoint_path)
    
    # Setup signal handlers
    setup_signal_handlers(checkpoint_path)
    
    # Initialize model
    model, tokenizer = initialize_model(config.model_name, config.device)
    
    # Load dataset
    if dataset_name == "gsm8k":
        dataset_loader = load_gsm8k_streaming(config.data_path)
    elif dataset_name == "humaneval":
        dataset_loader = load_humaneval_streaming(config.data_path)
    else:
        raise ValueError(f"Unsupported dataset: {dataset_name}")
    
    # Process samples
    results_to_write = []
    start_idx = checkpoint_data.get("processed_samples", 0)
    
    logger.info(f"Resuming from sample index: {start_idx}")
    
    for idx, sample in enumerate(dataset_loader):
        if idx < start_idx:
            continue
        
        try:
            result = process_sample(
                sample,
                model,
                tokenizer,
                config.block_sizes,
                config.device
            )
            
            results_to_write.append(result)
            
            # Update checkpoint state
            checkpoint_data["processed_samples"] = idx + 1
            checkpoint_data["last_sample_id"] = result["sample_id"]
            checkpoint_data["results"] = results_to_write[-100:]  # Keep last 100 in memory
            
            # Periodic checkpoint save
            if (idx + 1) % 10 == 0:
                save_checkpoint(checkpoint_path)
            
            logger.info(f"Processed sample {idx + 1}: {result['sample_id']} -> B*={result['optimal_block_size']}")
            
        except Exception as e:
            logger.error(f"Error processing sample {idx}: {e}")
            handle_oom_error(e)
            continue
    
    # Final write to output file
    with open(output_path, 'w') as f:
        for result in results_to_write:
            f.write(json.dumps(result) + '\n')
    
    save_checkpoint(checkpoint_path)
    logger.info(f"Sweep completed. Results written to {output_path}")
    return results_to_write

def main():
    """Main entry point for the sweep script."""
    config = load_config()
    sweep_config = config.sweep
    
    logger.info("Starting BlockPilot Sweep...")
    results = run_sweep(
        sweep_config,
        dataset_name="gsm8k",
        output_path="data/processed/ground_truth.jsonl",
        checkpoint_path="data/processed/sweep_checkpoint.json"
    )
    
    logger.info(f"Total samples processed: {len(results)}")
    logger.info("Sweep finished successfully.")

if __name__ == "__main__":
    main()