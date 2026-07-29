import os
import subprocess
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

# FR-008 Validation Sources Documentation
# =======================================
# The metrics extracted below are validated against standard literature and
# established static analysis tools (ruff/McCabe).
#
# 1. Cyclomatic Complexity (CC):
#    - Source: McCabe, T. J. (1976). "A Complexity Measure". IEEE Transactions on Software Engineering.
#    - Definition: The number of linearly independent paths through a program's source code.
#    - Thresholds:
#      - 1-10: Simple, low risk (McCabe original recommendation)
#      - 11-20: Moderate complexity, requires testing
#      - 21-50: High complexity, difficult to maintain
#      - >50: Untestable, critical refactoring needed
#    - Implementation: Calculated via 'ruff check' with 'mccabe' plugin (based on McCabe's algorithm).
#
# 2. Lines of Code (LOC):
#    - Source: Standard software engineering metric (e.g., Pressman, Software Engineering: A Practitioner's Approach).
#    - Definition: Count of non-blank, non-comment lines.
#    - Usage: Proxy for code size and potential maintenance burden.
#
# 3. Indentation Consistency:
#    - Source: PEP 8 (Python Style Guide) & general maintainability heuristics.
#    - Definition: Checks for mixed tabs/spaces or inconsistent indentation depth.
#    - Validation: Enforced by 'ruff check' (E111, E114, etc.).
#
# 4. Security Vulnerabilities (T029 - Flagging):
#    - Source: OWASP Top 10 (2021) & CWE (Common Weakness Enumeration).
#    - Specific Checks:
#      - Hardcoded Credentials (CWE-798): Detection of secrets in source.
#      - Eval Usage (CWE-95): Detection of dangerous dynamic execution.
#    - Action: Samples with these flags are marked for manual review (severity=low/medium)
#      but do NOT cause the execution test to fail, as per task T029 requirements.
#    - Tooling: 'ruff check' with 'ruff' security rules (e.g., S102 for eval, S105 for secrets).

def run_ruff_check(code_content: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Runs 'ruff check' on the provided code content via a temporary file.

    Returns a dictionary containing:
    - 'success': bool
    - 'errors': list of error messages
    - 'warnings': list of warning messages
    - 'info': list of info messages
    - 'metrics': dict of extracted metrics (cyclomatic_complexity, loc, etc.)
    - 'security_flags': list of security-related issues found (for T029)
    """
    result = {
        "success": True,
        "errors": [],
        "warnings": [],
        "info": [],
        "metrics": {
            "cyclomatic_complexity": 0,
            "lines_of_code": 0,
            "indentation_issues": 0,
        },
        "security_flags": []
    }

    if not code_content:
        result["success"] = False
        result["errors"].append("Empty code content provided")
        return result

    try:
        # Create a temporary file to hold the code for ruff
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            tmp_file.write(code_content)
            tmp_path = tmp_file.name

        try:
            # Run ruff with specific rules for metrics and security
            # Using --output-format=json for structured parsing
            # We enable:
            # - E: pycodestyle (includes indentation)
            # - F: Pyflakes
            # - C90: McCabe complexity
            # - S: flake8-bandit (security)
            cmd = [
                "ruff", "check",
                "--select", "E,F,C90,S",
                "--output-format=json",
                "--max-complexity=10", # Threshold for warning, though we parse the count
                tmp_path
            ]

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if proc.returncode == 0 and not proc.stdout.strip():
                # No issues found
                pass
            elif proc.returncode != 0 and proc.stdout.strip():
                # Parse JSON output
                try:
                    issues = json.loads(proc.stdout)
                    for issue in issues:
                        code = issue.get("code", "")
                        message = issue.get("message", "")
                        line = issue.get("row", 0)

                        # Categorize by rule prefix
                        if code.startswith("C90"):
                            # McCabe complexity
                            # Format: "C901: 'func' is too complex (X)"
                            result["metrics"]["cyclomatic_complexity"] = extract_complexity_value(message)
                        elif code.startswith("E1"):
                            # Indentation
                            result["metrics"]["indentation_issues"] += 1
                        elif code.startswith("S"):
                            # Security
                            result["security_flags"].append({
                                "rule": code,
                                "message": message,
                                "line": line,
                                "severity": "warning" # Do not fail test, just flag
                            })
                        elif code.startswith("E"):
                            result["warnings"].append(f"{code}: {message} (line {line})")
                        elif code.startswith("F"):
                            result["warnings"].append(f"{code}: {message} (line {line})")
                except json.JSONDecodeError:
                    # Fallback if ruff outputs text
                    result["errors"].append(f"Ruff output parse error: {proc.stdout}")
            else:
                # Ruff failed or stderr
                if proc.stderr:
                    result["errors"].append(f"Ruff error: {proc.stderr}")

            # Calculate LOC manually if not provided by ruff directly (ruff doesn't always output raw LOC)
            lines = code_content.splitlines()
            result["metrics"]["lines_of_code"] = sum(
                1 for line in lines if line.strip() and not line.strip().startswith('#')
            )

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except subprocess.TimeoutExpired:
        result["success"] = False
        result["errors"].append("Ruff check timed out")
    except FileNotFoundError:
        result["success"] = False
        result["errors"].append("Ruff not found in PATH. Please install: pip install ruff")
    except Exception as e:
        logger.error(f"Unexpected error running ruff: {e}")
        result["success"] = False
        result["errors"].append(f"Runtime error: {str(e)}")

    return result

def extract_complexity_value(message: str) -> int:
    """
    Extracts the numeric complexity value from a McCabe message string.
    Example: "C901: 'func_name' is too complex (12)" -> 12
    """
    import re
    match = re.search(r'\((\d+)\)', message)
    if match:
        return int(match.group(1))
    return 0

def analyze_generated_code(code_samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyzes a list of generated code samples (dicts with 'code' and 'id').

    Returns an enriched list with static analysis results.
    """
    enriched_samples = []

    for sample in code_samples:
        code_content = sample.get("code", "")
        sample_id = sample.get("id", "unknown")

        logger.info(f"Analyzing sample {sample_id}...")
        analysis_result = run_ruff_check(code_content)

        enriched = {
            **sample,
            "analysis": {
                "success": analysis_result["success"],
                "cyclomatic_complexity": analysis_result["metrics"]["cyclomatic_complexity"],
                "lines_of_code": analysis_result["metrics"]["lines_of_code"],
                "indentation_issues": analysis_result["metrics"]["indentation_issues"],
                "security_flags": analysis_result["security_flags"],
                "errors": analysis_result["errors"],
                "warnings": analysis_result["warnings"],
            }
        }
        enriched_samples.append(enriched)

        if not analysis_result["success"]:
            logger.warning(f"Analysis failed for {sample_id}: {analysis_result['errors']}")
        elif analysis_result["security_flags"]:
            logger.info(f"Security flags found for {sample_id}: {analysis_result['security_flags']}")

    return enriched_samples

def main():
    """
    Main entry point for static analysis testing.
    Expects a JSON file at data/processed/prompt_variants.parquet (converted to json for this script)
    or reads from a passed argument. For this task, we demonstrate the function call.
    """
    print("Static Analysis Module - Validation Sources Documented.")
    print("References: McCabe (1976), PEP 8, OWASP Top 10.")
    # In a real run, this would load data and call analyze_generated_code
    # sample = {"id": "test", "code": "def f():\n  x=1\n  return x"}
    # result = analyze_generated_code([sample])
    # print(result)

if __name__ == "__main__":
    main()
