"""
Independent Test Pipeline for User Story 1 (T010b).

Executes code/01_compute_metrics.py on a 50-function subset of the downloaded dataset.
Performs manual Radon calculations on the same subset.
Compares results and generates a validation report at tests/outputs/us1_validation_report.md.
"""
import ast
import csv
import logging
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path to import utils
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.metrics import calculate_cyclomatic_complexity, calculate_cognitive_complexity, validate_code_syntax
from radon.halstead import HalsteadMetrics
from radon.complexity import cc_visit_ast

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SUBSET_SIZE = 50
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "bigcodebench.csv"
DERIVED_METRICS_PATH = PROJECT_ROOT / "data" / "derived" / "metrics.csv"
REPORT_PATH = PROJECT_ROOT / "tests" / "outputs" / "us1_validation_report.md"
PIPELINE_SCRIPT = PROJECT_ROOT / "code" / "01_compute_metrics.py"

def load_sample_data() -> List[Dict[str, Any]]:
    """Load the raw dataset and extract a subset of 50 functions."""
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Raw data not found at {RAW_DATA_PATH}. Run 00_download_data.py first.")
    
    logger.info(f"Loading raw data from {RAW_DATA_PATH}...")
    functions = []
    with open(RAW_DATA_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= SUBSET_SIZE:
                break
            # Assume the column 'code' or 'function' contains the source code
            # Adjust column name based on actual dataset schema (usually 'code' or 'snippet')
            code = row.get('code') or row.get('function') or row.get('snippet')
            if code:
                functions.append({
                    'id': row.get('id', f'row_{i}'),
                    'code': code,
                    'row_index': i
                })
    
    if len(functions) == 0:
        raise ValueError("No valid code functions found in the raw dataset.")
    
    logger.info(f"Loaded {len(functions)} functions for validation subset.")
    return functions

def manual_calculate_metrics(code: str) -> Dict[str, Any]:
    """
    Perform manual Radon calculations to serve as ground truth.
    """
    if not validate_code_syntax(code):
        return {
            'cyclomatic': -1,
            'cognitive': -1,
            'halstead_n1': -1,
            'halstead_n2': -1,
            'halstead_N1': -1,
            'halstead_N2': -1,
            'error': 'SyntaxError'
        }

    try:
        tree = ast.parse(code)
        
        # Cyclomatic Complexity
        cc_results = cc_visit_ast(tree)
        cc_val = 0
        for r in cc_results:
            cc_val += r.complexity
        if cc_val == 0 and len(cc_results) == 0:
            cc_val = 1 # Base complexity for a function with no branches
        
        # Cognitive Complexity
        cog_val = calculate_cognitive_complexity(code)
        if cog_val is None:
            cog_val = 0

        # Halstead
        h_metrics = HalsteadMetrics(tree)
        h_val = {
            'n1': h_metrics.distinct_operators,
            'n2': h_metrics.distinct_operands,
            'N1': h_metrics.total_operators,
            'N2': h_metrics.total_operands
        }

        return {
            'cyclomatic': cc_val,
            'cognitive': cog_val,
            'halstead_n1': h_val['n1'],
            'halstead_n2': h_val['n2'],
            'halstead_N1': h_val['N1'],
            'halstead_N2': h_val['N2']
        }
    except Exception as e:
        return {
            'cyclomatic': -1,
            'cognitive': -1,
            'halstead_n1': -1,
            'halstead_n2': -1,
            'halstead_N1': -1,
            'halstead_N2': -1,
            'error': str(e)
        }

def run_pipeline_subset(functions: List[Dict[str, Any]]) -> None:
    """
    Run the main compute_metrics script with a specific subset size argument.
    This assumes 01_compute_metrics.py supports a --limit argument or similar.
    If not, we might need to patch it temporarily, but for this task we assume
    the script is designed to handle limits or we invoke it on a pre-filtered file.
    
    Strategy: We will invoke the script with a specific limit argument if supported,
    otherwise we rely on the script's internal sampling logic if it exists,
    or we assume the script processes the whole file but we only validate the first N.
    
    Given the task description "Execute ... on a 50-function subset", 
    we will try to pass --limit 50.
    """
    logger.info(f"Running pipeline script: {PIPELINE_SCRIPT} with limit={SUBSET_SIZE}")
    
    cmd = [
        sys.executable, str(PIPELINE_SCRIPT),
        "--input", str(RAW_DATA_PATH),
        "--output", str(DERIVED_METRICS_PATH),
        "--limit", str(SUBSET_SIZE)
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
        logger.info("Pipeline execution completed successfully.")
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
    except subprocess.CalledProcessError as e:
        logger.error(f"Pipeline execution failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise

def load_pipeline_results() -> Dict[str, Dict[str, Any]]:
    """Load results from the generated metrics.csv."""
    if not DERIVED_METRICS_PATH.exists():
        raise FileNotFoundError(f"Derived metrics not found at {DERIVED_METRICS_PATH}.")
    
    results = {}
    with open(DERIVED_METRICS_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize ID if necessary
            pid = row.get('id')
            if pid:
                results[pid] = {
                    'cyclomatic': float(row.get('cyclomatic_complexity', -1)),
                    'cognitive': float(row.get('cognitive_complexity', -1)),
                    'halstead_n1': float(row.get('halstead_n1', -1)),
                    'halstead_n2': float(row.get('halstead_n2', -1)),
                    'halstead_N1': float(row.get('halstead_N1', -1)),
                    'halstead_N2': float(row.get('halstead_N2', -1))
                }
    return results

def compare_results(manual: List[Dict], pipeline: Dict[str, Dict]) -> Tuple[List[str], int, int]:
    """Compare manual vs pipeline results and return discrepancies."""
    discrepancies = []
    total = 0
    passed = 0
    
    for item in manual:
        pid = item['id']
        if pid not in pipeline:
            discrepancies.append(f"ID {pid}: Missing in pipeline output.")
            continue
        
        total += 1
        m_metrics = item['metrics']
        p_metrics = pipeline[pid]
        
        match = True
        diffs = []
        
        keys = ['cyclomatic', 'cognitive', 'halstead_n1', 'halstead_n2', 'halstead_N1', 'halstead_N2']
        for key in keys:
            m_val = m_metrics.get(key)
            p_val = p_metrics.get(key)
            
            # Handle errors (-1)
            if m_val == -1 and p_val == -1:
                continue
            if m_val == -1 or p_val == -1:
                match = False
                diffs.append(f"{key}: Manual={m_val}, Pipeline={p_val}")
                continue
            
            # Allow small float tolerance
            if abs(float(m_val) - float(p_val)) > 0.01:
                match = False
                diffs.append(f"{key}: Manual={m_val}, Pipeline={p_val}")
        
        if match:
            passed += 1
        else:
            discrepancies.append(f"ID {pid}: {', '.join(diffs)}")
    
    return discrepancies, total, passed

def generate_report(discrepancies: List[str], total: int, passed: int) -> str:
    """Generate the markdown validation report."""
    status = "PASS" if len(discrepancies) == 0 else "FAIL"
    report = []
    report.append(f"# User Story 1 Validation Report (T010b)\n")
    report.append(f"**Status**: {status}\n")
    report.append(f"**Subset Size**: {SUBSET_SIZE}\n")
    report.append(f"**Total Checked**: {total}\n")
    report.append(f"**Passed**: {passed}\n")
    report.append(f"**Failed**: {total - passed}\n")
    report.append("\n## Summary\n")
    report.append(f"Manual Radon calculations were compared against the output of `code/01_compute_metrics.py`.\n")
    
    if discrepancies:
        report.append(f"## Discrepancies Found ({len(discrepancies)})\n")
        for i, disc in enumerate(discrepancies, 1):
            report.append(f"{i}. {disc}\n")
    else:
        report.append("## Discrepancies\n")
        report.append("No discrepancies found. All metrics match manual calculations.\n")
    
    report.append("---\n")
    report.append("*Generated by run_us1_validation.py*\n")
    
    return "\n".join(report)

def main():
    logger.info("Starting T010b Independent Test Pipeline...")
    
    # Ensure output directory exists
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Load Sample
        sample_data = load_sample_data()
        
        # 2. Run Pipeline
        run_pipeline_subset(sample_data)
        
        # 3. Load Pipeline Results
        pipeline_results = load_pipeline_results()
        
        # 4. Calculate Manual Metrics
        manual_results = []
        for item in sample_data:
            metrics = manual_calculate_metrics(item['code'])
            manual_results.append({
                'id': item['id'],
                'metrics': metrics
            })
        
        # 5. Compare
        discrepancies, total, passed = compare_results(manual_results, pipeline_results)
        
        # 6. Generate Report
        report_content = generate_report(discrepancies, total, passed)
        
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Validation report generated at {REPORT_PATH}")
        
        # Exit with error code if validation failed
        if discrepancies:
            logger.error("Validation FAILED. See report for details.")
            sys.exit(1)
        else:
            logger.info("Validation PASSED.")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Validation pipeline failed with exception: {e}")
        # Write a failure report
        error_report = f"# Validation Failed\n\nError: {str(e)}\n"
        with open(REPORT_PATH, 'w') as f:
            f.write(error_report)
        sys.exit(1)

if __name__ == "__main__":
    main()
