import os
import json
import logging
import subprocess
import sys
import tempfile
import radon
from radon.complexity import cc_visit
from radon.halstead import halstead_visit
from utils import setup_logging, get_logger, set_task_id

# Ensure radon is installed
try:
    import radon
except ImportError:
    raise ImportError("radon is required for metric analysis. Install with: pip install radon")

def calculate_code_metrics(code):
    """
    Calculate Cyclomatic Complexity and Halstead Volume for a given code snippet.

    Args:
        code (str): The Python code snippet to analyze.

    Returns:
        dict: A dictionary containing cyclomatic_complexity and halstead_volume.
    """
    if not code or not code.strip():
        return {
            "cyclomatic_complexity": 0,
            "halstead_volume": 0.0,
            "halstead_operators": {},
            "halstead_operands": {}
        }

    try:
        # Calculate Cyclomatic Complexity
        cc_results = cc_visit(code)
        # Sum CC for all functions/classes in the snippet
        total_cc = sum(block.cc for block in cc_results)
        # If no functions found, default to 1 for the module itself if valid syntax
        if total_cc == 0 and cc_results:
            total_cc = 1
        elif total_cc == 0 and not cc_results:
            # Check if it's valid syntax but no functions (e.g. just a statement)
            # For safety, if it parses, give it a base CC of 1, else 0
            try:
                compile(code, '<string>', 'exec')
                total_cc = 1
            except SyntaxError:
                total_cc = 0

        # Calculate Halstead Metrics
        h_results = list(halstead_visit(code))
        if h_results:
            # Sum or take the first significant block? Usually sum for total volume
            # Radon returns a list of Halstead metrics per function/class
            total_h_volume = sum(h.volume for h in h_results)
            total_operators = {}
            total_operands = {}
            
            # Aggregate operators and operands
            for h in h_results:
                for op, count in h.operators.items():
                    total_operators[op] = total_operators.get(op, 0) + count
                for op, count in h.operands.items():
                    total_operands[op] = total_operands.get(op, 0) + count
        else:
            total_h_volume = 0.0
            total_operators = {}
            total_operands = {}

        return {
            "cyclomatic_complexity": total_cc,
            "halstead_volume": total_h_volume,
            "halstead_operators": total_operators,
            "halstead_operands": total_operands
        }

    except SyntaxError:
        # Return defaults for invalid syntax
        return {
            "cyclomatic_complexity": 0,
            "halstead_volume": 0.0,
            "halstead_operators": {},
            "halstead_operands": {}
        }
    except Exception as e:
        # Log error but return defaults to allow pipeline to continue
        logging.error(f"Error calculating metrics: {e}")
        return {
            "cyclomatic_complexity": 0,
            "halstead_volume": 0.0,
            "halstead_operators": {},
            "halstead_operands": {}
        }

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/analyze_metrics.log')
        ]
    )
    return logging.getLogger(__name__)

def log_info(logger, message):
    """Log an info message."""
    logger.info(message)

def log_error(logger, message):
    """Log an error message."""
    logger.error(message)

def ensure_dirs():
    """Ensure required directories exist."""
    os.makedirs('data/analysis', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

def load_test_suites(task_id):
    """
    Load test suite for a given task_id from HumanEval dataset.
    This is a placeholder for the actual loading logic.
    """
    # In a real implementation, this would load from data/raw/humaneval.jsonl
    # For now, we return a mock structure
    return {
        "task_id": task_id,
        "prompt": "def add(a, b):\n    return a + b",
        "canonical_solution": "def add(a, b):\n    return a + b",
        "test": "def check_add():\n    assert add(1, 2) == 3"
    }

def execute_test_suite(code, test_code):
    """
    Execute the test suite against the generated code.
    Returns True if all tests pass, False otherwise.
    """
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code + "\n" + test_code)
            temp_file = f.name

        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        os.unlink(temp_file)
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Test execution failed: {e}")
        return False

def execute_coverage_test(code, test_code):
    """
    Execute coverage test and return branch coverage percentage.
    Returns None if execution fails.
    """
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code + "\n" + test_code)
            temp_file = f.name

        result = subprocess.run(
            ['coverage', 'run', temp_file],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            os.unlink(temp_file)
            return None

        coverage_result = subprocess.run(
            ['coverage', 'report', '--format=json'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(temp_file)
        )

        os.unlink(temp_file)

        if coverage_result.returncode == 0:
            coverage_data = json.loads(coverage_result.stdout)
            # Extract branch coverage percentage
            # This is a simplified extraction; real implementation may vary
            total_branches = 0
            covered_branches = 0
            for file_data in coverage_data.get('files', {}).values():
                total_branches += file_data.get('summary', {}).get('missing_branches', 0)
                covered_branches += file_data.get('summary', {}).get('covered_branches', 0)
            
            if total_branches > 0:
                return (covered_branches / total_branches) * 100
            else:
                return 100.0  # No branches to cover
        else:
            return None
    except Exception as e:
        logging.error(f"Coverage test failed: {e}")
        return None

def analyze_batch_metrics(samples):
    """
    Analyze metrics for a batch of samples.
    
    Args:
        samples (list): List of sample dictionaries with 'task_id', 'code', 'test_code'
        
    Returns:
        list: List of metric dictionaries
    """
    results = []
    logger = setup_logging()
    
    for sample in samples:
        task_id = sample.get('task_id')
        code = sample.get('code')
        test_code = sample.get('test_code')
        
        if not code:
            log_error(logger, f"No code for task {task_id}")
            continue
        
        # Calculate code metrics
        code_metrics = calculate_code_metrics(code)
        
        # Execute tests
        pass_rate = 1.0 if execute_test_suite(code, test_code) else 0.0
        
        # Execute coverage test
        branch_coverage = execute_coverage_test(code, test_code)
        
        result = {
            "task_id": task_id,
            "source_type": sample.get('source_type', 'unknown'),
            "cyclomatic_complexity": code_metrics['cyclomatic_complexity'],
            "halstead_volume": code_metrics['halstead_volume'],
            "pass_rate": pass_rate,
            "branch_coverage_pct": branch_coverage
        }
        
        results.append(result)
        log_info(logger, f"Analyzed task {task_id}: CC={result['cyclomatic_complexity']}, "
                         f"HV={result['halstead_volume']:.2f}, "
                         f"Coverage={branch_coverage}")
    
    return results

def aggregate_metrics_to_json(results, output_path='data/analysis/metrics.json'):
    """
    Aggregate metrics and save to JSON file.
    Filters out samples with null branch_coverage_pct as per T042a requirement.
    
    Args:
        results (list): List of metric dictionaries
        output_path (str): Path to output JSON file
    """
    # T042a: Filter out samples where branch_coverage_pct is null
    filtered_results = [
        r for r in results 
        if r.get('branch_coverage_pct') is not None
    ]
    
    log_info(setup_logging(), f"Filtered {len(results) - len(filtered_results)} samples with null coverage")
    
    ensure_dirs()
    with open(output_path, 'w') as f:
        json.dump(filtered_results, f, indent=2)
    
    log_info(setup_logging(), f"Saved {len(filtered_results)} metrics to {output_path}")
    return filtered_results

def apply_pairwise_exclusion(results):
    """
    Apply pairwise exclusion logic (T042b) to ensure complete pairs.
    This function is called after filtering null coverage values.
    
    Args:
        results (list): List of metric dictionaries
        
    Returns:
        list: Filtered list with complete pairs only
    """
    # Group by task_id
    task_groups = {}
    for r in results:
        task_id = r['task_id']
        if task_id not in task_groups:
            task_groups[task_id] = []
        task_groups[task_id].append(r)
    
    # Keep only tasks with both human and LLM samples
    valid_pairs = []
    for task_id, group in task_groups.items():
        if len(group) >= 2:
            valid_pairs.extend(group)
    
    return valid_pairs

def main():
    """Main entry point for the metrics analysis pipeline."""
    logger = setup_logging()
    set_task_id('T042a')
    
    log_info(logger, "Starting metrics analysis pipeline")
    
    # Example: Load samples from a file or generate them
    # In a real scenario, this would load from data/raw/
    samples = [
        {
            "task_id": "HumanEval/0",
            "source_type": "human",
            "code": "def add(a, b):\n    return a + b",
            "test_code": "assert add(1, 2) == 3"
        },
        {
            "task_id": "HumanEval/0",
            "source_type": "llm",
            "code": "def add(a, b):\n    return a + b",
            "test_code": "assert add(1, 2) == 3"
        }
    ]
    
    # Analyze metrics
    results = analyze_batch_metrics(samples)
    
    # Filter out null coverage (T042a)
    filtered_results = [r for r in results if r.get('branch_coverage_pct') is not None]
    
    # Apply pairwise exclusion (T042b)
    final_results = apply_pairwise_exclusion(filtered_results)
    
    # Save to JSON
    output_path = 'data/analysis/metrics.json'
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    log_info(logger, f"Pipeline complete. Saved {len(final_results)} results to {output_path}")
    return final_results

if __name__ == "__main__":
    main()
