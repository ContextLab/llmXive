"""
Reproducibility Audit Script for llmXive Project.

Generates a deterministic report of all random seeds, environment variables,
and dependency hashes used in the final run to ensure exact re-runnability
(Constitution Principle I).
"""
import os
import sys
import json
import hashlib
import subprocess
import argparse
import logging
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import project-specific seed configuration to ensure we capture the actual seeds used
from seed_config import get_seed, set_seeds, init_reproducibility

# Setup logging
def setup_logging() -> logging.Logger:
    """Configure logging for the audit script."""
    logger = logging.getLogger("audit_reproducibility")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def get_dependency_hashes(requirements_path: str = "code/requirements.txt") -> Dict[str, str]:
    """
    Compute SHA256 hashes of the requirements file and extract package versions.
    """
    logger = logging.getLogger("audit_reproducibility")
    hashes = {}
    
    if not os.path.exists(requirements_path):
        logger.warning(f"Requirements file not found at {requirements_path}")
        return hashes
    
    # Hash the requirements file itself
    with open(requirements_path, 'rb') as f:
        content = f.read()
        hashes["requirements.txt"] = hashlib.sha256(content).hexdigest()
    
    # Extract package versions for detailed audit
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            packages = {}
            for line in result.stdout.strip().split('\n'):
                if '==' in line:
                    pkg, ver = line.split('==', 1)
                    packages[pkg.strip()] = ver.strip()
            hashes["pip_freeze"] = packages
    except subprocess.TimeoutExpired:
        logger.warning("pip freeze timed out")
    except Exception as e:
        logger.warning(f"Could not run pip freeze: {e}")
    
    return hashes

def get_environment_info() -> Dict[str, Any]:
    """
    Collect system environment information.
    """
    logger = logging.getLogger("audit_reproducibility")
    info = {
        "timestamp": datetime.utcnow().isoformat(),
        "platform": {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "compiler": platform.python_compiler()
        },
        "environment_variables": {}
    }
    
    # Capture relevant environment variables
    relevant_vars = [
        "PATH", "HOME", "USER", "PWD", "PYTHONPATH",
        "CUDA_VISIBLE_DEVICES", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS"
    ]
    
    for var in relevant_vars:
        value = os.environ.get(var, "NOT_SET")
        # Mask sensitive variables if needed, but for reproducibility we want them
        info["environment_variables"][var] = value
    
    # Check for CUDA availability (should be None/False for CPU-only)
    try:
        import torch
        info["torch_cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            logger.warning("CUDA is available - this violates FR-004 (CPU-only)")
        else:
            info["torch_cuda_available"] = False
    except ImportError:
        info["torch_cuda_available"] = False
    
    return info

def get_seed_configuration() -> Dict[str, Any]:
    """
    Get the current seed configuration used by the project.
    """
    logger = logging.getLogger("audit_reproducibility")
    
    try:
        seed = get_seed()
        return {
            "global_seed": seed,
            "numpy_seed": np.random.get_state()[1][0] if 'numpy' in sys.modules else "not_set",
            "random_seed": random.getrandbits(64) if 'random' in sys.modules else "not_set",
            "status": "configured"
        }
    except Exception as e:
        logger.error(f"Error retrieving seed configuration: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def generate_audit_report(output_path: str = "data/results/reproducibility_audit.json") -> Dict[str, Any]:
    """
    Generate a comprehensive reproducibility audit report.
    """
    logger = setup_logging()
    logger.info("Starting reproducibility audit...")
    
    # Initialize reproducibility to ensure we capture the actual state
    init_reproducibility()
    
    report = {
        "audit_metadata": {
            "script": "audit_reproducibility.py",
            "task_id": "T039",
            "project_id": "PROJ-860-llmxive-follow-up-extending-dragmesh-2-p",
            "generated_at": datetime.utcnow().isoformat()
        },
        "environment": get_environment_info(),
        "seeds": get_seed_configuration(),
        "dependencies": get_dependency_hashes()
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write report to file
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Reproducibility audit report written to {output_path}")
    return report

def main():
    """Main entry point for the audit script."""
    parser = argparse.ArgumentParser(
        description="Generate a reproducibility audit report for the llmXive project."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/reproducibility_audit.json",
        help="Path to output the audit report JSON file."
    )
    parser.add_argument(
        "--requirements",
        type=str,
        default="code/requirements.txt",
        help="Path to the requirements.txt file."
    )
    
    args = parser.parse_args()
    
    try:
        report = generate_audit_report(args.output)
        
        # Validate critical reproducibility constraints
        if report["seeds"]["status"] != "configured":
            print("ERROR: Seed configuration not properly set. Reproducibility compromised.")
            sys.exit(1)
        
        if report["environment"]["torch_cuda_available"]:
            print("ERROR: CUDA is available. This violates FR-004 (CPU-only requirement).")
            sys.exit(1)
        
        print(f"SUCCESS: Reproducibility audit passed. Report saved to {args.output}")
        sys.exit(0)
        
    except Exception as e:
        print(f"ERROR: Reproducibility audit failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
