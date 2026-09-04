"""
Script to generate dummy adapter weights for testing purposes.
This is ONLY for unit testing or development when T010 has not yet run.
In production, T010 must run to generate real weights.
"""
import os
import torch
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

OUTPUT_PATH = "data/processed/adapter_weights.pt"

def main():
    # Ensure directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Create a dummy state dict matching the LinearProbe structure
    # Input dim: 768 (MobileViT small), Output dim: 10 (example action space)
    state_dict = {
        'probe.weight': torch.randn(10, 768),
        'probe.bias': torch.randn(10)
    }

    torch.save(state_dict, OUTPUT_PATH)
    print(f"Dummy weights generated at: {OUTPUT_PATH}")
    print("WARNING: These are synthetic weights. T010 must run for real results.")

if __name__ == "__main__":
    main()