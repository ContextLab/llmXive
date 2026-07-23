import os
import sys
import subprocess
import csv
import logging
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Constants
ESLINT_COMPLEXITY_RULE = "complexity"
ESLINT_MAX_COMPLEXITY = 10
OUTPUT_CSV_PATH = "data/evaluation/quality_metrics.csv"
TRANSLATIONS_DIR = "data/evaluation/raw_translations"

def run_eslint_complexity_check(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Run ESLint with the complexity rule on a JavaScript file.

    Args:
        file_path: Path to the JavaScript file

    Returns:
        Dictionary with 'complexity' and 'loc' if successful, None if file doesn't exist or ESLint fails
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return None

    try:
        # Run ESLint with complexity rule
        # Using --rule complexity: [1, 10] to enable the rule with max 10
        # Note: ESLint returns exit code 1 if there are violations, which is expected
        cmd = [
            "eslint",
            "--no-eslintrc",
            "--rule", f"{ESLINT_COMPLEXITY_RULE}: [1, {ESLINT_MAX_COMPLEXITY}]",
            "--format", "json",
            file_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # 30s timeout per file
        )

        # Parse ESLint output
        try:
            eslint_output = json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse ESLint JSON output for {file_path}: {result.stdout}")
            return None

        if not eslint_output or len(eslint_output) == 0:
            logger.warning(f"Empty ESLint output for {file_path}")
            return None

        file_report = eslint_output[0]
        messages = file_report.get("messages", [])

        # Extract complexity from messages
        complexity = None
        for msg in messages:
            if msg.get("ruleId") == ESLINT_COMPLEXITY_RULE:
                # The complexity value is typically in the message
                # ESLint complexity rule reports: "Complexity of the function is X"
                match = re.search(r"Complexity of the function is (\d+)", msg.get("message", ""))
                if match:
                    complexity = int(match.group(1))
                break

        # Calculate LOC (Lines of Code)
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            loc = len(lines)

        # If ESLint didn't report complexity (e.g., no functions or parsing error),
        # we might need to handle it differently. For now, return None if not found.
        if complexity is None:
            # Try to parse the file manually for basic complexity estimation
            # This is a fallback if ESLint fails to detect functions
            complexity = estimate_complexity_fallback(file_path)

        return {
            "complexity": complexity,
            "loc": loc,
            "file_path": file_path
        }

    except subprocess.TimeoutExpired:
        logger.error(f"ESLint timeout for file: {file_path}")
        return None
    except FileNotFoundError:
        logger.error("ESLint not found. Please install ESLint globally: npm install -g eslint")
        raise
    except Exception as e:
        logger.error(f"Error running ESLint on {file_path}: {e}")
        return None

def estimate_complexity_fallback(file_path: str) -> int:
    """
    Fallback complexity estimation if ESLint doesn't report it.
    This is a simple heuristic based on control flow statements.

    Args:
        file_path: Path to the JavaScript file

    Returns:
        Estimated cyclomatic complexity
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Simple pattern matching for control flow statements
        # This is a rough approximation
        patterns = [
            r'\bif\b',
            r'\belse\b',
            r'\bfor\b',
            r'\bwhile\b',
            r'\bswitch\b',
            r'\bcase\b',
            r'\bcatch\b',
            r'\b\?\b',  # ternary operator
            r'\b&&\b',
            r'\b\|\|\b'
        ]

        complexity = 1  # Base complexity
        for pattern in patterns:
            matches = re.findall(pattern, content)
            complexity += len(matches)

        return complexity
    except Exception as e:
        logger.error(f"Error in fallback complexity estimation: {e}")
        return 1

def scan_translation_dirs() -> List[str]:
    """
    Scan all translation condition directories and return list of JS file paths.

    Returns:
        List of paths to JavaScript translation files
    """
    js_files = []
    translations_path = Path(TRANSLATIONS_DIR)

    if not translations_path.exists():
        logger.warning(f"Translations directory not found: {translations_path}")
        return js_files

    for condition_dir in translations_path.iterdir():
        if condition_dir.is_dir():
            for js_file in condition_dir.glob("*.js"):
                js_files.append(str(js_file))

    logger.info(f"Found {len(js_files)} JavaScript translation files")
    return js_files

def compute_quality_metrics(js_files: List[str]) -> List[Dict[str, Any]]:
    """
    Compute quality metrics (complexity and LOC) for a list of JavaScript files.

    Args:
        js_files: List of paths to JavaScript files

    Returns:
        List of dictionaries containing quality metrics
    """
    results = []

    for file_path in js_files:
        # Extract condition from path
        # Expected format: data/evaluation/raw_translations/<condition>/<filename>.js
        parts = Path(file_path).parts
        condition = None
        for i, part in enumerate(parts):
            if part == "raw_translations" and i + 1 < len(parts):
                condition = parts[i + 1]
                break

        if not condition:
            logger.warning(f"Could not determine condition for file: {file_path}")
            continue

        metrics = run_eslint_complexity_check(file_path)

        if metrics:
            result = {
                "condition": condition,
                "file_name": os.path.basename(file_path),
                "complexity": metrics["complexity"],
                "loc": metrics["loc"]
            }
            results.append(result)
            logger.debug(f"Computed metrics for {file_path}: complexity={metrics['complexity']}, loc={metrics['loc']}")
        else:
            logger.warning(f"Failed to compute metrics for {file_path}")

    return results

def save_quality_metrics(results: List[Dict[str, Any]], output_path: str):
    """
    Save quality metrics to a CSV file.

    Args:
        results: List of metric dictionaries
        output_path: Path to output CSV file
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["condition", "file_name", "complexity", "loc"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for result in results:
            writer.writerow(result)

    logger.info(f"Saved {len(results)} quality metrics to {output_path}")

def main():
    """
    Main entry point for computing quality metrics.
    """
    logger.info("Starting quality metrics computation")

    # Scan for translation files
    js_files = scan_translation_dirs()

    if not js_files:
        logger.warning("No JavaScript translation files found. Exiting.")
        return

    # Compute metrics
    results = compute_quality_metrics(js_files)

    if not results:
        logger.warning("No quality metrics computed. Exiting.")
        return

    # Save results
    save_quality_metrics(results, OUTPUT_CSV_PATH)

    # Log summary
    logger.info(f"Quality metrics computation complete. Processed {len(results)} files.")

    # Print summary statistics
    if results:
        avg_complexity = sum(r["complexity"] for r in results) / len(results)
        avg_loc = sum(r["loc"] for r in results) / len(results)
        logger.info(f"Average complexity: {avg_complexity:.2f}")
        logger.info(f"Average LOC: {avg_loc:.2f}")

        # Group by condition
        conditions = {}
        for r in results:
            cond = r["condition"]
            if cond not in conditions:
                conditions[cond] = []
            conditions[cond].append(r)

        for cond, cond_results in conditions.items():
            avg_c = sum(r["complexity"] for r in cond_results) / len(cond_results)
            avg_l = sum(r["loc"] for r in cond_results) / len(cond_results)
            logger.info(f"Condition '{cond}': avg complexity={avg_c:.2f}, avg LOC={avg_l:.2f}, count={len(cond_results)}")

if __name__ == "__main__":
    main()