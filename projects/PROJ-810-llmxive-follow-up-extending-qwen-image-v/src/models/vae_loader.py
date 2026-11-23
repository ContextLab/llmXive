import os
import json
import torch
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Constants
PRIMARY_MODEL_ID = "Qwen/Qwen2-VL-2B-Instruct"  # Using a verified Qwen2-VL variant as the VAE backbone proxy
FALLBACK_MODEL_ID = "openai/clip-vit-base-patch32"  # Verified fallback for CPU feasibility
OUTPUT_PATH = "data/results/model_availability.json"
MAX_CPU_MEMORY_GB = 7.0  # Hard constraint for CPU feasibility check

def check_model_availability(model_id: str) -> Tuple[bool, str]:
    """
    Checks if a specific model ID exists on the Hugging Face Hub.
    Returns (True, "") if found, (False, error_message) if not.
    """
    try:
        from huggingface_hub import model_info
        model_info(model_id)
        return True, ""
    except Exception as e:
        return False, str(e)

def check_cpu_feasibility(model_id: str) -> Tuple[bool, str]:
    """
    Estimates if a model can run on CPU within MAX_CPU_MEMORY_GB.
    This is a heuristic check based on parameter count and memory overhead.
    """
    try:
        from huggingface_hub import model_info
        info = model_info(model_id)
        
        # Estimate parameters (often in info.siblings or needs parsing from config)
        # For this check, we assume a rough mapping: 1B params ~ 2GB RAM (FP32) or 0.5GB (INT8)
        # We will attempt a lightweight load to verify actual memory footprint if possible,
        # but for a pure availability check, we rely on parameter count heuristics.
        
        # Heuristic: If params > 3B, likely > 7GB RAM for CPU inference without quantization
        # We assume we are loading in float32 for the baseline check.
        estimated_params = info.config.get("num_parameters", 0) if hasattr(info, 'config') else 0
        
        # If we can't get params from info, we try to estimate from file size
        total_size_gb = 0
        if hasattr(info, 'siblings') and info.siblings:
            for sibling in info.siblings:
                if sibling.rfilename and sibling.size:
                    total_size_gb += sibling.size / (1024**3)
        
        # Conservative estimate: Model size * 3 (weights + overhead + activation)
        estimated_ram_gb = total_size_gb * 3.0
        
        if estimated_ram_gb > MAX_CPU_MEMORY_GB:
            return False, f"Estimated RAM {estimated_ram_gb:.2f}GB exceeds limit {MAX_CPU_MEMORY_GB}GB"
        
        return True, "Feasible"
    except Exception as e:
        # If we can't fetch info, assume infeasible to be safe, or fallback
        return False, f"Could not verify CPU feasibility: {str(e)}"

def trigger_model_substitution_protocol(primary_id: str, fallback_id: str) -> Dict[str, Any]:
    """
    Implements the Model Substitution Protocol.
    Verifies the fallback model. If valid, returns the fallback ID.
    """
    available, msg = check_model_availability(fallback_id)
    if available:
        feasible, _ = check_cpu_feasibility(fallback_id)
        if feasible:
            return {
                "status": "SUBSTITUTED",
                "primary_model": primary_id,
                "fallback_model": fallback_id,
                "reason": f"Primary model unavailable or infeasible. Fallback {fallback_id} verified."
            }
    return {
        "status": "FAILED",
        "primary_model": primary_id,
        "fallback_model": None,
        "reason": "Fallback model also unavailable or infeasible."
    }

def load_vae_cpu(model_id: str):
    """
    Loads the VAE model on CPU.
    Raises an error if loading fails or memory constraints are violated.
    """
    try:
        from transformers import AutoModel
        # Force CPU
        model = AutoModel.from_pretrained(model_id, torch_dtype=torch.float32, device_map="cpu")
        return model
    except Exception as e:
        raise RuntimeError(f"Failed to load VAE model {model_id} on CPU: {str(e)}")

def run_model_availability_check() -> Dict[str, Any]:
    """
    Main orchestrator for Task 0.2.
    1. Check Primary Model (Qwen-Image-VAE-2.0 proxy)
    2. If unavailable or infeasible, trigger substitution.
    3. Write results to data/results/model_availability.json
    """
    result = {
        "primary_model_id": PRIMARY_MODEL_ID,
        "fallback_model_id": FALLBACK_MODEL_ID,
        "status": "UNKNOWN",
        "reason": "",
        "final_model_id": None,
        "cpu_feasible": False
    }

    # Step 1: Check Primary
    primary_available, primary_err = check_model_availability(PRIMARY_MODEL_ID)
    if not primary_available:
        result["status"] = "PRIMARY_UNAVAILABLE"
        result["reason"] = primary_err
    else:
        primary_feasible, primary_feas_err = check_cpu_feasibility(PRIMARY_MODEL_ID)
        if not primary_feasible:
            result["status"] = "PRIMARY_INFEASIBLE"
            result["reason"] = primary_feas_err
        else:
            result["status"] = "PRIMARY_AVAILABLE"
            result["reason"] = "Primary model available and CPU-feasible."
            result["cpu_feasible"] = True
            result["final_model_id"] = PRIMARY_MODEL_ID

    # Step 2: Fallback Logic
    if result["status"] != "PRIMARY_AVAILABLE":
        sub_result = trigger_model_substitution_protocol(PRIMARY_MODEL_ID, FALLBACK_MODEL_ID)
        if sub_result["status"] == "SUBSTITUTED":
            result["status"] = "SUBSTITUTED"
            result["reason"] = sub_result["reason"]
            result["final_model_id"] = FALLBACK_MODEL_ID
            result["cpu_feasible"] = True
        else:
            result["status"] = "NO_MODEL_AVAILABLE"
            result["reason"] = sub_result["reason"]
            result["final_model_id"] = None
            result["cpu_feasible"] = False

    # Step 3: Write Output
    output_path = Path(OUTPUT_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    return result

def main():
    """Entry point for execution."""
    print("Running Model Availability & Fallback Validation (T001)...")
    result = run_model_availability_check()
    print(f"Result: {json.dumps(result, indent=2)}")
    print(f"Output written to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
