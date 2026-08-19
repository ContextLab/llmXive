import os
import sys
import json
import argparse
import subprocess
import tempfile
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_pmd_path() -> str:
    """
    Retrieve the PMD binary path from environment variable or default.
    Raises FileNotFoundError if PMD is not found.
    """
    pmd_path = os.environ.get('PMD_PATH', 'pmd')
    if not shutil.which(pmd_path):
        # Try common locations if not in PATH
        candidates = [
            '/usr/local/bin/pmd',
            '/opt/pmd/bin/pmd',
            os.path.expanduser('~/.local/bin/pmd')
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                pmd_path = candidate
                break
        else:
            raise FileNotFoundError(
                f"PMD binary not found. Please set PMD_PATH environment variable "
                f"or ensure 'pmd' is in your PATH."
            )
    return pmd_path

def load_file_list(file_list_path: str) -> List[str]:
    """
    Load a list of file paths from a JSON or text file.
    Supports both JSON arrays and newline-delimited text files.
    """
    path = Path(file_list_path)
    if not path.exists():
        raise FileNotFoundError(f"File list not found: {file_list_path}")

    if path.suffix == '.json':
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'files' in data:
                return data['files']
            else:
                raise ValueError(f"Invalid JSON structure in {file_list_path}")
    else:
        # Assume text file with one path per line
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save results to a JSON file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def calculate_cc_single_file(file_path: str, pmd_bin: str) -> Optional[int]:
    """
    Calculate Cyclomatic Complexity for a single Java file using PMD CLI.
    
    Args:
        file_path: Path to the Java file
        pmd_bin: Path to PMD binary
        
    Returns:
        Cyclomatic Complexity value (int) or None if parsing fails
        
    Raises:
        subprocess.CalledProcessError: If PMD command fails
        ValueError: If file cannot be parsed by PMD
    """
    # Validate file exists and is Java
    if not os.path.isfile(file_path):
        logger.warning(f"File not found: {file_path}")
        return None
        
    if not file_path.endswith('.java'):
        logger.warning(f"Not a Java file: {file_path}")
        return None

    try:
        # Run PMD CLI to get XML output
        # Using ruleset for complexity: rulesets/java/complexity.xml
        cmd = [
            pmd_bin,
            '-f', 'xml',
            '-d', file_path,
            '-R', 'rulesets/java/complexity.xml',
            '-no-cache'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            check=True
        )
        
        # Parse XML output
        xml_output = result.stdout
        
        # Check for parsing errors in PMD output
        if 'error' in xml_output.lower() and 'parse' in xml_output.lower():
            logger.warning(f"PMD parse error for {file_path}")
            return None
            
        # Parse XML to find Cyclomatic Complexity violations
        try:
            root = ET.fromstring(xml_output)
        except ET.ParseError:
            logger.warning(f"Invalid XML output from PMD for {file_path}")
            return None
            
        # Look for CyclomaticComplexity violations
        # PMD v7+ uses different structure, but we'll handle both
        cc_value = None
        
        # Search for violations with rule name containing 'CyclomaticComplexity'
        for violation in root.iter('violation'):
            rule = violation.get('rule', '')
            if 'CyclomaticComplexity' in rule or 'cyclomatic' in rule.lower():
                # Extract the complexity value from attributes
                # PMD usually includes 'violation' text or attributes with the value
                msg = violation.text or ''
                
                # Try to extract number from message like "CyclomaticComplexity=5"
                import re
                match = re.search(r'CyclomaticComplexity[=:]\s*(\d+)', msg)
                if match:
                    cc_value = int(match.group(1))
                    break
                    
                # Alternative: check attributes
                if 'complexity' in violation.attrib:
                    try:
                        cc_value = int(violation.attrib['complexity'])
                        break
                    except (ValueError, TypeError):
                        pass
        
        # If no violation found, complexity might be 1 (default for simple methods)
        # But we need to be careful - PMD might not report if below threshold
        # Default threshold is usually 10, so we might miss low complexity values
        # For now, return None if not found to indicate "not measured"
        if cc_value is None:
            logger.debug(f"No CyclomaticComplexity violation found for {file_path}")
            return None
            
        return cc_value
        
    except subprocess.TimeoutExpired:
        logger.error(f"PMD timeout for file: {file_path}")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"PMD failed for {file_path}: {e.stderr}")
        # Check if it's a parse error vs other error
        if 'parse' in e.stderr.lower() or 'syntax' in e.stderr.lower():
            logger.warning(f"Parse error for {file_path}, skipping")
            return None
        raise

def calculate_cc_batch(file_list: List[str], pmd_bin: str, batch_size: int = 50) -> List[Dict[str, Any]]:
    """
    Calculate Cyclomatic Complexity for multiple files.
    
    Args:
        file_list: List of Java file paths
        pmd_bin: Path to PMD binary
        batch_size: Number of files to process in each batch
        
    Returns:
        List of dictionaries with file_path and cc values
    """
    results = []
    failed = 0
    
    for i, file_path in enumerate(file_list):
        if (i + 1) % 100 == 0:
            logger.info(f"Processing file {i + 1}/{len(file_list)}")
            
        try:
            cc = calculate_cc_single_file(file_path, pmd_bin)
            results.append({
                'file_path': file_path,
                'cc': cc,
                'status': 'success' if cc is not None else 'no_violation'
            })
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            results.append({
                'file_path': file_path,
                'cc': None,
                'status': 'error',
                'error': str(e)
            })
            failed += 1
            
    logger.info(f"Batch complete: {len(results)} files processed, {failed} errors")
    return results

def calculate_cc_for_directory(dir_path: str, pmd_bin: str, output_path: str) -> None:
    """
    Calculate Cyclomatic Complexity for all Java files in a directory.
    
    Args:
        dir_path: Directory to scan for Java files
        pmd_bin: Path to PMD binary
        output_path: Path to save results JSON
    """
    dir_path = Path(dir_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
        
    # Find all Java files
    java_files = list(dir_path.rglob('*.java'))
    logger.info(f"Found {len(java_files)} Java files in {dir_path}")
    
    if not java_files:
        logger.warning("No Java files found in directory")
        save_results([], output_path)
        return
        
    # Process files
    results = calculate_cc_batch(
        [str(f) for f in java_files],
        pmd_bin,
        batch_size=50
    )
    
    # Save results
    save_results(results, output_path)

def main():
    """Main entry point for PMD wrapper script."""
    parser = argparse.ArgumentParser(
        description='Calculate Cyclomatic Complexity for Java files using PMD'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input: JSON file with file list OR directory path'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output JSON file path for results'
    )
    parser.add_argument(
        '--pmd-path',
        default=None,
        help='Path to PMD binary (default: use PMD_PATH env or PATH)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    try:
        # Determine PMD path
        pmd_bin = args.pmd_path if args.pmd_path else get_pmd_path()
        logger.info(f"Using PMD binary: {pmd_bin}")
        
        # Check if input is a file list or directory
        input_path = Path(args.input)
        if input_path.is_file():
            # Load file list
            file_list = load_file_list(args.input)
            logger.info(f"Loaded {len(file_list)} files from {args.input}")
            
            # Process batch
            results = calculate_cc_batch(file_list, pmd_bin)
            save_results(results, args.output)
            
        elif input_path.is_dir():
            # Process directory
            calculate_cc_for_directory(args.input, pmd_bin, args.output)
            
        else:
            raise ValueError(f"Input must be a file or directory: {args.input}")
            
        logger.info("PMD wrapper completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
