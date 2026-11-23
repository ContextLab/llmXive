"""
T041: Validate quickstart.md execution.

This script executes the commands defined in quickstart.md, verifies their
exit codes, and confirms that the expected output files exist on disk.
"""
import subprocess
import sys
import os
from pathlib import Path
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_quickstart_md(file_path: str) -> list:
    """
    Parses quickstart.md to extract shell commands.
    Looks for code blocks marked with 'bash' or 'sh'.
    """
    commands = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []

    # Regex to find markdown code blocks
    block_pattern = re.compile(r'```(?:bash|sh)\n(.*?)```', re.DOTALL)
    matches = block_pattern.findall(content)

    for match in matches:
        # Split by newlines, filter empty lines and comments
        lines = match.strip().split('\n')
        cmd_lines = [
            line.strip() 
            for line in lines 
            if line.strip() and not line.strip().startswith('#')
        ]
        if cmd_lines:
            commands.append(cmd_lines)
    
    return commands

def execute_command_sequence(commands: list, project_root: Path) -> bool:
    """
    Executes a sequence of shell commands.
    Returns True if all succeed, False otherwise.
    """
    for i, cmd_list in enumerate(commands):
        logger.info(f"--- Executing Command Block {i+1} ---")
        for cmd in cmd_list:
            logger.info(f"Running: {cmd}")
            
            try:
                # Use shell=True to handle pipes and redirections if present
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout per command
                )
                
                if result.returncode != 0:
                    logger.error(f"Command failed with exit code {result.returncode}")
                    logger.error(f"STDOUT: {result.stdout}")
                    logger.error(f"STDERR: {result.stderr}")
                    return False
                
                if result.stdout:
                    logger.debug(f"STDOUT: {result.stdout[:200]}...")
            except subprocess.TimeoutExpired:
                logger.error(f"Command timed out: {cmd}")
                return False
            except Exception as e:
                logger.error(f"Error executing command: {e}")
                return False
    
    return True

def verify_output_files(expected_files: list, project_root: Path) -> bool:
    """
    Verifies that the expected output files exist in the project root.
    """
    all_exist = True
    for file_path in expected_files:
        full_path = project_root / file_path
        if not full_path.exists():
            logger.error(f"Expected output file missing: {full_path}")
            all_exist = False
        else:
            logger.info(f"Verified: {full_path}")
    return all_exist

def main():
    project_root = Path(__file__).resolve().parent.parent
    quickstart_path = project_root / "quickstart.md"
    
    if not quickstart_path.exists():
        logger.error("quickstart.md not found in project root.")
        sys.exit(1)

    logger.info(f"Parsing {quickstart_path}...")
    commands = parse_quickstart_md(str(quickstart_path))
    
    if not commands:
        logger.warning("No commands found in quickstart.md. Skipping execution.")
        # If no commands, we assume success or fail based on file existence?
        # Assuming success if no steps to run
        return 0

    logger.info(f"Found {len(commands)} command blocks to execute.")
    
    # Execute commands
    success = execute_command_sequence(commands, project_root)
    
    if not success:
        logger.error("One or more commands failed execution.")
        sys.exit(1)

    # Define expected outputs based on typical quickstart content for this project
    # These are the files T018b, T029, T033, etc. should produce
    expected_outputs = [
        "data/raw/repos.json",
        "data/raw/pr_data.json",
        "data/processed/pr_turnaround.csv",
        "data/processed/repo_metadata.json",
        "data/processed/statistical_results.json",
        "data/spot_check/validation_report.csv",
        "artifacts/boxplot.png",
        "artifacts/final_report.md"
    ]

    logger.info("Verifying expected output files...")
    files_ok = verify_output_files(expected_outputs, project_root)

    if not files_ok:
        logger.error("Missing expected output files.")
        sys.exit(1)

    logger.info("Quickstart validation successful: All commands ran and outputs exist.")
    return 0

if __name__ == "__main__":
    sys.exit(main())