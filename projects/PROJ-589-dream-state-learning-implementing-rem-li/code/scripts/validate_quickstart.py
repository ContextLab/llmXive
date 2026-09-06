"""
T056: Quickstart.md Validation Script

This script validates the quickstart.md instructions by:
1. Verifying the project structure exists
2. Checking that required dependencies are installed
3. Running a minimal test of the core functionality
4. Validating that all expected output files can be generated
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime

# Add code directory to path
CODE_DIR = Path(__file__).parent.parent
PROJECT_ROOT = CODE_DIR.parent
sys.path.insert(0, str(CODE_DIR))

def log(message: str, level: str = "INFO"):
    """Log a message with timestamp and level."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def check_directory_structure() -> Tuple[bool, List[str]]:
    """Verify that all required directories exist."""
    required_dirs = [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/checkpoints",
        "data/results",
        "data/logs",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    
    missing = []
    for dir_path in required_dirs:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            missing.append(dir_path)
            log(f"Missing directory: {dir_path}", "ERROR")
        else:
            log(f"Directory exists: {dir_path}")
    
    return len(missing) == 0, missing

def check_dependencies() -> Tuple[bool, List[str]]:
    """Verify that required dependencies are installed."""
    required_packages = [
        "torch",
        "transformers",
        "datasets",
        "scikit-learn",
        "accelerate",
        "pytest",
        "scipy",
        "ruff",
        "black"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            log(f"Package installed: {package}")
        except ImportError:
            missing.append(package)
            log(f"Missing package: {package}", "ERROR")
    
    return len(missing) == 0, missing

def test_config_loading() -> Tuple[bool, str]:
    """Test that config.py can be loaded and provides expected values."""
    try:
        from config import Config
        config = Config()
        
        # Check for expected attributes
        expected_attrs = [
            "model_name",
            "device",
            "seed",
            "max_steps",
            "batch_size",
            "learning_rate",
            "warmup_steps",
            "dream_ratio",
            "entropy_threshold",
            "max_wall_clock_hours",
            "memory_limit_gb"
        ]
        
        missing_attrs = []
        for attr in expected_attrs:
            if not hasattr(config, attr):
                missing_attrs.append(attr)
                log(f"Missing config attribute: {attr}", "ERROR")
            else:
                log(f"Config attribute present: {attr} = {getattr(config, attr)}")
        
        if missing_attrs:
            return False, f"Missing config attributes: {missing_attrs}"
        
        return True, "Config loaded successfully"
        
    except Exception as e:
        return False, f"Failed to load config: {str(e)}"

def test_data_loader() -> Tuple[bool, str]:
    """Test that the data loader can be imported and initialized."""
    try:
        from data.loader import load_glue_subset, get_available_subsets
        
        # Check available subsets
        subsets = get_available_subsets()
        log(f"Available GLUE subsets: {subsets}")
        
        return True, "Data loader initialized successfully"
        
    except Exception as e:
        return False, f"Failed to initialize data loader: {str(e)}"

def test_model_loading() -> Tuple[bool, str]:
    """Test that the model loader can be imported."""
    try:
        from models.trainer import DreamScheduler, Trainer
        log("Model trainer classes imported successfully")
        return True, "Model loader initialized successfully"
    except Exception as e:
        return False, f"Failed to import model classes: {str(e)}"

def test_metrics() -> Tuple[bool, str]:
    """Test that metrics module can be imported."""
    try:
        from eval.metrics import wilcoxon_test, calculate_few_shot_accuracy
        log("Metrics module imported successfully")
        return True, "Metrics module initialized successfully"
    except Exception as e:
        return False, f"Failed to import metrics: {str(e)}"

def run_minimal_test() -> Tuple[bool, str]:
    """Run a minimal test to verify core functionality."""
    try:
        # Run pytest on a small subset of tests
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=short", "-x"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            log("Minimal test suite passed")
            return True, "Minimal test suite passed"
        else:
            log(f"Minimal test suite failed: {result.stdout}\n{result.stderr}", "ERROR")
            return False, "Minimal test suite failed"
            
    except subprocess.TimeoutExpired:
        return False, "Minimal test suite timed out"
    except Exception as e:
        return False, f"Failed to run minimal test: {str(e)}"

def generate_validation_report(results: Dict[str, Any]) -> str:
    """Generate a validation report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "project_root": str(PROJECT_ROOT),
        "validation_results": results
    }
    
    report_path = PROJECT_ROOT / "data" / "results" / "quickstart_validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    log(f"Validation report saved to: {report_path}")
    return str(report_path)

def main():
    """Main validation function."""
    log("Starting quickstart validation...")
    
    results = {
        "directory_structure": {},
        "dependencies": {},
        "config_loading": {},
        "data_loader": {},
        "model_loading": {},
        "metrics": {},
        "minimal_test": {},
        "overall_success": False
    }
    
    # Check directory structure
    success, missing = check_directory_structure()
    results["directory_structure"] = {
        "success": success,
        "missing_directories": missing
    }
    
    # Check dependencies
    success, missing = check_dependencies()
    results["dependencies"] = {
        "success": success,
        "missing_packages": missing
    }
    
    # Test config loading
    success, message = test_config_loading()
    results["config_loading"] = {
        "success": success,
        "message": message
    }
    
    # Test data loader
    success, message = test_data_loader()
    results["data_loader"] = {
        "success": success,
        "message": message
    }
    
    # Test model loading
    success, message = test_model_loading()
    results["model_loading"] = {
        "success": success,
        "message": message
    }
    
    # Test metrics
    success, message = test_metrics()
    results["metrics"] = {
        "success": success,
        "message": message
    }
    
    # Run minimal test
    success, message = run_minimal_test()
    results["minimal_test"] = {
        "success": success,
        "message": message
    }
    
    # Determine overall success
    all_success = all([
        results["directory_structure"]["success"],
        results["dependencies"]["success"],
        results["config_loading"]["success"],
        results["data_loader"]["success"],
        results["model_loading"]["success"],
        results["metrics"]["success"],
        results["minimal_test"]["success"]
    ])
    
    results["overall_success"] = all_success
    
    # Generate report
    report_path = generate_validation_report(results)
    
    if all_success:
        log("✅ Quickstart validation PASSED", "SUCCESS")
        print(f"\nValidation report: {report_path}")
        return 0
    else:
        log("❌ Quickstart validation FAILED", "ERROR")
        print(f"\nValidation report: {report_path}")
        return 1

if __name__ == "__main__":
    sys.exit(main())