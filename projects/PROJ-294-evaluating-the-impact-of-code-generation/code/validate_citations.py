"""
Citation Validation Gate (T006)
Implements a wrapper to invoke the external Reference-Validator Agent.

This script validates the `state/citations.yaml` file against the required schema
(list of objects with `id`, `url`, `title`) and invokes the external Reference-Validator
Agent. It raises SystemExit(1) on any validation failure or agent error.
"""
import os
import sys
import logging
import yaml
import subprocess
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def validate_citations(input_path: str, output_path: str) -> bool:
    """
    Validates citations using the external Reference-Validator Agent.
    
    Args:
        input_path: Path to the citations YAML file
        output_path: Path to write the validation report
        
    Returns:
        True if validation passes, False otherwise
    """
    logger.info(f"Validating citations from: {input_path}")
    
    # Check if input file exists
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return False
    
    # Load and validate input schema
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML input: {e}")
        return False
    
    # Handle schema flexibility: support both direct list and nested 'citations' key
    if isinstance(data, dict):
        if 'citations' in data:
            citations_list = data['citations']
            logger.info("Detected nested 'citations' key in YAML.")
        else:
            logger.error(f"Input is a dictionary but missing required 'citations' key. Keys found: {list(data.keys())}")
            return False
    elif isinstance(data, list):
        citations_list = data
    else:
        logger.error(f"Expected state/citations.yaml to contain a list or a dict with 'citations' key, got {type(data)}")
        return False
    
    if not isinstance(citations_list, list):
        logger.error(f"Expected 'citations' to be a list, got {type(citations_list)}")
        return False

    # Validate schema: must be a list of objects with id, url, title
    required_keys = {'id', 'url', 'title'}
    valid_count = 0
    for i, item in enumerate(citations_list):
        if not isinstance(item, dict):
            logger.error(f"Item {i} in citations list is not a dictionary")
            return False
        missing_keys = required_keys - set(item.keys())
        if missing_keys:
            logger.error(f"Item {i} missing required keys: {missing_keys}")
            return False
        valid_count += 1
    
    logger.info(f"Found {valid_count} valid citations. Invoking Reference-Validator Agent...")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Construct command to invoke the external agent
    # The agent is installed via T005b and should provide a CLI entry point
    # Fallback to 'reference-validate' if the module entry point fails
    cmd_module = [
        sys.executable, "-m", "reference_validator.cli",
        "--input", input_path,
        "--output", output_path
    ]
    cmd_cli = [
        "reference-validate",
        "--input", input_path,
        "--output", output_path
    ]
    
    result = None
    agent_error = None
    
    # Try module first
    try:
        result = subprocess.run(
            cmd_module,
            check=True,
            capture_output=True,
            text=True,
            timeout=60
        )
    except subprocess.CalledProcessError as e:
        agent_error = f"Module invocation failed with exit code {e.returncode}. Stderr: {e.stderr}"
        logger.warning(f"Module invocation failed: {agent_error}")
    except FileNotFoundError:
        logger.warning("Module reference_validator.cli not found, trying CLI entry point...")
    except subprocess.TimeoutExpired:
        agent_error = "Module invocation timed out."
        logger.warning(agent_error)
    
    # If module failed, try CLI entry point
    if result is None:
        try:
            result = subprocess.run(
                cmd_cli,
                check=True,
                capture_output=True,
                text=True,
                timeout=60
            )
        except subprocess.CalledProcessError as e:
            agent_error = f"CLI invocation failed with exit code {e.returncode}. Stderr: {e.stderr}"
            logger.error(agent_error)
        except FileNotFoundError:
            agent_error = "Reference-Validator Agent not found (neither module nor CLI). Ensure it is installed (T005b)."
            logger.error(agent_error)
        except subprocess.TimeoutExpired:
            agent_error = "CLI invocation timed out."
            logger.error(agent_error)
    
    if result is not None:
        logger.info("Reference-Validator Agent completed successfully.")
        if result.stdout:
            logger.info(result.stdout)
        # Verify output file was actually created
        if not os.path.exists(output_path):
            logger.error(f"Agent reported success but output file not created: {output_path}")
            return False
        return True
    else:
        # All attempts failed
        logger.critical(agent_error)
        return False

def main():
    """Main entry point for citation validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Citation Validation Gate")
    parser.add_argument(
        "--input",
        type=str,
        default="state/citations.yaml",
        help="Path to input citations YAML file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="state/validation_report.yaml",
        help="Path to write validation report"
    )
    
    args = parser.parse_args()
    
    success = validate_citations(args.input, args.output)
    
    if not success:
        logger.critical("Citation validation failed. Pipeline must abort.")
        sys.exit(1)
    
    logger.info("Citation validation passed. Pipeline may proceed.")
    sys.exit(0)

if __name__ == "__main__":
    main()