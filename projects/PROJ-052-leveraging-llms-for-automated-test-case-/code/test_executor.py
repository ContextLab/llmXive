import os
import subprocess
import tempfile
import shutil
import logging
import time
import xml.etree.ElementTree as ET
import re
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

from config import get_timeout_compile, get_timeout_exec, get_data_dir, get_output_dir, get_logs_dir

logger = logging.getLogger(__name__)

class CompilationFailedError(Exception):
    """Raised when test compilation fails after retries."""
    pass

class ExecutionError(Exception):
    """Raised when test execution fails."""
    pass

class ExecutionResult:
    def __init__(self, success: bool, coverage_data: Optional[Dict] = None, error_msg: Optional[str] = None):
        self.success = success
        self.coverage_data = coverage_data
        self.error_msg = error_msg

def retry_compile(compilation_func, max_retries: int = 3) -> Tuple[bool, Optional[str]]:
    """
    Attempts to compile a test file up to max_retries times with a short delay.
    Returns (success, error_message).
    """
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"Compilation attempt {attempt}/{max_retries}")
            success, error_msg = compilation_func()
            if success:
                return True, None
            last_error = error_msg
            if attempt < max_retries:
                delay = 0.5 * attempt
                logger.warning(f"Compilation failed, retrying in {delay}s... Error: {error_msg}")
                time.sleep(delay)
            else:
                logger.error(f"Compilation failed after {max_retries} attempts.")
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Compilation attempt {attempt} raised exception: {e}")
            if attempt < max_retries:
                time.sleep(0.5 * attempt)
    
    return False, last_error

def compile_test(java_file_path: str, classpath: str, timeout: Optional[int] = None) -> Tuple[bool, Optional[str]]:
    """
    Compiles a Java test file using javac.
    Returns (success, error_message).
    """
    if timeout is None:
        timeout = get_timeout_compile()
    
    try:
        # Determine output directory (same as source for simplicity, or temp)
        output_dir = os.path.dirname(java_file_path)
        if not output_dir:
            output_dir = os.getcwd()
        
        cmd = [
            'javac',
            '-d', output_dir,
            '-cp', classpath,
            java_file_path
        ]
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True
        )
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"Compilation successful in {elapsed:.2f}s")
            return True, None
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            logger.error(f"Compilation failed in {elapsed:.2f}s: {error_msg}")
            return False, error_msg

    except subprocess.TimeoutExpired:
        logger.error(f"Compilation timed out after {timeout}s")
        return False, f"Compilation timed out after {timeout}s"
    except FileNotFoundError:
        logger.error("javac not found in PATH")
        return False, "javac not found in PATH"
    except Exception as e:
        logger.error(f"Compilation error: {e}")
        return False, str(e)

def extract_compilation_error(log_output: str) -> List[str]:
    """
    Extracts specific compilation error strings from logs using regex.
    Returns a list of error strings.
    """
    pattern = r'(?:error:|Error:).*'
    matches = re.findall(pattern, log_output, re.IGNORECASE)
    return matches

def update_csv_for_failed_test(df: pd.DataFrame, project_id: str, test_type: str, error_msg: str) -> pd.DataFrame:
    """
    Updates the in-memory record for failed tests in the DataFrame.
    Sets coverage_percentage to null, status to 'failed_to_compile', and error_msg.
    For successful tests (not called here), status would be 'passed'.
    """
    # Check if record exists, if not create it
    mask = (df['project_id'] == project_id) & (df['test_type'] == test_type)
    
    if mask.any():
        df.loc[mask, 'coverage_percentage'] = None
        df.loc[mask, 'status'] = 'failed_to_compile'
        df.loc[mask, 'error_msg'] = error_msg
    else:
        new_row = pd.DataFrame([{
            'project_id': project_id,
            'test_type': test_type,
            'coverage_percentage': None,
            'status': 'failed_to_compile',
            'error_msg': error_msg,
            'assertion_density': None
        }])
        df = pd.concat([df, new_row], ignore_index=True)
    
    return df

def parse_jacoco_xml(xml_path: str) -> Dict[str, Any]:
    """
    Parses JaCoCo XML report to extract line-level coverage.
    Returns a dict mapping package.class to coverage stats.
    """
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f"JaCoCo XML not found: {xml_path}")
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    coverage_data = {}
    
    for package in root.findall('.//package'):
        pkg_name = package.get('name')
        for class_elem in package.findall('class'):
            class_name = class_elem.get('name')
            full_name = f"{pkg_name}.{class_name}" if pkg_name else class_name
            
            # Count covered and missed instructions/lines
            covered = 0
            missed = 0
            for counter in class_elem.findall('counter'):
                if counter.get('type') in ['LINE', 'INSTRUCTION']:
                    covered += int(counter.get('covered', 0))
                    missed += int(counter.get('missed', 0))
            
            total = covered + missed
            ratio = covered / total if total > 0 else 0.0
            
            coverage_data[full_name] = {
                'covered': covered,
                'missed': missed,
                'total': total,
                'ratio': ratio
            }
    
    return coverage_data

def run_with_jacoco(
    target_class_dir: str,
    test_class_dir: str,
    jacoco_agent_path: str,
    changed_lines: Dict[str, Dict[str, List[int]]],
    project_id: str,
    test_type: str,
    timeout: Optional[int] = None
) -> ExecutionResult:
    """
    Instruments target classes with JaCoCo, executes tests, and captures line-level coverage.
    Consumes changed_lines to filter coverage to specific lines.
    Produces data/jacoco_coverage.xml.
    """
    if timeout is None:
        timeout = get_timeout_exec()
    
    data_dir = get_data_dir()
    jacoco_output_xml = os.path.join(data_dir, "jacoco_coverage.xml")
    
    # Prepare JaCoCo agent arguments
    agent_args = f"-javaagent:{jacoco_agent_path}=destfile={jacoco_output_xml},includes=*"
    
    # Classpath construction
    target_cp = target_class_dir
    test_cp = test_class_dir
    full_cp = os.pathsep.join([target_cp, test_cp])
    
    # Determine test class name (simple heuristic: assume one test class per run for this task)
    # In a real scenario, we might iterate over all .class files in test_class_dir
    test_classes = [f.replace('.class', '') for f in os.listdir(test_class_dir) if f.endswith('.class')]
    if not test_classes:
        return ExecutionResult(False, error_msg="No test classes found in test directory")
    
    # Run JUnit with JaCoCo agent
    # Assuming JUnit 5 or 4 with a simple runner. Using java command directly.
    # For simplicity, we run the first test class found.
    main_test_class = test_classes[0]
    
    cmd = [
        'java',
        agent_args,
        '-cp', full_cp,
        'org.junit.runner.JUnitCore', # Or org.junit.platform.console.ConsoleLauncher for JUnit 5
        main_test_class
    ]
    
    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True
        )
        elapsed = time.time() - start_time
        
        if result.returncode != 0:
            logger.warning(f"Test execution failed (returncode {result.returncode}). Coverage might still be generated.")
            # We continue to parse coverage even if tests failed, as JaCoCo might have captured partial data
        
        logger.info(f"Test execution completed in {elapsed:.2f}s")
        
        if not os.path.exists(jacoco_output_xml):
            return ExecutionResult(False, error_msg="JaCoCo XML report not generated")
        
        coverage_raw = parse_jacoco_xml(jacoco_output_xml)
        
        # Calculate coverage on changed lines only
        coverage_ratio = calculate_coverage_ratio(coverage_raw, changed_lines, project_id)
        
        return ExecutionResult(
            success=True,
            coverage_data={'ratio': coverage_ratio, 'raw': coverage_raw},
            error_msg=None
        )

    except subprocess.TimeoutExpired:
        logger.error(f"Test execution timed out after {timeout}s")
        return ExecutionResult(False, error_msg=f"Execution timed out after {timeout}s")
    except Exception as e:
        logger.error(f"Execution error: {e}")
        return ExecutionResult(False, error_msg=str(e))

def calculate_coverage_ratio(coverage_data: Dict[str, Any], changed_lines: Dict[str, Dict[str, List[int]]], project_id: str) -> float:
    """
    Calculates coverage percentage on the specific changed lines only.
    Consumes changed_lines (project_id -> bug_id -> [lines]) and coverage_data.
    """
    if project_id not in changed_lines:
        logger.warning(f"No changed lines found for project {project_id}. Returning 0.0.")
        return 0.0
    
    bug_id = list(changed_lines[project_id].keys())[0] if changed_lines[project_id] else None
    if not bug_id:
        return 0.0
    
    target_lines = changed_lines[project_id][bug_id]
    if not target_lines:
        return 0.0
    
    covered_count = 0
    total_count = len(target_lines)
    
    # Simple mapping: assume coverage_data keys map to classes, and we need to map lines to classes.
    # In a real scenario, we'd need source-to-class mapping or line numbers in coverage XML.
    # For this optimization task, we assume the coverage_data contains line-level info if available,
    # or we approximate based on class coverage if line-level is missing in the simplified model.
    # Note: Real JaCoCo XML has line elements.
    
    # Re-parsing XML to get line-level info for specific classes if needed
    # Since parse_jacoco_xml simplified it, let's assume we need to re-read for line details or
    # assume a 1:1 mapping for the sake of this task's optimization logic demonstration.
    # A more robust implementation would parse <line> tags in XML.
    
    # For the purpose of this task (optimization), we assume the logic exists and is efficient.
    # We will simulate the logic: if class coverage ratio > 0 and class has changed lines, count them.
    # This is a simplification. The real logic requires line-by-line parsing of the XML.
    
    # Let's implement a proper line-level parser for the XML to satisfy the requirement.
    # Re-reading the XML to get line details
    data_dir = get_data_dir()
    xml_path = os.path.join(data_dir, "jacoco_coverage.xml")
    if not os.path.exists(xml_path):
        return 0.0
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # We need to map changed lines to specific classes.
    # Since changed_lines is just line numbers, we assume they belong to the classes in the project.
    # We iterate over all line elements in the XML.
    
    for package in root.findall('.//package'):
        pkg_name = package.get('name')
        for class_elem in package.findall('class'):
            class_name = class_elem.get('name')
            full_name = f"{pkg_name}.{class_name}"
            
            # Check if this class is relevant (simplified: assume all are relevant for now)
            # In reality, we'd check if the class contains the changed lines.
            
            for line_elem in class_elem.findall('line'):
                line_no = int(line_elem.get('nr', -1))
                if line_no in target_lines:
                    covered = int(line_elem.get('covered', 0))
                    missed = int(line_elem.get('missed', 0))
                    if covered > 0:
                        covered_count += 1
    
    return (covered_count / total_count) if total_count > 0 else 0.0

def count_assertions(java_code: str) -> int:
    """
    Counts assertions in generated Java code.
    Uses regex r'assert[A-Z][a-zA-Z]*|@Test'.
    """
    pattern = r'assert[A-Z][a-zA-Z]*|@Test'
    matches = re.findall(pattern, java_code)
    return len(matches)

def calculate_assertion_density(java_code: str, total_lines: int) -> float:
    """
    Calculates assertion density (assertions per line of code).
    """
    if total_lines == 0:
        return 0.0
    return count_assertions(java_code) / total_lines

def collect_coverage_records(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Aggregates all in-memory records into a single pandas DataFrame.
    """
    return pd.DataFrame(records)

def write_coverage_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Writes the aggregated DataFrame to a CSV file.
    Columns: project_id, test_type, coverage_percentage, status, assertion_density.
    """
    df.to_csv(output_path, index=False)
    logger.info(f"Coverage metrics written to {output_path}")

def main():
    """
    Main entry point for test executor optimization demonstration.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Test Executor Optimization Module Loaded.")
    # This module is intended to be imported and used by the pipeline.
    # The main function here serves as a placeholder for direct execution if needed.

if __name__ == "__main__":
    main()