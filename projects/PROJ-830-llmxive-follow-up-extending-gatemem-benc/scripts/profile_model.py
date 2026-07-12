"""
Script to profile the frozen DistilBERT model on CPU.
Verifies no GPU allocation and outputs a profile report to data/logs/model_profile.json.
"""
import json
import os
import sys
import time
import resource
import torch
from transformers import DistilBertTokenizer, DistilBertModel

# Ensure the script can run from the project root or scripts directory
def get_project_root():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Check if we are in scripts/
    if os.path.basename(current_dir) == "scripts":
        return os.path.dirname(current_dir)
    # Fallback: look for the project ID folder
    parent = os.path.dirname(current_dir)
    if "PROJ-830-llmxive-follow-up-extending-gatemem-benc" in parent:
        return parent
    return current_dir

PROJECT_ROOT = get_project_root()
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "logs", "model_profile.json")

# Ensure output directory exists
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

MODEL_NAME = "distilbert-base-uncased"

def get_memory_usage_mb():
    """Get current RAM usage in MB using resource module (Linux/macOS)."""
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024.0  # Convert KB to MB
    except AttributeError:
        # Fallback for non-Unix systems (approximate)
        return 0.0

def verify_cpu_only():
    """Verify that no GPU is available or being used."""
    if torch.cuda.is_available():
        return False, "CUDA is available but should be disabled for this task."
    if torch.cuda.device_count() > 0:
        return False, f"GPU devices detected: {torch.cuda.device_count()}"
    return True, "No GPU detected; running on CPU."

def profile_model():
    """Load DistilBERT, run a forward pass, and collect profile metrics."""
    results = {
        "model_name": MODEL_NAME,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "device": "cpu",
        "precision": "float32",
        "checks": {},
        "metrics": {}
    }

    # 1. Verify CPU-only constraint
    is_cpu, msg = verify_cpu_only()
    results["checks"]["cpu_only_verified"] = is_cpu
    results["checks"]["cpu_message"] = msg

    if not is_cpu:
        results["error"] = "GPU detected. Aborting profile to comply with CPU-only constraint."
        with open(OUTPUT_PATH, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Profile failed: {msg}")
        sys.exit(1)

    # 2. Record baseline memory
    baseline_mem = get_memory_usage_mb()
    results["metrics"]["baseline_memory_mb"] = round(baseline_mem, 2)

    print(f"Loading tokenizer and model: {MODEL_NAME} on CPU...")
    start_time = time.time()

    # 3. Load Tokenizer and Model (frozen, default precision)
    try:
        tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)
        model = DistilBertModel.from_pretrained(MODEL_NAME)
        model.eval()
        
        # Explicitly move to CPU to ensure no accidental GPU usage
        model = model.to("cpu")
        
        # Freeze parameters (frozen model)
        for param in model.parameters():
            param.requires_grad = False

    except Exception as e:
        results["error"] = f"Failed to load model: {str(e)}"
        with open(OUTPUT_PATH, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Error loading model: {e}")
        sys.exit(1)

    load_time = time.time() - start_time
    results["metrics"]["load_time_seconds"] = round(load_time, 3)
    print(f"Model loaded in {load_time:.3f}s")

    # 4. Verify no GPU tensors
    has_gpu_tensor = any(p.is_cuda for p in model.parameters())
    results["checks"]["no_gpu_tensors"] = not has_gpu_tensor
    if has_gpu_tensor:
        results["checks"]["no_gpu_tensors"] = False
        results["error"] = "Model parameters detected on GPU."
        with open(OUTPUT_PATH, "w") as f:
            json.dump(results, f, indent=2)
        sys.exit(1)

    # 5. Run a forward pass with sample input
    sample_text = "Hello, this is a test input for profiling."
    inputs = tokenizer(sample_text, return_tensors="pt")
    inputs = {k: v.to("cpu") for k, v in inputs.items()}

    print(f"Running forward pass with sample input: '{sample_text}'")
    start_inference = time.time()

    with torch.no_grad():
        outputs = model(**inputs)
        
    inference_time = time.time() - start_inference
    results["metrics"]["inference_time_seconds"] = round(inference_time, 3)
    results["metrics"]["output_hidden_size"] = outputs.last_hidden_state.shape[2]
    results["metrics"]["batch_size"] = outputs.last_hidden_state.shape[0]
    results["metrics"]["sequence_length"] = outputs.last_hidden_state.shape[1]

    # 6. Record peak memory
    peak_mem = get_memory_usage_mb()
    results["metrics"]["peak_memory_mb"] = round(peak_mem, 2)
    results["metrics"]["memory_delta_mb"] = round(peak_mem - baseline_mem, 2)

    # 7. Final status
    results["status"] = "success"
    results["message"] = "Profile completed successfully. No GPU allocation detected."

    # Write report
    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Profile report written to: {OUTPUT_PATH}")
    print(f"Status: {results['status']}")
    print(f"Memory Delta: {results['metrics']['memory_delta_mb']:.2f} MB")
    print(f"Inference Time: {results['metrics']['inference_time_seconds']:.3f} s")

if __name__ == "__main__":
    profile_model()
