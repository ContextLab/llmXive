"""
Script to verify that all required dependencies are installed and compatible.
This script is run after installation to ensure the environment is ready.
"""
import sys
import subprocess

def main():
    print("Checking Python version...")
    if not (sys.version_info.major == 3 and sys.version_info.minor == 11):
        print(f"ERROR: Python 3.11 is required. Found: {sys.version}")
        sys.exit(1)
    print("✓ Python 3.11 detected.")

    print("Checking PyTorch CPU configuration...")
    try:
        import torch
        if torch.cuda.is_available():
            print("WARNING: CUDA is available. This project is designed for CPU-only execution.")
            print("         Ensure you are using the CPU wheel if GPU resources are not intended.")
        else:
            print("✓ PyTorch is running in CPU-only mode.")
    except ImportError:
        print("ERROR: PyTorch is not installed.")
        sys.exit(1)

    print("Checking core libraries...")
    libs = ["transformers", "accelerate", "peft", "scikit-learn", "scipy", "pandas", "numpy"]
    for lib in libs:
        try:
            __import__(lib)
            print(f"✓ {lib} installed.")
        except ImportError:
            print(f"ERROR: {lib} is missing.")
            sys.exit(1)

    print("\nAll dependency checks passed.")

if __name__ == "__main__":
    main()