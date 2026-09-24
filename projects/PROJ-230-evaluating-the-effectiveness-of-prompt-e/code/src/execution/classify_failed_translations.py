import os
import sys
import csv
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import logging utilities from the project's utils
try:
    from src.utils.logging import get_logger
except ImportError:
    # Fallback for direct execution or different import paths
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

# Heuristics for classifying translation failures
# These patterns detect common non-code LLM outputs

# Pattern for explicit refusal or inability
REFUSAL_PATTERNS = [
    r"(?i)i\s+(cannot|can't|could not|unable to)\s+(do|translate|convert|generate)",
    r"(?i)as\s+a\s+(large\s+language\s+model|ai\s+assistant)",
    r"(?i)I\s+am\s+not\s+able\s+to",
    r"(?i)I\s+cannot\s+fulfill\s+this\s+request",
    r"(?i)I\s+cannot\s+translate",
    r"(?i)I\s+cannot\s+generate\s+code",
    r"(?i)I\s+cannot\s+execute\s+code",
    r"(?i)I\s+do\s+not\s+have\s+the\s+ability",
    r"(?i)I\s+am\s+an\s+AI\s+and\s+cannot",
]

# Pattern for conversational filler or meta-commentary
CONVERSATION_PATTERNS = [
    r"(?i)here\s+is\s+the\s+code",
    r"(?i)sure,\s+here\s+is",
    r"(?i)of\s+course",
    r"(?i)absolutely",
    r"(?i)I'd\s+be\s+happy\s+to",
    r"(?i)let\s+me\s+know\s+if",
    r"(?i)if\s+you\s+have\s+any\s+other",
    r"(?i)hope\s+this\s+helps",
    r"(?i)feel\s+free\s+to",
]

# Pattern for empty or whitespace-only output
EMPTY_PATTERNS = [
    r"^\s*$",
]

# Pattern for code-like output (JavaScript keywords, braces, etc.)
CODE_INDICATORS = [
    r"(?i)(function|const|let|var|if|else|for|while|return|class|import|export|async|await|console\.log)",
    r"\{",
    r"\}",
    r"\(",
    r"\)",
    r";",
    r"=>",
    r"==",
    r"===",
    r"!==",
    r"&&",
    r"\|\|",
    r"\.",
    r"\[",
    r"\]",
]

def is_empty_or_whitespace(output: str) -> bool:
    """Check if the output is empty or contains only whitespace."""
    if not output or not isinstance(output, str):
        return True
    return len(output.strip()) == 0

def detect_refusal(output: str) -> bool:
    """Detect if the output is a refusal or inability statement."""
    if not output or not isinstance(output, str):
        return False
    for pattern in REFUSAL_PATTERNS:
        if re.search(pattern, output):
            return True
    return False

def detect_conversation(output: str) -> bool:
    """Detect if the output is conversational filler or meta-commentary."""
    if not output or not isinstance(output, str):
        return False
    for pattern in CONVERSATION_PATTERNS:
        if re.search(pattern, output, re.IGNORECASE):
            return True
    return False

def looks_like_code(output: str) -> bool:
    """Check if the output resembles code (has code indicators)."""
    if not output or not isinstance(output, str):
        return False
    output_stripped = output.strip()
    if len(output_stripped) == 0:
        return False
    # Count code indicators
    indicator_count = 0
    for pattern in CODE_INDICATORS:
        if re.search(pattern, output_stripped):
            indicator_count += 1
    # If at least 3 distinct indicators are found, likely code
    return indicator_count >= 3

def classify_translation_output(output: str) -> str:
    """
    Classify a translation output into one of the failure categories or 'success'.

    Categories:
    - 'success': Output looks like valid code
    - 'refusal': Output is an explicit refusal or inability
    - 'conversation': Output is conversational filler or meta-commentary
    - 'empty': Output is empty or whitespace-only
    - 'unknown': Output doesn't fit other categories but isn't clearly code
    """
    if is_empty_or_whitespace(output):
        return 'empty'
    if detect_refusal(output):
        return 'refusal'
    if detect_conversation(output):
        return 'conversation'
    if looks_like_code(output):
        return 'success'
    return 'unknown'

def scan_translation_dirs(base_dir: str) -> List[Dict[str, Any]]:
    """
    Scan the translation output directories and classify each translation.

    Args:
        base_dir: Base directory containing condition subdirectories

    Returns:
        List of dictionaries with classification results
    """
    base_path = Path(base_dir)
    if not base_path.exists():
        logger.warning(f"Base directory {base_dir} does not exist")
        return []

    results = []
    condition_dirs = [d for d in base_path.iterdir() if d.is_dir()]

    for condition_dir in condition_dirs:
        condition_name = condition_dir.name
        json_files = list(condition_dir.glob("*.json"))

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                output_text = data.get('output', '')
                input_id = data.get('input_id', 'unknown')
                seed = data.get('seed', 'unknown')
                prompt_condition = data.get('prompt_condition', condition_name)

                classification = classify_translation_output(output_text)

                results.append({
                    'input_id': input_id,
                    'prompt_condition': prompt_condition,
                    'seed': seed,
                    'file_path': str(json_file),
                    'classification': classification,
                    'output_preview': output_text[:200] if len(output_text) > 200 else output_text
                })

            except Exception as e:
                logger.error(f"Error processing {json_file}: {e}")
                continue

    return results

def save_failure_log(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save the failure classification results to a CSV file.

    Args:
        results: List of classification results
        output_path: Path to the output CSV file
    """
    if not results:
        logger.warning("No results to save")
        return

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['input_id', 'prompt_condition', 'seed', 'file_path', 'classification', 'output_preview']

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Saved {len(results)} failure classifications to {output_path}")

def main():
    """Main entry point for the classification script."""
    # Default paths based on project structure
    base_dir = "data/evaluation/raw_translations"
    output_csv = "data/evaluation/failure_classification_log.csv"

    # Allow override via command line arguments
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_csv = sys.argv[2]

    logger.info(f"Scanning translations in {base_dir}")
    results = scan_translation_dirs(base_dir)

    if not results:
        logger.warning("No translations found to classify")
        sys.exit(0)

    # Log summary statistics
    classification_counts = {}
    for r in results:
        cat = r['classification']
        classification_counts[cat] = classification_counts.get(cat, 0) + 1

    logger.info("Classification summary:")
    for cat, count in classification_counts.items():
        logger.info(f"  {cat}: {count}")

    save_failure_log(results, output_csv)

    # Exit with non-zero if there are failures to flag for downstream tasks
    success_count = classification_counts.get('success', 0)
    failure_count = len(results) - success_count
    if failure_count > 0:
        logger.info(f"Found {failure_count} failed translations out of {len(results)} total")
        # Do not exit with error, just log the result for downstream analysis
    else:
        logger.info("All translations classified as successful")

if __name__ == "__main__":
    main()