"""
Quickstart Validation Script for PROJ-354-investigating-the-correlation-between-gu

This script executes the steps outlined in quickstart.md to verify the end-to-end
reproducibility of the gut microbiome-cognitive correlation study pipeline.

It validates:
1. Project structure existence
2. Data download step (simulated or real depending on availability)
3. Preprocessing pipeline execution
4. Statistical analysis execution
5. Visualization generation
6. Final output verification
"""

import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/validation/quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)

def check_structure() -> Tuple[bool, str]:
    """Verify that the required project directory structure exists."""
    logger.info("Checking project structure...")
    
    required_dirs = [
        'code',
        'data/raw',
        'data/processed',
        'data/interim',
        'results/associations',
        'results/plots',
        'results/sensitivity',
        'results/power',
        'results/validation',
        'tests'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        return False, f"Missing directories: {', '.join(missing_dirs)}"
    
    logger.info("Project structure validated successfully.")
    return True, "All required directories exist."

def run_download() -> Tuple[bool, str]:
    """Execute the data download step."""
    logger.info("Executing data download step...")
    
    try:
        # Run the download script
        result = subprocess.run(
            [sys.executable, 'code/download.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = f"Download failed: {result.stderr}"
            logger.error(error_msg)
            return False, error_msg
        
        # Verify output files exist
        expected_outputs = [
            'data/raw/microbiome_raw.parquet',
            'data/raw/cognitive_raw.parquet'
        ]
        
        missing_files = [f for f in expected_outputs if not Path(f).exists()]
        if missing_files:
            return False, f"Missing download outputs: {', '.join(missing_files)}"
        
        logger.info("Data download completed successfully.")
        return True, "Data downloaded and saved."
        
    except subprocess.TimeoutExpired:
        return False, "Download step timed out."
    except Exception as e:
        return False, f"Download step failed with exception: {str(e)}"

def run_preprocess() -> Tuple[bool, str]:
    """Execute the preprocessing pipeline."""
    logger.info("Executing preprocessing pipeline...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'code/preprocess.py'],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = f"Preprocessing failed: {result.stderr}"
            logger.error(error_msg)
            return False, error_msg
        
        # Verify output files exist
        expected_outputs = [
            'data/processed/filtered_cohort.parquet',
            'data/processed/zero_replaced_counts.parquet',
            'data/processed/ilr_coordinates.parquet',
            'data/processed/cohort_retention_log.json'
        ]
        
        missing_files = [f for f in expected_outputs if not Path(f).exists()]
        if missing_files:
            return False, f"Missing preprocessing outputs: {', '.join(missing_files)}"
        
        logger.info("Preprocessing completed successfully.")
        return True, "Preprocessing pipeline executed successfully."
        
    except subprocess.TimeoutExpired:
        return False, "Preprocessing step timed out."
    except Exception as e:
        return False, f"Preprocessing step failed with exception: {str(e)}"

def run_analysis() -> Tuple[bool, str]:
    """Execute the statistical analysis."""
    logger.info("Executing statistical analysis...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'code/analysis.py'],
            capture_output=True,
            text=True,
            timeout=900  # 15 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = f"Analysis failed: {result.stderr}"
            logger.error(error_msg)
            return False, error_msg
        
        # Verify output files exist
        expected_outputs = [
            'results/associations/main_effects.parquet',
            'results/associations/main_effects_lasso.parquet',
            'results/associations/interaction_effects.parquet',
            'results/associations/interaction_effects_bh.parquet'
        ]
        
        missing_files = [f for f in expected_outputs if not Path(f).exists()]
        if missing_files:
            return False, f"Missing analysis outputs: {', '.join(missing_files)}"
        
        logger.info("Statistical analysis completed successfully.")
        return True, "Statistical analysis executed successfully."
        
    except subprocess.TimeoutExpired:
        return False, "Analysis step timed out."
    except Exception as e:
        return False, f"Analysis step failed with exception: {str(e)}"

def run_visualize() -> Tuple[bool, str]:
    """Execute the visualization generation."""
    logger.info("Executing visualization generation...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'code/visualize.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = f"Visualization failed: {result.stderr}"
            logger.error(error_msg)
            return False, error_msg
        
        # Verify output files exist
        expected_outputs = [
            'results/plots/manhattan_plot.png',
            'results/sensitivity/threshold_sweep_report.json',
            'results/sensitivity/interaction_comparison_report.json'
        ]
        
        missing_files = [f for f in expected_outputs if not Path(f).exists()]
        if missing_files:
            return False, f"Missing visualization outputs: {', '.join(missing_files)}"
        
        logger.info("Visualization generation completed successfully.")
        return True, "Visualization generation executed successfully."
        
    except subprocess.TimeoutExpired:
        return False, "Visualization step timed out."
    except Exception as e:
        return False, f"Visualization step failed with exception: {str(e)}"

def verify_outputs() -> Tuple[bool, str]:
    """Verify all expected output files exist and are valid."""
    logger.info("Verifying all output files...")
    
    all_outputs = [
        # Download outputs
        'data/raw/microbiome_raw.parquet',
        'data/raw/cognitive_raw.parquet',
        # Preprocessing outputs
        'data/processed/filtered_cohort.parquet',
        'data/processed/zero_replaced_counts.parquet',
        'data/processed/ilr_coordinates.parquet',
        'data/processed/cohort_retention_log.json',
        # Analysis outputs
        'results/associations/main_effects.parquet',
        'results/associations/main_effects_lasso.parquet',
        'results/associations/interaction_effects.parquet',
        'results/associations/interaction_effects_bh.parquet',
        # Visualization outputs
        'results/plots/manhattan_plot.png',
        'results/sensitivity/threshold_sweep_report.json',
        'results/sensitivity/interaction_comparison_report.json'
    ]
    
    missing_files = []
    invalid_files = []
    
    for file_path in all_outputs:
        path = Path(file_path)
        if not path.exists():
            missing_files.append(file_path)
            continue
        
        # Check file size (should be > 0)
        if path.stat().st_size == 0:
            invalid_files.append(file_path)
    
    if missing_files:
        return False, f"Missing output files: {', '.join(missing_files)}"
    
    if invalid_files:
        return False, f"Invalid (empty) output files: {', '.join(invalid_files)}"
    
    logger.info("All output files verified successfully.")
    return True, "All output files exist and are valid."

def main() -> int:
    """Main validation function that executes the quickstart steps."""
    logger.info("Starting Quickstart Validation...")
    start_time = time.time()
    
    validation_results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'steps': {},
        'overall_status': 'failed',
        'message': ''
    }
    
    # Step 1: Check structure
    success, message = check_structure()
    validation_results['steps']['structure_check'] = {
        'status': 'passed' if success else 'failed',
        'message': message
    }
    if not success:
        validation_results['message'] = message
        validation_results['overall_status'] = 'failed'
        logger.error(f"Validation failed at structure check: {message}")
        return 1
    
    # Step 2: Run download
    success, message = run_download()
    validation_results['steps']['download'] = {
        'status': 'passed' if success else 'failed',
        'message': message
    }
    if not success:
        validation_results['message'] = message
        validation_results['overall_status'] = 'failed'
        logger.error(f"Validation failed at download: {message}")
        return 1
    
    # Step 3: Run preprocessing
    success, message = run_preprocess()
    validation_results['steps']['preprocessing'] = {
        'status': 'passed' if success else 'failed',
        'message': message
    }
    if not success:
        validation_results['message'] = message
        validation_results['overall_status'] = 'failed'
        logger.error(f"Validation failed at preprocessing: {message}")
        return 1
    
    # Step 4: Run analysis
    success, message = run_analysis()
    validation_results['steps']['analysis'] = {
        'status': 'passed' if success else 'failed',
        'message': message
    }
    if not success:
        validation_results['message'] = message
        validation_results['overall_status'] = 'failed'
        logger.error(f"Validation failed at analysis: {message}")
        return 1
    
    # Step 5: Run visualization
    success, message = run_visualize()
    validation_results['steps']['visualization'] = {
        'status': 'passed' if success else 'failed',
        'message': message
    }
    if not success:
        validation_results['message'] = message
        validation_results['overall_status'] = 'failed'
        logger.error(f"Validation failed at visualization: {message}")
        return 1
    
    # Step 6: Verify all outputs
    success, message = verify_outputs()
    validation_results['steps']['output_verification'] = {
        'status': 'passed' if success else 'failed',
        'message': message
    }
    if not success:
        validation_results['message'] = message
        validation_results['overall_status'] = 'failed'
        logger.error(f"Validation failed at output verification: {message}")
        return 1
    
    # All steps passed
    end_time = time.time()
    validation_results['overall_status'] = 'passed'
    validation_results['message'] = 'All quickstart steps completed successfully.'
    validation_results['total_duration_seconds'] = end_time - start_time
    
    # Save validation report
    output_path = Path('results/validation/quickstart_pass.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    logger.info(f"Quickstart validation completed successfully in {validation_results['total_duration_seconds']:.2f} seconds.")
    logger.info(f"Validation report saved to {output_path}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())