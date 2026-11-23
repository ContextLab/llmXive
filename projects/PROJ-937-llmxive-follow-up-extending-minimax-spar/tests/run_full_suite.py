"""
Task T035: Run full pytest suite on CPU-only runner to verify all tests pass.

This script executes the complete test suite defined in the project,
ensuring all unit and integration tests pass on a CPU-only environment.
It sets the necessary environment variables to enforce CPU execution
and runs pytest with appropriate flags for the llmXive project.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def enforce_cpu_environment():
    """Ensure the environment is set to CPU-only for testing."""
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['PYTORCH_NO_CUDA'] = '1'
    os.environ['TORCH_USE_CUDA_DSA'] = '0'
    
    # Verify torch is using CPU
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("CUDA is available but will be ignored for tests.")
        logger.info(f"Torch device: {torch.device('cpu')}")
    except ImportError:
        logger.warning("PyTorch not found, skipping device check.")

def run_pytest_suite():
    """Run the full pytest suite on the project."""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / 'tests'
    
    if not tests_dir.exists():
        logger.error(f"Tests directory not found at {tests_dir}")
        return False
    
    # Construct pytest command
    pytest_cmd = [
        sys.executable, '-m', 'pytest',
        str(tests_dir),
        '-v',                    # Verbose output
        '--tb=short',            # Short traceback format
        '-x',                    # Stop on first failure
        '--maxfail=1',           # Stop after one failure
        '--disable-warnings',    # Reduce noise
        '--color=yes',           # Ensure colored output
    ]
    
    # Add specific test markers if needed (e.g., for slow tests)
    # pytest_cmd.extend(['-m', 'not slow'])
    
    logger.info(f"Running pytest from {project_root}")
    logger.info(f"Command: {' '.join(pytest_cmd)}")
    
    try:
        result = subprocess.run(
            pytest_cmd,
            cwd=project_root,
            capture_output=False,  # Stream output directly
            text=True,
            timeout=3600  # 1 hour timeout for full suite
        )
        
        if result.returncode == 0:
            logger.info("✅ All tests passed successfully!")
            return True
        else:
            logger.error(f"❌ Test suite failed with return code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Test suite timed out after 1 hour")
        return False
    except FileNotFoundError as e:
        logger.error(f"❌ pytest not found: {e}")
        logger.info("Install pytest: pip install pytest")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error running tests: {e}")
        return False

def main():
    """Main entry point for the test runner."""
    logger.info("Starting full pytest suite execution (T035)")
    
    # Enforce CPU environment
    enforce_cpu_environment()
    
    # Run the test suite
    success = run_pytest_suite()
    
    if success:
        logger.info("T035: Verification complete - All tests passed.")
        sys.exit(0)
    else:
        logger.error("T035: Verification failed - Some tests did not pass.")
        sys.exit(1)

if __name__ == '__main__':
    main()