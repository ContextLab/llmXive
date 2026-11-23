import os
import subprocess
import tempfile
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET

from src.config import validate_pmd_path

logger = logging.getLogger(__name__)

def get_pmd_path() -> str:
    """
    Retrieve the path to the PMD executable.
    Uses the PMD_PATH environment variable or defaults to 'pmd'.
    """
    pmd_path = os.environ.get('PMD_PATH', 'pmd')
    if not shutil.which(pmd_path):
        raise FileNotFoundError(f"PMD executable not found at '{pmd_path}'. "
                                "Please set PMD_PATH environment variable or install PMD.")
    return pmd_path

def load_file_list(file_paths: List[str]) -> List[str]:
    """
    Filter and return a list of valid file paths.
    """
    valid_files = []
    for p in file_paths:
        if os.path.isfile(p):
            valid_files.append(p)
        else:
            logger.warning(f"Skipping non-existent file: {p}")
    return valid_files

def validate_java_syntax(file_path: str) -> bool:
    """
    Basic validation that the file exists and has a .java extension.
    PMD will handle actual syntax parsing errors during analysis.
    """
    if not file_path.endswith('.java'):
        return False
    return os.path.isfile(file_path)

def calculate_cc_single_file(file_path: str, pmd_path: Optional[str] = None) -> int:
    """
    Calculate Cyclomatic Complexity for a single Java file using PMD CLI.
    
    Logic:
    1. Run PMD CLI: `pmd -f xml -d <file> -rulesets rulesets/java/complexity.xml`
    2. Parse the XML output.
    3. Sum the 'complexity' attribute of all <violation> tags.
    4. If PMD returns no output or no violations, return 0.
    5. If PMD fails to parse (syntax error), log and raise an exception or return -1 
       (depending on caller strategy, here we log and raise DataParseError equivalent).
    
    Args:
        file_path: Path to the Java file.
        pmd_path: Optional path to PMD executable.
        
    Returns:
        Integer Cyclomatic Complexity score.
        
    Raises:
        subprocess.CalledProcessError: If PMD command fails unexpectedly.
        RuntimeError: If PMD cannot parse the file (syntax error).
    """
    if pmd_path is None:
        pmd_path = get_pmd_path()
        
    if not validate_java_syntax(file_path):
        logger.error(f"Invalid Java file: {file_path}")
        raise ValueError(f"Invalid Java file: {file_path}")

    cmd = [
        pmd_path,
        '-f', 'xml',
        '-d', file_path,
        '-R', 'rulesets/java/complexity.xml'
    ]

    try:
        # Run PMD with a timeout to prevent hanging on large files
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60, # 60 seconds per file
            check=False
        )
    except subprocess.TimeoutExpired:
        logger.error(f"PMD timed out for file: {file_path}")
        raise RuntimeError(f"PMD timed out for file: {file_path}")

    stdout = result.stdout.decode('utf-8', errors='ignore')
    stderr = result.stderr.decode('utf-8', errors='ignore')

    # Check for PMD specific error codes or messages indicating parse failure
    # PMD usually returns exit code 0 even with violations, but non-zero on critical errors.
    # However, syntax errors often result in violations with specific rules or just empty output if skipped.
    if result.returncode != 0:
        # Check if it's a parse error
        if "Cannot parse" in stderr or "ParseException" in stderr:
            logger.warning(f"PMD failed to parse file (syntax error): {file_path}")
            raise RuntimeError(f"PMD parse error: {file_path} - {stderr}")
        # If it's a different error, log it but maybe not fail the whole batch immediately
        logger.warning(f"PMD returned non-zero for {file_path}: {stderr}")

    # Parse XML
    if not stdout.strip():
        # No output means no violations found (CC = 0) or empty file
        logger.debug(f"No PMD output for {file_path}, assuming CC=0")
        return 0

    try:
        root = ET.fromstring(stdout)
    except ET.ParseError as e:
        # This might happen if PMD outputs something other than valid XML due to a crash
        logger.error(f"Failed to parse PMD XML output for {file_path}: {e}")
        raise RuntimeError(f"Invalid PMD XML output for {file_path}")

    total_complexity = 0
    violations = root.findall('.//violation')
    
    for v in violations:
        complexity_attr = v.get('complexity')
        if complexity_attr:
            try:
                total_complexity += int(complexity_attr)
            except ValueError:
                logger.warning(f"Invalid complexity value in PMD output for {file_path}: {complexity_attr}")

    logger.debug(f"Calculated CC for {file_path}: {total_complexity}")
    return total_complexity

def calculate_cc_batch(file_paths: List[str], pmd_path: Optional[str] = None) -> Dict[str, int]:
    """
    Calculate Cyclomatic Complexity for a list of Java files.
    
    Args:
        file_paths: List of paths to Java files.
        pmd_path: Optional path to PMD executable.
        
    Returns:
        Dictionary mapping file_path -> CC score.
        Files that fail to parse are skipped and logged.
    """
    if pmd_path is None:
        pmd_path = get_pmd_path()
        
    results = {}
    exclusion_count = 0

    for f_path in file_paths:
        try:
            cc = calculate_cc_single_file(f_path, pmd_path)
            results[f_path] = cc
        except RuntimeError as e:
            # Handle parse errors gracefully as per task requirement
            logger.warning(f"Skipping file due to PMD error: {f_path} - {e}")
            exclusion_count += 1
        except Exception as e:
            logger.error(f"Unexpected error processing {f_path}: {e}")
            exclusion_count += 1

    if exclusion_count > 0:
        logger.info(f"Excluded {exclusion_count} files from CC calculation due to errors.")
        
    return results

def calculate_cc_for_directory(directory_path: str, pmd_path: Optional[str] = None) -> Dict[str, int]:
    """
    Calculate Cyclomatic Complexity for all .java files in a directory.
    
    Args:
        directory_path: Path to the directory containing Java files.
        pmd_path: Optional path to PMD executable.
        
    Returns:
        Dictionary mapping file_path -> CC score.
    """
    directory = Path(directory_path)
    java_files = list(directory.rglob('*.java'))
    file_paths = [str(f) for f in java_files]
    
    if not file_paths:
        logger.warning(f"No Java files found in {directory_path}")
        return {}
        
    return calculate_cc_batch(file_paths, pmd_path)

def save_results(results: Dict[str, int], output_path: str) -> None:
    """
    Save the CC results to a JSON file.
    
    Args:
        results: Dictionary of file_path -> CC.
        output_path: Path to the output JSON file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    """
    CLI entry point for calculating Cyclomatic Complexity.
    Usage: python -m src.metrics_pmd --input <path> --output <path> [--directory]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate Cyclomatic Complexity using PMD')
    parser.add_argument('--input', '-i', required=True, help='Input file path or directory')
    parser.add_argument('--output', '-o', required=True, help='Output JSON file path')
    parser.add_argument('--directory', '-d', action='store_true', help='Treat input as a directory')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        if args.directory:
            results = calculate_cc_for_directory(args.input)
        else:
            results = calculate_cc_single_file(args.input)
            results = {args.input: results}
        
        save_results(results, args.output)
        print(f"Successfully processed {len(results)} files.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
