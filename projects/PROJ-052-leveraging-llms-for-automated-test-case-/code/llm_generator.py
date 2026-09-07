import os
import logging
import traceback
import time
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List

# Import shared configuration
from config import get_model_path, get_timeout_inference, get_output_dir, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global model instance (lazy load)
_model = None

def load_model():
    """
    Load the CPU-optimized LLM (Phi-2 or similar) using llama-cpp-python.
    Returns the loaded model instance.
    """
    global _model
    if _model is not None:
        return _model

    model_path = get_model_path()
    if not model_path or not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}. Please set MODEL_PATH env var.")

    logger.info(f"Loading model from {model_path}...")
    try:
        from llama_cpp import Llama
        # Load with Q4_K_M quantization logic implied by the model file path
        # and constrained RAM settings from config.
        _model = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            verbose=False
        )
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    return _model

def generate_from_prompt(prompt: str, max_tokens: int = 512) -> str:
    """
    Generate text from a prompt using the loaded model.
    """
    model = load_model()
    try:
        output = model(
            prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            stop=["###", "```"],
            echo=False
        )
        return output['choices'][0]['text'].strip()
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise

def generate_test_code(bug_description: str, output_dir: Optional[str] = None) -> Tuple[str, bool]:
    """
    Generate a JUnit test case from a bug description.
    
    Args:
        bug_description: The natural language description of the bug.
        output_dir: Directory to write the generated .java file.
        
    Returns:
        A tuple (file_path, success).
        If the input is ambiguous (len < 20), returns the default template path.
    """
    if output_dir is None:
        output_dir = get_output_dir()
    ensure_directories()
    
    # 1. Check for ambiguous input
    if len(bug_description.strip()) < 20:
        logger.warning(f"Ambiguous input detected (length={len(bug_description)}). Loading default template.")
        template_path = Path("data/templates/default_test.java")
        if not template_path.exists():
            raise FileNotFoundError(f"Default template not found at {template_path}")
        
        # Read template and return path
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Write to output directory as a fallback
        output_file = Path(output_dir) / "DefaultBugFixTest.java"
        with open(output_file, 'w') as f:
            f.write(content)
        
        logger.warning(f"Default template written to {output_file}")
        return str(output_file), True

    # 2. Construct Prompt
    # Based on typical LLM prompting for code generation
    system_prompt = """You are an expert Java developer. Generate a valid JUnit 4 test class to verify the fix for the described bug.
    The test should be in a class named `BugFixTest`.
    Include meaningful assertions based on the bug description.
    Do not include markdown code blocks (```java), just the raw code.
    """
    user_prompt = f"Bug Description: {bug_description}\n\nGenerate the test class:"
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    # 3. Generate Code
    try:
        generated_code = generate_from_prompt(full_prompt)
    except Exception as e:
        logger.error(f"LLM generation failed for input: {bug_description[:50]}... Error: {e}")
        return "", False

    # 4. Clean and Save
    # Remove potential markdown wrappers if the model added them despite instructions
    if generated_code.startswith("```java"):
        generated_code = generated_code[7:]
    if generated_code.endswith("```"):
        generated_code = generated_code[:-3]
    generated_code = generated_code.strip()

    # Create a unique filename based on a hash or timestamp if needed, 
    # but for simplicity in this task, we assume the caller handles naming or we use a generic one.
    # However, the task implies returning a file path. Let's create a deterministic name.
    # In a real pipeline, we might map bug_id to filename. Here we use a temp name.
    import hashlib
    safe_name = hashlib.md5(bug_description.encode()).hexdigest()[:8]
    filename = f"BugFixTest_{safe_name}.java"
    output_path = Path(output_dir) / filename

    with open(output_path, 'w') as f:
        f.write(generated_code)

    logger.info(f"Generated test code saved to {output_path}")
    return str(output_path), True

def validate_syntax_java(file_path: str) -> bool:
    """
    Validate the syntax of a Java file using `javac`.
    Returns True if compilation succeeds (no syntax errors), False otherwise.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False

    try:
        # Run javac with the file
        result = subprocess.run(
            ['javac', file_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logger.debug(f"Syntax validation passed for {file_path}")
            return True
        else:
            logger.warning(f"Syntax validation failed for {file_path}:\n{result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"Compilation timeout for {file_path}")
        return False
    except FileNotFoundError:
        logger.error("javac not found in PATH. Please install Java Development Kit.")
        raise

def main():
    """
    Entry point for testing the generator logic directly.
    """
    # Example usage
    test_cases = [
        "Short",  # Should trigger default
        "This is a very long and detailed bug description that explains exactly what is wrong with the sorting algorithm in the list class when duplicate values are present.", # Should trigger LLM
    ]
    
    output_dir = get_output_dir()
    ensure_directories()

    for desc in test_cases:
        print(f"Processing: '{desc}'")
        path, success = generate_test_code(desc, output_dir)
        if success:
            is_valid = validate_syntax_java(path)
            print(f"  -> Generated: {path}, Valid: {is_valid}")
        else:
            print(f"  -> Failed to generate")
        print("-" * 20)

if __name__ == "__main__":
    main()