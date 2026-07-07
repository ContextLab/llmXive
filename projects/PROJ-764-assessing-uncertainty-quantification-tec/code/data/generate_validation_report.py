import os
import json

def generate_validation_report(input_path: str, output_path: str) -> None:
    """
    Reads the exclusion log from preprocessing and writes a validation report.
    
    Args:
        input_path: Path to data/processed/exclusion_log.json
        output_path: Path to data/validation_report.json
    
    The report adheres to the schema:
    {
        "excluded_count": int,
        "missing_columns": [str]
    }
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r') as f:
        exclusion_data = json.load(f)

    # Validate schema presence to ensure we are reading the correct format
    if "excluded_count" not in exclusion_data:
        raise ValueError("Input JSON missing 'excluded_count' key")
    if "missing_columns" not in exclusion_data:
        raise ValueError("Input JSON missing 'missing_columns' key")

    validation_report = {
        "excluded_count": int(exclusion_data["excluded_count"]),
        "missing_columns": list(exclusion_data["missing_columns"])
    }

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_path, 'w') as f:
        json.dump(validation_report, f, indent=2)

def main():
    """
    Entry point for the validation report generation script.
    Reads from data/processed/exclusion_log.json and writes to data/validation_report.json.
    """
    # Define paths relative to project root
    # Assuming this script is run from the project root or via python code/data/...
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    
    input_file = os.path.join(project_root, "data", "processed", "exclusion_log.json")
    output_file = os.path.join(project_root, "data", "validation_report.json")
    
    print(f"Reading exclusion log from: {input_file}")
    print(f"Writing validation report to: {output_file}")
    
    generate_validation_report(input_file, output_file)
    print("Validation report generated successfully.")

if __name__ == "__main__":
    main()