"""
Audit script to identify all files matching the t0*.py pattern in the code/ directory.
This supports task T1201a: [HYGIENE] Audit code/ directory to identify all files matching t0*.py pattern.
"""
import os
import sys
from pathlib import Path
import logging

# Add parent directory to path to allow imports if needed, though this script is standalone
sys.path.insert(0, str(Path(__file__).parent.parent))

def audit_t0_scripts(code_dir: str = "code") -> list:
    """
    Scans the specified directory for files matching the pattern t0*.py.
    
    Args:
        code_dir (str): Path to the code directory.
        
    Returns:
        list: A list of filenames matching the pattern.
    """
    code_path = Path(code_dir)
    if not code_path.exists():
        logging.error(f"Directory {code_dir} does not exist.")
        return []
        
    matching_files = []
    for file_path in code_path.iterdir():
        if file_path.is_file() and file_path.name.startswith("t0") and file_path.suffix == ".py":
            matching_files.append(file_path.name)
            
    return sorted(matching_files)

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("Starting audit of t0*.py scripts in code/ directory...")
    
    # Perform the audit
    t0_scripts = audit_t0_scripts("code")
    
    if not t0_scripts:
        logger.info("No files matching 't0*.py' found in code/ directory.")
        print("Audit Result: No t0*.py scripts found.")
    else:
        logger.info(f"Found {len(t0_scripts)} file(s) matching 't0*.py':")
        print(f"Audit Result: Found {len(t0_scripts)} t0*.py script(s):")
        for script in t0_scripts:
            print(f"  - {script}")
            logger.info(f"  - {script}")
            
    return t0_scripts

if __name__ == "__main__":
    main()
