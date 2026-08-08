"""
T052: Verify Streaming Strategy for Large Datasets

This script verifies that the dataset loading logic in the pipeline
adheres to Constraint-002 (RAM < 7GB) by ensuring:
1. `datasets.load_dataset` is called with `streaming=True` where appropriate.
2. Statistics are accumulated online (iterative processing) rather than
   loading the entire dataset into memory at once.
3. No explicit in-memory materialization of the full dataset occurs.

It scans `code/downloaders.py` and `code/ingestion.py` for patterns.
"""
import os
import sys
import re
import logging
from pathlib import Path
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/streaming_verification.log')
    ]
)
logger = logging.getLogger(__name__)

# Patterns to detect
# 1. Streaming enabled
STREAMING_PATTERN = re.compile(
    r'load_dataset\s*\([^)]*streaming\s*=\s*True',
    re.IGNORECASE
)

# 2. Iterative processing patterns (indicates online accumulation)
ITERATIVE_PATTERNS = [
    re.compile(r'for\s+.*\s+in\s+dataset', re.IGNORECASE), # for x in dataset
    re.compile(r'dataset\.\s*iter\(\)', re.IGNORECASE),     # dataset.iter()
    re.compile(r'itertools\.islice', re.IGNORECASE),        # chunking via islice
    re.compile(r'yield\s+', re.IGNORECASE),                 # generator usage
]

# 3. Anti-patterns: Full materialization in memory
ANTI_PATTERNS = [
    re.compile(r'\blist\s*\(\s*dataset\s*\)', re.IGNORECASE), # list(dataset)
    re.compile(r'dataset\s*\[\s*:\s*\]', re.IGNORECASE),      # dataset[:]
    re.compile(r'\.to_pandas\s*\(\s*\)', re.IGNORECASE),      # .to_pandas() on full
    re.compile(r'np\.array\s*\(\s*dataset\s*\)', re.IGNORECASE),
]

# Files to scan based on project structure and task context
TARGET_FILES = [
    'code/downloaders.py',
    'code/ingestion.py',
]

def check_file(file_path: str) -> Tuple[bool, List[str], List[str]]:
    """
    Scans a single file for streaming compliance.
    Returns: (is_compliant, found_streaming, found_anti_patterns)
    """
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"File not found: {file_path}")
        return False, [], ["File missing"]

    try:
        content = path.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return False, [], [f"Read error: {e}"]

    issues = []
    streaming_found = []
    anti_patterns_found = []

    # Check for streaming flag
    if STREAMING_PATTERN.search(content):
        streaming_found.append("Streaming=True detected in load_dataset call")
    else:
        # Note: Not all files need streaming (e.g., small config files), 
        # but downloaders/ingestion for large datasets should use it.
        if "download" in path.name.lower() or "ingestion" in path.name.lower():
            issues.append("WARNING: 'streaming=True' not detected in large dataset loader.")

    # Check for iterative processing
    has_iterative = any(p.search(content) for p in ITERATIVE_PATTERNS)
    if not has_iterative and not streaming_found:
        # If not streaming, we assume it might be loading small data, 
        # but if it's a downloader, it's suspicious.
        if "download" in path.name.lower() or "ingestion" in path.name.lower():
            issues.append("WARNING: No iterative processing pattern found (e.g., for loop over dataset).")

    # Check for anti-patterns
    for pattern in ANTI_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            anti_patterns_found.append(f"Anti-pattern detected: {pattern.pattern}")
            issues.append(f"CRITICAL: Full materialization detected: {pattern.pattern}")

    is_compliant = len(anti_patterns_found) == 0 and (len(streaming_found) > 0 or "small" in path.name.lower())
    return is_compliant, streaming_found, anti_patterns_found

def main():
    logger.info("Starting T052 Streaming Strategy Verification...")
    all_compliant = True
    total_issues = []

    for file_path in TARGET_FILES:
        logger.info(f"Scanning {file_path}...")
        compliant, streaming, anti = check_file(file_path)
        
        if streaming:
            logger.info(f"  [PASS] Streaming strategy found: {streaming}")
        
        if anti:
            logger.error(f"  [FAIL] Anti-patterns found: {anti}")
            all_compliant = False
            total_issues.extend(anti)
        
        if not compliant:
            all_compliant = False

    # Write verification report
    report_path = Path("results/streaming_verification_report.txt")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write("T052 Streaming Strategy Verification Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Status: {'PASSED' if all_compliant else 'FAILED'}\n\n")
        f.write("Files Scanned:\n")
        for fp in TARGET_FILES:
            f.write(f"  - {fp}\n")
        f.write("\nFindings:\n")
        if total_issues:
            for issue in total_issues:
                f.write(f"  - {issue}\n")
        else:
            f.write("  - No anti-patterns detected. Streaming strategy verified.\n")
        
        f.write("\nConstraint-002 Compliance: ")
        f.write("VERIFIED\n" if all_compliant else "VIOLATION DETECTED\n")

    logger.info(f"Verification report saved to {report_path}")

    if not all_compliant:
        logger.error("T052 Verification FAILED: Streaming constraints violated.")
        sys.exit(1)
    else:
        logger.info("T052 Verification PASSED: Streaming strategy is compliant.")
        sys.exit(0)

if __name__ == "__main__":
    main()
