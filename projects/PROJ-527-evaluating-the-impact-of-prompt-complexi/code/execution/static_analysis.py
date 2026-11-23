from __future__ import annotations

import os
import subprocess
import json
import tempfile
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

from config import Paths
from utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# VALIDATION SOURCES (FR-008)
# ============================================================================
# The metrics extracted in this module are validated against the following
# authoritative sources:
#
# 1. Cyclomatic Complexity (McCabe):
#    - Source: McCabe, J. (1976). "A Complexity Measure". IEEE Transactions
#      on Software Engineering, SE-2(4), 308-320.
#    - Definition: A software metric used to indicate the complexity of a
#      program. It is a measure of the number of linearly independent paths
#      through a program's source code.
#    - Implementation: Calculated using `radon cc` (radon library), which
#      implements the standard McCabe algorithm for Python AST analysis.
#
# 2. Ruff Static Analysis:
#    - Source: Ruff Documentation v0.1.0 (https://docs.astral.sh/ruff/)
#    - Usage: Used for security vulnerability detection (SEC rules) and
#      code style consistency checks.
# ============================================================================

def run_ruff_check(code_content: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Run Ruff static analysis on the provided code content.

    Args:
        code_content: The Python code string to analyze.

    Returns:
        Tuple of (success, error_message, list_of_issues).
        If success is False, error_message contains the stderr output.
        If success is True, list_of_issues contains the parsed JSON results.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code_content)
        temp_path = f.name

    try:
        # Run ruff check with JSON output
        # Using --output-format=json for machine-readable results
        result = subprocess.run(
            ['ruff', 'check', temp_path, '--output-format=json', '--quiet'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # No issues found
            return True, "", []
        elif result.returncode == 1:
            # Issues found (return code 1 is standard for linter findings)
            try:
                issues = json.loads(result.stdout)
                return True, "", issues
            except json.JSONDecodeError:
                return False, "Failed to parse Ruff JSON output", []
        else:
            # Error running ruff (syntax error in code, missing file, etc.)
            return False, result.stderr.strip(), []
    except subprocess.TimeoutExpired:
        return False, "Ruff check timed out", []
    except Exception as e:
        return False, str(e), []
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass

def extract_complexity_value(code_content: str) -> Optional[float]:
    """
    Extract cyclomatic complexity (McCabe) from code using radon.

    Implements the complexity measure defined in:
    McCabe, J. (1976). A Complexity Measure. IEEE Transactions on Software Engineering.

    Args:
        code_content: The Python code string to analyze.

    Returns:
        The maximum cyclomatic complexity value found in the code, or None if
        extraction fails.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code_content)
        temp_path = f.name

    try:
        # Run radon cc (cyclomatic complexity) with JSON output
        result = subprocess.run(
            ['radon', 'cc', temp_path, '-s', '-j'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0 and result.returncode != 1:
            # radon returns 1 if issues are found but still outputs JSON
            # returns non-zero for actual errors
            logger.warning(f"Radon CC returned error code {result.returncode}: {result.stderr}")
            return None

        try:
            data = json.loads(result.stdout)
            if not data:
                return None

            # Find the maximum complexity across all functions/classes
            max_cc = 0.0
            for block in data:
                if 'complexity' in block:
                    # 'complexity' can be a dict with 'total' key for nested structures
                    if isinstance(block['complexity'], dict):
                        max_cc = max(max_cc, block['complexity'].get('total', 0))
                    else:
                        max_cc = max(max_cc, block.get('complexity', 0))
            return float(max_cc) if max_cc > 0 else None
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse radon JSON output: {result.stdout}")
            return None
    except subprocess.TimeoutExpired:
        logger.error("Radon CC timed out")
        return None
    except FileNotFoundError:
        logger.error("Radon not found. Please install: pip install radon")
        return None
    except Exception as e:
        logger.error(f"Error running radon CC: {e}")
        return None
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass

def check_security_vulnerabilities(code_content: str) -> List[str]:
    """
    Check for security vulnerabilities using Ruff SEC rules.

    Args:
        code_content: The Python code string to analyze.

    Returns:
        List of security rule codes detected (e.g., 'SEC101', 'SEC301').
    """
    success, _, issues = run_ruff_check(code_content)
    if not success:
        return []

    security_codes = []
    for issue in issues:
        # Ruff JSON output typically includes 'code' or 'rule' field
        code = issue.get('code') or issue.get('rule')
        if code and code.startswith('SEC'):
            security_codes.append(code)

    return security_codes

def analyze_generated_code(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze generated code for static metrics: cyclomatic complexity and lines of code.

    This function implements the metrics defined in standard literature:
    - Cyclomatic Complexity: Per McCabe (1976)
    - Lines of Code: Standard metric for code size

    Args:
        df: DataFrame containing 'code' column with generated Python code.

    Returns:
        DataFrame with appended columns:
        - 'cyclomatic_complexity': Max McCabe complexity (float)
        - 'lines_of_code': Total lines of code (int)
        - 'security_issues': List of detected security rule codes (list)
    """
    results = {
        'cyclomatic_complexity': [],
        'lines_of_code': [],
        'security_issues': []
    }

    logger.info(f"Analyzing {len(df)} code samples for static metrics...")

    for idx, row in df.iterrows():
        code = row.get('code', '')
        if not code or not isinstance(code, str):
            results['cyclomatic_complexity'].append(None)
            results['lines_of_code'].append(0)
            results['security_issues'].append([])
            continue

        # Calculate Lines of Code
        lines = [line for line in code.split('\n') if line.strip()]
        loc = len(lines)

        # Calculate Cyclomatic Complexity (McCabe)
        cc = extract_complexity_value(code)

        # Check Security Vulnerabilities
        sec_issues = check_security_vulnerabilities(code)

        results['cyclomatic_complexity'].append(cc)
        results['lines_of_code'].append(loc)
        results['security_issues'].append(sec_issues)

        if (idx + 1) % 50 == 0:
            logger.info(f"Processed {idx + 1}/{len(df)} samples")

    df['cyclomatic_complexity'] = results['cyclomatic_complexity']
    df['lines_of_code'] = results['lines_of_code']
    df['security_issues'] = results['security_issues']

    logger.info("Static analysis complete.")
    return df

def main():
    """Main entry point for static analysis script."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze generated code for static metrics.")
    parser.add_argument(
        '--input',
        type=str,
        default=str(Paths.PROCESSED_DATA_DIR / 'prompt_variants.parquet'),
        help='Input parquet file path'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=str(Paths.PROCESSED_DATA_DIR / 'prompt_variants_with_analysis.parquet'),
        help='Output parquet file path'
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1

    logger.info(f"Loading data from {input_path}")
    df = pd.read_parquet(input_path)

    logger.info(f"Analyzing code in {len(df)} rows")
    analyzed_df = analyze_generated_code(df)

    logger.info(f"Writing results to {output_path}")
    analyzed_df.to_parquet(output_path, index=False)

    # Also write a summary CSV for manual review if needed
    summary_csv = Paths.RESULTS_DIR / 'static_analysis_summary.csv'
    analyzed_df[['problem_id', 'variant_label', 'cyclomatic_complexity', 'lines_of_code', 'security_issues']].to_csv(summary_csv, index=False)
    logger.info(f"Summary written to {summary_csv}")

    return 0

if __name__ == '__main__':
    exit(main())
