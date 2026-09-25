import argparse
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

def setup_directories(base_path):
    """Ensure required directories exist."""
    processed_dir = base_path / "data" / "processed"
    results_dir = base_path / "results"
    processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir, results_dir

def load_dominant_eigenvalue(results_dir):
    """Load the dominant eigenvalue from the filtered data calculation."""
    eigenvalue_path = results_dir / "dominant_eigenvalue.json"
    if not eigenvalue_path.exists():
        raise FileNotFoundError(f"Required file not found: {eigenvalue_path}")
    
    with open(eigenvalue_path, 'r') as f:
        data = json.load(f)
    return data

def load_covariance_matrix(results_dir):
    """Load the global covariance matrix from the filtered data calculation."""
    matrix_path = results_dir / "covariance_matrix.json"
    if not matrix_path.exists():
        raise FileNotFoundError(f"Required file not found: {matrix_path}")
    
    with open(matrix_path, 'r') as f:
        data = json.load(f)
    return data

def load_dimension_list(base_path):
    """Load the list of dimension names from the dataset schema or a config."""
    # Attempt to load from a standard location if it exists, otherwise default
    schema_path = base_path / "specs" / "001-llmxive-follow-up-extending-beyond-scala" / "contracts" / "dataset.schema.yaml"
    if schema_path.exists():
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        # Assuming schema has a 'columns' or similar structure defining dimensions
        # Based on task T001d description, we expect 4 rubric dimensions.
        # If the schema defines them, use them; else default to generic names.
        if 'columns' in schema:
            # Filter for dimension columns if possible, or just take the first 4 relevant ones
            dims = [col['name'] for col in schema['columns'] if 'dimension' in col.get('name', '').lower()]
            if len(dims) >= 4:
                return dims[:4]
    return ["rubric_1", "rubric_2", "rubric_3", "rubric_4"]

def generate_entanglement_report(eigenvalue_data, matrix_data, dimension_list):
    """Assemble the global entanglement report."""
    report = {
        "covariance_matrix": matrix_data.get("matrix", matrix_data),
        "dominant_eigenvalue": eigenvalue_data.get("dominant_eigenvalue", eigenvalue_data),
        "computation_source": "filtered_data",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dimension_list": dimension_list
    }
    return report

def save_report(report, processed_dir):
    """Save the report to the processed directory."""
    output_path = processed_dir / "global_entanglement_report.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logging.info(f"Global entanglement report saved to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Generate Global Entanglement Report")
    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path("."),
        help="Base path of the project (default: current directory)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()
    logger.info("Starting Global Entanglement Report generation...")

    processed_dir, results_dir = setup_directories(args.base_path)

    try:
        # Load dependencies
        eigenvalue_data = load_dominant_eigenvalue(results_dir)
        matrix_data = load_covariance_matrix(results_dir)
        dimension_list = load_dimension_list(args.base_path)

        # Generate report
        report = generate_entanglement_report(eigenvalue_data, matrix_data, dimension_list)

        # Save report
        save_report(report, processed_dir)

        logger.info("Global Entanglement Report generation completed successfully.")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
