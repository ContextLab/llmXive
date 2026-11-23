"""
Memory Footprint Verification for Quantized Base LLM.

This script explicitly verifies the memory footprint of the quantized base LLM
on the target runner before proceeding with the full evaluation loop.
It performs a dry-run inference to ensure compliance with the system memory constraint (7GB).
"""
import os
import sys
import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.utils.config import get_artifacts_path, get_results_path, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3
DUMMY_PROMPT = "This is a test prompt for memory verification."

def get_memory_usage() -> float:
    """
    Get current system memory usage in bytes.
    Tries psutil first, falls back to /proc/self/status on Linux.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
    except ImportError:
        logger.warning("psutil not found. Attempting Linux /proc fallback.")
        try:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        # VmRSS is in kB
                        return int(line.split()[1]) * 1024
        except Exception as e:
            logger.error(f"Could not read memory usage: {e}")
    return 0.0

def load_gguf_model(gguf_path: Path) -> Optional[Any]:
    """
    Attempts to load the GGUF model using llama-cpp-python.
    Returns the model object if successful, None otherwise.
    """
    try:
        from llama_cpp import Llama
        logger.info(f"Attempting to load model from: {gguf_path}")
        
        # Check file existence
        if not gguf_path.exists():
            logger.error(f"Model file not found: {gguf_path}")
            return None

        # Load with minimal settings for memory check
        model = Llama(
            model_path=str(gguf_path),
            n_ctx=128,  # Minimal context for dry run
            n_gpu_layers=0,  # Force CPU for consistent memory measurement
            verbose=False
        )
        logger.info(f"Model loaded successfully: {model}")
        return model
    except ImportError:
        logger.error("llama-cpp-python not installed. Cannot verify memory footprint.")
        return None
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None

def run_dry_run_inference(model: Any, prompt: str = DUMMY_PROMPT) -> bool:
    """
    Runs a minimal inference to trigger memory allocation.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info("Running dry-run inference...")
        # Minimal generation
        output = model(
            prompt,
            max_tokens=4,
            temperature=0.0,
            echo=False
        )
        logger.info("Dry-run inference completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Dry-run inference failed: {e}")
        return False

def verify_memory_footprint(
    gguf_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main verification logic.
    
    Args:
        gguf_path: Path to the quantized GGUF model. If None, attempts to find it in artifacts.
        output_path: Path to save the verification report.
        
    Returns:
        Dictionary containing verification results.
    """
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "memory_limit_gb": MEMORY_LIMIT_GB,
        "model_path": None,
        "pre_inference_memory_gb": 0.0,
        "post_inference_memory_gb": 0.0,
        "peak_memory_gb": 0.0,
        "memory_delta_gb": 0.0,
        "status": "UNKNOWN",
        "message": ""
    }

    # Ensure directories
    ensure_directories()
    
    # Resolve model path
    if gguf_path is None:
        artifacts_path = get_artifacts_path()
        # Look for GGUF files in artifacts/models
        models_dir = artifacts_path / "models"
        if models_dir.exists():
            gguf_files = list(models_dir.glob("*.gguf"))
            if gguf_files:
                gguf_path = gguf_files[0]
                logger.info(f"Auto-detected model: {gguf_path}")
            else:
                logger.error(f"No GGUF files found in {models_dir}")
                results["status"] = "FAILED"
                results["message"] = "No GGUF model found in artifacts/models"
                return results
        else:
            logger.error(f"Artifacts models directory not found: {models_dir}")
            results["status"] = "FAILED"
            results["message"] = "Artifacts models directory not found"
            return results

    results["model_path"] = str(gguf_path)

    # Check initial memory
    pre_memory = get_memory_usage()
    results["pre_inference_memory_gb"] = pre_memory / (1024**3)
    logger.info(f"Pre-inference memory usage: {results['pre_inference_memory_gb']:.2f} GB")

    # Load model
    model = load_gguf_model(gguf_path)
    if model is None:
        results["status"] = "FAILED"
        results["message"] = "Failed to load model"
        return results

    # Run dry run
    if not run_dry_run_inference(model):
        results["status"] = "FAILED"
        results["message"] = "Dry-run inference failed"
        return results

    # Check memory after inference
    post_memory = get_memory_usage()
    results["post_inference_memory_gb"] = post_memory / (1024**3)
    results["peak_memory_gb"] = max(pre_memory, post_memory) / (1024**3)
    results["memory_delta_gb"] = (post_memory - pre_memory) / (1024**3)
    
    logger.info(f"Post-inference memory usage: {results['post_inference_memory_gb']:.2f} GB")
    logger.info(f"Memory delta: {results['memory_delta_gb']:.2f} GB")

    # Verify against limit
    if post_memory > MEMORY_LIMIT_BYTES:
        results["status"] = "FAILED"
        results["message"] = f"Memory usage ({results['peak_memory_gb']:.2f} GB) exceeds limit ({MEMORY_LIMIT_GB} GB)"
    else:
        results["status"] = "SUCCESS"
        results["message"] = f"Memory usage ({results['peak_memory_gb']:.2f} GB) is within limit ({MEMORY_LIMIT_GB} GB)"

    # Save report if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Verification report saved to: {output_path}")

    return results

def main():
    """Main entry point."""
    logger.info("Starting memory footprint verification...")
    
    # Default paths
    results_path = get_results_path()
    output_file = results_path / "memory_footprint_verification.json"
    
    # Run verification
    results = verify_memory_footprint(output_path=output_file)
    
    # Log final status
    if results["status"] == "SUCCESS":
        logger.info("Memory verification PASSED.")
        return 0
    else:
        logger.error(f"Memory verification FAILED: {results['message']}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
