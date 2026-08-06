import os
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_validation_report(input_path: str, output_path: str) -> dict:
    """
    Generates a validation report by reading the exclusion log and writing
    a formatted report.

    Args:
        input_path: Path to the exclusion log JSON file.
        output_path: Path where the validation report JSON will be written.

    Returns:
        dict: The generated validation report data.

    Raises:
        FileNotFoundError: If the input file does not exist.
        json.JSONDecodeError: If the input file is not valid JSON.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Reading exclusion log from {input_path}")
    with open(input_file, 'r', encoding='utf-8') as f:
        exclusion_data = json.load(f)

    # Validate schema of input data to ensure robustness
    if not isinstance(exclusion_data, dict):
        raise ValueError("Input JSON must be a dictionary.")
    
    required_keys = {'excluded_count', 'missing_columns'}
    if not required_keys.issubset(exclusion_data.keys()):
        missing = required_keys - set(exclusion_data.keys())
        raise ValueError(f"Input JSON missing required keys: {missing}")

    # Construct the validation report
    # The schema is identical to the exclusion log for this task,
    # but we explicitly reconstruct it to ensure type safety and formatting.
    report = {
        "excluded_count": int(exclusion_data["excluded_count"]),
        "missing_columns": list(exclusion_data["missing_columns"])
    }

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing validation report to {output_path}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info("Validation report generated successfully.")
    return report

def main():
    """
    Main entry point for the validation report generator.
    Reads from code/data/../exclusion_log.json and writes to data/validation_report.json.
    """
    # Define paths relative to project root
    # Assuming this script is run from the project root or via python -m
    project_root = Path(__file__).resolve().parent.parent.parent
    
    input_file = project_root / "data" / "processed" / "exclusion_log.json"
    output_file = project_root / "data" / "validation_report.json"

    try:
        generate_validation_report(str(input_file), str(output_file))
        print(f"Success: Validation report written to {output_file}")
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        print(f"Error: {e}")
        exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON error: {e}")
        print(f"Error: Invalid JSON in input file - {e}")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()