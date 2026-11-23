"""
PMD Execution Wrapper Module.

Executes PMD CLI on code samples to detect code smells.
Refactored to use shared utilities from utils.pmd_utils.
"""

import os
import sys
import json
import subprocess
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.pmd_utils import run_pmd_on_file, run_pmd_cli, get_pmd_ruleset_path
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)


def run_pmd_on_file_wrapper(file_path: Path, smell_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Wrapper to run PMD on a single file.

    Args:
        file_path: Path to the source file.
        smell_types: List of smell types to check.

    Returns:
        Dict with 'success', 'metrics', 'errors', 'exit_code'.
    """
    return run_pmd_on_file(file_path, smell_types)


def run_pmd_batch(
    file_paths: List[Path],
    smell_types: Optional[List[str]] = None,
    output_file: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Runs PMD on a batch of files.

    Args:
        file_paths: List of file paths to analyze.
        smell_types: List of smell types to check.
        output_file: Optional path to save raw results as JSON.

    Returns:
        List of result dictionaries.
    """
    results = []
    start_time = time.time()

    for idx, f_path in enumerate(file_paths):
        logger.info(f"Analyzing {idx+1}/{len(file_paths)}: {f_path}")
        try:
            result = run_pmd_on_file_wrapper(f_path, smell_types)
            result["file_path"] = str(f_path)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to analyze {f_path}: {e}")
            results.append({
                "file_path": str(f_path),
                "success": False,
                "metrics": [],
                "errors": [str(e)],
                "exit_code": -1
            })

    duration = time.time() - start_time
    logger.info(f"Batch analysis completed in {duration:.2f}s for {len(file_paths)} files.")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {output_file}")

    return results


def main():
    """
    Main entry point for running PMD on a directory of samples.
    Expects environment variable SAMPLE_DIR or command line argument.
    """
    config = get_config()
    sample_dir = Path(os.environ.get("SAMPLE_DIR", config.get("data_raw_dir", "data/raw")))
    output_dir = Path(config.get("data_intermediate_dir", "data/intermediate"))

    # Default smell types
    smell_types = ["LongMethod", "DuplicatedCode", "FeatureEnvy", "LongParameterList"]

    # Find all Python and Java files
    files = []
    for ext in ["*.py", "*.java"]:
        files.extend(list(sample_dir.rglob(ext)))

    if not files:
        logger.warning(f"No sample files found in {sample_dir}")
        return

    logger.info(f"Found {len(files)} files to analyze.")

    output_file = output_dir / "pmd_raw_results.json"
    results = run_pmd_batch(files, smell_types, output_file)

    success_count = sum(1 for r in results if r.get("success", False))
    logger.info(f"Analysis complete. Success: {success_count}/{len(results)}")


if __name__ == "__main__":
    main()
