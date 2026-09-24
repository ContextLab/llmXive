"""
Translate Python unit tests to JavaScript using the strategy defined in T027a.

Strategy: LLM-based fallback with deterministic prompting (default).
Optional: Attempt 'transcrypt' if USE_TRANSPILERS=True, then fallback to LLM.

Dependencies:
- huggingface_hub (API access)
- node (syntax validation)
- transcrypt (optional)

Output:
- data/evaluation/translated_tests/<input_id>.js
- data/evaluation/translation_log.csv
"""

import os
import sys
import subprocess
import logging
import csv
import tempfile
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Import API client from existing surface
from src.execution.api_client import call_inference_api, InferenceError
from src.utils.logging import get_logger

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TRANSLATED_TESTS_DIR = PROJECT_ROOT / "data" / "evaluation" / "translated_tests"
TRANSLATION_LOG_PATH = PROJECT_ROOT / "data" / "evaluation" / "translation_log.csv"
PROMPT_PATH = PROJECT_ROOT / "data" / "prompts" / "zero_shot_basic.txt"

# Setup logger
logger = get_logger(__name__)

def ensure_transcrypt_available() -> bool:
    """Check if transcrypt is installed and available."""
    try:
        result = subprocess.run(
            ["transcrypt", "-h"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False

def run_transcrypt(input_py_path: Path, output_js_path: Path) -> bool:
    """
    Attempt to transpile Python to JavaScript using transcrypt.
    Returns True if successful and output is valid JS.
    """
    if not ensure_transcrypt_available():
        logger.warning("transcrypt not available, skipping deterministic tool.")
        return False
    
    try:
        # Run transcrypt
        # Note: transcrypt output structure varies; we target the generated JS
        cmd = [
            "transcrypt",
            "-a",  # Annotate
            "-b",  # No browser launch
            "-m",  # Minify (optional)
            "-nocheck", # Skip runtime checks for speed
            str(input_py_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=input_py_path.parent
        )
        
        if result.returncode != 0:
            logger.error(f"transcrypt failed for {input_py_path}: {result.stderr}")
            return False
        
        # Transcrypt usually outputs to __target__/...
        # We need to locate the generated file. 
        # For simplicity in this research context, we assume standard output or handle errors.
        # If transcrypt generates a __target__ directory, we look there.
        target_dir = input_py_path.parent / "__target__"
        if target_dir.exists():
            # Find the .js file
            js_files = list(target_dir.glob("*.js"))
            if js_files:
                generated_js = js_files[0]
                # Move to expected output path
                import shutil
                shutil.copy(generated_js, output_js_path)
                return True
        
        logger.error("transcrypt ran but no output found in expected location.")
        return False
        
    except subprocess.TimeoutExpired:
        logger.error(f"transcrypt timed out for {input_py_path}")
        return False
    except Exception as e:
        logger.error(f"transcrypt error: {e}")
        return False

def validate_js_syntax(js_path: Path) -> bool:
    """Validate JavaScript syntax using node --check."""
    try:
        result = subprocess.run(
            ["node", "--check", str(js_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
        logger.error(f"Node validation failed for {js_path}: {e}")
        return False

def translate_python_test_to_js(py_code: str, input_id: str, seed: int) -> Optional[str]:
    """
    Translate Python test code to JavaScript using LLM.
    Uses the same deterministic constraints as T021.
    """
    # Load prompt template
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_PATH}")
    
    with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    # Inject code
    prompt = prompt_template.replace("{code}", py_code)
    
    try:
        # Call API with deterministic settings
        # Using CodeLlama-7B as per project specs
        response = call_inference_api(
            prompt=prompt,
            model="codellama/CodeLlama-7b-Instruct-hf",
            seed=seed,
            temperature=0.0,
            max_tokens=1024,
            do_sample=False
        )
        
        # Extract content
        if isinstance(response, dict) and "choices" in response:
            content = response["choices"][0]["text"].strip()
        elif isinstance(response, str):
            content = response.strip()
        else:
            logger.error(f"Unexpected API response format: {type(response)}")
            return None
        
        # Clean up potential markdown blocks
        if content.startswith("```javascript"):
            content = content.split("```javascript")[1]
        if content.startswith("```js"):
            content = content.split("```js")[1]
        if content.endswith("```"):
            content = content.rsplit("```", 1)[0]
        
        return content.strip()
        
    except InferenceError as e:
        logger.error(f"API error translating {input_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error translating {input_id}: {e}")
        return None

def translate_test_directory(input_dir: Path, output_dir: Path, log_path: Path) -> None:
    """
    Process all Python test files in input_dir, translate to JS, and save to output_dir.
    Logs results to log_path.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    log_path = Path(log_path)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare CSV log
    log_exists = log_path.exists()
    fieldnames = ["input_id", "strategy_used", "success", "error_msg"]
    
    if not log_exists:
        with open(log_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
    
    # Find Python test files
    py_files = list(input_dir.glob("*.py"))
    if not py_files:
        logger.warning(f"No Python files found in {input_dir}")
        return
    
    logger.info(f"Found {len(py_files)} Python test files to translate.")
    
    use_transcrypt = os.getenv("USE_TRANSPILERS", "False").lower() == "true"
    transcrypt_available = use_transcrypt and ensure_transcrypt_available()
    
    if use_transcrypt and not transcrypt_available:
        logger.warning("USE_TRANSPILERS=True but transcrypt not available. Falling back to LLM.")
    
    for py_file in py_files:
        input_id = py_file.stem
        output_js_path = output_dir / f"{input_id}.js"
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                py_code = f.read()
            
            strategy = "llm"
            success = False
            error_msg = ""
            js_code = None
            
            # Attempt deterministic tool if configured and available
            if use_transcrypt and transcrypt_available:
                logger.info(f"Attempting transcrypt for {input_id}...")
                if run_transcrypt(py_file, output_js_path):
                    if validate_js_syntax(output_js_path):
                        success = True
                        strategy = "transcrypt"
                        logger.info(f"transcrypt succeeded for {input_id}")
                    else:
                        error_msg = "transcrypt output invalid JS syntax"
                        logger.warning(error_msg)
                        # Remove invalid output
                        output_js_path.unlink(missing_ok=True)
            
            # Fallback to LLM if deterministic failed or not used
            if not success:
                logger.info(f"Falling back to LLM for {input_id}...")
                # Use a deterministic seed based on input_id to ensure reproducibility
                seed = int(hashlib.md5(input_id.encode()).hexdigest(), 16) % (2**31)
                js_code = translate_python_test_to_js(py_code, input_id, seed)
                
                if js_code:
                    with open(output_js_path, 'w', encoding='utf-8') as f:
                        f.write(js_code)
                    
                    if validate_js_syntax(output_js_path):
                        success = True
                        strategy = "llm"
                        logger.info(f"LLM translation valid for {input_id}")
                    else:
                        error_msg = "LLM output invalid JS syntax"
                        logger.warning(error_msg)
                        output_js_path.unlink(missing_ok=True)
                else:
                    error_msg = "LLM translation failed (no output or API error)"
                    logger.error(error_msg)
            
            # Log result
            with open(log_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow({
                    "input_id": input_id,
                    "strategy_used": strategy,
                    "success": success,
                    "error_msg": error_msg
                })
                
        except Exception as e:
            logger.error(f"Failed to process {py_file}: {e}")
            with open(log_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow({
                    "input_id": input_id,
                    "strategy_used": "error",
                    "success": False,
                    "error_msg": str(e)
                })

def main():
    """Main entry point for test translation."""
    # Define paths
    # Assuming tests are generated or located in a specific directory structure
    # For this research pipeline, we assume the source Python tests are in data/raw/tests
    # or generated by the preprocessing step. 
    # If the corpus contains test code, we might need to extract it.
    # Based on T028 (run_node_tests), we expect tests to exist.
    # Let's assume a standard location for source tests: data/raw/tests
    
    input_dir = PROJECT_ROOT / "data" / "raw" / "tests"
    if not input_dir.exists():
        # Fallback: check if we need to extract from corpus or use a different path
        # For now, raise error if not found, as this is a critical step
        logger.error(f"Source test directory not found: {input_dir}")
        logger.error("Please ensure Python test files are available in data/raw/tests")
        sys.exit(1)
    
    output_dir = TRANSLATED_TESTS_DIR
    log_path = TRANSLATION_LOG_PATH
    
    logger.info(f"Starting test translation from {input_dir} to {output_dir}")
    translate_test_directory(input_dir, output_dir, log_path)
    logger.info("Test translation completed.")

if __name__ == "__main__":
    import hashlib
    main()