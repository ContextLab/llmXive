"""
Tests for T043: Verify requirements.txt compliance.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code directory to path to import the verification logic if needed,
# but here we test the logic directly or the file content.

def test_no_gpu_libraries_in_requirements():
    """
    Verify that requirements.txt does not contain GPU-specific libraries.
    """
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "requirements.txt"
    
    if not requirements_path.exists():
        pytest.skip("requirements.txt not found in project root")

    gpu_libs = {
        'torch', 'torchvision', 'torchaudio',
        'tensorflow', 'tensorflow-gpu', 'tf-keras',
        'jax', 'jaxlib', 'flax',
        'cupy', 'horovod', 'deepspeed'
    }

    with open(requirements_path, 'r', encoding='utf-8') as f:
        content = f.read().lower()

    for lib in gpu_libs:
        # Check for the library name as a whole word to avoid false positives
        # e.g., "my-torch-tool" shouldn't trigger, but "torch" should.
        # Simple check: if the lib name appears at start of line or after newline/space
        # Since we are reading full text, we look for the lib name followed by non-alphanumeric or end of string
        # But simpler: split by lines and check start
        lines = content.split('\n')
        for line in lines:
            if line.startswith('#') or not line.strip():
                continue
            pkg = line.split('==')[0].split('>=')[0].split('<=')[0].split('[')[0].strip()
            if pkg == lib:
                pytest.fail(f"GPU library '{lib}' found in requirements.txt")

def test_no_llm_libraries_in_requirements():
    """
    Verify that requirements.txt does not contain LLM-specific inference libraries.
    Note: 'datasets' and 'huggingface-hub' are allowed for data loading,
    but inference engines like 'transformers', 'langchain' are not.
    """
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "requirements.txt"
    
    if not requirements_path.exists():
        pytest.skip("requirements.txt not found in project root")

    llm_libs = {
        'transformers', 'langchain', 'langchain-core', 'langchain-community',
        'llama-index', 'llama-index-core',
        'openai', 'anthropic', 'cohere',
        'peft', 'bitsandbytes', 'trl'
    }

    with open(requirements_path, 'r', encoding='utf-8') as f:
        content = f.read().lower()

    for lib in llm_libs:
        lines = content.split('\n')
        for line in lines:
            if line.startswith('#') or not line.strip():
                continue
            pkg = line.split('==')[0].split('>=')[0].split('<=')[0].split('[')[0].strip()
            if pkg == lib:
                pytest.fail(f"LLM library '{lib}' found in requirements.txt")

def test_requirements_file_exists():
    """
    Ensure requirements.txt exists.
    """
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt must exist"
