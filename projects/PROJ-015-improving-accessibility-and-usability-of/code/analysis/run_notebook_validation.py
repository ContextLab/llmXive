import os
import sys
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from pathlib import Path
import pandas as pd
import json
from utils.logger import get_logger

logger = get_logger(__name__)

def log_message(message: str, log_file: Path):
    with open(log_file, 'a') as f:
        f.write(f"{message}\n")
    logger.info(message)

def check_dependencies():
    """Check if required dependencies are installed."""
    required = ['pandas', 'numpy', 'scipy', 'matplotlib', 'nbformat', 'nbconvert']
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        raise ImportError(f"Missing dependencies: {', '.join(missing)}")
    logger.info("All dependencies verified.")

def preprocess_notebook(notebook_path: Path):
    """Preprocess notebook to ensure relative paths are resolved."""
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
    
    # Ensure working directory is project root for relative paths
    # Add a setup cell if not present
    setup_code = """
import os
import sys
from pathlib import Path
# Set working directory to project root for relative paths
project_root = Path(__file__).resolve().parent.parent.parent
os.chdir(project_root)
print(f"Working directory set to: {os.getcwd()}")
"""
    
    # Insert setup cell at the beginning
    nb.cells.insert(0, nbformat.v4.new_code_cell(setup_code))
    
    # Set seed in first code cell if not already set
    seed_code = """
import numpy as np
import random
np.random.seed(42)
random.seed(42)
print("Seeds set to 42")
"""
    
    # Check if first cell is code and doesn't already set seeds
    if nb.cells[0].cell_type == 'code':
        if 'seed' not in nb.cells[0].source.lower():
            nb.cells[0].source = seed_code + "\n" + nb.cells[0].source
    else:
        nb.cells.insert(1, nbformat.v4.new_code_cell(seed_code))
    
    return nb

def execute_notebook(notebook_path: Path, output_path: Path):
    """Execute the notebook and save output."""
    nb = preprocess_notebook(notebook_path)
    
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    
    try:
        ep.preprocess(nb, {'metadata': {'path': str(notebook_path.parent)}})
        
        # Save the executed notebook
        with open(output_path, 'w', encoding='utf-8') as f:
            nbformat.write(nb, f)
        
        logger.info(f"Notebook executed successfully: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Notebook execution failed: {e}")
        raise

def verify_outputs(output_dir: Path, log_file: Path):
    """Verify that all expected outputs were generated."""
    required_files = [
        'metrics_summary.csv',
        'boxplot_completion_time.png',
        'boxplot_error_count.png',
        'boxplot_sus.png',
        'report_summary.txt'
    ]
    
    missing = []
    invalid = []
    
    # Check metrics_summary.csv
    metrics_path = output_dir / 'metrics_summary.csv'
    if not metrics_path.exists():
        missing.append('metrics_summary.csv')
    else:
        try:
            df = pd.read_csv(metrics_path)
            required_cols = ['F_statistic', 'p_value', 'adjusted_p_value', 'effect_size', 'metric_name', 'interface_type']
            if not all(col in df.columns for col in required_cols):
                invalid.append('metrics_summary.csv: missing required columns')
            elif df.empty:
                invalid.append('metrics_summary.csv: empty dataframe')
            else:
                # Check for non-zero values in key columns
                if df['F_statistic'].sum() == 0:
                    invalid.append('metrics_summary.csv: F_statistic all zeros')
        except Exception as e:
            invalid.append(f'metrics_summary.csv: {str(e)}')
    
    # Check plot files
    for plot in ['boxplot_completion_time.png', 'boxplot_error_count.png', 'boxplot_sus.png']:
        plot_path = output_dir / plot
        if not plot_path.exists():
            missing.append(plot)
        elif plot_path.stat().st_size == 0:
            invalid.append(f'{plot}: empty file')
    
    # Check report file
    report_path = output_dir / 'report_summary.txt'
    if not report_path.exists():
        missing.append('report_summary.txt')
    
    # Write log
    with open(log_file, 'w') as f:
        if missing or invalid:
            f.write('FAIL\n')
            if missing:
                f.write(f"Missing files: {', '.join(missing)}\n")
            if invalid:
                f.write(f"Invalid files: {', '.join(invalid)}\n")
            logger.error(f"Validation failed. Missing: {missing}, Invalid: {invalid}")
            return False
        else:
            f.write('PASS\n')
            logger.info("Validation passed. All outputs verified.")
            return True

def main():
    """Main entry point for notebook validation."""
    project_root = Path(__file__).resolve().parent.parent.parent
    notebook_path = project_root / 'code' / 'analysis.ipynb'
    output_dir = project_root / 'data' / 'processed'
    output_notebook = output_dir / 'analysis_executed.ipynb'
    log_file = output_dir / 'notebook_execution_log.txt'
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear log file
    if log_file.exists():
        log_file.unlink()
    
    try:
        # Check dependencies
        check_dependencies()
        log_message("Dependencies check passed", log_file)
        
        # Execute notebook
        log_message("Executing notebook...", log_file)
        execute_notebook(notebook_path, output_notebook)
        log_message("Notebook execution completed", log_file)
        
        # Verify outputs
        success = verify_outputs(output_dir, log_file)
        
        if success:
            log_message("Final validation: PASS", log_file)
            print("Validation successful. All outputs generated correctly.")
            return 0
        else:
            log_message("Final validation: FAIL", log_file)
            print("Validation failed. Check notebook_execution_log.txt for details.")
            return 1
            
    except Exception as e:
        log_message(f"Error: {str(e)}", log_file)
        logger.error(f"Validation failed with error: {e}")
        with open(log_file, 'a') as f:
            f.write(f"ERROR: {str(e)}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())