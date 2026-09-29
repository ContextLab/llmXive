import os
import sys
import subprocess
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / '.git').exists() or (current / 'tasks.md').exists():
            return current
        current = current.parent
    return current.parent

def run_command(cmd: list, description: str, timeout: int = 3600) -> Dict[str, Any]:
    """Run a shell command and capture output."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=get_project_root()
        )
        duration = time.time() - start_time
        
        return {
            "command": ' '.join(cmd),
            "description": description,
            "returncode": result.returncode,
            "stdout": result.stdout[:2000] if result.stdout else "",
            "stderr": result.stderr[:2000] if result.stderr else "",
            "duration_seconds": duration,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        logger.error(f"Command timed out after {duration}s: {description}")
        return {
            "command": ' '.join(cmd),
            "description": description,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Timeout expired after {timeout} seconds",
            "duration_seconds": duration,
            "success": False
        }
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Command failed: {description} - {str(e)}")
        return {
            "command": ' '.join(cmd),
            "description": description,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "duration_seconds": duration,
            "success": False
        }

def validate_quickstart() -> Dict[str, Any]:
    """
    Validate quickstart.md reproducibility on free tier.
    
    This script simulates the quickstart process by:
    1. Verifying required directories exist
    2. Checking if dependencies can be imported
    3. Running key pipeline stages with small samples
    4. Validating output files are created
    """
    project_root = get_project_root()
    results = {
        "validation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "project_root": str(project_root),
        "steps": [],
        "summary": {
            "total_steps": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0
        }
    }
    
    # Step 1: Verify directory structure
    logger.info("Step 1: Verifying directory structure")
    required_dirs = [
        "code", "tests", "data", "code/lib", "code/data", 
        "code/models", "code/evaluation", "data/results", 
        "data/logs", "data/intermediate", "data/config"
    ]
    
    dir_check = {
        "step": "Directory Structure Verification",
        "checks": [],
        "success": True
    }
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        exists = dir_path.exists() and dir_path.is_dir()
        dir_check["checks"].append({
            "path": dir_name,
            "exists": exists
        })
        if not exists:
            dir_check["success"] = False
            logger.warning(f"Missing directory: {dir_name}")
    
    results["steps"].append(dir_check)
    results["summary"]["total_steps"] += 1
    if dir_check["success"]:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1
    
    # Step 2: Verify dependencies
    logger.info("Step 2: Verifying dependencies")
    deps_to_check = [
        "transformers", "torch", "datasets", "scikit-learn", 
        "spacy", "kenlm", "numpy", "pandas", "llama-cpp-python"
    ]
    
    deps_check = {
        "step": "Dependency Verification",
        "checks": [],
        "success": True
    }
    
    for dep in deps_to_check:
        try:
            __import__(dep)
            deps_check["checks"].append({
                "package": dep,
                "importable": True
            })
            logger.info(f"Dependency {dep} is available")
        except ImportError as e:
            deps_check["checks"].append({
                "package": dep,
                "importable": False,
                "error": str(e)
            })
            deps_check["success"] = False
            logger.warning(f"Dependency {dep} is missing: {e}")
    
    results["steps"].append(deps_check)
    results["summary"]["total_steps"] += 1
    if deps_check["success"]:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1
    
    # Step 3: Run data download with streaming (small sample)
    logger.info("Step 3: Testing data download with streaming")
    download_result = run_command(
        [sys.executable, "-m", "code.data.download", "--sample-size", "5", "--streaming"],
        "Data download with streaming (5 documents)"
    )
    results["steps"].append(download_result)
    results["summary"]["total_steps"] += 1
    if download_result["success"]:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1
    
    # Step 4: Run feature extraction on sample
    logger.info("Step 4: Testing feature extraction on sample")
    feature_result = run_command(
        [sys.executable, "-m", "code.data.compute_features", "--sample-size", "5"],
        "Feature extraction on sample"
    )
    results["steps"].append(feature_result)
    results["summary"]["total_steps"] += 1
    if feature_result["success"]:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1
    
    # Step 5: Verify output files
    logger.info("Step 5: Verifying output files")
    expected_outputs = [
        "data/intermediate/rtpurbo_labels.parquet",
        "data/intermediate/attention_maps.h5",
        "data/intermediate/merged_dataset.csv",
        "data/logs/anomalies.csv"
    ]
    
    output_check = {
        "step": "Output File Verification",
        "checks": [],
        "success": True
    }
    
    for output_file in expected_outputs:
        file_path = project_root / output_file
        exists = file_path.exists()
        output_check["checks"].append({
            "file": output_file,
            "exists": exists
        })
        if not exists:
            output_check["success"] = False
            logger.warning(f"Missing output file: {output_file}")
    
    results["steps"].append(output_check)
    results["summary"]["total_steps"] += 1
    if output_check["success"]:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1
    
    # Step 6: Run unit tests
    logger.info("Step 6: Running unit tests")
    test_result = run_command(
        [sys.executable, "-m", "pytest", "code/tests/unit", "-v", "--tb=short"],
        "Unit tests"
    )
    results["steps"].append(test_result)
    results["summary"]["total_steps"] += 1
    if test_result["success"]:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1
    
    # Step 7: Memory usage check
    logger.info("Step 7: Memory usage validation")
    memory_result = run_command(
        [sys.executable, "-m", "pytest", "code/tests/unit/test_data_loader.py::test_peak_memory", "-v"],
        "Memory usage test"
    )
    results["steps"].append(memory_result)
    results["summary"]["total_steps"] += 1
    if memory_result["success"]:
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1
    
    # Generate summary report
    success_rate = (results["summary"]["passed"] / results["summary"]["total_steps"]) * 100
    results["summary"]["success_rate"] = f"{success_rate:.1f}%"
    results["summary"]["overall_status"] = "PASSED" if results["summary"]["failed"] == 0 else "FAILED"
    
    logger.info(f"Validation complete: {results['summary']['overall_status']}")
    logger.info(f"Success rate: {results['summary']['success_rate']}")
    
    return results

def main():
    """Main entry point for quickstart validation."""
    logger.info("Starting quickstart.md validation")
    
    try:
        results = validate_quickstart()
        
        # Save results to JSON
        output_path = get_project_root() / "data" / "results" / "quickstart_validation_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Validation report saved to: {output_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("QUICKSTART VALIDATION SUMMARY")
        print("="*60)
        print(f"Project Root: {results['project_root']}")
        print(f"Validation Time: {results['validation_time']}")
        print(f"Total Steps: {results['summary']['total_steps']}")
        print(f"Passed: {results['summary']['passed']}")
        print(f"Failed: {results['summary']['failed']}")
        print(f"Success Rate: {results['summary']['success_rate']}")
        print(f"Overall Status: {results['summary']['overall_status']}")
        print("="*60)
        
        # Exit with appropriate code
        sys.exit(0 if results['summary']['failed'] == 0 else 1)
        
    except Exception as e:
        logger.error(f"Validation failed with exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()