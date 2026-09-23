"""
LLM-based test code generation module.
Uses llama-cpp-python for CPU-optimized inference.
"""
import os
import logging
import traceback
import time
import subprocess
import tempfile
from typing import Optional, List
from pathlib import Path

from config import get_model_path, get_timeout_inference, get_sample_limit
from utils.retry import execute_with_retry

logger = logging.getLogger(__name__)

class MemoryExceededError(Exception):
    """Raised when model loading exceeds memory limits."""
    pass

def load_model(
    model_path: Optional[str] = None,
    n_ctx: int = 2048,
    n_threads: int = 4
):
    """
    Load the LLM model.
    
    Args:
        model_path: Path to the model file.
        n_ctx: Context size.
        n_threads: Number of threads.
        
    Returns:
        Loaded model object.
    """
    from llama_cpp import Llama
    import psutil
    
    path = model_path or get_model_path()
    
    # Check memory before loading
    mem = psutil.virtual_memory()
    if mem.available < 7 * 1024 * 1024 * 1024:  # 7GB
        raise MemoryExceededError(f"Insufficient memory available: {mem.available / (1024**3):.2f}GB")
    
    def _load():
        return Llama(
            model_path=path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=0  # CPU only
        )
    
    try:
        return execute_with_retry(
            _load,
            max_retries=3,
            base_delay=5.0,
            timeout=120.0,
            exception_types=(MemoryError, OSError)
        )
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_from_prompt(
    model,
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.0,
    seed: int = 42
) -> str:
    """
    Generate text from a prompt.
    
    Args:
        model: The loaded LLM model.
        prompt: Input prompt.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
        seed: Random seed.
        
    Returns:
        Generated text.
    """
    def _generate():
        output = model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            seed=seed,
            stop=["</test>", "```"]
        )
        return output['choices'][0]['text']
    
    try:
        return execute_with_retry(
            _generate,
            max_retries=3,
            base_delay=2.0,
            timeout=get_timeout_inference(),
            exception_types=(Exception,)
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise

def generate_test_code(
    bug_description: str,
    model: Optional = None
) -> str:
    """
    Generate test code from a bug description.
    
    Args:
        bug_description: The bug description.
        model: Optional pre-loaded model.
        
    Returns:
        Generated Java test code.
    """
    if model is None:
        model = load_model()
    
    prompt = f"""
    Generate a JUnit 4 test class for the following bug description:
    {bug_description}
    
    Ensure the test is syntactically valid Java.
    Include at least one @Test method.
    """
    
    return generate_from_prompt(model, prompt)

def validate_syntax_java(code: str, output_path: Path) -> bool:
    """
    Validate Java syntax by attempting compilation.
    
    Args:
        code: Java source code.
        output_path: Path to write the temporary file.
        
    Returns:
        True if syntax is valid.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix='.java', delete=False, dir=output_path.parent) as f:
            f.write(code.encode('utf-8'))
            temp_file = Path(f.name)
        
        cmd = ['javac', '-Xlint:none', str(temp_file)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        os.unlink(temp_file)
        
        if result.returncode == 0:
            return True
        else:
            logger.warning(f"Syntax validation failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False

def main():
    """Main entry point for LLM generator module."""
    logger.info("LLM generator module loaded.")

if __name__ == "__main__":
    main()