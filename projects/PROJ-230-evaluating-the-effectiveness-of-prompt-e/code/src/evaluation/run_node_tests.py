import os
import sys
import subprocess
import logging
import csv
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from src.utils.timeout_utils import run_with_test_timeout, TimeoutError as ProjectTimeoutError
from src.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
EVAL_DIR = DATA_DIR / "evaluation"
TRANSLATIONS_DIR = EVAL_DIR / "raw_translations"
TESTS_DIR = EVAL_DIR / "translated_tests"
OUTPUT_CSV = EVAL_DIR / "test_execution_results.csv"
TIMEOUT_SECONDS = 10

# Node.js test runner script content
NODE_RUNNER_SCRIPT = """
const fs = require('fs');
const path = require('path');

// Read arguments
const testFile = process.argv[2];
const translationFile = process.argv[3];

if (!testFile || !translationFile) {
    console.error('Usage: node runner.js <test_file> <translation_file>');
    process.exit(1);
}

// Read the test file
if (!fs.existsSync(testFile)) {
    console.error('Test file not found: ' + testFile);
    process.exit(1);
}

// Read the translation file
if (!fs.existsSync(translationFile)) {
    console.error('Translation file not found: ' + translationFile);
    process.exit(1);
}

// Load the translation
let translation;
try {
    const content = fs.readFileSync(translationFile, 'utf8');
    // The translation file is JSON with a 'translated_code' field
    const data = JSON.parse(content);
    translation = data.translated_code;
    if (!translation) {
        throw new Error('No translated_code found in JSON');
    }
} catch (e) {
    console.error('Error reading translation file:', e.message);
    process.exit(1);
}

// We need to execute the translation and then run the tests.
// The test file likely contains assertions that depend on the translation.
// For this runner, we assume the translation defines the functions/exports
// that the test file imports or expects.

// Strategy:
// 1. Write the translation to a temporary JS file (if not already a module)
// 2. Require/Run the translation in the same context as the test
// 3. Run the test file
//
// Since the tests were translated from Python using Transcrypt, they likely
// use a specific testing framework or assertion style.
// Transcrypt typically generates code that can be run directly.
// We will attempt to execute the translation first, then the test.

let testResult = { passed: true, error: null, output: '' };

try {
    // Create a context to run the translation
    // We'll use a simple approach: evaluate the translation code
    // Note: This is a basic runner. A more robust one would use a proper test framework.
    
    // Since we cannot easily isolate modules without a bundler, we will
    // concatenate the translation and the test code and run them together.
    // However, this might cause conflicts.
    //
    // Better approach for Transcrypt-generated code:
    // The test file usually imports from the module being tested.
    // We will assume the translation file exports the necessary functions.
    
    // Let's try to run the translation code first to define the functions.
    // We use 'vm' module for sandboxing if possible, but for simplicity:
    // We will require the translation file if it's a module, or eval it.
    
    // Transcrypt output is often a single file that defines classes/functions.
    // We'll try to load it as a module.
    
    // Write translation to a temp file to ensure it's a file we can require
    const tempTranslationPath = path.join(path.dirname(translationFile), 'temp_translation_' + Date.now() + '.js');
    fs.writeFileSync(tempTranslationPath, translation);
    
    let translationModule;
    try {
        translationModule = require(tempTranslationPath);
    } catch (e) {
        // If require fails, try to eval the code
        // This is less safe but handles non-module scripts
        try {
            eval(translation);
        } catch (evalError) {
            throw new Error('Failed to load translation: ' + evalError.message);
        }
    } finally {
        // Clean up temp file
        if (fs.existsSync(tempTranslationPath)) {
            fs.unlinkSync(tempTranslationPath);
        }
    }

    // Now run the test file
    const testContent = fs.readFileSync(testFile, 'utf8');
    
    // If the test file is a Transcrypt test, it might have specific imports.
    // We'll try to run it directly.
    try {
        // We need to make the translation module available to the test.
        // If the test uses 'require', we need to ensure our translation is in the module cache.
        // We already required it above, so it should be in module cache.
        
        // Run the test file
        require(testFile);
        
        // If we reach here, the test file executed without throwing.
        // We assume the test framework (if any) would have thrown on failure.
        testResult.passed = true;
    } catch (testError) {
        testResult.passed = false;
        testResult.error = testError.message;
    }

} catch (e) {
    testResult.passed = false;
    testResult.error = e.message;
}

// Output result as JSON
console.log(JSON.stringify(testResult));
"""

def find_test_files_for_translation(translation_path: Path) -> Tuple[Path, Path]:
    """
    Find the corresponding translated test file for a given translation file.
    Assumes the test file has a similar name structure in the translated_tests directory.
    """
    # Extract the base name without extension and condition
    # Example: translation_path: data/evaluation/raw_translations/zero_shot_basic/entry_001.js
    # Expected test: data/evaluation/translated_tests/entry_001.js (or similar)
    
    # The translation files are named like: entry_XXX.js
    # The test files should be named similarly but in the translated_tests directory
    # We need to map the entry ID from the translation filename to the test filename.
    
    # Let's assume the translation file is named: {entry_id}.js
    # And the test file is named: {entry_id}_test.js or similar.
    # Actually, looking at T027, it translates test files to JS.
    # The test files in data/evaluation/translated_tests are likely named like: {original_test_name}_test.js
    # But we need to match them to the translation.
    
    # Alternative: The translation file name might contain the original test ID.
    # Let's assume the translation file is named: entry_{id}.js
    # And the corresponding test file is: {id}_test.js or similar.
    
    # A more robust way: The translation file is saved with the entry ID from the corpus.
    # The test file should be generated from the same entry ID.
    # Let's look for a test file that matches the entry ID.
    
    # Since the structure is:
    # data/evaluation/raw_translations/{condition}/{entry_id}.js
    # data/evaluation/translated_tests/{entry_id}_test.js  (or similar)
    
    # We'll try to find a test file that contains the entry ID in its name.
    entry_id = translation_path.stem  # e.g., "entry_001"
    
    # Look in the translated_tests directory for a file that matches
    # We'll try common patterns: {entry_id}_test.js, {entry_id}.js, etc.
    test_patterns = [
        f"{entry_id}_test.js",
        f"{entry_id}.js",
        f"test_{entry_id}.js"
    ]
    
    for pattern in test_patterns:
        candidate = TESTS_DIR / pattern
        if candidate.exists():
            return candidate, translation_path
    
    # If not found by pattern, try to find any file that might correspond
    # This is a fallback and might not be accurate
    logger.warning(f"Could not find exact test file for {entry_id}, searching for any match...")
    for test_file in TESTS_DIR.glob("*.js"):
        if entry_id in test_file.stem:
            return test_file, translation_path
    
    raise FileNotFoundError(f"Could not find corresponding test file for translation: {translation_path}")


def run_single_test(test_file: Path, translation_file: Path) -> Dict[str, Any]:
    """
    Run a single Node.js test for a given translation.
    Returns a dictionary with the result.
    """
    result = {
        "test_file": str(test_file),
        "translation_file": str(translation_file),
        "passed": False,
        "error": None,
        "timeout": False,
        "execution_time": 0.0
    }

    # Create a temporary directory for the runner script
    temp_dir = Path(tempfile.mkdtemp())
    runner_script = temp_dir / "runner.js"
    runner_script.write_text(NODE_RUNNER_SCRIPT)

    start_time = time.time()
    try:
        # Run the Node.js script with timeout
        process = subprocess.run(
            ["node", str(runner_script), str(test_file), str(translation_file)],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=temp_dir
        )

        execution_time = time.time() - start_time
        result["execution_time"] = execution_time

        if process.returncode != 0:
            result["error"] = f"Node.js process exited with code {process.returncode}. Stderr: {process.stderr}"
            result["passed"] = False
        else:
            # Parse the JSON output from the runner
            try:
                output = process.stdout.strip()
                if output:
                    test_result = json.loads(output)
                    result["passed"] = test_result.get("passed", False)
                    result["error"] = test_result.get("error")
                else:
                    result["error"] = "No output from test runner"
                    result["passed"] = False
            except json.JSONDecodeError as e:
                result["error"] = f"Failed to parse test output as JSON: {e}. Output: {process.stdout}"
                result["passed"] = False

    except subprocess.TimeoutExpired:
        result["timeout"] = True
        result["error"] = f"Test execution timed out after {TIMEOUT_SECONDS} seconds"
        result["execution_time"] = TIMEOUT_SECONDS
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        result["execution_time"] = time.time() - start_time
    finally:
        # Clean up temp directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    return result


def scan_translations() -> List[Tuple[Path, Path, str]]:
    """
    Scan the raw_translations directory for all translation files.
    Returns a list of (test_file, translation_file, condition) tuples.
    """
    results = []
    if not TRANSLATIONS_DIR.exists():
        logger.error(f"Translations directory not found: {TRANSLATIONS_DIR}")
        return results

    for condition_dir in TRANSLATIONS_DIR.iterdir():
        if condition_dir.is_dir():
            condition = condition_dir.name
            for translation_file in condition_dir.glob("*.js"):
                try:
                    test_file, _ = find_test_files_for_translation(translation_file)
                    results.append((test_file, translation_file, condition))
                except FileNotFoundError as e:
                    logger.warning(f"Skipping {translation_file}: {e}")
    return results


def main():
    """
    Main function to run all Node.js tests.
    """
    logger.info("Starting Node.js test execution for all translations")
    
    # Ensure output directory exists
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    # Scan for translations
    test_pairs = scan_translations()
    if not test_pairs:
        logger.warning("No translation files found to test.")
        # Write an empty CSV with headers
        with open(OUTPUT_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["test_file", "translation_file", "condition", "passed", "error", "timeout", "execution_time"])
        return

    logger.info(f"Found {len(test_pairs)} translation files to test.")

    # Run tests and collect results
    all_results = []
    for i, (test_file, translation_file, condition) in enumerate(test_pairs):
        logger.info(f"Running test {i+1}/{len(test_pairs)}: {translation_file.name} (condition: {condition})")
        result = run_single_test(test_file, translation_file)
        result["condition"] = condition
        all_results.append(result)

        # Log progress
        if (i + 1) % 10 == 0:
            logger.info(f"Completed {i+1}/{len(test_pairs)} tests")

    # Write results to CSV
    with open(OUTPUT_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["test_file", "translation_file", "condition", "passed", "error", "timeout", "execution_time"])
        for result in all_results:
            writer.writerow([
                result["test_file"],
                result["translation_file"],
                result["condition"],
                result["passed"],
                result["error"],
                result["timeout"],
                result["execution_time"]
            ])

    # Log summary
    total = len(all_results)
    passed = sum(1 for r in all_results if r["passed"])
    timeouts = sum(1 for r in all_results if r["timeout"])
    errors = total - passed - timeouts

    logger.info(f"Test execution complete. Total: {total}, Passed: {passed}, Timeouts: {timeouts}, Errors: {errors}")
    logger.info(f"Results written to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
