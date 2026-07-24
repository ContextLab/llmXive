import os
import logging
import traceback
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
import json

from config import get_model_path, get_timeout_inference, ensure_directories, get_data_dir, get_output_dir
from data_loader import load_defects4j_data, extract_bug_fix_description

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

_model = None
_model_path = None

def load_model(model_path: Optional[str] = None, n_ctx: int = 2048, n_threads: int = 4) -> Any:
    """
    Load the Phi-2 model using llama-cpp-python.
    Caches the loaded model globally to avoid reloading.
    """
    global _model, _model_path

    if model_path is None:
        model_path = get_model_path()

    if _model is not None and _model_path == model_path:
        logger.info(f"Model already loaded from {model_path}")
        return _model

    logger.info(f"Loading model from {model_path}...")
    
    try:
        from llama_cpp import Llama
        
        # Ensure the model file exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}. "
                                    "Please download the quantized Phi-2 model (e.g., Q4_K_M.gguf) first.")

        _model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=0,  # CPU-only as per constraints
            verbose=False
        )
        _model_path = model_path
        logger.info("Model loaded successfully.")
        return _model
    except ImportError:
        logger.error("llama-cpp-python not installed. Please install it via requirements.txt.")
        raise
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_from_prompt(
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.0,
    seed: int = 42,
    stop_sequences: Optional[List[str]] = None
) -> str:
    """
    Generate text from a prompt using the loaded model with deterministic settings.
    """
    global _model

    if _model is None:
        logger.warning("Model not loaded. Attempting to load with defaults.")
        load_model()

    if _model is None:
        raise RuntimeError("Model failed to load. Cannot generate text.")

    if stop_sequences is None:
        stop_sequences = ["\n\n", "```", "</s>"]

    logger.info(f"Generating text for prompt length: {len(prompt)}")
    
    try:
        start_time = time.time()
        output = _model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.95,
            top_k=40,
            stop=stop_sequences,
            echo=False,
            seed=seed
        )
        
        elapsed = time.time() - start_time
        logger.info(f"Generation completed in {elapsed:.2f}s")
        
        return output['choices'][0]['text'].strip()
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        traceback.print_exc()
        raise

def generate_test_code(
    bug_id: str,
    description: str,
    output_dir: Optional[str] = None,
    model_path: Optional[str] = None,
    max_tokens: int = 512,
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a JUnit test case for a given bug description using Phi-2.
    
    Args:
        bug_id: Unique identifier for the bug (e.g., 'Lang-1')
        description: Natural language description of the bug fix
        output_dir: Directory to save the generated .java file
        model_path: Path to the Phi-2 model (overrides config)
        max_tokens: Maximum tokens to generate
        timeout: Timeout in seconds for the generation process
    
    Returns:
        Dict containing 'file_path', 'generated_code', 'status', 'error'
    """
    if output_dir is None:
        output_dir = get_output_dir()
    
    ensure_directories()
    
    # Format the prompt
    system_prompt = """You are an expert Java developer. Your task is to write a JUnit 4 test case 
    that verifies the fix for a specific bug. The test should be a single class file.
    Include necessary imports. Use standard JUnit assertions (@Test, assertEquals, assertTrue, etc.).
    Do not include markdown formatting (no ```java ... ```). Just output the raw Java code."""
    
    user_prompt = f"""
    Bug ID: {bug_id}
    Bug Description: {description}
    
    Please generate the JUnit test code now.
    """
    
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    try:
        # Load model if not already loaded
        load_model(model_path=model_path)
        
        # Generate code
        generated_code = generate_from_prompt(
            full_prompt,
            max_tokens=max_tokens,
            temperature=0.0,  # Deterministic
            seed=42          # Deterministic
        )
        
        # Clean up code (remove potential markdown artifacts if model hallucinates them)
        if generated_code.startswith("```java"):
            generated_code = generated_code[7:]
        if generated_code.startswith("```"):
            generated_code = generated_code[3:]
        if generated_code.endswith("```"):
            generated_code = generated_code[:-3]
        
        generated_code = generated_code.strip()
        
        # Sanitize filename
        safe_id = "".join(c if c.isalnum() else "_" for c in bug_id)
        filename = f"Test_{safe_id}.java"
        file_path = Path(output_dir) / filename
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(generated_code)
        
        logger.info(f"Generated test code for {bug_id} saved to {file_path}")
        
        return {
            "file_path": str(file_path),
            "generated_code": generated_code,
            "status": "success",
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Failed to generate test code for {bug_id}: {e}")
        traceback.print_exc()
        return {
            "file_path": None,
            "generated_code": None,
            "status": "failed",
            "error": str(e)
        }

def validate_syntax_java(file_path: str) -> bool:
    """
    Validate Java syntax using javac.
    Returns True if valid, False otherwise.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    
    try:
        # Attempt to compile
        result = subprocess.run(
            ['javac', '-Xlint:none', '-proc:none', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f"Syntax validation passed for {file_path}")
            return True
        else:
            logger.warning(f"Syntax validation failed for {file_path}: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.error("javac not found in PATH. Cannot validate syntax.")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"Compilation timeout for {file_path}")
        return False
    except Exception as e:
        logger.error(f"Error during validation: {e}")
        return False

def main():
    """
    Main entry point for generating test codes from Defects4J data.
    """
    logger.info("Starting test code generation pipeline...")
    
    # Ensure data is loaded
    try:
        data = load_defects4j_data()
    except Exception as e:
        logger.error(f"Failed to load Defects4J data: {e}")
        return
    
    if data is None or data.empty:
        logger.error("No data loaded.")
        return
    
    # Get sample limit from config
    from config import get_sample_limit
    sample_limit = get_sample_limit()
    
    # Process up to sample_limit bugs
    count = 0
    for idx, row in data.iterrows():
        if count >= sample_limit:
            logger.info(f"Reached sample limit ({sample_limit}). Stopping.")
            break
        
        bug_id = row.get('project_id', row.get('bug_id', f'bug_{idx}'))
        description = extract_bug_fix_description(row)
        
        if not description or len(description) < 20:
            logger.warning(f"Skipping {bug_id}: Description too short or empty.")
            continue
        
        result = generate_test_code(
            bug_id=bug_id,
            description=description,
            max_tokens=512,
            temperature=0.0,
            seed=42
        )
        
        if result['status'] == 'success':
            logger.info(f"Successfully generated test for {bug_id}")
            # Optional: Validate syntax immediately
            # if validate_syntax_java(result['file_path']):
            #     logger.info(f"Syntax valid for {bug_id}")
            # else:
            #     logger.warning(f"Syntax invalid for {bug_id}")
            count += 1
        else:
            logger.error(f"Failed to generate test for {bug_id}: {result['error']}")
    
    logger.info(f"Generation pipeline finished. Processed {count} bugs.")

if __name__ == "__main__":
    main()
