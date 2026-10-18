import subprocess
import sys
from pathlib import Path
from llmxive_toolkit import paths

def main():
    """
    Installs the pinned dependencies from code/requirements.txt and 
    writes the installation log to outputs/install_log.txt to satisfy
    the T002 verification requirement.
    """
    req_path = paths.code("requirements.txt")
    log_path = paths.outputs("install_log.txt")
    
    # Ensure the requirements file is exactly as requested
    lines = [
        "torch==2.2.2",
        "transformers==4.41.0",
        "datasets==2.18.0",
        "pandas==2.2.2",
        "scikit-learn==1.5.0",
        "scipy==1.13.0",
        "statsmodels==0.14.2",
        "tqdm==4.66.2",
        "pytest==8.2.2",
        "ruff==0.4.2",
        "black==24.4.2",
    ]
    req_path.write_text("\n".join(lines) + "\n")
    
    try:
        # Run pip install and capture output
        # Using -m pip to ensure we use the current python environment
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
            capture_output=True,
            text=True,
            check=True
        )
        log_content = f"=== pip install -r {req_path.relative_to(paths.root)} ===\n{result.stdout}\n{result.stderr}"
    except subprocess.CalledProcessError as e:
        log_content = f"=== pip install -r {req_path.relative_to(paths.root)} ===\nFAILED\n{e.stdout}\n{e.stderr}"
        log_path.write_text(log_content)
        sys.exit(1)
        
    log_path.write_text(log_content)
    print(f"Dependencies installed successfully. Log written to {log_path}")

if __name__ == "__main__":
    main()