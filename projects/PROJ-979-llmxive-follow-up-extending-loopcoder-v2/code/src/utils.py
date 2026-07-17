"""
Utility functions for the llmXive pipeline.

Includes FLOPs calculation for baseline computation and other shared helpers.
"""
from typing import Union

def calculate_flops(parameters: int, sequence_length: int, k: int) -> float:
    """
    Calculate the baseline Floating Point Operations (FLOPs) for a model execution.
    
    Implements the formula: FLOPs = parameters * sequence_length * k
    
    This is used for:
    - FR-006: Comparing dynamic routing vs static baseline efficiency.
    - SC-002: Estimating computational cost savings.
    
    Args:
        parameters (int): Total number of model parameters.
        sequence_length (int): Length of the input/output sequence.
        k (int): Number of inference loops or iterations.
        
    Returns:
        float: The estimated total FLOPs.
        
    Raises:
        ValueError: If any input is negative.
    """
    if parameters < 0 or sequence_length < 0 or k < 0:
        raise ValueError("parameters, sequence_length, and k must be non-negative.")
    
    return float(parameters * sequence_length * k)

def get_model_param_count(model_name: str) -> int:
    """
    Returns the approximate parameter count for known CodeLlama variants.
    
    Args:
        model_name (str): The HuggingFace model identifier.
        
    Returns:
        int: Estimated parameter count in billions (multiplied by 1e9).
        
    Note:
        This is a helper for quick estimation. For precise counts, use the
        model config from the transformers library.
    """
    model_name_lower = model_name.lower()
    
    if "1.3b" in model_name_lower:
        return int(1.3e9)
    elif "3b" in model_name_lower or "34b" in model_name_lower: # Assuming 34b typo in prompt context or specific variant, but sticking to 3b as per plan
        if "34b" in model_name_lower:
            return int(34e9)
        return int(3e9)
    elif "7b" in model_name_lower:
        return int(7e9)
    elif "70b" in model_name_lower:
        return int(70e9)
    else:
        # Default fallback for unknown models - raise or return 0? 
        # Returning 0 to force explicit configuration if unknown
        raise ValueError(f"Unknown model parameter count for: {model_name}. Please specify manually.")

def main():
    """
    CLI entry point for testing FLOPs calculation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate baseline FLOPs.")
    parser.add_argument("--params", type=int, default=1300000000, help="Model parameters (e.g., 1.3e9)")
    parser.add_argument("--seq-len", type=int, default=512, help="Sequence length")
    parser.add_argument("--k", type=int, default=2, help="Number of loops")
    
    args = parser.parse_args()
    
    flops = calculate_flops(args.params, args.seq_len, args.k)
    print(f"Parameters: {args.params}")
    print(f"Sequence Length: {args.seq_len}")
    print(f"K (Loops): {args.k}")
    print(f"Estimated FLOPs: {flops:.2e}")

if __name__ == "__main__":
    main()