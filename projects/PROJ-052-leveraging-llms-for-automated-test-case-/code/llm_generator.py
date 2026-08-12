import os
import logging
import traceback
import time
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from config import get_model_path, get_timeout_inference, ensure_directories
from data_loader import load_defects4j_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global model instance (lazy load)
_model_instance = None

def load_model():
    """
    Load the quantized LLM model using llama-cpp-python.
    Implements CPU-optimized loading with Q4_K_M quantization.
    """
    global _model_instance
    if _model_instance is not None:
        return _model_instance

    model_path = get_model_path()
    if not model_path or not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}. "
                                "Please set MODEL_PATH env var or download the model.")

    logger.info(f"Loading model from {model_path}...")
    try:
        from llama_cpp import Llama
        _model_instance = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            n_batch=512,
            use_mmap=True,
            use_mlock=False,
            verbose=False
        )
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    return _model_instance

def generate_from_prompt(prompt: str, max_tokens: int = 512) -> str:
    """
    Generate text from a given prompt using the loaded model.
    """
    model = load_model()
    try:
        output = model(
            prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            stop=["</test>", "```"],
            echo=False
        )
        return output['choices'][0]['text'].strip()
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise

def generate_test_code(bug_description: str, project_id: str) -> Tuple[str, bool]:
    """
    Generate a JUnit test case string based on the bug description.
    
    Args:
        bug_description: The natural language description of the bug.
        project_id: Identifier for the project (used for logging/output naming).
        
    Returns:
        Tuple of (generated_code_string, success_boolean)
        
    Note:
        If the prompt length is < 20 chars, this function falls back to a
        default template (data/templates/default_test.java) to ensure
        syntactic validity, acknowledging potential low coverage.
    """
    # Ensure output directories exist
    ensure_directories()
    output_dir = Path(os.environ.get('OUTPUT_DIR', 'data/generated'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # T018: Error handling for ambiguous inputs
    if len(bug_description) < 20:
        logger.warning(f"Ambiguous input detected for project {project_id}: "
                       f"Prompt length ({len(bug_description)}) < 20 chars. "
                       "Falling back to default template.")
        
        template_path = Path("code/templates/default_test.java")
        if not template_path.exists():
            raise FileNotFoundError(f"Default template not found at {template_path}. "
                                    "Cannot fallback for ambiguous input.")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            default_code = f.read()
        
        # Log metric for SC-005 (template usage count)
        # In a real system, this would update a persistent counter in state
        logger.info(f"SC-005 Metric: Default template used for {project_id}")
        
        return default_code, True

    # Construct prompt
    prompt = f"""
    You are an expert Java developer. Generate a JUnit 4 test case to verify the fix for the following bug.
    
    Bug Description:
    {bug_description}
    
    Requirements:
    1. The test must be a valid Java class extending a generic Test structure.
    2. Include at least one @Test annotated method.
    3. Use standard JUnit assertions (assertEquals, assertTrue, etc.).
    4. Output ONLY the Java code, no markdown formatting.
    5. Class name: BugFixTest_{project_id.replace('-', '_')}
    
    Java Code:
    """

    try:
        generated_code = generate_from_prompt(prompt)
        
        # Clean up potential markdown artifacts if the model ignored instructions
        if generated_code.startswith("```java"):
            generated_code = generated_code[7:]
        if generated_code.endswith("```"):
            generated_code = generated_code[:-3]
        
        return generated_code.strip(), True
        
    except Exception as e:
        logger.error(f"Failed to generate code for {project_id}: {e}")
        return "", False

def validate_syntax_java(code_string: str, project_id: str) -> bool:
    """
    Validate the generated Java code for syntax errors using javac.
    
    Args:
        code_string: The Java source code to validate.
        project_id: Identifier for logging.
        
    Returns:
        True if syntax is valid, False otherwise.
    """
    if not code_string:
        logger.warning(f"No code to validate for {project_id}")
        return False

    # Extract class name if possible, or use a generic name
    class_name = "GeneratedTest"
    if "class" in code_string:
        try:
            # Simple regex-like extraction
            start = code_string.find("class") + 6
            end = code_string.find("{", start)
            if end > start:
                class_name = code_string[start:end].strip()
        except:
            pass

    # Write to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(code_string)
        temp_path = f.name

    try:
        # Run javac
        # We use javac from the system PATH. If not available, this will fail.
        result = subprocess.run(
            ['javac', '-version'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error("javac not found in system PATH. Cannot validate syntax.")
            return False

        compile_result = subprocess.run(
            ['javac', '-cp', '.', temp_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        if compile_result.returncode == 0:
            logger.info(f"Syntax validation passed for {project_id}")
            return True
        else:
            logger.warning(f"Syntax validation failed for {project_id}: {compile_result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"Compilation timed out for {project_id}")
        return False
    except FileNotFoundError:
        logger.error("javac not found. Please ensure JDK is installed and in PATH.")
        return False
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        # Clean up potential class file
        class_file = temp_path.replace('.java', '.class')
        if os.path.exists(class_file):
            os.remove(class_file)

def main():
    """
    Entry point for the LLM generator module.
    Can be used to test generation on a single sample or as part of a pipeline.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m code.llm_generator <bug_description>")
        sys.exit(1)

    description = sys.argv[1]
    project_id = "test_run"
    
    logger.info(f"Generating test for: {description[:50]}...")
    
    code, success = generate_test_code(description, project_id)
    
    if success:
        # Validate syntax
        if validate_syntax_java(code, project_id):
            print("SUCCESS: Generated valid Java code.")
            print(code)
        else:
            print("FAILURE: Generated code has syntax errors.")
            print(code)
    else:
        print("FAILURE: Generation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()