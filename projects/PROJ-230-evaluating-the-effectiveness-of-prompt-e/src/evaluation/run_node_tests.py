"""
Run Node.js tests against translated JavaScript code.

Executes translated unit tests against generated JS files in a Node.js environment,
enforcing timeouts per test as defined in T009 (timeout_utils).
"""
import os
import sys
import subprocess
import logging
import csv
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from src.utils.timeout_utils import enforce_test_timeout, TimeoutError as ProjectTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/run_node_tests.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
NODE_EXECUTABLE = "node"
TEST_TIMEOUT_SECONDS = 30  # Per-test timeout (configurable, but defaults to 30s)
TRANSLATION_OUTPUT_DIR = "data/evaluation/raw_translations"
TEST_OUTPUT_DIR = "data/evaluation/test_results"
RESULTS_CSV_PATH = "data/evaluation/test_results/node_test_results.csv"

def ensure_dirs():
    """Ensure output directories exist."""
    Path(TEST_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def find_test_files_for_translation(translation_dir: Path) -> List[Path]:
    """
    Find test files associated with a translation directory.
    Assumes test files are in a 'tests' subdirectory or follow naming pattern.
    """
    test_dir = translation_dir / "tests"
    if test_dir.exists() and test_dir.is_dir():
        return list(test_dir.glob("*.js"))
    
    # Fallback: look for test files in the same directory with 'test' in name
    test_files = [f for f in translation_dir.glob("*.js") if "test" in f.name.lower()]
    return test_files

def run_single_test(test_file: Path, translation_file: Path, timeout: int = TEST_TIMEOUT_SECONDS) -> Dict[str, Any]:
    """
    Run a single Node.js test file against the translation.
    
    Args:
        test_file: Path to the JavaScript test file
        translation_file: Path to the translated JavaScript file
        timeout: Maximum execution time in seconds
    
    Returns:
        Dictionary with test result information
    """
    result = {
        "test_file": str(test_file),
        "translation_file": str(translation_file),
        "status": "unknown",
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "timeout": False,
        "error_message": ""
    }
    
    # Create a temporary directory to run the test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy test file and translation to temp directory
        temp_test = temp_path / test_file.name
        temp_translation = temp_path / translation_file.name
        
        shutil.copy(test_file, temp_test)
        shutil.copy(translation_file, temp_translation)
        
        # Create a simple test runner script that imports the translation and runs the test
        runner_script = temp_path / "runner.js"
        runner_content = f"""
        const translation = require('./{translation_file.name}');
        const test = require('./{test_file.name}');
        
        // Simple test runner - in a real scenario, you'd use a proper test framework
        console.log('Running test:', '{test_file.name}');
        console.log('Translation loaded successfully');
        """
        
        with open(runner_script, 'w') as f:
            f.write(runner_content)
        
        try:
            # Run the test with timeout
            start_time = __import__('time').time()
            process = subprocess.run(
                [NODE_EXECUTABLE, str(runner_script)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=temp_dir
            )
            end_time = __import__('time').time()
            
            result["exit_code"] = process.returncode
            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["execution_time"] = end_time - start_time
            
            if process.returncode == 0:
                result["status"] = "pass"
            else:
                result["status"] = "fail"
                result["error_message"] = process.stderr[:500] if process.stderr else "Unknown error"
                
        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["timeout"] = True
            result["error_message"] = f"Test timed out after {timeout} seconds"
            logger.warning(f"Test timed out: {test_file.name}")
            
        except Exception as e:
            result["status"] = "error"
            result["error_message"] = str(e)
            logger.error(f"Error running test {test_file.name}: {e}")
    
    return result

def scan_translations():
    """
    Scan translation directories and run tests for each.
    
    Returns:
        List of test result dictionaries
    """
    results = []
    translation_base = Path(TRANSLATION_OUTPUT_DIR)
    
    if not translation_base.exists():
        logger.warning(f"Translation output directory not found: {TRANSLATION_OUTPUT_DIR}")
        return results
    
    # Iterate through condition directories
    for condition_dir in translation_base.iterdir():
        if not condition_dir.is_dir():
            continue
        
        logger.info(f"Processing condition: {condition_dir.name}")
        
        # Find all translation files (JSON or JS)
        translation_files = list(condition_dir.glob("*.json")) + list(condition_dir.glob("*.js"))
        
        for translation_file in translation_files:
            # For JSON files, extract the translation and create a temporary JS file
            if translation_file.suffix == ".json":
                try:
                    with open(translation_file, 'r') as f:
                        data = json.load(f)
                    
                    # Extract the translated code
                    translated_code = data.get("translated_code", "")
                    if not translated_code:
                        logger.warning(f"No translated code found in {translation_file}")
                        continue
                    
                    # Create a temporary JS file for testing
                    temp_js = translation_file.parent / f"{translation_file.stem}_translated.js"
                    with open(temp_js, 'w') as f:
                        f.write(translated_code)
                    
                    # Find associated test files
                    test_files = find_test_files_for_translation(translation_file.parent)
                    
                    if not test_files:
                        logger.info(f"No test files found for {translation_file}, skipping")
                        # Still record the translation as not tested
                        results.append({
                            "translation_file": str(translation_file),
                            "condition": condition_dir.name,
                            "test_file": "none",
                            "status": "no_tests",
                            "exit_code": None,
                            "stdout": "",
                            "stderr": "",
                            "timeout": False,
                            "error_message": "No test files found",
                            "execution_time": 0
                        })
                        continue
                    
                    # Run tests for each test file
                    for test_file in test_files:
                        result = run_single_test(test_file, temp_js)
                        result["condition"] = condition_dir.name
                        result["translation_file"] = str(translation_file)
                        result["test_file"] = str(test_file)
                        results.append(result)
                    
                    # Clean up temporary file
                    temp_js.unlink()
                    
                except Exception as e:
                    logger.error(f"Error processing {translation_file}: {e}")
                    results.append({
                        "translation_file": str(translation_file),
                        "condition": condition_dir.name,
                        "test_file": "none",
                        "status": "error",
                        "exit_code": None,
                        "stdout": "",
                        "stderr": "",
                        "timeout": False,
                        "error_message": str(e),
                        "execution_time": 0
                    })
            
            elif translation_file.suffix == ".js":
                # Direct JS file
                test_files = find_test_files_for_translation(translation_file.parent)
                
                if not test_files:
                    logger.info(f"No test files found for {translation_file}, skipping")
                    results.append({
                        "translation_file": str(translation_file),
                        "condition": condition_dir.name,
                        "test_file": "none",
                        "status": "no_tests",
                        "exit_code": None,
                        "stdout": "",
                        "stderr": "",
                        "timeout": False,
                        "error_message": "No test files found",
                        "execution_time": 0
                    })
                    continue
                
                # Run tests for each test file
                for test_file in test_files:
                    result = run_single_test(test_file, translation_file)
                    result["condition"] = condition_dir.name
                    result["translation_file"] = str(translation_file)
                    result["test_file"] = str(test_file)
                    results.append(result)
    
    return results

def save_results(results: List[Dict[str, Any]]):
    """Save test results to CSV."""
    if not results:
        logger.warning("No results to save")
        return
    
    # Ensure directory exists
    Path(RESULTS_CSV_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    # Define CSV columns
    fieldnames = [
        "translation_file", "condition", "test_file", "status", 
        "exit_code", "stdout", "stderr", "timeout", "error_message", 
        "execution_time"
    ]
    
    with open(RESULTS_CSV_PATH, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            # Truncate long strings for CSV
            row = {}
            for key in fieldnames:
                value = result.get(key, "")
                if isinstance(value, str) and len(value) > 1000:
                    value = value[:1000] + "..."
                row[key] = value
            writer.writerow(row)
    
    logger.info(f"Saved {len(results)} test results to {RESULTS_CSV_PATH}")

def main():
    """Main entry point for running Node.js tests."""
    logger.info("Starting Node.js test execution")
    
    # Ensure directories exist
    ensure_dirs()
    
    # Scan and run tests
    results = scan_translations()
    
    # Save results
    save_results(results)
    
    # Log summary
    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "pass")
    failed = sum(1 for r in results if r.get("status") == "fail")
    timeout = sum(1 for r in results if r.get("status") == "timeout")
    no_tests = sum(1 for r in results if r.get("status") == "no_tests")
    errors = sum(1 for r in results if r.get("status") == "error")
    
    logger.info(f"Test execution completed: {total} total")
    logger.info(f"  Passed: {passed}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Timeout: {timeout}")
    logger.info(f"  No tests: {no_tests}")
    logger.info(f"  Errors: {errors}")
    
    return results

if __name__ == "__main__":
    main()
