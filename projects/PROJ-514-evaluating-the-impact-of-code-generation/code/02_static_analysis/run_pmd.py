import os
import sys
import json
import subprocess
import time
import logging
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# Add project root to path to resolve utils imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_project_root, get_limits, get_timeouts
from utils.logger import get_logger
from utils.validators import get_language_from_extension, validate_file_syntax

logger = get_logger(__name__)

# Constants derived from task requirements
# PMD rulesets for the four required categories
PMD_RULESET_PATH = "pmd_ruleset.xml" 
# Default memory limit: 2GB
DEFAULT_MEMORY_LIMIT = "2G"
# Default timeout: 2 minutes (120 seconds)
DEFAULT_TIMEOUT_SECONDS = 120

def _get_pmd_ruleset_path() -> str:
    """
    Returns the path to the PMD ruleset file.
    The ruleset must define rules for LongMethod, DuplicatedCode, 
    FeatureEnvy, and LongParameterList.
    """
    # In a real deployment, this would point to a specific ruleset file 
    # in the project or a standard PMD ruleset.
    # For this implementation, we assume a custom ruleset exists at:
    # project_root / "code" / "02_static_analysis" / "pmd_ruleset.xml"
    # If not found, we fall back to a standard PMD ruleset path if available,
    # or raise an error.
    
    custom_ruleset = project_root / "code" / "02_static_analysis" / "pmd_ruleset.xml"
    if custom_ruleset.exists():
        return str(custom_ruleset)
    
    # Fallback to standard PMD java-basic ruleset if the custom one is missing,
    # though the project should ideally provide the specific custom ruleset.
    # Note: Standard PMD installation usually places rulesets in $PMD_HOME/rulesets
    pmd_home = os.environ.get("PMD_HOME")
    if pmd_home:
        standard_ruleset = Path(pmd_home) / "rulesets" / "java" / "codesize.xml"
        if standard_ruleset.exists():
            logger.warning(f"Custom ruleset not found. Using standard codesize ruleset: {standard_ruleset}")
            return str(standard_ruleset)
    
    raise FileNotFoundError(
        f"Could not find PMD ruleset. Expected at {custom_ruleset} or standard PMD ruleset in $PMD_HOME."
    )

def run_pmd_on_file(file_path: str) -> Tuple[Optional[str], Optional[str], int]:
    """
    Executes PMD CLI on a single file.
    
    Args:
        file_path: Path to the code file (Python or Java) to analyze.
        
    Returns:
        Tuple of (stdout, stderr, exit_code).
        If the process times out or fails due to resource limits, 
        stderr will contain the error message and exit_code will be non-zero.
        Returns (None, None, -1) if the file is invalid or PMD is unavailable.
    """
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        logger.error(f"File not found: {file_path}")
        return None, None, -1

    # Validate syntax before running PMD to avoid unnecessary execution
    lang = get_language_from_extension(file_path_obj.suffix)
    if lang not in ("python", "java"):
        logger.warning(f"Skipping unsupported file type for PMD: {file_path}")
        return None, None, -1

    # Validate syntax
    if not validate_file_syntax(file_path):
        logger.warning(f"Syntax validation failed for: {file_path}. Skipping PMD.")
        return None, None, -1

    limits = get_limits()
    timeouts = get_timeouts()
    
    # Use config values or defaults
    memory_limit = limits.get("pmd_memory_mb", 2048)
    timeout_seconds = timeouts.get("pmd_per_file", 120)
    
    pmd_executable = os.environ.get("PMD_BIN", "pmd")
    ruleset = _get_pmd_ruleset_path()
    
    # Construct command
    # PMD CLI syntax: pmd check -R <ruleset> -d <file> -f xml
    cmd = [
        pmd_executable,
        "check",
        "-R", ruleset,
        "-d", str(file_path),
        "-f", "xml" # XML is easier to parse for specific violations
    ]
    
    # Set environment variables for memory limit
    env = os.environ.copy()
    # Note: PMD memory settings are often passed via JVM options if running Java-based PMD
    # If using the Java wrapper, we might need to pass -D or use JAVA_OPTS
    # Assuming standard PMD CLI which handles its own memory or relies on system limits.
    # If PMD is running as a Java process, we might need to inject JAVA_OPTS.
    # For robustness, we try to set JAVA_OPTS if PMD is Java-based.
    if "PMD_HOME" in env:
        env["JAVA_OPTS"] = f"-Xmx{memory_limit}m"
    
    start_time = time.time()
    stdout_data = None
    stderr_data = None
    exit_code = -1

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            env=env,
            cwd=str(project_root)
        )
        stdout_data = proc.stdout
        stderr_data = proc.stderr
        exit_code = proc.returncode
        
        elapsed = time.time() - start_time
        logger.debug(f"PMD analysis for {file_path} took {elapsed:.2f}s, exit code: {exit_code}")
        
    except subprocess.TimeoutExpired as e:
        logger.error(f"PMD timeout for {file_path} after {timeout_seconds}s")
        return None, f"Timeout: {e}", -1
    except FileNotFoundError:
        logger.error(f"PMD executable not found: {pmd_executable}. Ensure PMD is installed and in PATH or set PMD_BIN.")
        return None, f"Error: PMD executable not found: {pmd_executable}", -1
    except Exception as e:
        logger.error(f"Unexpected error running PMD on {file_path}: {e}")
        return None, str(e), -1

    return stdout_data, stderr_data, exit_code

def run_pmd_batch(file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Runs PMD on a batch of files sequentially.
    
    Args:
        file_paths: List of file paths to analyze.
        
    Returns:
        Dictionary mapping file_path to a dict containing:
            - 'stdout': raw stdout
            - 'stderr': raw stderr
            - 'exit_code': exit code
            - 'success': boolean
            - 'error': error message if failed
    """
    results = {}
    for fp in file_paths:
        stdout, stderr, exit_code = run_pmd_on_file(fp)
        results[fp] = {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "success": (exit_code == 0), # Note: PMD returns non-zero if violations found
            "error": stderr if exit_code != 0 and stdout is None else None
        }
    return results

def main():
    """
    Main entry point for running PMD analysis.
    Expects a list of file paths as arguments or reads from a manifest.
    For this task, we demonstrate running on a specific directory or file.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run PMD static analysis on code files.")
    parser.add_argument("--input", "-i", type=str, required=True, 
                        help="Input file or directory containing code files.")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output file for raw results (JSON). If None, prints to stdout.")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    files_to_analyze = []
    if input_path.is_file():
        files_to_analyze.append(str(input_path))
    elif input_path.is_dir():
        # Recursively find .py and .java files
        files_to_analyze = [str(f) for f in input_path.rglob("*") if f.suffix in (".py", ".java")]
        if not files_to_analyze:
            logger.error(f"No .py or .java files found in {input_path}")
            sys.exit(1)
    else:
        logger.error(f"Input path does not exist: {input_path}")
        sys.exit(1)
        
    logger.info(f"Found {len(files_to_analyze)} files to analyze.")
    
    results = run_pmd_batch(files_to_analyze)
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results written to {args.output}")
    else:
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
