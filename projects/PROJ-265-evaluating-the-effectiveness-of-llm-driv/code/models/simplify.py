import ast
import re
import sys
import time
import json
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# Local imports based on provided API surface
from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error, log_stage_exclusion

logger = get_logger(__name__)

class SimplificationError(Exception):
    """Custom exception for simplification failures."""
    pass

def _is_valid_ast(code_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that the generated code string parses into a valid AST.
    Returns (True, None) if valid, (False, error_message) if invalid.
    """
    if not code_str or not isinstance(code_str, str):
        return False, "Empty or non-string code provided."
    
    try:
        ast.parse(code_str)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Unexpected error parsing AST: {str(e)}"

def _has_function_body(code_str: str) -> bool:
    """
    Check if the AST contains at least one function definition with a non-empty body.
    """
    try:
        tree = ast.parse(code_str)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.body) > 0:
                    return True
        return False
    except SyntaxError:
        return False

def simplify_function(
    original_code: str, 
    model_loader, 
    prompt_template: str, 
    max_retries: int = 3, 
    retry_delay: float = 1.0
) -> Optional[str]:
    """
    Simplify a function using the provided model loader with AST validation integrated into the retry loop.
    
    Args:
        original_code: The original Python function code.
        model_loader: An object with a `generate(prompt)` method.
        prompt_template: A string template with {code} placeholder.
        max_retries: Maximum number of generation attempts before giving up.
        retry_delay: Seconds to wait between retries.
        
    Returns:
        The simplified code string if successful and valid, None otherwise.
    """
    if not original_code:
        logger.error("Original code is empty.")
        return None

    prompt = prompt_template.format(code=original_code)
    
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        logger.info(f"Generation attempt {attempt}/{max_retries}")
        
        try:
            # Generate code using the model loader
            generated_code = model_loader.generate(prompt)
            
            if not generated_code:
                logger.warning("Model returned empty string.")
                last_error = "Empty generation"
                time.sleep(retry_delay)
                continue

            # Clean up markdown code blocks if present
            generated_code = re.sub(r'^```python\s*', '', generated_code, flags=re.MULTILINE)
            generated_code = re.sub(r'^```\s*', '', generated_code, flags=re.MULTILINE)
            generated_code = re.sub(r'```\s*$', '', generated_code, flags=re.MULTILINE)
            generated_code = generated_code.strip()

            # AST Validation Check (Integrated into retry loop)
            is_valid, error_msg = _is_valid_ast(generated_code)
            
            if not is_valid:
                logger.warning(f"Attempt {attempt} failed AST validation: {error_msg}")
                log_stage_exclusion("simplify", "ast_invalid", original_code[:50], error_msg)
                last_error = error_msg
                time.sleep(retry_delay)
                continue

            # Additional check: Ensure it's not just the original code repeated
            if generated_code.strip() == original_code.strip():
                logger.warning("Attempt {attempt} returned identical code.")
                last_error = "No simplification (identical)"
                time.sleep(retry_delay)
                continue

            # Ensure there is at least one function with a body
            if not _has_function_body(generated_code):
                logger.warning("Attempt {attempt} produced code without valid function bodies.")
                last_error = "No function body"
                time.sleep(retry_delay)
                continue

            # Success: Valid AST and structure
            logger.info(f"Generation successful on attempt {attempt}.")
            return generated_code

        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"Attempt {attempt} raised exception: {e}\n{error_trace}")
            last_error = str(e)
            time.sleep(retry_delay)
            continue

    # Exhausted retries
    logger.error(f"Simplification failed after {max_retries} attempts. Last error: {last_error}")
    return None

def run_simplification_pipeline(
    input_path: str, 
    output_path: str, 
    model_loader, 
    prompt_template: str,
    max_retries: int = 3
) -> Dict[str, int]:
    """
    Run the simplification pipeline on a JSONL file of functions.
    
    Args:
        input_path: Path to input JSONL file (data/processed/validated_functions.jsonl).
        output_path: Path to output JSONL file (data/processed/simplified_functions.jsonl).
        model_loader: Model loader instance.
        prompt_template: Prompt template string.
        max_retries: Max retries per function.
        
    Returns:
        Dictionary with counts of processed, successful, and failed items.
    """
    logger.info(f"Starting simplification pipeline: {input_path} -> {output_path}")
    log_stage_start("simplification_pipeline", input_path)

    input_file = Path(input_path)
    if not input_file.exists():
        logger.error(f"Input file not found: {input_path}")
        log_stage_error("simplification_pipeline", "Input file not found")
        return {"processed": 0, "success": 0, "failed": 0}

    results = []
    stats = {"processed": 0, "success": 0, "failed": 0}

    try:
        with open(input_file, 'r', encoding='utf-8') as f_in:
            for line_num, line in enumerate(f_in, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    original_code = data.get("code", "")
                    func_id = data.get("id", f"line_{line_num}")
                    
                    stats["processed"] += 1
                    
                    simplified_code = simplify_function(
                        original_code=original_code,
                        model_loader=model_loader,
                        prompt_template=prompt_template,
                        max_retries=max_retries
                    )
                    
                    if simplified_code:
                        stats["success"] += 1
                        results.append({
                            "id": func_id,
                            "original": original_code,
                            "simplified": simplified_code,
                            "status": "success"
                        })
                        logger.debug(f"Success for {func_id}")
                    else:
                        stats["failed"] += 1
                        results.append({
                            "id": func_id,
                            "original": original_code,
                            "simplified": None,
                            "status": "failed"
                        })
                        logger.warning(f"Failed for {func_id}")
                        
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON on line {line_num}")
                    stats["failed"] += 1
                except Exception as e:
                    logger.error(f"Error processing line {line_num}: {e}")
                    stats["failed"] += 1

        # Write output
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for item in results:
                f_out.write(json.dumps(item) + "\n")
                
        logger.info(f"Pipeline complete. Processed: {stats['processed']}, Success: {stats['success']}, Failed: {stats['failed']}")
        log_stage_complete("simplification_pipeline", output_path, stats)
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        log_stage_error("simplification_pipeline", str(e))
        
    return stats

def main():
    """Entry point for running the simplification pipeline from command line."""
    # Example usage - in real execution, arguments would be parsed
    input_file = "data/processed/validated_functions.jsonl"
    output_file = "data/processed/simplified_functions.jsonl"
    
    if not Path(input_file).exists():
        print(f"Error: Input file {input_file} not found. Please run data pipeline first.")
        sys.exit(1)
        
    # Mock loader for demonstration if actual model isn't loaded here
    # In T023/T022 context, this would be passed a real loader
    class MockLoader:
        def generate(self, prompt):
            # This is a placeholder; in real usage, T023 provides the real model
            return "# Simplified code placeholder\n"

    # If running as script, we expect a real loader to be injected or configured
    # For now, we just show the structure
    print("Simplification pipeline initialized.")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    # stats = run_simplification_pipeline(input_file, output_file, MockLoader(), "Simplify: {code}")
    # print(stats)

if __name__ == "__main__":
    main()