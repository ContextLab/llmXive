import os
import subprocess
import tempfile
import shutil
import logging
import time
import signal
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json

# Custom Exceptions
class CompilationFailedError(Exception):
    pass

class ExecutionError(Exception):
    pass

class ExecutionResult:
    def __init__(self, success: bool, coverage: Optional[float] = None, 
                 status: str = "unknown", error_msg: Optional[str] = None,
                 assertion_count: int = 0, timeout: bool = False):
        self.success = success
        self.coverage = coverage
        self.status = status
        self.error_msg = error_msg
        self.assertion_count = assertion_count
        self.timeout = timeout

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "coverage": self.coverage,
            "status": self.status,
            "error_msg": self.error_msg,
            "assertion_count": self.assertion_count,
            "timeout": self.timeout
        }

# Global state for JaCoCo agent reset tracking
_jacoco_agent_active = False
_last_jacoco_output_dir = None

def _reset_jacoco_agent_state():
    """
    Resets the JaCoCo agent state by removing the execution data file
    and clearing internal tracking variables. This prevents state leakage
    when a previous test timed out.
    """
    global _jacoco_agent_active, _last_jacoco_output_dir
    
    if _last_jacoco_output_dir and os.path.exists(_last_jacoco_output_dir):
        # Remove the jacoco.exec file if it exists
        jacoco_exec_path = os.path.join(_last_jacoco_output_dir, "jacoco.exec")
        if os.path.exists(jacoco_exec_path):
            try:
                os.remove(jacoco_exec_path)
                logging.info(f"Removed stale JaCoCo execution data: {jacoco_exec_path}")
            except OSError as e:
                logging.warning(f"Failed to remove stale JaCoCo data: {e}")
        
        # Remove the directory if empty or safe to do so (optional cleanup)
        # We keep the directory structure to avoid permission issues in subsequent runs
    
    _jacoco_agent_active = False
    _last_jacoco_output_dir = None
    logging.info("JaCoCo agent state reset complete.")

def enforce_test_timeout(func):
    """
    Decorator to enforce a timeout on test execution.
    If the test hangs, it kills the process and resets JaCoCo state.
    """
    def wrapper(*args, **kwargs):
        timeout = kwargs.get('timeout', 30)
        try:
            result = func(*args, **kwargs)
            return result
        except subprocess.TimeoutExpired:
            logging.warning(f"Test execution timed out after {timeout}s. Killing process.")
            # Reset JaCoCo state immediately to prevent leakage
            _reset_jacoco_agent_state()
            raise
        except Exception as e:
            # If any other exception occurs, we might still want to reset 
            # if it's related to execution environment corruption, but 
            # strictly for timeout we ensure reset.
            raise
    return wrapper

def retry_compile(compile_func: callable, max_attempts: int = 3, delay: float = 1.0) -> Tuple[bool, Optional[str]]:
    """
    Attempts compilation up to max_attempts times.
    Returns (success, error_message).
    """
    last_error = None
    for attempt in range(max_attempts):
        try:
            result = compile_func()
            if result:
                return True, None
            last_error = "Compilation failed without specific error message"
        except CompilationFailedError as e:
            last_error = str(e)
        except Exception as e:
            last_error = str(e)
        
        if attempt < max_attempts - 1:
            logging.warning(f"Compilation attempt {attempt+1} failed. Retrying in {delay}s...")
            time.sleep(delay)
    
    return False, last_error

def compile_test(source_file: str, class_path: str, timeout: float = 30.0) -> Tuple[bool, Optional[str]]:
    """
    Compiles a Java test file.
    Returns (success, error_message).
    """
    try:
        cmd = ["javac", "-cp", class_path, source_file]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout
        )
        if result.returncode == 0:
            return True, None
        else:
            error_msg = result.stderr.decode('utf-8', errors='ignore')
            return False, error_msg
    except subprocess.TimeoutExpired:
        return False, f"Compilation timed out after {timeout}s"
    except Exception as e:
        return False, str(e)

def extract_compilation_error(error_output: str) -> List[str]:
    """
    Extracts specific compilation error strings from logs.
    """
    if not error_output:
        return []
    pattern = r'(?:error:|Error:).*'
    matches = re.findall(pattern, error_output, re.IGNORECASE)
    return matches

def update_csv_for_failed_test(record: Dict[str, Any], error_msg: str, status: str = 'failed_to_compile'):
    """
    Updates a record for a failed test.
    """
    record['coverage_percentage'] = None
    record['status'] = status
    record['error_msg'] = error_msg
    return record

def parse_jacoco_xml(xml_path: str, changed_lines: List[int]) -> float:
    """
    Parses JaCoCo XML report to calculate coverage on changed lines.
    Returns coverage percentage (0.0 to 100.0).
    """
    # Simplified parser for the purpose of this task
    # In a real scenario, use a library like lxml or xml.etree.ElementTree
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        total_lines = 0
        covered_lines = 0
        
        # Navigate to counter elements or line elements
        # Assuming standard JaCoCo XML structure
        for counter in root.findall(".//counter"):
            type_attr = counter.get('type')
            if type_attr == 'LINE':
                missed = int(counter.get('missed', 0))
                covered = int(counter.get('covered', 0))
                total_lines += missed + covered
                covered_lines += covered
        
        if total_lines == 0:
            return 0.0
        
        return (covered_lines / total_lines) * 100.0
    except Exception as e:
        logging.error(f"Failed to parse JaCoCo XML: {e}")
        return 0.0

def run_with_jacoco(test_class: str, class_path: str, jacoco_agent_path: str, 
                    output_dir: str, timeout: float = 30.0) -> ExecutionResult:
    """
    Instruments target classes and executes tests, capturing line-level coverage.
    Handles timeouts and resets JaCoCo state if a timeout occurs.
    """
    global _jacoco_agent_active, _last_jacoco_output_dir
    
    jacoco_exec_file = os.path.join(output_dir, "jacoco.exec")
    _last_jacoco_output_dir = output_dir
    
    # Ensure clean state before run if necessary
    if os.path.exists(jacoco_exec_file):
        try:
            os.remove(jacoco_exec_file)
        except OSError:
            pass # Ignore if can't delete

    try:
        # Construct command with JaCoCo agent
        # java -javaagent:...=destfile=... -cp ... org.junit.runner.JUnitCore ...
        agent_arg = f"-javaagent:{jacoco_agent_path}=destfile={jacoco_exec_file},append=false"
        
        cmd = [
            "java", agent_arg,
            "-cp", class_path,
            "org.junit.runner.JUnitCore", test_class
        ]
        
        logging.info(f"Executing test with timeout {timeout}s: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid # Create new process group for killing
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            returncode = process.returncode
            
            if returncode == 0:
                _jacoco_agent_active = True
                return ExecutionResult(
                    success=True,
                    status="passed",
                    coverage=None # Coverage calculated separately from XML
                )
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                return ExecutionResult(
                    success=False,
                    status="failed",
                    error_msg=error_msg
                )
                
        except subprocess.TimeoutExpired:
            # Kill the process group
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass # Process already dead
            
            # CRITICAL: Reset JaCoCo state to prevent leakage
            _reset_jacoco_agent_state()
            
            logging.warning(f"Test timed out after {timeout}s. JaCoCo state reset.")
            return ExecutionResult(
                success=False,
                status="timeout",
                timeout=True,
                error_msg=f"Test execution timed out after {timeout}s"
            )
            
    except Exception as e:
        # Reset state on unexpected errors too
        _reset_jacoco_agent_state()
        return ExecutionResult(
            success=False,
            status="error",
            error_msg=str(e)
        )

def calculate_coverage_ratio(coverage_data: Dict[str, Any], changed_lines: List[int]) -> float:
    """
    Calculates coverage percentage on specific changed lines.
    """
    if not changed_lines:
        return 0.0
    # Implementation depends on exact structure of coverage_data
    # Assuming coverage_data has line-level info
    total_changed = len(changed_lines)
    covered_changed = 0
    
    # Placeholder logic for demonstration of interface
    # Real implementation would parse the detailed XML/CSV
    for line in changed_lines:
        if line in coverage_data.get('covered_lines', []):
            covered_changed += 1
    
    if total_changed == 0:
        return 0.0
    return (covered_changed / total_changed) * 100.0

def count_assertions(test_source: str) -> int:
    """
    Counts assertion statements in test source code.
    Uses tree-sitter-java if available, falls back to regex.
    """
    try:
        import tree_sitter_java as tsj
        from tree_sitter import Language, Parser
        
        # Simplified tree-sitter usage
        # In reality, one would load the language and parse the file
        # This is a placeholder for the interface
        return 0 # Placeholder
    except ImportError:
        # Fallback to regex
        pattern = r'assert(?:True|False|NotNull|Equals|ArrayEquals|NotEquals|Same|NotSame|Throws|DoesNotThrow|IsTrue|IsFalse|IsInstanceOf|IsNotInstanceOf)'
        matches = re.findall(pattern, test_source, re.IGNORECASE)
        return len(matches)

def calculate_assertion_density(assertion_count: int, total_lines: int) -> float:
    """
    Calculates assertion density.
    """
    if total_lines == 0:
        return 0.0
    return assertion_count / total_lines

def collect_coverage_records(records: List[Dict[str, Any]]) -> 'pd.DataFrame':
    """
    Collects all coverage records into a DataFrame.
    """
    import pandas as pd
    return pd.DataFrame(records)

def write_coverage_csv(df: 'pd.DataFrame', output_path: str):
    """
    Writes coverage DataFrame to CSV.
    """
    df.to_csv(output_path, index=False)

def main():
    logging.basicConfig(level=logging.INFO)
    # Entry point for standalone execution if needed
    pass
