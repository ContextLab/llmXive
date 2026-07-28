import os
import yaml

def main():
    """
    Validates that the contract schemas exist and are valid YAML.
    This script serves as a setup verification for T009.
    """
    contracts_dir = "contracts"
    schemas = [
        "task.schema.yaml",
        "skill.schema.yaml",
        "experiment_log.schema.yaml"
    ]

    if not os.path.exists(contracts_dir):
        print(f"Error: Directory '{contracts_dir}' does not exist.")
        return 1

    for schema_file in schemas:
        path = os.path.join(contracts_dir, schema_file)
        if not os.path.exists(path):
            print(f"Error: Missing schema file: {path}")
            return 1

        try:
            with open(path, 'r') as f:
                content = yaml.safe_load(f)
                if not isinstance(content, dict):
                    print(f"Error: {schema_file} is not a valid YAML object.")
                    return 1
                print(f"Verified: {schema_file} is valid YAML.")
        except yaml.YAMLError as e:
            print(f"Error: {schema_file} has invalid YAML syntax: {e}")
            return 1

    print("All contract schemas validated successfully.")
    return 0

if __name__ == "__main__":
    exit(main())