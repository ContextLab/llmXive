import os
import sys
import json
import argparse
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_pmd_path() -> str:
    """
    Retrieve the PMD binary path from environment or default locations.
    Raises FileNotFoundError if PMD is not found.
    """
    pmd_path = os.environ.get('PMD_PATH')
    if pmd_path:
        if not os.path.exists(pmd_path):
            raise FileNotFoundError(f"PMD binary not found at specified path: {pmd_path}")
        return pmd_path
    
    # Default locations to search
    default_paths = [
        '/usr/bin/pmd',
        '/usr/local/bin/pmd',
        '/opt/pmd/bin/pmd',
        'pmd' # relies on PATH
    ]
    
    for path in default_paths:
        if os.path.exists(path) or shutil.which(path):
            return path
    
    raise FileNotFoundError(
        "PMD binary not found. Please install PMD or set the PMD_PATH environment variable."
    )

def load_file_list(file_paths: List[str]) -> List[Path]:
    """
    Load and validate a list of file paths.
    Returns a list of Path objects for existing Java files.
    """
    valid_files = []
    for fp in file_paths:
        path = Path(fp)
        if path.exists() and path.suffix == '.java':
            valid_files.append(path)
        else:
            logger.warning(f"Skipping invalid or non-Java file: {fp}")
    return valid_files

def validate_java_syntax(file_path: Path) -> bool:
    """
    Validate that a Java file parses without syntax errors using PMD.
    This acts as a pre-check before calculating complexity.
    Returns True if valid, False otherwise.
    """
    pmd_cmd = [
        get_pmd_path(),
        'check',
        '-f', 'text',
        '-R', 'rulesets/java/quickstart.xml', # Quick check rule set
        str(file_path)
    ]
    
    try:
        result = subprocess.run(
            pmd_cmd,
            capture_output=True,
            text=True,
            timeout=30 # Timeout for single file validation
        )
        # If return code is 0, no violations (including syntax errors) found
        # If return code is 1, violations found (might be syntax or style)
        # If return code is 2, error occurred (e.g., parse error)
        if result.returncode == 2:
            logger.error(f"Syntax error in {file_path}: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout validating syntax for {file_path}")
        return False
    except Exception as e:
        logger.error(f"Error validating syntax for {file_path}: {e}")
        return False

def calculate_cc_single_file(file_path: Path) -> Optional[int]:
    """
    Calculate Cyclomatic Complexity for a single Java file using PMD CLI.
    
    Exact CLI: pmd -f xml -d <dir> -rulesets rulesets/java/complexity.xml
    We adapt this to run on a single file by passing the file path as the directory 
    or using the 'check' command with specific rules.
    
    Since PMD 7.0.0 'check' is the primary command, we use:
    pmd check -f xml -R rulesets/java/complexity.xml <file>
    
    Parses <violation> tags for CyclomaticComplexity.
    """
    pmd_path = get_pmd_path()
    ruleset = 'rulesets/java/complexity.xml'
    
    # Construct command
    # Note: For single file, we can pass the file directly to 'check'
    cmd = [
        pmd_path,
        'check',
        '-f', 'xml',
        '-R', ruleset,
        str(file_path)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode not in (0, 1):
            # Return code 2 usually indicates a parse error or internal error
            logger.warning(f"PMD execution failed for {file_path}: {result.stderr}")
            return None

        # Parse XML output
        # We need to find <violation ... rule="CyclomaticComplexity" ...>
        import xml.etree.ElementTree as ET
        
        try:
            root = ET.fromstring(result.stdout)
        except ET.ParseError:
            logger.warning(f"Failed to parse PMD XML output for {file_path}")
            return None
        
        # PMD XML structure: <pmd> ... <file> ... <violation> ... </file> ... </pmd>
        # We look for violations with rule name "CyclomaticComplexity"
        cc_value = None
        
        for violation in root.iter('violation'):
            if violation.get('rule') == 'CyclomaticComplexity':
                # The value is often in the 'externalInfoUrl' or as text, 
                # but PMD usually puts the metric value in the 'msg' attribute or as text content.
                # In PMD 7, the complexity value is often in the 'msg' attribute or as text.
                # Let's check the text content or attributes.
                msg = violation.get('msg', '')
                # Example msg: "CyclomaticComplexity is 15"
                # We need to extract the number.
                import re
                match = re.search(r'\d+', msg)
                if match:
                    cc_value = int(match.group())
                    break
                
                # Fallback: check if the value is in the element text
                if violation.text and violation.text.strip().isdigit():
                    cc_value = int(violation.text.strip())
                    break
        
        return cc_value

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout calculating CC for {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error calculating CC for {file_path}: {e}")
        return None

def calculate_cc_batch(file_paths: List[Path]) -> Dict[str, int]:
    """
    Calculate Cyclomatic Complexity for a batch of Java files.
    Returns a dictionary mapping file path (str) to CC (int).
    """
    results = {}
    for file_path in file_paths:
        # Validate syntax first
        if not validate_java_syntax(file_path):
            logger.warning(f"Skipping {file_path} due to syntax errors.")
            continue
        
        cc = calculate_cc_single_file(file_path)
        if cc is not None:
            results[str(file_path)] = cc
        else:
            logger.warning(f"Could not calculate CC for {file_path}")
    
    return results

def calculate_cc_for_directory(directory: Path, output_file: Optional[Path] = None) -> Dict[str, int]:
    """
    Traverse a directory, find all Java files, and calculate CC.
    If output_file is provided, saves results as JSON.
    """
    java_files = list(directory.rglob('*.java'))
    logger.info(f"Found {len(java_files)} Java files in {directory}")
    
    results = calculate_cc_batch(java_files)
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_file}")
    
    return results

def save_results(results: Dict[str, int], output_path: str) -> None:
    """
    Save results to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Calculate Cyclomatic Complexity using PMD')
    parser.add_argument('--input', type=str, required=True, help='Input file or directory path')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file path')
    parser.add_argument('--validate', action='store_true', help='Validate Java syntax before calculation')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        if input_path.suffix != '.java':
            logger.error("Input file must be a .java file")
            sys.exit(1)
        
        if args.validate and not validate_java_syntax(input_path):
            logger.error("Input file has syntax errors")
            sys.exit(1)
        
        results = {str(input_path): calculate_cc_single_file(input_path)}
    elif input_path.is_dir():
        results = calculate_cc_for_directory(input_path, Path(args.output))
    else:
        logger.error("Input path does not exist")
        sys.exit(1)
    
    # Filter out None values if any
    clean_results = {k: v for k, v in results.items() if v is not None}
    save_results(clean_results, args.output)

if __name__ == '__main__':
    main()