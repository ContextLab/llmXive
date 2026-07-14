"""
Validation script for quickstart.md to ensure end-to-end reproducibility.
Executes the full pipeline and verifies all expected output artifacts are generated.
"""
import os
import sys
import logging
import subprocess
import time
from pathlib import Path
from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_name: str, timeout: int = 300) -> bool:
    """
    Execute a Python script with a timeout.
    
    Args:
        script_name: Name of the script in code/ directory
        timeout: Maximum execution time in seconds
        
    Returns:
        True if script completed successfully, False otherwise
    """
    script_path = Path('code') / script_name
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False
    
    logger.info(f"Executing {script_name}...")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"✓ {script_name} completed successfully in {elapsed:.2f}s")
            if result.stdout:
                logger.debug(f"stdout:\n{result.stdout}")
            return True
        else:
            logger.error(f"✗ {script_name} failed with return code {result.returncode}")
            logger.error(f"stderr:\n{result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"✗ {script_name} timed out after {timeout}s")
        return False
    except Exception as e:
        logger.error(f"✗ {script_name} raised exception: {str(e)}")
        return False

def validate_outputs() -> dict:
    """
    Validate that all expected output artifacts exist and are non-empty.
    
    Returns:
        Dictionary with validation results for each artifact
    """
    config = get_config()
    base_path = Path(config['data_path'])
    
    expected_artifacts = [
        # Raw and processed data
        base_path / 'raw' / 'survey_data.csv',
        base_path / 'processed' / 'cleaned_data.csv',
        base_path / 'processed' / 'engineered_data.csv',
        
        # Results and metrics
        Path('results') / 'model_results.yaml',
        Path('results') / 'validity_metrics.yaml',
        Path('results') / 'mediation_results.yaml',
        
        # Reports and logs
        Path('results') / 'final_report.pdf',
        Path('modeling_log.yaml'),
        Path('data') / 'metadata.yaml',
        
        # Figures
        Path('figures') / 'roc_curve.png',
        Path('figures') / 'mediation_plot.png',
    ]
    
    results = {
        'total': len(expected_artifacts),
        'passed': 0,
        'failed': 0,
        'missing': [],
        'empty': [],
        'passed_artifacts': []
    }
    
    for artifact_path in expected_artifacts:
        if artifact_path.exists():
            file_size = artifact_path.stat().st_size
            if file_size > 0:
                results['passed'] += 1
                results['passed_artifacts'].append(str(artifact_path))
                logger.info(f"✓ Found: {artifact_path} ({file_size} bytes)")
            else:
                results['failed'] += 1
                results['empty'].append(str(artifact_path))
                logger.error(f"✗ Empty file: {artifact_path}")
        else:
            results['failed'] += 1
            results['missing'].append(str(artifact_path))
            logger.error(f"✗ Missing: {artifact_path}")
    
    return results

def main():
    """
    Main validation pipeline:
    1. Execute all pipeline scripts in order
    2. Validate all expected outputs
    3. Generate validation summary
    """
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation Pipeline")
    logger.info("=" * 60)
    
    # Define pipeline scripts in execution order
    pipeline_scripts = [
        '01_download_data.py',
        '02_clean_data.py',
        '03_engineer_features.py',
        '04_model_analysis.py',
        '05_generate_report.py',
        '06_finalize_results.py'
    ]
    
    # Execute pipeline
    execution_results = {}
    all_passed = True
    
    for script in pipeline_scripts:
        success = run_script(script)
        execution_results[script] = success
        if not success:
            all_passed = False
            logger.warning(f"Pipeline broken at {script}")
            break
    
    # Validate outputs
    logger.info("-" * 60)
    logger.info("Validating output artifacts...")
    validation_results = validate_outputs()
    
    # Generate summary
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Pipeline scripts executed: {len(execution_results)}")
    logger.info(f"Successful executions: {sum(execution_results.values())}")
    logger.info(f"Failed executions: {sum(not v for v in execution_results.values())}")
    logger.info(f"Artifacts found: {validation_results['passed']}/{validation_results['total']}")
    logger.info(f"Missing artifacts: {len(validation_results['missing'])}")
    logger.info(f"Empty artifacts: {len(validation_results['empty'])}")
    
    if all_passed and validation_results['failed'] == 0:
        logger.info("✓ VALIDATION PASSED: End-to-end reproducibility confirmed")
        return 0
    else:
        logger.error("✗ VALIDATION FAILED: Reproducibility issues detected")
        if validation_results['missing']:
            logger.error(f"Missing files: {', '.join(validation_results['missing'])}")
        if validation_results['empty']:
            logger.error(f"Empty files: {', '.join(validation_results['empty'])}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
