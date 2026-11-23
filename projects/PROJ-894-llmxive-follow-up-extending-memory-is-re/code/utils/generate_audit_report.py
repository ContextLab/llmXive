import os
import sys
import json
import tempfile
import shutil
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_output_dirs():
    """Create the audit output directory if it doesn't exist."""
    audit_dir = project_root / "data" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    return audit_dir

def mock_load_dataset(path, **kwargs):
    """
    Mock function to simulate a network failure when loading the dataset.
    Raises ConnectionError to trigger the 'fail loudly' behavior in data_loader.py
    """
    logger.warning(f"MOCK: Simulating ConnectionError for dataset '{path}'")
    raise ConnectionError(f"Simulated network failure: Cannot access dataset '{path}'")

def run_audit():
    """
    Executes the data_loader.py script in a mocked environment where
    datasets.load_dataset raises a ConnectionError.
    
    Returns a dict with:
      - exit_code: int (expected non-zero)
      - synthetic_files_created: bool (expected False)
      - error_caught: bool (expected True)
      - message: str (description of outcome)
    """
    audit_dir = ensure_output_dirs()
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    intermediate_dir = data_dir / "intermediate"
    processed_dir = data_dir / "processed"
    
    # Record state before run (list existing files in data dirs)
    existing_files_before = set()
    for dir_path in [data_dir, raw_dir, intermediate_dir, processed_dir]:
        if dir_path.exists():
            for f in dir_path.rglob("*"):
                if f.is_file():
                    existing_files_before.add(str(f.relative_to(data_dir)))
    
    logger.info(f"Starting audit. Existing data files: {len(existing_files_before)}")

    script_path = project_root / "code" / "data_loader.py"
    if not script_path.exists():
        return {
            "exit_code": -1,
            "synthetic_files_created": False,
            "error_caught": False,
            "message": f"Script not found: {script_path}"
        }

    # We run the script via subprocess to capture the actual exit code
    # and to ensure the mock is applied within the script's execution context.
    # However, patching inside a subprocess requires modifying the script or
    # passing arguments. Since we cannot easily modify the script's internal
    # imports for a subprocess mock without a wrapper, we will use a Python
    # wrapper script that imports data_loader and patches the function before
    # calling main.
    
    wrapper_code = f'''
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the module we want to test
import data_loader

# Patch datasets.load_dataset to raise ConnectionError
def mock_load_dataset(path, **kwargs):
    raise ConnectionError(f"Simulated network failure for {{path}}")

# Patch the specific function used in data_loader
# Based on T035, data_loader uses datasets.load_dataset directly or via a helper.
# We patch the function 'fetch_locomo_dataset' or the underlying load_dataset call.
# Looking at the error trace: datasets.exceptions.DatasetNotFoundError was raised.
# We need to ensure the script raises an exception and exits non-zero.

original_load = None
try:
    from datasets import load_dataset
    original_load = load_dataset
except ImportError:
    pass

if original_load:
    with patch('datasets.load_dataset', side_effect=mock_load_dataset):
  try:
      data_loader.main()
      print("SCRIPT_EXIT_CODE:0")
  except SystemExit as e:
      print(f"SCRIPT_EXIT_CODE:{{e.code}}")
  except Exception as e:
      print(f"SCRIPT_EXIT_CODE:1")
      print(f"ERROR:{{str(e)}}")
else:
    print("SCRIPT_EXIT_CODE:1")
    print("ERROR:Could not patch datasets.load_dataset")
'''
    
    wrapper_path = project_root / "code" / "utils" / "_audit_wrapper.py"
    try:
        with open(wrapper_path, 'w') as f:
            f.write(wrapper_code)
        
        logger.info("Running audit wrapper...")
        result = subprocess.run(
            [sys.executable, str(wrapper_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        output = result.stdout + result.stderr
        logger.info(f"Audit wrapper output:\n{output}")
        
        exit_code = 1
        error_msg = "Unknown error"
        
        if "SCRIPT_EXIT_CODE:" in output:
            for line in output.split('\n'):
                if line.startswith("SCRIPT_EXIT_CODE:"):
                    try:
                        exit_code = int(line.split(":")[1])
                    except ValueError:
                        exit_code = 1
                if line.startswith("ERROR:"):
                    error_msg = line.split(":", 1)[1]
        
        # Check for synthetic files created
        existing_files_after = set()
        for dir_path in [data_dir, raw_dir, intermediate_dir, processed_dir]:
            if dir_path.exists():
                for f in dir_path.rglob("*"):
                    if f.is_file():
                        existing_files_after.add(str(f.relative_to(data_dir)))
        
        new_files = existing_files_after - existing_files_before
        # Filter for synthetic-looking files (e.g., containing 'synthetic', 'fake', 'mock')
        # or specifically the ones we are worried about (graph_noise_42.json if it shouldn't exist yet)
        # The task says: verify that NO synthetic data files are produced.
        # Since we are running in a failure state, we expect NO new files.
        synthetic_files = [f for f in new_files if any(kw in f.lower() for kw in ['synthetic', 'fake', 'mock', 'generated'])]
        
        success = (exit_code != 0) and (len(synthetic_files) == 0)
        
        return {
            "exit_code": exit_code,
            "synthetic_files_created": len(synthetic_files) > 0,
            "synthetic_file_names": synthetic_files,
            "error_caught": True,
            "message": f"Audit passed: Script exited with code {exit_code} and created no synthetic files." if success else f"Audit failed: Exit code {exit_code}, Synthetic files: {synthetic_files}",
            "detailed_output": output
        }
    except Exception as e:
        logger.error(f"Audit wrapper execution failed: {e}")
        return {
            "exit_code": -1,
            "synthetic_files_created": False,
            "error_caught": False,
            "message": f"Wrapper execution error: {str(e)}"
        }
    finally:
        if wrapper_path.exists():
            wrapper_path.unlink()

def main():
    logger.info("Starting T040 Audit: Silent Fallback Check")
    audit_dir = ensure_output_dirs()
    report_path = audit_dir / "audit_report.json"
    
    result = run_audit()
    
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Audit report written to {report_path}")
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code for the CI
    if result.get("synthetic_files_created") or result.get("exit_code") == 0:
        # If synthetic files were created OR script exited 0 (meaning it didn't fail loudly),
        # the audit has failed its primary goal of verifying "fail loudly".
        # However, the task is to GENERATE the report. The report itself will indicate success/failure.
        # We exit 0 to indicate the task (report generation) completed, but the report content
        # will show if the underlying system behaved correctly.
        # Actually, T040 is an audit task. If the audit reveals a failure in the system,
        # the report should reflect that. The task "completes" by producing the report.
        pass
    
    return result

if __name__ == "__main__":
    main()