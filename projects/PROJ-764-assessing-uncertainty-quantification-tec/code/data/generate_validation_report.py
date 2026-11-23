import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Configure project root for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def setup_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
    """Sets up a logger that writes to both file and console."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    fh.setFormatter(formatter)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger

def load_exclusion_log(exclusion_log_path: Path) -> Dict[str, Any]:
    """
    Loads the exclusion log JSON file.
    
    Args:
        exclusion_log_path: Path to the exclusion_log.json file.
        
    Returns:
        Dictionary containing exclusion data.
        
    Raises:
        FileNotFoundError: If the exclusion log file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not exclusion_log_path.exists():
        raise FileNotFoundError(f"Exclusion log not found at {exclusion_log_path}. "
                                "Ensure T006b2 has been executed successfully.")
    
    with open(exclusion_log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Validate schema
    if 'excluded_count' not in data or 'missing_columns' not in data:
        raise ValueError(f"Invalid schema in {exclusion_log_path}. "
                         "Expected 'excluded_count' and 'missing_columns' keys.")
                         
    return data

def generate_validation_report(exclusion_data: Dict[str, Any], output_path: Path) -> Dict[str, Any]:
    """
    Generates the validation report based on exclusion data.
    
    Adheres to FR-010 schema: {"excluded_count": int, "missing_columns": [str]}
    
    Args:
        exclusion_data: The data loaded from the exclusion log.
        output_path: Path where the validation_report.json will be written.
        
    Returns:
        The generated validation report dictionary.
    """
    validation_report = {
        "excluded_count": exclusion_data["excluded_count"],
        "missing_columns": exclusion_data["missing_columns"]
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(validation_report, f, indent=2)
        
    return validation_report

def main():
    """
    Main entry point for generating the validation report.
    Consumes data/processed/exclusion_log.json and writes data/validation_report.json.
    """
    # Define paths relative to project root
    exclusion_log_path = project_root / "data" / "processed" / "exclusion_log.json"
    validation_report_path = project_root / "data" / "validation_report.json"
    log_path = project_root / "logs" / "pipeline.log"
    
    # Ensure logs directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = setup_logger("ValidationReportGenerator", str(log_path))
    logger.info("Starting validation report generation.")
    
    try:
        # Load exclusion log
        logger.info(f"Loading exclusion log from {exclusion_log_path}")
        exclusion_data = load_exclusion_log(exclusion_log_path)
        logger.info(f"Loaded exclusion data: {exclusion_data}")
        
        # Generate report
        logger.info(f"Generating validation report at {validation_report_path}")
        report = generate_validation_report(exclusion_data, validation_report_path)
        
        logger.info(f"Validation report generated successfully.")
        logger.info(f"Excluded count: {report['excluded_count']}")
        logger.info(f"Missing columns: {report['missing_columns']}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in exclusion log: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Schema validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation report generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()