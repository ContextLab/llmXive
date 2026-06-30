import argparse
import sys
import os

# Ensure src is on path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.quantization.base import Quantizer
from src.quantization.uniform import UniformQuantizer
# KVarNQuantizer is expected to be implemented in T012, but we import it here
# to demonstrate the architecture. If T012 is not done, this import will fail,
# which is the correct behavior (fail loudly).
try:
    from src.quantization.kvarn import KVarNQuantizer
except ImportError:
    KVarNQuantizer = None

from src.benchmarks.loader import load_dataset_by_name, get_dataset_stats
from src.inference.hooks import KVCacheInterceptor

def get_quantizer(name: str, bits: int = 8) -> Quantizer:
    """Factory function to instantiate quantizers by name."""
    if name.lower() == "uniform":
        return UniformQuantizer(bits=bits)
    elif name.lower() == "kvarn":
        if KVarNQuantizer is None:
            raise RuntimeError(
                "KVarNQuantizer not found. Please ensure T012 (kvarn.py) is implemented."
            )
        return KVarNQuantizer(bits=bits)
    else:
        raise ValueError(f"Unknown quantization method: {name}. Choose 'uniform' or 'kvarn'.")

def run_experiment(model_id: str, dataset_name: str, quant_method: str, bits: int = 8):
    """
    Executes a single experiment:
    1. Loads the specified dataset.
    2. Instantiates the specified quantizer.
    3. (Placeholder for inference loop) - In a full implementation, this would
       load the model, run inference with the quantizer hooked in, and log results.
    
    For the purpose of T009 (Entry Point Configuration), this function demonstrates
    the argument parsing and setup logic.
    """
    print(f"--- Starting Experiment ---")
    print(f"Model: {model_id}")
    print(f"Dataset: {dataset_name}")
    print(f"Quantization: {quant_method} (bits={bits})")

    # 1. Load Dataset
    try:
        dataset = load_dataset_by_name(dataset_name)
        print(f"Dataset loaded: {len(dataset)} samples.")
        stats = get_dataset_stats(dataset_name)
        print(f"Dataset stats: {stats}")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    # 2. Initialize Quantizer
    try:
        quantizer = get_quantizer(quant_method, bits)
        print(f"Quantizer initialized: {type(quantizer).__name__}")
    except Exception as e:
        print(f"Error initializing quantizer: {e}")
        return

    # 3. Initialize Hook (Placeholder for engine integration)
    # In a real run, this would be passed to the inference engine
    hook = KVCacheInterceptor()
    print("KV Cache Interceptor initialized.")

    # 4. Execution Placeholder
    # A real implementation would:
    # - Load model (e.g., Phi-2)
    # - Run generation loop
    # - Capture errors
    # - Save to data/processed/
    print("Experiment configuration complete. Ready to run inference loop.")
    print("--- Experiment Configuration Verified ---")

def main():
    parser = argparse.ArgumentParser(
        description="Run KVarN Quantization Experiment",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--model",
        type=str,
        default="microsoft/phi-2",
        help="HuggingFace model ID (e.g., microsoft/phi-2)"
    )

    parser.add_argument(
        "--dataset",
        type=str,
        default="math_dataset",
        choices=["math_dataset", "aime", "human_eval", "ifeval"],
        help="Dataset to evaluate against"
    )

    parser.add_argument(
        "--method",
        type=str,
        default="uniform",
        choices=["uniform", "kvarn"],
        help="Quantization method: 'uniform' (baseline) or 'kvarn' (variance-normalized)"
    )

    parser.add_argument(
        "--bits",
        type=int,
        default=8,
        help="Number of bits for quantization"
    )

    args = parser.parse_args()

    run_experiment(
        model_id=args.model,
        dataset_name=args.dataset,
        quant_method=args.method,
        bits=args.bits
    )

if __name__ == "__main__":
    main()