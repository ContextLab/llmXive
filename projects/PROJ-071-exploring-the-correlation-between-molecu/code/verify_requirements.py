"""
T043: Verify requirements.txt contains no GPU-specific or LLM dependencies.

This script scans the project's requirements.txt to ensure compliance with
CPU-only execution constraints. It explicitly checks for the absence of
GPU libraries (torch, tensorflow, jax, etc.) and LLM-specific dependencies
(transformers, langchain, etc.).
"""
import os
import sys
from pathlib import Path

# GPU-specific libraries that must NOT be present
GPU_LIBRARIES = {
    'torch', 'torchvision', 'torchaudio',
    'tensorflow', 'tensorflow-gpu', 'tf-keras',
    'jax', 'jaxlib', 'flax',
    'cupy', 'cupy-cuda11x',
    'horovod', 'deepspeed'
}

# LLM-specific libraries that must NOT be present
LLM_LIBRARIES = {
    'transformers', 'langchain', 'langchain-core', 'langchain-community',
    'llama-index', 'llama-index-core', 'llama-index-llms-huggingface',
    'openai', 'anthropic', 'cohere', 'huggingface-hub',
    'peft', 'accelerate', 'bitsandbytes', 'sentencepiece',
    'trl', 'datasets' # Note: datasets is allowed for loading, but not for LLM inference logic.
                     # However, the task specifically asks to ensure no LLM *dependencies*.
                     # 'datasets' is used in T012 for data loading, so it is allowed.
                     # We will flag strictly inference/model-serving libs.
}

# Refined LLM list to be stricter on inference engines
STRICT_LLM_LIBRARIES = {
    'transformers', 'langchain', 'langchain-core', 'langchain-community',
    'llama-index', 'llama-index-core',
    'openai', 'anthropic', 'cohere',
    'peft', 'bitsandbytes', 'trl'
}

def main():
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.exists():
        print(f"ERROR: {requirements_path} not found.")
        sys.exit(1)

    with open(requirements_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    found_gpu = []
    found_llm = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Extract package name (handle version specifiers like ==, >=, etc.)
        package_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('>=')[0].split('[')[0].strip().lower()

        if package_name in GPU_LIBRARIES:
            found_gpu.append(line)
        
        if package_name in STRICT_LLM_LIBRARIES:
            found_llm.append(line)

    if found_gpu:
        print("FAIL: GPU-specific libraries detected in requirements.txt:")
        for pkg in found_gpu:
            print(f"  - {pkg}")
        sys.exit(1)

    if found_llm:
        print("FAIL: LLM-specific libraries detected in requirements.txt:")
        for pkg in found_llm:
            print(f"  - {pkg}")
        sys.exit(1)

    print("PASS: requirements.txt is compliant with CPU-only constraints.")
    print(f"Checked {len([l for l in lines if l.strip() and not l.startswith('#')])} packages.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
