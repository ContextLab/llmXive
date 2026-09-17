import os
import subprocess
import tempfile
import shutil
import logging
import time
import csv
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import get_data_dir, get_timeout_compile, get_timeout_exec

logger = logging.getLogger(__name__)

class CompilationFailedError(Exception):
    """Raised when test compilation fails after retries."""
    pass

class ExecutionError(Exception):
    """Raised when test execution fails."""
    pass

class ExecutionResult:
    def __init__(self, success: bool, coverage: Optional[float] = None, 
                 error_msg: Optional[str] = None, stdout: str = "", stderr: str = ""):
        self.success = success
        self.coverage = coverage
        self.error_msg = error_msg
        self.stdout = stdout
        self.stderr = stderr

def retry_compile(source_dir: str, classpath: str, timeout: int = None) -> Tuple[bool, str]:
    """
    Attempts compilation up to 3 times with 1s delay.
    Returns (success, error_message).
    """
    timeout = timeout or get_timeout_compile()
    max_attempts = 3
    delay = 1.0
    last_error = ""

    javac_path = "javac"

    for attempt in range(1, max_attempts + 1):
        try:
            # Find all .java files
            java_files = []
            for root, _, files in os.walk(source_dir):
                for f in files:
                    if f.endswith(".java"):
                        java_files.append(os.path.join(root, f))
            
            if not java_files:
                return True, "" # Nothing to compile

            cmd = [javac_path, "-cp", classpath] + java_files
            
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout
            )

            if proc.returncode == 0:
                logger.info(f"Compilation successful on attempt {attempt}")
                return True, ""
            else:
                last_error = proc.stderr.decode('utf-8', errors='ignore')
                if not last_error:
                    last_error = proc.stdout.decode('utf-8', errors='ignore')
                logger.warning(f"Compilation attempt {attempt} failed: {last_error[:200]}")
                if attempt < max_attempts:
                    time.sleep(delay)
        except subprocess.TimeoutExpired:
            last_error = f"Compilation timed out after {timeout}s"
            logger.warning(f"Compilation attempt {attempt} timed out")
            if attempt < max_attempts:
                time.sleep(delay)
        except FileNotFoundError:
            raise CompilationFailedError(f"javac not found in PATH. Please install Java JDK.")
        except Exception as e:
            last_error = str(e)
            logger.error(f"Compilation attempt {attempt} raised exception: {e}")
            if attempt < max_attempts:
                time.sleep(delay)

    logger.error(f"Compilation failed after {max_attempts} attempts. Last error: {last_error}")
    return False, last_error

def compile_test(source_dir: str, classpath: str) -> bool:
    """
    Compile test sources. Raises CompilationFailedError on failure.
    """
    success, error = retry_compile(source_dir, classpath)
    if not success:
        raise CompilationFailedError(error)
    return True

def extract_compilation_error(log_output: str) -> List[str]:
    """
    Extract specific compilation error strings from logs or JaCoCo output.
    Uses regex pattern r'(?:error:|Error:).*' to find errors.
    Returns a list of error strings.
    """
    if not log_output:
        return []
    
    # Pattern to match lines containing 'error:' or 'Error:'
    # Case insensitive for 'error' but usually Java errors start with 'error:'
    pattern = r'(?:error:|Error:).*'
    matches = re.findall(pattern, log_output, re.IGNORECASE)
    
    # Clean up and deduplicate
    unique_errors = list(set([m.strip() for m in matches if m.strip()]))
    return unique_errors

def update_csv_for_failed_test(csv_path: str, project_id: str, test_type: str, 
                               error_msg: List[str]) -> None:
    """
    Update the coverage_metrics.csv row for a failed test.
    Sets coverage_percentage to null, status to 'failed_to_compile',
    and error_msg to the extracted string from T028a.
    
    Args:
        csv_path: Path to the coverage_metrics.csv file.
        project_id: The project ID to update.
        test_type: The test type (e.g., 'llm_generated', 'manual').
        error_msg: List of error strings extracted by extract_compilation_error.
    """
    data_dir = get_data_dir()
    if not csv_path:
        csv_path = os.path.join(data_dir, "coverage_metrics.csv")
    
    # Ensure the file exists with headers if it doesn't
    fieldnames = ['project_id', 'test_type', 'coverage_percentage', 'status', 'error_msg', 'assertion_density']
    
    if not os.path.exists(csv_path):
        logger.warning(f"CSV file {csv_path} does not exist. Creating it with headers.")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
    
    # Read existing data
    rows = []
    found = False
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['project_id'] == project_id and row['test_type'] == test_type:
                # Update the existing row
                row['coverage_percentage'] = 'null'
                row['status'] = 'failed_to_compile'
                # Join list of errors into a single string, escaping newlines
                row['error_msg'] = '; '.join(error_msg).replace('\n', ' ')
                found = True
            rows.append(row)
    
    if not found:
        # If the row didn't exist, add it as a new row
        logger.info(f"Row for {project_id}/{test_type} not found. Adding new row.")
        new_row = {
            'project_id': project_id,
            'test_type': test_type,
            'coverage_percentage': 'null',
            'status': 'failed_to_compile',
            'error_msg': '; '.join(error_msg).replace('\n', ' '),
            'assertion_density': 'null'
        }
        rows.append(new_row)
    
    # Write back
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Updated CSV for failed test: {project_id} ({test_type})")

def parse_jacoco_xml(xml_path: str) -> Dict[str, Any]:
    """
    Parse JaCoCo XML report to extract line coverage.
    Returns a dict with total lines, covered lines, and coverage percentage.
    """
    import xml.etree.ElementTree as ET
    
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f"JaCoCo XML not found: {xml_path}")
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    total_lines = 0
    covered_lines = 0
    
    for counter in root.iter('counter'):
        if counter.get('type') == 'LINE':
            total_lines = int(counter.get('covered', 0)) + int(counter.get('missed', 0))
            covered_lines = int(counter.get('covered', 0))
            break
    
    if total_lines == 0:
        coverage_pct = 0.0
    else:
        coverage_pct = (covered_lines / total_lines) * 100
    
    return {
        'total_lines': total_lines,
        'covered_lines': covered_lines,
        'coverage_percentage': coverage_pct
    }

def run_with_jacoco(project_dir: str, test_class: str, target_class: str, 
                    changed_lines: List[int]) -> ExecutionResult:
    """
    Instrument target classes and execute tests, capturing line-level coverage.
    Consumes changed_lines to filter coverage metrics.
    """
    # This is a skeleton implementation for the task context.
    # In a real run, this would invoke jacoco-cli and java with specific args.
    # For the purpose of T028b, we focus on the CSV update logic which depends on this.
    
    # Placeholder logic to simulate a run result
    # In reality, this would execute the test and parse the XML
    return ExecutionResult(success=True, coverage=0.0)

def calculate_coverage_ratio(coverage_data: Dict[str, Any], changed_lines: List[int]) -> float:
    """
    Calculate coverage percentage on the specific changed lines only.
    """
    if not changed_lines:
        return 0.0
    # Logic to intersect coverage data with changed lines
    # Placeholder implementation
    return 0.0

def generate_coverage_csv(results: List[Dict[str, Any]], output_path: str = None) -> str:
    """
    Write coverage metrics to CSV.
    """
    data_dir = get_data_dir()
    if not output_path:
        output_path = os.path.join(data_dir, "coverage_metrics.csv")
    
    fieldnames = ['project_id', 'test_type', 'coverage_percentage', 'status', 'error_msg', 'assertion_density']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    return output_path

def main():
    """
    Main entry point for test executor module.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Test Executor Module Initialized")

if __name__ == "__main__":
    main()