"""
Validate sentence-transformers model compatibility for CPU-only execution.

This script verifies that the selected sentence-transformers model variant
for leakage detection operates correctly on CPU without requiring GPU
allocation or quantization libraries.

Output: data/logs/sentence_transformers_validation.json
"""
import json
import os
import sys
import time
from pathlib import Path

# Ensure we can import from the project root if needed, though this is a standalone script
# Add the project root to path just in case, but we rely on standard library + installed packages
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def validate_sentence_transformers():
    """
    Validates the sentence-transformers model for CPU-only compatibility.
    
    Returns:
        dict: Validation results including status, model info, and metrics.
    """
    results = {
        "status": "pending",
        "model_name": "all-MiniLM-L6-v2",  # Standard lightweight model for semantic similarity
        "cpu_only": False,
        "quantization_required": False,
        "inference_time_ms": None,
        "memory_peak_mb": None,
        "error": None,
        "details": []
    }

    try:
        # Check for GPU libraries availability (but do not use them)
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            results["details"].append(f"CUDA available: {cuda_available}")
            
            # Explicitly force CPU device
            device = "cpu"
            if cuda_available:
                results["details"].append("WARNING: GPU detected, but forcing CPU execution as per constraints.")
        except ImportError:
            results["details"].append("PyTorch not found or not installed with CUDA support.")
            device = "cpu"

        # Import sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            results["status"] = "failed"
            results["error"] = "sentence-transformers library not installed. Please install it via requirements.txt."
            return results

        # Load the model explicitly on CPU
        # Using 'all-MiniLM-L6-v2' as it is a standard, lightweight model suitable for CPU
        model_name = results["model_name"]
        results["details"].append(f"Loading model: {model_name}")
        
        start_load = time.time()
        model = SentenceTransformer(model_name, device=device)
        load_time = time.time() - start_load
        results["details"].append(f"Model loaded in {load_time:.2f}s")

        # Verify device placement
        model_device = next(model.parameters()).device
        results["details"].append(f"Model device: {model_device}")
        
        if "cuda" in str(model_device):
            results["status"] = "failed"
            results["error"] = "Model was loaded on GPU despite CPU constraint."
            return results

        results["cpu_only"] = True
        results["quantization_required"] = False

        # Perform a dummy inference to verify functionality and measure time
        test_sentences = [
            "The user requested deletion of their personal data.",
            "This is a test sentence for embedding validation.",
            "Leakage detection requires semantic similarity checks."
        ]

        results["details"].append("Running inference on test sentences...")
        start_inference = time.time()
        embeddings = model.encode(test_sentences, show_progress_bar=False)
        inference_time = time.time() - start_inference
        results["inference_time_ms"] = round(inference_time * 1000, 2)
        results["details"].append(f"Inference completed in {results['inference_time_ms']}ms")

        # Verify embeddings shape and type
        if embeddings.shape[0] != len(test_sentences):
            results["status"] = "failed"
            results["error"] = "Embeddings shape mismatch."
            return results

        # Check memory usage (approximate using torch if available, else skip)
        try:
            if torch.cuda.is_available():
                # Even if we force CPU, checking peak memory on CPU is not directly supported by torch.cuda
                # We rely on the fact that we forced CPU and no CUDA tensors were created
                results["memory_peak_mb"] = None
                results["details"].append("Memory peak not measured (CPU mode).")
            else:
                results["memory_peak_mb"] = None
                results["details"].append("Memory peak not measured (CPU mode).")
        except Exception as mem_err:
            results["details"].append(f"Could not measure memory: {str(mem_err)}")

        results["status"] = "success"
        results["details"].append("Validation passed: Model is CPU-only and functional.")

    except Exception as e:
        results["status"] = "failed"
        results["error"] = str(e)
        results["details"].append(f"Unexpected error: {str(e)}")

    return results

def main():
    """Main entry point."""
    print("Starting sentence-transformers validation...")
    
    # Ensure output directory exists
    output_dir = Path("data/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "sentence_transformers_validation.json"

    results = validate_sentence_transformers()

    # Write results to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Validation complete. Results written to: {output_path}")
    
    if results["status"] == "success":
        print("SUCCESS: Model is compatible with CPU-only execution.")
        sys.exit(0)
    else:
        print(f"FAILED: {results.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
